#!/usr/bin/env python3
"""Test script to verify background task processing is working"""

import asyncio
import tempfile
import os
from pathlib import Path
from uuid import UUID
import time

# Add the src directory to the path so we can import modules
import sys
sys.path.insert(0, str(Path(__file__).parent / "src"))

from routers.assessment_router import process_uploaded_document_background
from database import get_db
from repositories.assessment_repository import AssessmentRepository

async def test_background_task():
    """Test the background task processing"""
    print("🧪 Testing background task processing...")
    
    # Create a temporary PDF file for testing
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
        # Write some dummy PDF content
        tmp_file.write(b"%PDF-1.4\n1 0 obj\n<</Type/Catalog/Pages 2 0 R>>\nendobj\n")
        tmp_file.write(b"2 0 obj\n<</Type/Pages/Kids[3 0 R]/Count 1>>\nendobj\n")
        tmp_file.write(b"3 0 obj\n<</Type/Page/Parent 2 0 R/Contents 4 0 R>>\nendobj\n")
        tmp_file.write(b"4 0 obj\n<</Length 44>>stream\nBT\n/F1 12 Tf\n72 720 Td\n(Test Document) Tj\nET\nendstream\nendobj\n")
        tmp_file.write(b"xref\n0 5\n0000000000 65535 f \n0000000009 00000 n \n0000000074 00000 n \n0000000120 00000 n \n0000000179 00000 n \n")
        tmp_file.write(b"trailer\n<</Size 5/Root 1 0 R>>\nstartxref\n264\n%%EOF\n")
        tmp_file.flush()
        test_file_path = tmp_file.name
    
    try:
        print(f"📁 Created test file: {test_file_path}")
        print(f"📊 File size: {os.path.getsize(test_file_path)} bytes")
        
        # Create a test document in the database first
        print("📄 Creating test document record...")
        
        async for db in get_db():
            assessment_repo = AssessmentRepository(db)
            
            # Create a test document
            document_data = {
                "student_id": "550e8400-e29b-41d4-a716-446655440000",  # UUID format
                "document_type": "psychoeducational",
                "file_name": "test_document.pdf",
                "file_path": test_file_path,
                "processing_status": "uploaded"
            }
            
            created_document = await assessment_repo.create_assessment_document(document_data)
            document_id = created_document["id"]
            print(f"✅ Test document created with ID: {document_id}")
            
            # Test the background task processing
            print("🚀 Testing background task processing...")
            start_time = time.time()
            
            try:
                # This is the fixed background task function
                await process_uploaded_document_background(document_id, test_file_path)
                
                processing_time = time.time() - start_time
                print(f"✅ Background task completed in {processing_time:.2f}s")
                
                # Check the final document status
                final_document = await assessment_repo.get_assessment_document(UUID(document_id))
                if final_document:
                    print(f"📊 Final document status: {final_document['processing_status']}")
                    print(f"🔍 Extraction confidence: {final_document.get('extraction_confidence', 'N/A')}")
                    print(f"⏱️ Processing duration: {final_document.get('processing_duration', 'N/A')}")
                    
                    if final_document['processing_status'] == 'completed':
                        print("🎉 SUCCESS: Document processing completed successfully!")
                    else:
                        print(f"⚠️ WARNING: Document status is {final_document['processing_status']}")
                        print(f"❌ Error message: {final_document.get('error_message', 'N/A')}")
                        
                else:
                    print("❌ ERROR: Could not retrieve final document status")
                    
            except Exception as e:
                print(f"❌ Background task failed: {e}")
                import traceback
                print(f"Traceback: {traceback.format_exc()}")
                
                # Check document status after failure
                failed_document = await assessment_repo.get_assessment_document(UUID(document_id))
                if failed_document:
                    print(f"📊 Failed document status: {failed_document['processing_status']}")
                    print(f"❌ Error message: {failed_document.get('error_message', 'N/A')}")
            
            break  # Exit after first iteration
            
    finally:
        # Clean up the test file
        try:
            os.unlink(test_file_path)
            print(f"🗑️ Cleaned up test file: {test_file_path}")
        except Exception as e:
            print(f"⚠️ Could not clean up test file: {e}")

if __name__ == "__main__":
    print("🧪 Starting background task test...")
    asyncio.run(test_background_task())
    print("✅ Test completed!")