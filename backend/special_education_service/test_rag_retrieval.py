#!/usr/bin/env python3
"""Test RAG retrieval functionality with populated vector store"""

import asyncio
import sys
import os
import logging

# Add project paths - following the same pattern as start_test_service.py
from pathlib import Path
project_root = Path(__file__).parent.parent  # Points to /Users/anshu/Documents/GitHub/tlaongcloudv1/backend/
sys.path.insert(0, str(project_root))
sys.path.append('/Users/anshu/Documents/GitHub/tlaongcloudv1/backend/special_education_service')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_rag_retrieval():
    """Test RAG retrieval functionality"""
    
    # Set required environment variables (like start_test_service.py does)
    os.environ.update({
        "ENVIRONMENT": "development",
        "DATABASE_URL": "sqlite+aiosqlite:///./test_special_ed.db",
        "JWT_SECRET_KEY": "test_secret_key_for_development_only",
        "GCP_PROJECT_ID": "thela002",
        "GCS_BUCKET_NAME": "betrag-data-test-a",
        "GEMINI_MODEL": "gemini-2.5-flash"
    })
    
    try:
        # Import dependencies
        from common.src.vector_store import VectorStore
        from src.rag.iep_generator import IEPGenerator
        from common.src.config import get_settings
        
        # Initialize components  
        settings = get_settings()
        vector_store = VectorStore(
            project_id=getattr(settings, 'gcp_project_id', 'default-project'),
            collection_name="rag_documents"
        )
        iep_generator = IEPGenerator(vector_store=vector_store, settings=settings)
        
        logger.info("✅ Components initialized successfully")
        
        # Test vector store has content
        logger.info("🔍 Testing vector store content...")
        test_query_embedding = [0.1] * 384  # Simple test embedding
        basic_results = vector_store.search(query_embedding=test_query_embedding, top_k=5)
        logger.info(f"📊 Vector store contains {len(basic_results)} retrievable documents")
        
        if len(basic_results) == 0:
            logger.error("❌ Vector store appears to be empty - RAG will not work")
            return False
            
        # Test RAG retrieval with realistic queries
        test_queries = [
            "IEP for SLD grade 6",
            "IEP for autism grade 5", 
            "reading goals for learning disability",
            "math accommodations for special education",
            "present levels of performance"
        ]
        
        logger.info("🎯 Testing RAG retrieval with realistic queries...")
        
        for i, query in enumerate(test_queries, 1):
            logger.info(f"🔍 Test {i}/5: '{query}'")
            
            try:
                # Use the same method as IEP generator
                similar_ieps = await iep_generator._retrieve_similar_ieps(query, top_k=3)
                logger.info(f"   📊 Retrieved {len(similar_ieps)} similar IEPs")
                
                if similar_ieps:
                    # Show first result metadata
                    first_result = similar_ieps[0]
                    if isinstance(first_result, dict):
                        content_preview = str(first_result.get('content', ''))[:150]
                        logger.info(f"   📄 Sample content: {content_preview}...")
                    else:
                        logger.info(f"   📄 Result type: {type(first_result)}")
                else:
                    logger.warning(f"   ⚠️ No results for query: '{query}'")
                    
            except Exception as e:
                logger.error(f"   ❌ Error retrieving for '{query}': {e}")
        
        # Test context preparation
        logger.info("🔧 Testing context preparation...")
        
        sample_template = {
            "sections": {
                "student_info": "Student Information",
                "present_levels": "Present Levels of Performance", 
                "goals": "Annual Goals"
            }
        }
        
        sample_student_data = {
            "student_name": "Test Student",
            "disability_type": ["SLD"],
            "grade_level": "6",
            "current_achievement": "Reading at 5th grade level",
            "strengths": "Good verbal skills, motivated learner",
            "areas_for_growth": "Reading comprehension, math facts"
        }
        
        try:
            # Test similar IEP retrieval
            query = f"IEP for {sample_student_data.get('disability_type', ['SLD'])} grade {sample_student_data.get('grade_level', '6')}"
            similar_ieps = await iep_generator._retrieve_similar_ieps(query)
            
            # Test context preparation
            context = iep_generator._prepare_context(
                template=sample_template,
                student_data=sample_student_data,
                previous_ieps=[],
                previous_assessments=[],
                similar_ieps=similar_ieps
            )
            
            logger.info(f"✅ Context prepared successfully")
            logger.info(f"   📊 Context keys: {list(context.keys())}")
            logger.info(f"   📄 Similar examples length: {len(context.get('similar_examples', ''))}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error in context preparation: {e}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Fatal error in RAG testing: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main test function"""
    logger.info("🚀 Starting RAG retrieval testing...")
    
    success = await test_rag_retrieval()
    
    if success:
        logger.info("✅ RAG retrieval testing completed successfully")
        logger.info("🎉 RAG system is ready for improved IEP generation!")
    else:
        logger.error("❌ RAG retrieval testing failed")
        logger.error("🔧 Please check vector store and dependencies")
    
    return success

if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)