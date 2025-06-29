#!/usr/bin/env python3
"""Test script to validate the RAG pipeline with real Gemini API"""

import asyncio
import os
import sys
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_gemini_client():
    """Test the Gemini client directly"""
    logger.info("🧪 Testing Gemini Client")
    
    # Set API key
    os.environ["GEMINI_API_KEY"] = "AIzaSyB3lmaSoWXbyNRLKHCEe6cKxRPsTfZ9Q50"
    
    try:
        from src.utils.gemini_client import GeminiClient
        
        client = GeminiClient()
        logger.info("✅ Gemini client initialized successfully")
        
        # Test data
        student_data = {
            "student_id": "test-123",
            "first_name": "John",
            "last_name": "Doe",
            "grade_level": "5",
            "disability_codes": ["SLD"]
        }
        
        template_data = {
            "template_name": "Elementary SLD Template",
            "sections": ["student_info", "present_levels", "goals", "services"]
        }
        
        # Test generation
        logger.info("🚀 Testing IEP content generation...")
        result = await client.generate_iep_content(
            student_data=student_data,
            template_data=template_data
        )
        
        logger.info(f"✅ Generation successful! Request ID: {result['request_id']}")
        logger.info(f"Duration: {result['duration_seconds']:.2f}s")
        logger.info(f"Tokens used: {result['usage']['total_tokens']}")
        logger.info(f"Compressed: {result['compressed']}")
        
        # Check if we have valid JSON
        import json
        raw_text = result['raw_text']
        if result.get('compressed'):
            import gzip
            import base64
            compressed_data = base64.b64decode(raw_text.encode('ascii'))
            raw_text = gzip.decompress(compressed_data).decode('utf-8')
        
        parsed_content = json.loads(raw_text)
        logger.info(f"✅ Valid JSON response with keys: {list(parsed_content.keys())}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Gemini client test failed: {e}")
        return False

async def test_async_job_service():
    """Test the async job service"""
    logger.info("🧪 Testing Async Job Service")
    
    try:
        from src.database import get_async_session
        from src.services.async_job_service import AsyncJobService, IEPGenerationRequest
        
        async for session in get_async_session():
            try:
                service = AsyncJobService(session)
                logger.info("✅ AsyncJobService initialized successfully")
                
                # Test job submission
                request = IEPGenerationRequest(
                    student_id="a5c65e54-29b2-4aaf-a0f2-805049b3169e",
                    template_id="f4c379bd-3d23-4890-90f9-3fb468b95191",
                    academic_year="2025-2026",
                    include_previous_ieps=True,
                    include_assessments=True,
                    priority=8
                )
                
                job_id = await service.submit_iep_generation_job(
                    request=request,
                    created_by_auth_id="test-user"
                )
                
                logger.info(f"✅ Job submitted successfully: {job_id}")
                
                # Check job status
                status = await service.get_job_status(job_id)
                logger.info(f"✅ Job status: {status.status} - {status.status_message}")
                
                return True
                
            except Exception as e:
                await session.rollback()
                logger.error(f"❌ Async job service test failed: {e}")
                return False
            finally:
                await session.close()
                
    except Exception as e:
        logger.error(f"❌ Async job service setup failed: {e}")
        return False

async def test_worker_initialization():
    """Test worker initialization"""
    logger.info("🧪 Testing Worker Initialization")
    
    try:
        from src.workers.sqlite_async_worker import SQLiteAsyncWorker
        
        worker = SQLiteAsyncWorker(worker_id="test-worker", poll_interval=5)
        logger.info("✅ Worker initialized successfully")
        
        # Test that worker can access required services
        logger.info("✅ Worker can be created without errors")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Worker initialization failed: {e}")
        return False

async def test_rag_integration():
    """Test the complete RAG integration"""
    logger.info("🧪 Testing Complete RAG Integration")
    
    try:
        # Set environment
        os.environ.setdefault("ENVIRONMENT", "development")
        os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./special_ed.db")
        
        from src.database import get_async_session
        from src.repositories.iep_repository import IEPRepository
        from src.repositories.pl_repository import PLRepository
        from src.services.iep_service import IEPService
        from src.rag.iep_generator import IEPGenerator
        from common.src.vector_store import VectorStore
        from common.src.config import get_settings
        from uuid import UUID
        
        settings = get_settings()
        
        # Initialize vector store
        vector_store = VectorStore(
            project_id=getattr(settings, 'gcp_project_id', 'default-project'),
            collection_name="rag_documents"
        )
        logger.info("✅ Vector store initialized")
        
        async for session in get_async_session():
            try:
                # Initialize repositories
                iep_repo = IEPRepository(session)
                pl_repo = PLRepository(session)
                
                # Initialize IEP generator
                iep_generator = IEPGenerator(
                    vector_store=vector_store,
                    project_id=getattr(settings, 'gcp_project_id', 'default-project'),
                    bucket_name=getattr(settings, 'gcs_bucket_name', 'default-bucket'),
                    model_name=getattr(settings, 'gemini_model', 'gemini-1.5-pro')
                )
                logger.info("✅ IEP generator initialized")
                
                # Initialize IEP service
                iep_service = IEPService(
                    repository=iep_repo,
                    pl_repository=pl_repo,
                    vector_store=vector_store,
                    iep_generator=iep_generator,
                    workflow_client=None,
                    audit_client=None
                )
                logger.info("✅ IEP service initialized")
                
                # Test RAG generation
                student_uuid = UUID("a5c65e54-29b2-4aaf-a0f2-805049b3169e")
                template_uuid = UUID("f4c379bd-3d23-4890-90f9-3fb468b95191")
                
                initial_data = {
                    "content": {
                        "assessment_summary": "Student demonstrates strong visual learning abilities"
                    },
                    "meeting_date": "2025-01-15",
                    "effective_date": "2025-01-15", 
                    "review_date": "2026-01-15"
                }
                
                logger.info("🚀 Starting RAG IEP generation...")
                created_iep = await iep_service.create_iep_with_rag(
                    student_id=student_uuid,
                    template_id=template_uuid,
                    academic_year="2025-2026",
                    initial_data=initial_data,
                    user_id=1,
                    user_role="test"
                )
                
                logger.info(f"✅ RAG IEP generation completed!")
                logger.info(f"IEP ID: {created_iep.get('id', 'N/A')}")
                logger.info(f"Status: {created_iep.get('status', 'N/A')}")
                logger.info(f"AI Generated: {created_iep.get('content', {}).get('ai_generated', False)}")
                
                return True
                
            except Exception as e:
                await session.rollback()
                logger.error(f"❌ RAG integration test failed: {e}")
                return False
            finally:
                await session.close()
                
    except Exception as e:
        logger.error(f"❌ RAG integration setup failed: {e}")
        return False

async def main():
    """Run all tests"""
    logger.info("🚀 Starting RAG Pipeline Validation Tests")
    logger.info("=" * 60)
    
    tests = [
        ("Gemini Client", test_gemini_client),
        ("Async Job Service", test_async_job_service),
        ("Worker Initialization", test_worker_initialization),
        ("Complete RAG Integration", test_rag_integration)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        logger.info(f"\n{'=' * 20} {test_name} {'=' * 20}")
        try:
            result = await test_func()
            results[test_name] = result
            if result:
                logger.info(f"✅ {test_name}: PASSED")
            else:
                logger.info(f"❌ {test_name}: FAILED")
        except Exception as e:
            logger.error(f"💥 {test_name}: CRASHED - {e}")
            results[test_name] = False
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("📊 TEST RESULTS SUMMARY")
    logger.info("=" * 60)
    
    passed = sum(1 for r in results.values() if r)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        logger.info(f"{test_name}: {status}")
    
    logger.info("-" * 60)
    logger.info(f"Total: {total} | Passed: {passed} | Failed: {total - passed}")
    
    if passed == total:
        logger.info("🎉 ALL TESTS PASSED!")
        return True
    else:
        logger.error(f"💥 {total - passed} TESTS FAILED")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)