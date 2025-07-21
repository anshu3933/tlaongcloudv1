#!/usr/bin/env python3
"""
Test non-grounding path to ensure it's hermetically sealed
"""

import os
import asyncio
import json
from src.utils.gemini_client import GeminiClient

async def test_non_grounding():
    """Test non-grounding functionality is isolated and working"""
    
    # Set up environment
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ GEMINI_API_KEY not set")
        return
    
    print("🔧 Testing NON-grounding path (should be hermetically sealed)...")
    
    # Initialize client
    client = GeminiClient()
    
    # Test data with grounding DISABLED
    student_data = {
        "student_name": "Test Student",
        "grade_level": "5",
        "disability_type": "Specific Learning Disability",
        "case_manager_name": "Ms. Test",
        "test_scores": [
            {
                "test_name": "WISC-V",
                "subtest_name": "Verbal Comprehension Index",
                "standard_score": 85,
                "percentile_rank": 16,
                "score_interpretation": "Below Average"
            }
        ]
    }
    
    template_data = {
        "name": "Test Template",
        "sections": {
            "student_info": "Basic student information",
            "long_term_goal": "Annual academic goals",
            "services": "Special education services"
        }
    }
    
    try:
        print("📝 Testing WITHOUT Google Search grounding (standard path)...")
        
        # Test with grounding DISABLED
        result_no_grounding = await client.generate_iep_content(
            student_data=student_data,
            template_data=template_data,
            enable_google_search_grounding=False  # EXPLICITLY DISABLED
        )
        
        print(f"✅ Generation completed in {result_no_grounding['duration_seconds']:.2f}s")
        print(f"📄 Response size: {len(result_no_grounding['raw_text'])} characters")
        
        # Should NOT have grounding metadata
        if "grounding_metadata" in result_no_grounding:
            print("⚠️ UNEXPECTED: grounding metadata found when grounding disabled")
        else:
            print("✅ No grounding metadata (as expected when disabled)")
        
        # Test parsing the JSON response
        try:
            parsed_response = json.loads(result_no_grounding['raw_text'])
            print("✅ JSON parsing successful")
            
            # Check that grounding_metadata is NOT in the content
            if "grounding_metadata" in parsed_response:
                print("⚠️ UNEXPECTED: grounding_metadata in non-grounded response content")
            else:
                print("✅ No grounding_metadata in non-grounded response content (as expected)")
            
            # Check schema compliance
            required_sections = ["student_info", "long_term_goal", "services"]
            for section in required_sections:
                if section in parsed_response:
                    print(f"✅ Found required section: {section}")
                else:
                    print(f"⚠️ Missing required section: {section}")
                    
            # Check for extra fields that might indicate grounding contamination
            extra_fields = []
            for section_name, section_data in parsed_response.items():
                if isinstance(section_data, dict):
                    for field_name in section_data.keys():
                        if field_name in ["current", "goals"] and section_name in ["concept", "math", "reading", "writing"]:
                            extra_fields.append(f"{section_name}.{field_name}")
            
            if extra_fields:
                print(f"📋 Extra fields generated (from grounding): {extra_fields}")
            else:
                print("✅ No extra grounding fields in standard response")
                
        except json.JSONDecodeError as e:
            print(f"❌ JSON parsing failed: {e}")
            print(f"🔍 Raw response sample: {result_no_grounding['raw_text'][:500]}...")
        
        print("\n🎉 Non-grounding path test completed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_non_grounding())