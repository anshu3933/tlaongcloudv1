#!/usr/bin/env python3
"""
Comprehensive Assessment Pipeline Testing
Tests the complete flow from frontend simulation to database storage with detailed logging
"""

import asyncio
import logging
import json
import sys
import tempfile
import aiohttp
import aiofiles
from pathlib import Path
import time
from datetime import datetime
from typing import Dict, Any, List

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Configure comprehensive logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(name)s | %(levelname)s | %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(f'pipeline_test_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    ]
)
logger = logging.getLogger(__name__)

class PipelineTestRunner:
    """Comprehensive pipeline testing with detailed logging"""
    
    def __init__(self):
        self.base_url = "http://localhost:8005"
        self.test_student_id = "c6f74363-c1fb-4b0f-bd6b-0ae5c8a6f826"
        self.document_id = None
        self.test_results = {}
        
    async def create_comprehensive_test_document(self) -> str:
        """Create a comprehensive test document with multiple assessment types"""
        logger.info("📄 STEP 1: Creating comprehensive test document")
        
        try:
            from reportlab.pdfgen import canvas
            from reportlab.lib.pagesizes import letter
            
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
            logger.info(f"📁 Creating PDF at: {temp_file.name}")
            
            c = canvas.Canvas(temp_file.name, pagesize=letter)
            
            # Header
            c.setFont("Helvetica-Bold", 16)
            c.drawString(100, 750, "Comprehensive Psychoeducational Assessment Report")
            c.setFont("Helvetica", 12)
            c.drawString(100, 730, f"Student: Test Student | Date: {datetime.now().strftime('%B %d, %Y')}")
            
            # WISC-V Section
            y_pos = 680
            c.setFont("Helvetica-Bold", 14)
            c.drawString(100, y_pos, "WISC-V Cognitive Assessment")
            c.setFont("Helvetica", 12)
            y_pos -= 25
            
            wisc_scores = [
                ("Full Scale IQ Standard Score:", "95"),
                ("Verbal Comprehension Index (VCI):", "102"),
                ("Perceptual Reasoning Index (PRI):", "98"),
                ("Working Memory Index (WMI):", "88"),
                ("Processing Speed Index (PSI):", "85"),
                ("General Ability Index (GAI):", "100")
            ]
            
            for label, score in wisc_scores:
                c.drawString(120, y_pos, f"{label} {score}")
                y_pos -= 18
                
            # WIAT-IV Section  
            y_pos -= 20
            c.setFont("Helvetica-Bold", 14)
            c.drawString(100, y_pos, "WIAT-IV Academic Achievement")
            c.setFont("Helvetica", 12)
            y_pos -= 25
            
            wiat_scores = [
                ("Total Achievement Standard Score:", "87"),
                ("Basic Reading SS:", "82"),
                ("Reading Comprehension Standard Score:", "89"),
                ("Math Problem Solving SS:", "91"),
                ("Written Expression Standard Score:", "84"),
                ("Spelling SS:", "86")
            ]
            
            for label, score in wiat_scores:
                c.drawString(120, y_pos, f"{label} {score}")
                y_pos -= 18
                
            # BASC-3 Section
            y_pos -= 20
            c.setFont("Helvetica-Bold", 14)
            c.drawString(100, y_pos, "BASC-3 Behavioral Assessment")
            c.setFont("Helvetica", 12)
            y_pos -= 25
            
            basc_scores = [
                ("Behavioral Symptoms Index T-Score:", "68"),
                ("Externalizing Problems T Score:", "65"),
                ("Internalizing Problems T-Score:", "58"),
                ("Attention Problems T Score:", "72"),
                ("Hyperactivity T-Score:", "65"),
                ("Learning Problems T Score:", "69"),
                ("Aggression T-Score:", "60")
            ]
            
            for label, score in basc_scores:
                c.drawString(120, y_pos, f"{label} {score}")
                y_pos -= 18
                
            # KTEA-3 Section
            y_pos -= 20
            c.setFont("Helvetica-Bold", 14)
            c.drawString(100, y_pos, "KTEA-3 Academic Skills")
            c.setFont("Helvetica", 12)
            y_pos -= 25
            
            ktea_scores = [
                ("Comprehensive Achievement Standard Score:", "85"),
                ("Reading Composite SS:", "83"),
                ("Math Composite Standard Score:", "88"),
                ("Written Language SS:", "81")
            ]
            
            for label, score in ktea_scores:
                c.drawString(120, y_pos, f"{label} {score}")
                y_pos -= 18
                
            c.save()
            
            logger.info(f"✅ PDF created successfully: {temp_file.name}")
            logger.info(f"📊 Test data includes: WISC-V (6 scores), WIAT-IV (6 scores), BASC-3 (7 scores), KTEA-3 (4 scores)")
            
            return temp_file.name
            
        except ImportError:
            logger.warning("📝 reportlab not available, creating text file fallback")
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".txt", mode='w')
            
            content = f"""
Comprehensive Psychoeducational Assessment Report
Student: Test Student | Date: {datetime.now().strftime('%B %d, %Y')}

WISC-V Cognitive Assessment
Full Scale IQ Standard Score: 95
Verbal Comprehension Index (VCI): 102
Perceptual Reasoning Index (PRI): 98
Working Memory Index (WMI): 88
Processing Speed Index (PSI): 85
General Ability Index (GAI): 100

WIAT-IV Academic Achievement  
Total Achievement Standard Score: 87
Basic Reading SS: 82
Reading Comprehension Standard Score: 89
Math Problem Solving SS: 91
Written Expression Standard Score: 84
Spelling SS: 86

BASC-3 Behavioral Assessment
Behavioral Symptoms Index T-Score: 68
Externalizing Problems T Score: 65
Internalizing Problems T-Score: 58
Attention Problems T Score: 72
Hyperactivity T-Score: 65
Learning Problems T Score: 69
Aggression T-Score: 60

KTEA-3 Academic Skills
Comprehensive Achievement Standard Score: 85
Reading Composite SS: 83
Math Composite Standard Score: 88
Written Language SS: 81
            """
            
            temp_file.write(content)
            temp_file.close()
            
            logger.info(f"✅ Text file created: {temp_file.name}")
            return temp_file.name
    
    async def simulate_frontend_upload(self, file_path: str) -> Dict[str, Any]:
        """Simulate the frontend file upload process"""
        logger.info("🌐 STEP 2: Simulating frontend file upload")
        
        start_time = time.time()
        
        try:
            async with aiohttp.ClientSession() as session:
                logger.info(f"📤 Preparing multipart form data for: {file_path}")
                
                data = aiohttp.FormData()
                
                # Read file and add to form data
                async with aiofiles.open(file_path, 'rb') as f:
                    file_content = await f.read()
                    logger.info(f"📁 File size: {len(file_content)} bytes")
                    
                data.add_field('file', file_content, 
                             filename='comprehensive_assessment.pdf', 
                             content_type='application/pdf')
                
                # Add metadata (simulating frontend form)
                metadata = {
                    'student_id': self.test_student_id,
                    'assessment_type': 'wisc_v',
                    'assessor_name': 'Dr. Test Psychologist',
                    'assessment_date': datetime.now().isoformat()
                }
                
                for key, value in metadata.items():
                    data.add_field(key, str(value))
                    logger.info(f"📋 Metadata: {key} = {value}")
                
                # Send upload request
                upload_url = f"{self.base_url}/api/v1/assessments/documents/upload"
                logger.info(f"🚀 Sending POST request to: {upload_url}")
                
                async with session.post(upload_url, data=data) as response:
                    upload_time = time.time() - start_time
                    logger.info(f"⏱️ Upload request completed in {upload_time:.2f} seconds")
                    
                    response_text = await response.text()
                    logger.info(f"📡 Response status: {response.status}")
                    logger.info(f"📡 Response headers: {dict(response.headers)}")
                    
                    if response.status == 201:
                        result = json.loads(response_text)
                        self.document_id = result.get('id')
                        
                        logger.info("✅ Upload successful!")
                        logger.info(f"📄 Document ID: {self.document_id}")
                        logger.info(f"📁 Server file path: {result.get('file_path')}")
                        logger.info(f"🔄 Processing status: {result.get('processing_status')}")
                        logger.info(f"📊 Extraction confidence: {result.get('extraction_confidence', 'N/A')}")
                        
                        self.test_results['upload'] = {
                            'success': True,
                            'document_id': self.document_id,
                            'upload_time': upload_time,
                            'status': result.get('processing_status')
                        }
                        
                        return result
                    else:
                        logger.error(f"❌ Upload failed with status {response.status}")
                        logger.error(f"❌ Response: {response_text}")
                        
                        self.test_results['upload'] = {
                            'success': False,
                            'error': f"HTTP {response.status}: {response_text}"
                        }
                        
                        return None
                        
        except Exception as e:
            logger.error(f"❌ Upload exception: {e}", exc_info=True)
            self.test_results['upload'] = {
                'success': False,
                'error': str(e)
            }
            return None
    
    async def monitor_processing_progress(self) -> Dict[str, Any]:
        """Monitor the background processing with detailed logging"""
        logger.info("🔄 STEP 3: Monitoring background processing progress")
        
        if not self.document_id:
            logger.error("❌ No document ID available for monitoring")
            return None
        
        processing_start = time.time()
        check_interval = 2  # seconds
        max_wait_time = 60  # seconds
        
        async with aiohttp.ClientSession() as session:
            while time.time() - processing_start < max_wait_time:
                try:
                    status_url = f"{self.base_url}/api/v1/assessments/documents/{self.document_id}"
                    logger.info(f"📊 Checking status: {status_url}")
                    
                    async with session.get(status_url) as response:
                        if response.status == 200:
                            status_data = await response.json()
                            current_status = status_data.get('processing_status')
                            confidence = status_data.get('extraction_confidence')
                            error_msg = status_data.get('error_message')
                            
                            elapsed = time.time() - processing_start
                            logger.info(f"⏱️ Status check ({elapsed:.1f}s): {current_status}")
                            
                            if confidence is not None:
                                logger.info(f"🎯 Extraction confidence: {confidence}")
                            
                            if error_msg:
                                logger.error(f"❌ Error message: {error_msg}")
                            
                            # Check for completion
                            if current_status == 'completed':
                                total_time = time.time() - processing_start
                                logger.info(f"✅ Processing completed in {total_time:.2f} seconds!")
                                
                                self.test_results['processing'] = {
                                    'success': True,
                                    'final_status': current_status,
                                    'processing_time': total_time,
                                    'confidence': confidence
                                }
                                
                                return status_data
                                
                            elif current_status == 'failed':
                                logger.error(f"❌ Processing failed: {error_msg}")
                                
                                self.test_results['processing'] = {
                                    'success': False,
                                    'final_status': current_status,
                                    'error': error_msg
                                }
                                
                                return status_data
                        else:
                            logger.warning(f"⚠️ Status check failed: {response.status}")
                            
                except Exception as e:
                    logger.error(f"❌ Status check error: {e}")
                
                # Wait before next check
                logger.info(f"⏳ Waiting {check_interval}s before next status check...")
                await asyncio.sleep(check_interval)
            
            # Timeout reached
            logger.error(f"⏰ Processing timeout after {max_wait_time} seconds")
            self.test_results['processing'] = {
                'success': False,
                'error': f"Timeout after {max_wait_time} seconds"
            }
            return None
    
    async def inspect_document_ai_response(self) -> Dict[str, Any]:
        """Inspect the detailed Document AI response"""
        logger.info("🔍 STEP 4: Inspecting Document AI extraction results")
        
        if not self.document_id:
            logger.error("❌ No document ID available for inspection")
            return None
        
        try:
            async with aiohttp.ClientSession() as session:
                # Get extracted data
                extracted_url = f"{self.base_url}/api/v1/assessments/extracted-data/document/{self.document_id}"
                logger.info(f"📊 Fetching extracted data: {extracted_url}")
                
                async with session.get(extracted_url) as response:
                    if response.status == 200:
                        extracted_data = await response.json()
                        
                        logger.info("✅ Document AI extraction data retrieved")
                        logger.info(f"📄 Raw content length: {len(extracted_data.get('raw_content', ''))}")
                        logger.info(f"🔧 Extraction method: {extracted_data.get('extraction_method')}")
                        logger.info(f"🎯 Confidence score: {extracted_data.get('confidence_score')}")
                        
                        # Inspect structured data
                        structured_data = extracted_data.get('structured_data', {})
                        if structured_data:
                            logger.info("📋 Structured data inspection:")
                            
                            # Document AI entities
                            entities = structured_data.get('entities', [])
                            logger.info(f"🏷️ Entities found: {len(entities)}")
                            for i, entity in enumerate(entities[:5]):  # Show first 5
                                logger.info(f"   Entity {i+1}: {entity.get('type')} = '{entity.get('mention_text')}' (confidence: {entity.get('confidence', 0):.2f})")
                            
                            # Tables
                            tables = structured_data.get('tables', [])
                            logger.info(f"📊 Tables found: {len(tables)}")
                            for i, table in enumerate(tables):
                                rows = table.get('rows', [])
                                cols = table.get('column_count', 0)
                                logger.info(f"   Table {i+1}: {len(rows)} rows x {cols} columns")
                            
                            # Extracted scores
                            scores = structured_data.get('extracted_scores', [])
                            logger.info(f"📈 Scores extracted: {len(scores)}")
                            
                            # Group by test type
                            by_test = {}
                            for score in scores:
                                test_name = score.get('test_name', 'Unknown')
                                if test_name not in by_test:
                                    by_test[test_name] = []
                                by_test[test_name].append(score)
                            
                            for test_name, test_scores in by_test.items():
                                logger.info(f"🧪 {test_name}: {len(test_scores)} scores")
                                for score in test_scores[:3]:  # Show first 3 per test
                                    subtest = score.get('subtest_name')
                                    value = score.get('standard_score')
                                    conf = score.get('extraction_confidence', 0)
                                    source = score.get('source', 'unknown')
                                    logger.info(f"     {subtest}: {value} (confidence: {conf:.2f}, source: {source})")
                        
                        self.test_results['document_ai'] = {
                            'success': True,
                            'scores_found': len(structured_data.get('extracted_scores', [])),
                            'entities_found': len(structured_data.get('entities', [])),
                            'tables_found': len(structured_data.get('tables', [])),
                            'test_types': list(by_test.keys()) if 'by_test' in locals() else []
                        }
                        
                        return extracted_data
                    else:
                        error_msg = f"Failed to retrieve extracted data: {response.status}"
                        logger.error(f"❌ {error_msg}")
                        self.test_results['document_ai'] = {
                            'success': False,
                            'error': error_msg
                        }
                        return None
                        
        except Exception as e:
            logger.error(f"❌ Document AI inspection error: {e}", exc_info=True)
            self.test_results['document_ai'] = {
                'success': False,
                'error': str(e)
            }
            return None
    
    async def validate_database_storage(self) -> Dict[str, Any]:
        """Validate that data was properly stored in database"""
        logger.info("💾 STEP 5: Validating database storage")
        
        if not self.document_id:
            logger.error("❌ No document ID available for validation")
            return None
        
        try:
            async with aiohttp.ClientSession() as session:
                # Check document record
                doc_url = f"{self.base_url}/api/v1/assessments/documents/{self.document_id}"
                logger.info(f"📄 Validating document record: {doc_url}")
                
                async with session.get(doc_url) as response:
                    if response.status == 200:
                        doc_data = await response.json()
                        logger.info("✅ Document record found")
                        logger.info(f"📁 File name: {doc_data.get('file_name')}")
                        logger.info(f"📂 File path: {doc_data.get('file_path')}")
                        logger.info(f"🔄 Status: {doc_data.get('processing_status')}")
                        logger.info(f"👤 Student ID: {doc_data.get('student_id')}")
                        logger.info(f"📊 Assessment type: {doc_data.get('document_type')}")
                    else:
                        logger.error(f"❌ Document not found: {response.status}")
                        return None
                
                # Check scores
                scores_url = f"{self.base_url}/api/v1/assessments/scores/document/{self.document_id}"
                logger.info(f"📈 Validating extracted scores: {scores_url}")
                
                async with session.get(scores_url) as response:
                    if response.status == 200:
                        scores_data = await response.json()
                        logger.info(f"✅ Found {len(scores_data)} stored scores")
                        
                        # Group by test type
                        by_test = {}
                        for score in scores_data:
                            test_name = score.get('test_name', 'Unknown')
                            if test_name not in by_test:
                                by_test[test_name] = 0
                            by_test[test_name] += 1
                        
                        for test_name, count in by_test.items():
                            logger.info(f"📊 {test_name}: {count} scores stored")
                        
                        # Show sample scores
                        logger.info("📈 Sample stored scores:")
                        for i, score in enumerate(scores_data[:5]):
                            test_name = score.get('test_name')
                            subtest = score.get('subtest_name')
                            value = score.get('standard_score')
                            conf = score.get('extraction_confidence')
                            logger.info(f"   {i+1}. {test_name} - {subtest}: {value} (confidence: {conf})")
                    else:
                        logger.warning(f"⚠️ No scores found: {response.status}")
                        scores_data = []
                
                # Check student assessments summary
                student_url = f"{self.base_url}/api/v1/assessments/documents/student/{self.test_student_id}"
                logger.info(f"👤 Validating student assessments: {student_url}")
                
                async with session.get(student_url) as response:
                    if response.status == 200:
                        student_docs = await response.json()
                        logger.info(f"✅ Student has {len(student_docs)} total documents")
                        
                        # Find our document
                        our_doc = None
                        for doc in student_docs:
                            if doc.get('id') == self.document_id:
                                our_doc = doc
                                break
                        
                        if our_doc:
                            logger.info("✅ Our test document found in student records")
                            logger.info(f"📅 Upload date: {our_doc.get('upload_date')}")
                            logger.info(f"🔄 Status: {our_doc.get('processing_status')}")
                        else:
                            logger.error("❌ Test document not found in student records")
                    else:
                        logger.error(f"❌ Student validation failed: {response.status}")
                
                self.test_results['database'] = {
                    'success': True,
                    'document_stored': True,
                    'scores_stored': len(scores_data),
                    'test_types_stored': list(by_test.keys()) if 'by_test' in locals() else []
                }
                
                return {
                    'document': doc_data,
                    'scores': scores_data,
                    'student_docs': student_docs if 'student_docs' in locals() else []
                }
                
        except Exception as e:
            logger.error(f"❌ Database validation error: {e}", exc_info=True)
            self.test_results['database'] = {
                'success': False,
                'error': str(e)
            }
            return None
    
    async def generate_test_report(self):
        """Generate comprehensive test report"""
        logger.info("📋 STEP 6: Generating comprehensive test report")
        
        print("\n" + "="*80)
        print("🧪 COMPREHENSIVE ASSESSMENT PIPELINE TEST REPORT")
        print("="*80)
        
        # Summary
        total_steps = len(self.test_results)
        successful_steps = sum(1 for result in self.test_results.values() if result.get('success', False))
        
        print(f"\n📊 OVERALL RESULTS: {successful_steps}/{total_steps} steps successful")
        
        # Detailed results
        for step_name, result in self.test_results.items():
            status = "✅ PASSED" if result.get('success', False) else "❌ FAILED"
            print(f"\n{step_name.upper()}: {status}")
            
            if result.get('success', False):
                if step_name == 'upload':
                    print(f"  ⏱️ Upload time: {result.get('upload_time', 0):.2f}s")
                    print(f"  📄 Document ID: {result.get('document_id')}")
                elif step_name == 'processing':
                    print(f"  ⏱️ Processing time: {result.get('processing_time', 0):.2f}s")
                    print(f"  🎯 Confidence: {result.get('confidence', 0)}")
                elif step_name == 'document_ai':
                    print(f"  📈 Scores found: {result.get('scores_found', 0)}")
                    print(f"  🧪 Test types: {', '.join(result.get('test_types', []))}")
                    print(f"  📊 Tables found: {result.get('tables_found', 0)}")
                elif step_name == 'database':
                    print(f"  💾 Scores stored: {result.get('scores_stored', 0)}")
                    print(f"  🧪 Test types stored: {', '.join(result.get('test_types_stored', []))}")
            else:
                print(f"  ❌ Error: {result.get('error', 'Unknown error')}")
        
        # Performance metrics
        if 'upload' in self.test_results and 'processing' in self.test_results:
            upload_time = self.test_results['upload'].get('upload_time', 0)
            processing_time = self.test_results['processing'].get('processing_time', 0)
            total_time = upload_time + processing_time
            
            print(f"\n⏱️ PERFORMANCE METRICS:")
            print(f"  📤 Upload time: {upload_time:.2f}s")
            print(f"  🔄 Processing time: {processing_time:.2f}s")
            print(f"  🕐 Total pipeline time: {total_time:.2f}s")
        
        # Feature validation
        if 'document_ai' in self.test_results and self.test_results['document_ai'].get('success'):
            test_types = self.test_results['document_ai'].get('test_types', [])
            expected_types = ['WISC-V', 'WIAT-IV', 'BASC-3', 'KTEA-3']
            found_expected = [t for t in expected_types if t in test_types]
            
            print(f"\n🧪 FEATURE VALIDATION:")
            print(f"  📋 Expected assessment types: {', '.join(expected_types)}")
            print(f"  ✅ Found assessment types: {', '.join(found_expected)}")
            print(f"  📊 Coverage: {len(found_expected)}/{len(expected_types)} ({len(found_expected)/len(expected_types)*100:.0f}%)")
        
        print("\n" + "="*80)
        
        if successful_steps == total_steps:
            print("🎉 ALL TESTS PASSED! Assessment pipeline is fully functional.")
        else:
            print(f"⚠️ {total_steps - successful_steps} test(s) failed. Review logs above.")
        
        print("="*80)
    
    async def run_comprehensive_test(self):
        """Run the complete comprehensive test suite"""
        logger.info("🚀 Starting comprehensive assessment pipeline test")
        
        try:
            # Step 1: Create test document
            test_file = await self.create_comprehensive_test_document()
            
            # Step 2: Simulate frontend upload
            upload_result = await self.simulate_frontend_upload(test_file)
            if not upload_result:
                logger.error("❌ Upload failed, stopping test")
                await self.generate_test_report()
                return
            
            # Step 3: Monitor processing
            processing_result = await self.monitor_processing_progress()
            if not processing_result:
                logger.warning("⚠️ Processing monitoring failed or timed out")
            
            # Step 4: Inspect Document AI response
            ai_result = await self.inspect_document_ai_response()
            
            # Step 5: Validate database storage
            db_result = await self.validate_database_storage()
            
            # Step 6: Generate report
            await self.generate_test_report()
            
            # Cleanup
            import os
            try:
                os.unlink(test_file)
                logger.info(f"🗑️ Cleaned up test file: {test_file}")
            except:
                pass
                
        except Exception as e:
            logger.error(f"❌ Comprehensive test failed: {e}", exc_info=True)

async def main():
    """Main test runner"""
    print("🧪 Assessment Pipeline Comprehensive Testing")
    print("=" * 50)
    
    runner = PipelineTestRunner()
    await runner.run_comprehensive_test()

if __name__ == "__main__":
    asyncio.run(main())