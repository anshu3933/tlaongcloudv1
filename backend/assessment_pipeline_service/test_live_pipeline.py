#!/usr/bin/env python3
"""
Live End-to-End Assessment Pipeline Testing
Tests the actual running services with full input/output logging
"""

import asyncio
import json
import logging
import sys
import requests
from datetime import datetime, date
from typing import Dict, Any, List
import traceback

# Configure comprehensive logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('live_pipeline_test.log')
    ]
)
logger = logging.getLogger(__name__)

class LiveAssessmentPipelineTester:
    """Test the live assessment pipeline services"""
    
    def __init__(self):
        self.base_url_special_ed = "http://localhost:8005"
        self.base_url_assessment = "http://localhost:8006"
        self.session = requests.Session()
        self.session.headers.update({'Content-Type': 'application/json'})
        
        # Test data storage
        self.test_data = {}
        self.results = {}
        
    def log_api_call(self, method: str, url: str, payload: Dict = None, response: requests.Response = None):
        """Log API call details"""
        logger.info(f"🌐 API CALL: {method} {url}")
        if payload:
            logger.info(f"📤 REQUEST PAYLOAD ({len(json.dumps(payload))} chars):")
            logger.info(json.dumps(payload, indent=2)[:1000] + "..." if len(json.dumps(payload)) > 1000 else json.dumps(payload, indent=2))
        
        if response:
            logger.info(f"📥 RESPONSE STATUS: {response.status_code}")
            logger.info(f"📥 RESPONSE HEADERS: {dict(response.headers)}")
            try:
                response_data = response.json()
                logger.info(f"📥 RESPONSE BODY ({len(json.dumps(response_data))} chars):")
                logger.info(json.dumps(response_data, indent=2)[:2000] + "..." if len(json.dumps(response_data)) > 2000 else json.dumps(response_data, indent=2))
            except:
                logger.info(f"📥 RESPONSE BODY (text): {response.text[:1000]}...")

    def test_service_health(self):
        """Test health of both services"""
        logger.info("🏥 Testing Service Health...")
        
        # Test special education service
        try:
            url = f"{self.base_url_special_ed}/health"
            response = self.session.get(url)
            self.log_api_call("GET", url, response=response)
            
            if response.status_code == 200:
                logger.info("✅ Special Education Service: HEALTHY")
                self.results['special_ed_health'] = 'healthy'
            else:
                logger.warning(f"⚠️ Special Education Service: {response.status_code}")
                self.results['special_ed_health'] = 'unhealthy'
        except Exception as e:
            logger.error(f"❌ Special Education Service health check failed: {e}")
            self.results['special_ed_health'] = 'error'
        
        # Test assessment pipeline service
        try:
            url = f"{self.base_url_assessment}/health"
            response = self.session.get(url)
            self.log_api_call("GET", url, response=response)
            
            if response.status_code == 200:
                logger.info("✅ Assessment Pipeline Service: HEALTHY")
                self.results['assessment_health'] = 'healthy'
            else:
                logger.warning(f"⚠️ Assessment Pipeline Service: {response.status_code}")
                self.results['assessment_health'] = 'unhealthy'
        except Exception as e:
            logger.error(f"❌ Assessment Pipeline Service health check failed: {e}")
            self.results['assessment_health'] = 'error'

    def get_test_student(self) -> Dict[str, Any]:
        """Get a test student for the pipeline"""
        logger.info("👤 Getting test student...")
        
        url = f"{self.base_url_special_ed}/api/v1/students"
        response = self.session.get(url)
        self.log_api_call("GET", url, response=response)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('items'):
                student = data['items'][0]
                logger.info(f"✅ Using student: {student['first_name']} {student['last_name']} (ID: {student['id']})")
                self.test_data['student'] = student
                return student
        
        logger.error("❌ No test student available")
        raise Exception("No test student found")

    def get_test_template(self) -> Dict[str, Any]:
        """Get a test template for IEP generation"""
        logger.info("📋 Getting test template...")
        
        url = f"{self.base_url_special_ed}/api/v1/templates"
        response = self.session.get(url)
        self.log_api_call("GET", url, response=response)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('items'):
                template = data['items'][0]
                logger.info(f"✅ Using template: {template['name']} (ID: {template['id']})")
                self.test_data['template'] = template
                return template
        
        logger.error("❌ No test template available")
        raise Exception("No test template found")

    def create_sample_assessment_data(self) -> Dict[str, Any]:
        """Create comprehensive sample assessment data for RAG input"""
        logger.info("📝 Creating sample assessment data...")
        
        assessment_data = {
            "student_name": self.test_data['student']['first_name'] + " " + self.test_data['student']['last_name'],
            "grade_level": "5",
            "case_manager_name": "Dr. Sarah Johnson",
            "assessment_summary": {
                "current_achievement": "Student demonstrates significant challenges in reading comprehension and written expression. Current reading level is approximately 2.5 grade levels below peers.",
                "strengths": [
                    "Strong visual-spatial processing abilities",
                    "Excellent mathematical reasoning skills",
                    "Good social interaction with peers",
                    "Demonstrates persistence when provided appropriate support"
                ],
                "areas_for_growth": [
                    "Reading fluency and comprehension",
                    "Written expression and organization",
                    "Working memory for multi-step tasks",
                    "Attention and focus during academic tasks"
                ],
                "learning_profile": "Student is a visual learner who benefits from graphic organizers, visual supports, and hands-on activities. Learns best in small group settings with frequent breaks.",
                "interests": [
                    "Art and drawing",
                    "Building with blocks/Legos", 
                    "Animals and nature",
                    "Technology and computers"
                ]
            },
            "cognitive_profile": {
                "verbal_comprehension": 85,
                "visual_spatial": 92,
                "fluid_reasoning": 88,
                "working_memory": 79,
                "processing_speed": 83,
                "full_scale_iq": 84
            },
            "academic_scores": {
                "reading": {
                    "letter_word_identification": 78,
                    "reading_fluency": 82,
                    "passage_comprehension": 75
                },
                "writing": {
                    "spelling": 80,
                    "writing_samples": 77
                },
                "math": {
                    "calculation": 89,
                    "math_facts_fluency": 85,
                    "applied_problems": 91
                }
            },
            "behavioral_profile": {
                "attention_problems": 68,
                "learning_problems": 72,
                "anxiety": 58,
                "social_skills": 52
            },
            "disability_categories": ["SLD"],
            "previous_interventions": [
                "Small group reading instruction",
                "Extended time for assignments",
                "Use of graphic organizers",
                "Frequent check-ins with teacher"
            ]
        }
        
        logger.info("✅ Sample assessment data created")
        logger.info(f"📊 Data includes: {list(assessment_data.keys())}")
        self.test_data['assessment_data'] = assessment_data
        return assessment_data

    def test_rag_iep_generation(self) -> Dict[str, Any]:
        """Test the RAG IEP generation with full logging"""
        logger.info("🤖 Testing RAG IEP Generation...")
        
        student = self.test_data['student']
        template = self.test_data['template'] 
        assessment_data = self.test_data['assessment_data']
        
        # Prepare RAG IEP request
        rag_request = {
            "student_id": student['id'],
            "template_id": template['id'],
            "academic_year": "2024-2025",
            "content": assessment_data,
            "meeting_date": "2025-01-15",
            "effective_date": "2025-01-15", 
            "review_date": "2026-01-15",
            "goals": []
        }
        
        logger.info("🎯 STARTING RAG IEP GENERATION")
        logger.info("=" * 80)
        
        # Log the input to the RAG system
        logger.info("📥 RAG INPUT DATA:")
        logger.info(f"Student ID: {rag_request['student_id']}")
        logger.info(f"Template ID: {rag_request['template_id']}")
        logger.info(f"Academic Year: {rag_request['academic_year']}")
        logger.info(f"Content Keys: {list(rag_request['content'].keys())}")
        logger.info("Assessment Summary:")
        for key, value in rag_request['content']['assessment_summary'].items():
            logger.info(f"  {key}: {value}")
        
        # Make the RAG API call
        url = f"{self.base_url_special_ed}/api/v1/ieps/advanced/create-with-rag"
        params = {
            "current_user_id": 1,
            "current_user_role": "teacher"
        }
        
        logger.info("🚀 CALLING RAG ENDPOINT...")
        start_time = datetime.now()
        
        try:
            response = self.session.post(url, json=rag_request, params=params, timeout=300)
            end_time = datetime.now()
            duration = end_time - start_time
            
            logger.info(f"⏱️ RAG PROCESSING TIME: {duration.total_seconds():.2f} seconds")
            
            self.log_api_call("POST", url, rag_request, response)
            
            if response.status_code == 200:
                rag_result = response.json()
                
                logger.info("🎉 RAG IEP GENERATION SUCCESSFUL!")
                logger.info("=" * 80)
                
                # Log the generated IEP structure
                logger.info("📄 GENERATED IEP STRUCTURE:")
                logger.info(f"IEP ID: {rag_result.get('id', 'N/A')}")
                logger.info(f"Student ID: {rag_result.get('student_id', 'N/A')}")
                logger.info(f"Status: {rag_result.get('status', 'N/A')}")
                logger.info(f"Academic Year: {rag_result.get('academic_year', 'N/A')}")
                
                # Log the content sections
                if 'content' in rag_result:
                    content = rag_result['content']
                    logger.info("📝 GENERATED CONTENT SECTIONS:")
                    for section_name, section_content in content.items():
                        if isinstance(section_content, str):
                            logger.info(f"  {section_name}: {len(section_content)} characters")
                            logger.info(f"    Preview: {section_content[:200]}...")
                        elif isinstance(section_content, dict):
                            logger.info(f"  {section_name}: {list(section_content.keys())}")
                        elif isinstance(section_content, list):
                            logger.info(f"  {section_name}: {len(section_content)} items")
                        else:
                            logger.info(f"  {section_name}: {type(section_content)}")
                
                # Log goals if present
                if 'goals' in rag_result and rag_result['goals']:
                    logger.info("🎯 GENERATED GOALS:")
                    for i, goal in enumerate(rag_result['goals']):
                        logger.info(f"  Goal {i+1}:")
                        logger.info(f"    Domain: {goal.get('domain', 'N/A')}")
                        logger.info(f"    Text: {goal.get('goal_text', 'N/A')[:100]}...")
                        logger.info(f"    Target: {goal.get('target_criteria', 'N/A')}")
                
                # Store results
                self.results['rag_generation'] = {
                    'status': 'success',
                    'duration_seconds': duration.total_seconds(),
                    'content_sections': len(rag_result.get('content', {})),
                    'goals_count': len(rag_result.get('goals', [])),
                    'total_response_size': len(json.dumps(rag_result))
                }
                
                self.test_data['generated_iep'] = rag_result
                return rag_result
                
            else:
                logger.error(f"❌ RAG IEP generation failed with status {response.status_code}")
                logger.error(f"Error response: {response.text}")
                self.results['rag_generation'] = {
                    'status': 'failed',
                    'error': response.text,
                    'status_code': response.status_code
                }
                raise Exception(f"RAG generation failed: {response.status_code}")
                
        except requests.exceptions.Timeout:
            logger.error("❌ RAG IEP generation timed out after 5 minutes")
            self.results['rag_generation'] = {'status': 'timeout'}
            raise
        except Exception as e:
            logger.error(f"❌ RAG IEP generation error: {e}")
            self.results['rag_generation'] = {'status': 'error', 'error': str(e)}
            raise

    def test_generated_iep_retrieval(self):
        """Test retrieving the generated IEP with details"""
        logger.info("🔍 Testing Generated IEP Retrieval...")
        
        if 'generated_iep' not in self.test_data:
            logger.warning("⚠️ No generated IEP to retrieve")
            return
        
        iep_id = self.test_data['generated_iep']['id']
        url = f"{self.base_url_special_ed}/api/v1/ieps/advanced/{iep_id}/with-details"
        params = {
            "include_history": True,
            "include_goals": True
        }
        
        response = self.session.get(url, params=params)
        self.log_api_call("GET", url, response=response)
        
        if response.status_code == 200:
            detailed_iep = response.json()
            logger.info("✅ IEP retrieval successful")
            logger.info(f"📄 Retrieved IEP details: {list(detailed_iep.keys())}")
            self.results['iep_retrieval'] = 'success'
        else:
            logger.error(f"❌ IEP retrieval failed: {response.status_code}")
            self.results['iep_retrieval'] = 'failed'

    def test_flattener_health(self):
        """Test the response flattener health"""
        logger.info("🔧 Testing Response Flattener Health...")
        
        url = f"{self.base_url_special_ed}/api/v1/ieps/advanced/health/flattener"
        response = self.session.get(url)
        self.log_api_call("GET", url, response=response)
        
        if response.status_code == 200:
            flattener_health = response.json()
            logger.info("✅ Response flattener health check successful")
            logger.info(f"🔧 Flattener status: {flattener_health.get('status', 'Unknown')}")
            if 'statistics' in flattener_health:
                stats = flattener_health['statistics']
                logger.info(f"📊 Flattener statistics: {stats}")
            self.results['flattener_health'] = 'success'
        else:
            logger.error(f"❌ Flattener health check failed: {response.status_code}")
            self.results['flattener_health'] = 'failed'

    def run_complete_test(self):
        """Run the complete live pipeline test"""
        logger.info("🚀 STARTING LIVE ASSESSMENT PIPELINE TEST")
        logger.info("=" * 100)
        
        start_time = datetime.now()
        
        try:
            # Step 1: Test service health
            logger.info("\nSTEP 1: Testing Service Health")
            logger.info("-" * 50)
            self.test_service_health()
            
            # Step 2: Get test data
            logger.info("\nSTEP 2: Preparing Test Data")
            logger.info("-" * 50)
            self.get_test_student()
            self.get_test_template()
            self.create_sample_assessment_data()
            
            # Step 3: Test RAG IEP generation (main event!)
            logger.info("\nSTEP 3: RAG IEP Generation (MAIN TEST)")
            logger.info("-" * 50)
            self.test_rag_iep_generation()
            
            # Step 4: Test IEP retrieval
            logger.info("\nSTEP 4: Testing IEP Retrieval")
            logger.info("-" * 50)
            self.test_generated_iep_retrieval()
            
            # Step 5: Test flattener health
            logger.info("\nSTEP 5: Testing Response Flattener")
            logger.info("-" * 50)
            self.test_flattener_health()
            
            # Generate final report
            end_time = datetime.now()
            total_duration = end_time - start_time
            
            logger.info("\n" + "=" * 100)
            logger.info("🎉 LIVE PIPELINE TEST COMPLETED!")
            logger.info("=" * 100)
            
            logger.info(f"📅 Test Start: {start_time}")
            logger.info(f"📅 Test End: {end_time}")
            logger.info(f"⏱️ Total Duration: {total_duration}")
            
            logger.info("\n📊 TEST RESULTS SUMMARY:")
            for test_name, result in self.results.items():
                if isinstance(result, dict):
                    status = result.get('status', 'unknown')
                    logger.info(f"  {test_name}: {status.upper()}")
                    if 'duration_seconds' in result:
                        logger.info(f"    Duration: {result['duration_seconds']:.2f}s")
                    if 'content_sections' in result:
                        logger.info(f"    Content Sections: {result['content_sections']}")
                    if 'total_response_size' in result:
                        logger.info(f"    Response Size: {result['total_response_size']} chars")
                else:
                    logger.info(f"  {test_name}: {result.upper()}")
            
            # Success indicators
            rag_success = self.results.get('rag_generation', {}).get('status') == 'success'
            services_healthy = (self.results.get('special_ed_health') == 'healthy' and 
                              self.results.get('assessment_health') == 'healthy')
            
            if rag_success and services_healthy:
                logger.info("\n🎯 OVERALL TEST STATUS: ✅ SUCCESS")
                logger.info("🚀 Assessment pipeline is FULLY OPERATIONAL!")
            else:
                logger.info("\n🎯 OVERALL TEST STATUS: ⚠️ PARTIAL SUCCESS")
                logger.info("🔧 Some components may need attention")
            
        except Exception as e:
            logger.error(f"❌ Test execution failed: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            
        finally:
            # Save results
            self.save_test_results()

    def save_test_results(self):
        """Save test results to file"""
        try:
            results_file = "live_pipeline_test_results.json"
            
            comprehensive_results = {
                "test_metadata": {
                    "test_date": datetime.now().isoformat(),
                    "test_type": "live_end_to_end_assessment_pipeline",
                    "services_tested": [
                        "special_education_service:8005",
                        "assessment_pipeline_service:8006"
                    ]
                },
                "test_data": self.test_data,
                "results": self.results
            }
            
            with open(results_file, 'w') as f:
                json.dump(comprehensive_results, f, indent=2, default=str)
            
            logger.info(f"📁 Test results saved to {results_file}")
            
        except Exception as e:
            logger.error(f"❌ Failed to save test results: {e}")

def main():
    """Main test execution"""
    try:
        tester = LiveAssessmentPipelineTester()
        tester.run_complete_test()
    except Exception as e:
        logger.error(f"❌ Test execution failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()