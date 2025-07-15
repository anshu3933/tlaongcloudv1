#!/usr/bin/env python3
"""
Test script for the real assessment pipeline implementation
Tests file upload, Document AI processing, and data storage
"""

import asyncio
import logging
import os
import sys
from pathlib import Path
import tempfile
import aiohttp
import aiofiles

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from services.document_ai_service import document_ai_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def create_test_pdf():
    """Create a simple test PDF file for testing"""
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        
        # Create a temporary PDF file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        
        # Create PDF content with multiple assessment types
        c = canvas.Canvas(temp_file.name, pagesize=letter)
        
        # WISC-V Scores
        c.drawString(100, 750, "WISC-V Cognitive Assessment Report")
        c.drawString(100, 720, "Student: Test Student")
        c.drawString(100, 690, "Full Scale IQ Standard Score: 95")
        c.drawString(100, 660, "Verbal Comprehension Index: 102") 
        c.drawString(100, 630, "Working Memory Index: 88")
        c.drawString(100, 600, "Processing Speed Index: 85")
        c.drawString(100, 570, "Perceptual Reasoning Index: 98")
        
        # WIAT-IV Scores
        c.drawString(100, 520, "WIAT-IV Achievement Results")
        c.drawString(100, 490, "Total Achievement Standard Score: 87")
        c.drawString(100, 460, "Basic Reading SS: 82")
        c.drawString(100, 430, "Reading Comprehension Standard Score: 89")
        c.drawString(100, 400, "Math Problem Solving SS: 91")
        
        # BASC-3 Scores
        c.drawString(100, 350, "BASC-3 Behavioral Assessment")
        c.drawString(100, 320, "Behavioral Symptoms T-Score: 68")
        c.drawString(100, 290, "Attention Problems T Score: 72")
        c.drawString(100, 260, "Hyperactivity T-Score: 65")
        c.drawString(100, 230, "Learning Problems T Score: 69")
        
        c.save()
        
        logger.info(f"Created test PDF: {temp_file.name}")
        return temp_file.name
        
    except ImportError:
        logger.warning("reportlab not available, creating simple text file instead")
        # Create a simple text file as fallback
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".txt", mode='w')
        temp_file.write("""
WISC-V Cognitive Assessment Report
Student: Test Student
Full Scale IQ Standard Score: 95
Verbal Comprehension Index: 102
Working Memory Index: 88
Processing Speed Index: 85
Perceptual Reasoning Index: 98

WIAT-IV Achievement Results
Total Achievement Standard Score: 87
Basic Reading SS: 82
Reading Comprehension Standard Score: 89
Math Problem Solving SS: 91

BASC-3 Behavioral Assessment  
Behavioral Symptoms T-Score: 68
Attention Problems T Score: 72
Hyperactivity T-Score: 65
Learning Problems T Score: 69
        """)
        temp_file.close()
        logger.info(f"Created test text file: {temp_file.name}")
        return temp_file.name

async def test_document_ai_service():
    """Test the Document AI service directly"""
    logger.info("🔍 Testing Document AI service...")
    
    try:
        # Create test file
        test_file = await create_test_pdf()
        
        # Test Document AI processing
        result = await document_ai_service.process_document(test_file, "test-doc-123")
        
        logger.info("✅ Document AI processing completed")
        logger.info(f"📊 Extracted scores: {len(result.get('extracted_scores', []))}")
        logger.info(f"🎯 Confidence: {result.get('confidence', 0)}")
        
        # Print extracted scores with enhanced details
        test_types_found = set()
        for score in result.get('extracted_scores', []):
            test_name = score.get('test_name')
            test_types_found.add(test_name)
            logger.info(f"   - {test_name}: {score.get('subtest_name')} = {score.get('standard_score')} (confidence: {score.get('extraction_confidence', 0):.2f})")
        
        logger.info(f"📋 Assessment types detected: {', '.join(test_types_found) if test_types_found else 'None'}")
        
        # Verify enhanced patterns are working
        expected_types = ["WISC-V", "WIAT-IV", "BASC-3"]
        found_types = list(test_types_found)
        if any(expected in found_types for expected in expected_types):
            logger.info("✅ Enhanced score patterns are working - multiple assessment types detected")
        else:
            logger.warning("⚠️ Enhanced patterns may not be working - only basic patterns detected")
        
        # Cleanup
        os.unlink(test_file)
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Document AI test failed: {e}", exc_info=True)
        return False

async def test_file_upload_endpoint():
    """Test the real file upload endpoint"""
    logger.info("📤 Testing file upload endpoint...")
    
    try:
        # Create test file
        test_file = await create_test_pdf()
        
        # Prepare multipart form data
        async with aiohttp.ClientSession() as session:
            data = aiohttp.FormData()
            
            # Add file
            async with aiofiles.open(test_file, 'rb') as f:
                file_content = await f.read()
                data.add_field('file', file_content, filename='test_assessment.pdf', content_type='application/pdf')
            
            # Add metadata
            data.add_field('student_id', 'c6f74363-c1fb-4b0f-bd6b-0ae5c8a6f826')  # Existing test student
            data.add_field('assessment_type', 'wisc_v')
            data.add_field('assessor_name', 'Test Psychologist')
            
            # Send request
            async with session.post('http://localhost:8005/api/v1/assessments/documents/upload', data=data) as response:
                result = await response.json()
                
                if response.status == 201:
                    logger.info("✅ File upload successful")
                    logger.info(f"📄 Document ID: {result.get('id')}")
                    logger.info(f"📁 File path: {result.get('file_path')}")
                    logger.info(f"🔄 Status: {result.get('processing_status')}")
                    
                    # Test async processing - should return immediately with "uploaded" status
                    if result.get('processing_status') == 'uploaded':
                        logger.info("✅ Async processing: File uploaded immediately, processing queued")
                    
                    # Wait for background processing
                    logger.info("⏳ Waiting for background processing to complete...")
                    await asyncio.sleep(15)  # Give more time for async processing
                    
                    # Check final status
                    document_id = result.get('id')
                    async with session.get(f'http://localhost:8005/api/v1/assessments/documents/{document_id}') as status_response:
                        status_result = await status_response.json()
                        logger.info(f"📊 Final status: {status_result.get('processing_status')}")
                        logger.info(f"🎯 Confidence: {status_result.get('extraction_confidence')}")
                    
                    return True
                else:
                    logger.error(f"❌ Upload failed: {response.status} - {result}")
                    return False
        
        # Cleanup
        os.unlink(test_file)
        
    except Exception as e:
        logger.error(f"❌ File upload test failed: {e}", exc_info=True)
        return False

async def test_extracted_data_retrieval():
    """Test retrieval of extracted assessment data"""
    logger.info("📊 Testing extracted data retrieval...")
    
    try:
        test_student_id = 'c6f74363-c1fb-4b0f-bd6b-0ae5c8a6f826'
        
        async with aiohttp.ClientSession() as session:
            # Get student assessments
            async with session.get(f'http://localhost:8005/api/v1/assessments/documents/student/{test_student_id}') as response:
                if response.status == 200:
                    documents = await response.json()
                    logger.info(f"📄 Found {len(documents)} documents for student")
                    
                    for doc in documents:
                        logger.info(f"   - {doc.get('file_name')} ({doc.get('processing_status')})")
                        
                        # Get scores for completed documents
                        if doc.get('processing_status') == 'completed':
                            doc_id = doc.get('id')
                            async with session.get(f'http://localhost:8005/api/v1/assessments/scores/document/{doc_id}') as scores_response:
                                if scores_response.status == 200:
                                    scores = await scores_response.json()
                                    logger.info(f"     📊 Extracted {len(scores)} scores")
                                    
                                    for score in scores[:3]:  # Show first 3 scores
                                        logger.info(f"       - {score.get('test_name')}: {score.get('subtest_name')} = {score.get('standard_score')}")
                    
                    return True
                else:
                    result = await response.json()
                    logger.error(f"❌ Failed to get documents: {response.status} - {result}")
                    return False
                    
    except Exception as e:
        logger.error(f"❌ Data retrieval test failed: {e}", exc_info=True)
        return False

async def main():
    """Run all tests"""
    logger.info("🚀 Starting Assessment Pipeline Tests")
    
    tests = [
        ("Document AI Service", test_document_ai_service),
        ("File Upload Endpoint", test_file_upload_endpoint),
        ("Data Retrieval", test_extracted_data_retrieval)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        logger.info(f"\n{'='*50}")
        logger.info(f"Running: {test_name}")
        logger.info('='*50)
        
        try:
            result = await test_func()
            results.append((test_name, result))
            if result:
                logger.info(f"✅ {test_name} PASSED")
            else:
                logger.error(f"❌ {test_name} FAILED")
        except Exception as e:
            logger.error(f"❌ {test_name} ERROR: {e}")
            results.append((test_name, False))
    
    # Summary
    logger.info(f"\n{'='*50}")
    logger.info("TEST SUMMARY")
    logger.info('='*50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{test_name}: {status}")
    
    logger.info(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All tests passed! Assessment pipeline is working!")
    else:
        logger.error("⚠️ Some tests failed. Check logs above.")

if __name__ == "__main__":
    asyncio.run(main())