#!/usr/bin/env python3
"""
Test grounding path with the fixed schema
"""

import os
import asyncio
import json
from src.utils.gemini_client import GeminiClient

async def test_grounding_fixed():
    """Test grounding functionality with flexible schema"""
    
    # Set up environment
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ GEMINI_API_KEY not set")
        return
    
    print("🔧 Testing Google Search grounding with flexible schema...")
    
    # Initialize client
    client = GeminiClient()
    
    # Test data with grounding ENABLED
    student_data = {
        "student_name": "Akio Tanaka",
        "grade_level": "5",
        "disability_type": "Specific Learning Disability",
        "case_manager_name": "Ms. Johnson",
        "test_scores": [
            {
                "test_name": "WISC-V",
                "subtest_name": "Verbal Comprehension Index",
                "standard_score": 88,
                "percentile_rank": 21,
                "score_interpretation": "Low Average"
            }
        ]
    }
    
    template_data = {
        "name": "Comprehensive Academic Areas IEP Template",
        "sections": {
            "student_info": "Basic student information",
            "long_term_goal": "Annual academic goals",
            "services": "Special education services"
        }
    }
    
    try:
        print("🌐 Testing WITH Google Search grounding...")
        
        # Test with grounding ENABLED
        result_with_grounding = await client.generate_iep_content(
            student_data=student_data,
            template_data=template_data,
            enable_google_search_grounding=True  # ENABLED
        )
        
        print(f"✅ Generation completed in {result_with_grounding['duration_seconds']:.2f}s")
        print(f"📄 Response size: {len(result_with_grounding['raw_text'])} characters")
        
        # Check for grounding metadata in response
        if "grounding_metadata" in result_with_grounding:
            gm = result_with_grounding["grounding_metadata"]
            print("🌐 Backend grounding metadata found!")
            print(f"   - Search queries: {len(gm.get('web_search_queries', []))}")
            print(f"   - Sources: {len(gm.get('grounding_chunks', []))}")
        else:
            print("⚠️ No backend grounding metadata found")
        
        # Test parsing the JSON response
        try:
            parsed_response = json.loads(result_with_grounding['raw_text'])
            print("✅ JSON parsing successful with grounding!")
            
            # Check if grounding_metadata is in the LLM response
            if "grounding_metadata" in parsed_response:
                gm_content = parsed_response["grounding_metadata"]
                print("🎯 LLM grounding metadata found in generated content!")
                print(f"   - Google Search used: {gm_content.get('google_search_used', False)}")
                print(f"   - Search queries reported: {len(gm_content.get('search_queries_performed', []))}")
                print(f"   - Improvements reported: {len(gm_content.get('evidence_based_improvements', []))}")
            else:
                print("ℹ️ No LLM grounding metadata in generated content (may not be required)")
            
            # Check for rich grounding fields
            rich_fields = []
            for section_name, section_data in parsed_response.items():
                if isinstance(section_data, dict):
                    for field_name in section_data.keys():
                        if field_name in ["current", "goals"] and section_name in ["concept", "math", "reading", "writing", "spelling"]:
                            rich_fields.append(f"{section_name}.{field_name}")
            
            if rich_fields:
                print(f"📋 Rich grounding fields captured: {rich_fields}")
                
                # Show sample content from rich fields
                for field_path in rich_fields[:3]:  # Show first 3
                    section, field = field_path.split('.')
                    content = parsed_response[section][field]
                    print(f"   📝 {field_path}: {content[:100]}...")
            else:
                print("⚠️ No rich grounding fields found")
                
        except json.JSONDecodeError as e:
            print(f"❌ JSON parsing failed: {e}")
            print(f"🔍 Raw response sample: {result_with_grounding['raw_text'][:500]}...")
        
        print("\n🎉 Grounding path test completed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_grounding_fixed())