#!/usr/bin/env python3
"""Test the sync background task processing directly"""

import asyncio
import logging
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from database import get_engine, async_session_factory
from repositories.assessment_repository import AssessmentRepository
from routers.assessment_router import process_uploaded_document_background_sync

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_sync_background_task():
    """Test the sync background task directly"""
    
    # Get engine for background task
    engine = await get_engine()
    
    # Test document info (use the uploaded document)
    document_id = "9e210eb4-bef9-43a7-8f88-0099484e9292"
    file_path = "uploads/assessments/9e210eb4-bef9-43a7-8f88-0099484e9292.pdf"
    
    logger.info(f"🧪 Testing sync background task for document {document_id}")
    logger.info(f"📁 File path: {file_path}")
    
    # Check if file exists
    if not Path(file_path).exists():
        logger.error(f"❌ File does not exist: {file_path}")
        return False
    
    # Test the sync background task directly
    try:
        logger.info(f"🚀 Starting sync background task test...")
        
        # Call the sync background task function directly
        process_uploaded_document_background_sync(document_id, file_path, engine)
        
        logger.info(f"✅ Sync background task completed successfully")
        
        # Check the document status after processing
        async with async_session_factory() as db:
            assessment_repo = AssessmentRepository(db)
            updated_doc = await assessment_repo.get_assessment_document(document_id)
            
            if updated_doc:
                logger.info(f"📊 Document status after processing: {updated_doc.get('processing_status')}")
                logger.info(f"🎯 Extraction confidence: {updated_doc.get('extraction_confidence')}")
                return True
            else:
                logger.error(f"❌ Could not retrieve document after processing")
                return False
                
    except Exception as e:
        logger.error(f"❌ Sync background task failed: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    result = asyncio.run(test_sync_background_task())
    if result:
        logger.info("🎉 Background task test PASSED")
        sys.exit(0)
    else:
        logger.error("💥 Background task test FAILED")
        sys.exit(1)