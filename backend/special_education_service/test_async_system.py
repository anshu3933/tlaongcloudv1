"""Test script for the complete async IEP generation system"""

import asyncio
import json
import logging
import sys
import os
from pathlib import Path
from datetime import datetime
from uuid import uuid4

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.database import get_async_session, init_db
from src.services.async_job_service import AsyncJobService, IEPGenerationRequest
from src.workers.sqlite_async_worker import SQLiteAsyncWorker
from src.repositories.student_repository import StudentRepository
from src.repositories.template_repository import TemplateRepository

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def setup_test_data():
    """Set up test student and template data"""
    async for session in get_async_session():
        try:
            student_repo = StudentRepository(session)
            template_repo = TemplateRepository(session)
            
            # Create test student
            test_student_data = {
                'first_name': 'Test',
                'last_name': 'Student',
                'date_of_birth': '2015-01-01',
                'grade_level': '5',
                'disability_codes': ['SLD'],
                'school_district': 'Test District',
                'school_name': 'Test Elementary'
            }
            
            student = await student_repo.create(test_student_data, created_by_auth_id="test-user")
            logger.info(f"Created test student: {student.id}")
            
            # Get an existing template or create one
            templates = await template_repo.get_all(limit=1)
            if templates.items:
                template = templates.items[0]
                logger.info(f"Using existing template: {template.id}")
            else:
                logger.warning("No templates found - system may not be fully initialized")
                template = None
            
            return student.id, template.id if template else None
            
        except Exception as e:
            await session.rollback()
            logger.error(f"Error setting up test data: {e}")
            raise
        finally:
            await session.close()


async def test_job_submission():
    """Test job submission and status checking"""
    logger.info("=== Testing Job Submission ===")
    
    try:
        # Set up test data
        student_id, template_id = await setup_test_data()
        
        async for session in get_async_session():
            try:
                service = AsyncJobService(session)
                
                # Submit IEP generation job
                request = IEPGenerationRequest(
                    student_id=str(student_id),
                    template_id=str(template_id) if template_id else None,
                    academic_year="2025-2026",
                    include_previous_ieps=True,
                    include_assessments=True,
                    priority=8
                )
                
                job_id = await service.submit_iep_generation_job(
                    request=request,
                    created_by_auth_id="test-user"
                )
                
                logger.info(f"✅ Successfully submitted job: {job_id}")
                
                # Check initial status
                status = await service.get_job_status(job_id)
                logger.info(f"✅ Job status: {status.status} - {status.status_message}")
                
                # Test queue stats
                stats = await service.get_queue_stats()
                logger.info(f"✅ Queue stats: {stats}")
                
                return job_id
                
            except Exception as e:
                await session.rollback()
                logger.error(f"❌ Job submission failed: {e}")
                raise
            finally:
                await session.close()
                
    except Exception as e:
        logger.error(f"❌ Test setup failed: {e}")
        raise


async def test_worker_processing():
    """Test worker job processing"""
    logger.info("=== Testing Worker Processing ===")
    
    try:
        # Submit a job first
        job_id = await test_job_submission()
        
        # Create and run worker for a short time
        worker = SQLiteAsyncWorker(worker_id="test-worker", poll_interval=2)
        
        # Start worker as background task
        worker_task = asyncio.create_task(worker.start())
        
        # Monitor job progress
        async for session in get_async_session():
            try:
                service = AsyncJobService(session)
                
                # Poll for completion (max 60 seconds)
                for i in range(30):
                    status = await service.get_job_status(job_id)
                    logger.info(f"Job {job_id}: {status.status} ({status.progress_percentage}%) - {status.status_message}")
                    
                    if status.status in ['completed', 'failed', 'cancelled']:
                        break
                    
                    await asyncio.sleep(2)
                
                # Stop worker
                await worker.stop()
                worker_task.cancel()
                
                # Final status check
                final_status = await service.get_job_status(job_id)
                
                if final_status.status == 'completed':
                    logger.info("✅ Job completed successfully!")
                    logger.info(f"✅ Result keys: {list(final_status.result.keys()) if final_status.result else 'No result'}")
                    return True
                elif final_status.status == 'failed':
                    logger.error(f"❌ Job failed: {final_status.error_details}")
                    return False
                else:
                    logger.warning(f"⚠️ Job status: {final_status.status}")
                    return False
                    
            except Exception as e:
                await session.rollback()
                logger.error(f"❌ Worker test failed: {e}")
                raise
            finally:
                await session.close()
                
    except Exception as e:
        logger.error(f"❌ Worker processing test failed: {e}")
        return False


async def test_error_handling():
    """Test error handling and retry logic"""
    logger.info("=== Testing Error Handling ===")
    
    try:
        async for session in get_async_session():
            try:
                service = AsyncJobService(session)
                
                # Test invalid student ID
                try:
                    request = IEPGenerationRequest(
                        student_id="invalid-uuid",
                        academic_year="2025-2026"
                    )
                    await service.submit_iep_generation_job(request, "test-user")
                    logger.error("❌ Should have failed with invalid student ID")
                    return False
                except Exception as e:
                    logger.info(f"✅ Correctly rejected invalid student ID: {e}")
                
                # Test invalid template ID
                try:
                    request = IEPGenerationRequest(
                        student_id=str(uuid4()),
                        template_id="invalid-uuid",
                        academic_year="2025-2026"
                    )
                    await service.submit_iep_generation_job(request, "test-user")
                    logger.error("❌ Should have failed with invalid template ID")
                    return False
                except Exception as e:
                    logger.info(f"✅ Correctly rejected invalid template ID: {e}")
                
                return True
                
            except Exception as e:
                await session.rollback()
                logger.error(f"❌ Error handling test failed: {e}")
                raise
            finally:
                await session.close()
                
    except Exception as e:
        logger.error(f"❌ Error handling test setup failed: {e}")
        return False


async def test_job_cancellation():
    """Test job cancellation"""
    logger.info("=== Testing Job Cancellation ===")
    
    try:
        # Set up test data
        student_id, template_id = await setup_test_data()
        
        async for session in get_async_session():
            try:
                service = AsyncJobService(session)
                
                # Submit job
                request = IEPGenerationRequest(
                    student_id=str(student_id),
                    template_id=str(template_id) if template_id else None,
                    academic_year="2025-2026",
                    priority=1  # Low priority to stay in queue
                )
                
                job_id = await service.submit_iep_generation_job(request, "test-user")
                logger.info(f"Submitted job for cancellation: {job_id}")
                
                # Cancel job
                success = await service.cancel_job(job_id, "test-user")
                
                if success:
                    logger.info("✅ Job cancelled successfully")
                    
                    # Verify status
                    status = await service.get_job_status(job_id)
                    if status.status == 'cancelled':
                        logger.info("✅ Job status correctly shows cancelled")
                        return True
                    else:
                        logger.error(f"❌ Job status should be cancelled but is: {status.status}")
                        return False
                else:
                    logger.error("❌ Job cancellation failed")
                    return False
                
            except Exception as e:
                await session.rollback()
                logger.error(f"❌ Job cancellation test failed: {e}")
                raise
            finally:
                await session.close()
                
    except Exception as e:
        logger.error(f"❌ Job cancellation test setup failed: {e}")
        return False


async def run_all_tests():
    """Run all tests"""
    logger.info("🚀 Starting Async IEP Generation System Tests")
    logger.info("=" * 60)
    
    # Initialize database
    try:
        await init_db()
        logger.info("✅ Database initialized")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        return False
    
    test_results = {}
    
    # Run tests
    try:
        test_results['job_submission'] = await test_job_submission()
        logger.info("✅ Job submission test completed")
    except Exception as e:
        logger.error(f"❌ Job submission test failed: {e}")
        test_results['job_submission'] = False
    
    try:
        test_results['error_handling'] = await test_error_handling()
        logger.info("✅ Error handling test completed")
    except Exception as e:
        logger.error(f"❌ Error handling test failed: {e}")
        test_results['error_handling'] = False
    
    try:
        test_results['job_cancellation'] = await test_job_cancellation()
        logger.info("✅ Job cancellation test completed")
    except Exception as e:
        logger.error(f"❌ Job cancellation test failed: {e}")
        test_results['job_cancellation'] = False
    
    # Only test worker if Gemini API key is available
    if os.getenv("GEMINI_API_KEY"):
        try:
            test_results['worker_processing'] = await test_worker_processing()
            logger.info("✅ Worker processing test completed")
        except Exception as e:
            logger.error(f"❌ Worker processing test failed: {e}")
            test_results['worker_processing'] = False
    else:
        logger.warning("⚠️ Skipping worker processing test - GEMINI_API_KEY not set")
        test_results['worker_processing'] = 'skipped'
    
    # Print results summary
    logger.info("=" * 60)
    logger.info("🎯 TEST RESULTS SUMMARY")
    logger.info("=" * 60)
    
    passed = 0
    failed = 0
    skipped = 0
    
    for test_name, result in test_results.items():
        if result is True:
            logger.info(f"✅ {test_name}: PASSED")
            passed += 1
        elif result is False:
            logger.info(f"❌ {test_name}: FAILED")
            failed += 1
        else:
            logger.info(f"⚠️ {test_name}: SKIPPED")
            skipped += 1
    
    logger.info("-" * 60)
    logger.info(f"Total: {len(test_results)} | Passed: {passed} | Failed: {failed} | Skipped: {skipped}")
    
    if failed == 0:
        logger.info("🎉 ALL TESTS PASSED!")
        return True
    else:
        logger.error(f"💥 {failed} TESTS FAILED")
        return False


if __name__ == "__main__":
    # Set environment for testing
    os.environ.setdefault("ENVIRONMENT", "development")
    os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./test_special_ed.db")
    
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)