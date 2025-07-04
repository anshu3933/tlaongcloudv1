#!/usr/bin/env python3
"""Quick test to verify flattener is working"""

import requests
import json

# Test data with known problematic structures
test_data = {
    "student_id": "a5c65e54-29b2-4aaf-a0f2-805049b3169e",
    "template_id": "f4c379bd-3d23-4890-90f9-3fb468b95191",
    "academic_year": "2025-2026",
    "content": {
        "student_name": "Flattener Test",
        "grade_level": "5th",
        "case_manager_name": "Test Manager",
        # This should trigger the flattener
        "services": {
            "services": {
                "special_education": [
                    {"name": "Reading Support", "frequency": "3x per week"}
                ]
            }
        },
        "present_levels": {
            "present_levels": "Student shows good progress"
        },
        "assessment_summary": {
            "reading_level": "Grade 3",
            "strengths": ["Visual learning"],
            "areas_for_growth": ["Reading fluency"]
        }
    },
    "meeting_date": "2025-01-15",
    "effective_date": "2025-01-15",
    "review_date": "2026-01-15"
}

print("🧪 Testing flattener with complex nested structures...")

try:
    response = requests.post(
        "http://localhost:8005/api/v1/ieps/advanced/create-with-rag?current_user_id=1&current_user_role=teacher",
        json=test_data,
        timeout=300
    )
    
    if response.status_code == 200:
        result = response.json()
        
        # Check for [object Object] errors
        response_str = json.dumps(result)
        has_object_errors = "[object Object]" in response_str
        
        print(f"Status: {'❌ FAILED' if has_object_errors else '✅ PASSED'}")
        print(f"Response size: {len(response_str)} characters")
        
        if 'content' in result:
            content = result['content']
            
            # Check each problematic field
            for field in ['services', 'present_levels', 'assessment_summary']:
                if field in content:
                    field_type = type(content[field]).__name__
                    print(f"{field}: {field_type}")
                    
                    if field_type == 'str':
                        print(f"  ✅ {field} properly flattened to string")
                        # Show first 100 chars
                        preview = content[field][:100] + "..." if len(content[field]) > 100 else content[field]
                        print(f"  Preview: {preview}")
                    else:
                        print(f"  ⚠️  {field} not flattened (still {field_type})")
            
            # Check for transformation metadata
            if '_transformation_metadata' in result:
                metadata = result['_transformation_metadata']
                print(f"Transformation metadata found:")
                print(f"  Structures transformed: {metadata.get('transformation_summary', {}).get('total_transformed', 0)}")
                print(f"  Problems detected: {len(metadata.get('problems_detected', []))}")
        
        # Save result for inspection
        with open('/tmp/flattener_test_result.json', 'w') as f:
            json.dump(result, f, indent=2)
        print("Full result saved to /tmp/flattener_test_result.json")
        
    else:
        print(f"❌ API call failed: {response.status_code}")
        print(f"Response: {response.text[:500]}...")

except Exception as e:
    print(f"❌ Test failed with error: {e}")