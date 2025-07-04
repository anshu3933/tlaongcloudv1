#!/usr/bin/env python3
"""
Integration test for Response Flattener with actual API
Tests the flattener in the context of the running service
"""

import sys
import os
import json
import requests
import time
from datetime import datetime

# Test configuration
BASE_URL = "http://localhost:8005"
TEST_TIMEOUT = 30

def test_flattener_health_endpoint():
    """Test the flattener health endpoint"""
    print("🔍 Testing flattener health endpoint...")
    
    try:
        response = requests.get(f"{BASE_URL}/api/v1/ieps/advanced/health/flattener", timeout=TEST_TIMEOUT)
        
        if response.status_code == 200:
            health_data = response.json()
            print(f"✅ Flattener health check passed")
            print(f"   Status: {health_data.get('status')}")
            print(f"   Statistics: {health_data.get('statistics')}")
            return True
        else:
            print(f"❌ Health check failed with status {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Health check request failed: {e}")
        return False

def test_api_with_flattener():
    """Test actual API endpoint with flattener"""
    print("🧪 Testing API with flattener integration...")
    
    # First, get a list of students to use for testing
    try:
        students_response = requests.get(f"{BASE_URL}/api/v1/students", timeout=TEST_TIMEOUT)
        if students_response.status_code != 200:
            print(f"❌ Failed to get students: {students_response.status_code}")
            return False
        
        students_data = students_response.json()
        if not students_data.get('items'):
            print("❌ No students available for testing")
            return False
        
        student_id = students_data['items'][0]['id']
        print(f"   Using student ID: {student_id}")
        
        # Get templates
        templates_response = requests.get(f"{BASE_URL}/api/v1/templates", timeout=TEST_TIMEOUT)
        if templates_response.status_code != 200:
            print(f"❌ Failed to get templates: {templates_response.status_code}")
            return False
        
        templates_data = templates_response.json()
        if not templates_data.get('items'):
            print("❌ No templates available for testing")
            return False
        
        template_id = templates_data['items'][0]['id']
        print(f"   Using template ID: {template_id}")
        
        # Create test IEP data with complex structures that would cause [object Object] errors
        test_iep_data = {
            "student_id": student_id,
            "template_id": template_id,
            "academic_year": "2025-2026",
            "content": {
                "student_name": "Flattener Test Student",
                "grade_level": "7th",
                "case_manager_name": "Test Case Manager",
                "assessment_summary": {
                    "current_achievement": "Test student data for flattener validation",
                    "strengths": ["Problem solving", "Verbal communication"],
                    "areas_for_growth": ["Reading comprehension", "Written expression"],
                    "learning_profile": {
                        "learning_style": "Visual-kinesthetic",
                        "processing_speed": "Average"
                    }
                }
            },
            "meeting_date": "2025-01-15",
            "effective_date": "2025-01-15", 
            "review_date": "2026-01-15"
        }
        
        # Make API call to create IEP with RAG
        print("   Creating IEP with RAG...")
        start_time = time.time()
        
        create_response = requests.post(
            f"{BASE_URL}/api/v1/ieps/advanced/create-with-rag?current_user_id=1&current_user_role=teacher",
            json=test_iep_data,
            timeout=300  # 5 minute timeout for RAG generation
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        if create_response.status_code == 200:
            iep_data = create_response.json()
            
            # Check for [object Object] errors
            response_str = json.dumps(iep_data)
            has_object_errors = "[object Object]" in response_str or "object Object" in response_str
            
            if has_object_errors:
                print(f"❌ [object Object] errors found in response!")
                print(f"   Response length: {len(response_str)} characters")
                return False
            else:
                print(f"✅ No [object Object] errors found")
                print(f"   Response generated in {duration:.2f} seconds")
                print(f"   Response length: {len(response_str)} characters")
                
                # Check if content sections are properly flattened
                content = iep_data.get('content', {})
                
                # Check services (likely to be complex)
                if 'services' in content:
                    services_type = type(content['services']).__name__
                    print(f"   Services type: {services_type}")
                    if services_type != 'str':
                        print(f"   ⚠️  Services not flattened to string (type: {services_type})")
                
                # Check present_levels
                if 'present_levels' in content:
                    pl_type = type(content['present_levels']).__name__
                    print(f"   Present levels type: {pl_type}")
                
                # Check for transformation metadata
                if '_transformation_metadata' in iep_data:
                    metadata = iep_data['_transformation_metadata']
                    print(f"   Transformation metadata present: {metadata.get('transformation_summary', {}).get('total_transformed', 0)} structures flattened")
                
                return True
        else:
            print(f"❌ IEP creation failed with status {create_response.status_code}")
            print(f"   Response: {create_response.text[:500]}...")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ API request failed: {e}")
        return False

def test_service_availability():
    """Test that the service is running and accessible"""
    print("🔗 Testing service availability...")
    
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=TEST_TIMEOUT)
        
        if response.status_code == 200:
            print("✅ Service is running and accessible")
            return True
        else:
            print(f"❌ Service health check failed: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Service is not accessible: {e}")
        print(f"   Make sure the service is running on {BASE_URL}")
        return False

def run_integration_tests():
    """Run all integration tests"""
    print("🚀 Starting Response Flattener Integration Tests")
    print("=" * 60)
    print(f"Testing against: {BASE_URL}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()
    
    tests = [
        ("Service Availability", test_service_availability),
        ("Flattener Health Endpoint", test_flattener_health_endpoint),
        ("API with Flattener", test_api_with_flattener)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"Running: {test_name}")
        try:
            result = test_func()
            results.append((test_name, result))
            print(f"{'✅ PASSED' if result else '❌ FAILED'}: {test_name}")
        except Exception as e:
            print(f"💥 ERROR in {test_name}: {e}")
            results.append((test_name, False))
        print()
    
    # Summary
    print("=" * 60)
    print("📊 Integration Test Summary")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print(f"Tests passed: {passed}/{total}")
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status}: {test_name}")
    
    if passed == total:
        print("\n🎉 All integration tests passed!")
        print("The response flattener is working correctly with the API.")
    else:
        print(f"\n❌ {total - passed} test(s) failed.")
        print("Check the service logs and ensure all dependencies are running.")
    
    return passed == total

if __name__ == "__main__":
    success = run_integration_tests()
    sys.exit(0 if success else 1)