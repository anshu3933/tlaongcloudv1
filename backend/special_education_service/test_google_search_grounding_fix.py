#!/usr/bin/env python3
"""
Test script to verify Google Search grounding is working correctly
"""

import os
import asyncio
import json
from src.utils.gemini_client import GeminiClient

async def test_grounding():
    """Test Google Search grounding functionality"""
    
    # Set up environment
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ GEMINI_API_KEY not set")
        return
    
    print("🔧 Testing Google Search grounding implementation...")
    
    # Initialize client
    client = GeminiClient()
    
    # Test data with grounding enabled
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
        print("🌐 Testing WITH Google Search grounding...")
        
        # Test with grounding enabled
        result_with_grounding = await client.generate_iep_content(
            student_data=student_data,
            template_data=template_data,
            enable_google_search_grounding=True
        )
        
        print(f"✅ Generation completed in {result_with_grounding['duration_seconds']:.2f}s")
        print(f"📄 Response size: {len(result_with_grounding['raw_text'])} characters")
        
        # Check for grounding metadata
        if "grounding_metadata" in result_with_grounding:
            gm = result_with_grounding["grounding_metadata"]
            print(f"🌐 Grounding metadata found!")
            print(f"   - Search queries: {len(gm.get('web_search_queries', []))}")
            print(f"   - Sources found: {len(gm.get('grounding_chunks', []))}")
            print(f"   - Grounding supports: {len(gm.get('grounding_supports', []))}")
            
            # Print first few search queries
            queries = gm.get('web_search_queries', [])
            if queries:
                print(f"   - Sample queries: {queries[:3]}")
                
            # Print first few sources
            chunks = gm.get('grounding_chunks', [])
            if chunks:
                print(f"   - Sample sources: {[chunk.get('title', 'Unknown') for chunk in chunks[:3]]}")
                
        else:
            print("⚠️ No grounding metadata found in response")
        
        # Test parsing the JSON response
        try:
            parsed_response = json.loads(result_with_grounding['raw_text'])
            print(f"✅ JSON parsing successful")
            
            # Check if grounding_metadata is in the actual response content
            if "grounding_metadata" in parsed_response:
                print("🎯 Grounding metadata found in generated IEP JSON!")
                gm_content = parsed_response["grounding_metadata"]
                print(f"   - LLM reported Google Search used: {gm_content.get('google_search_used', False)}")
                print(f"   - LLM reported search queries: {len(gm_content.get('search_queries_performed', []))}")
                print(f"   - LLM reported improvements: {len(gm_content.get('evidence_based_improvements', []))}")
            else:
                print("⚠️ No grounding_metadata in generated IEP content (LLM didn't include it)")
                
        except json.JSONDecodeError as e:
            print(f"❌ JSON parsing failed: {e}")
        
        print("\n" + "="*60 + "\n")
        
        print("🔄 Testing WITHOUT Google Search grounding...")
        
        # Test without grounding for comparison
        result_without_grounding = await client.generate_iep_content(
            student_data=student_data,
            template_data=template_data,
            enable_google_search_grounding=False
        )
        
        print(f"✅ Generation completed in {result_without_grounding['duration_seconds']:.2f}s")
        print(f"📄 Response size: {len(result_without_grounding['raw_text'])} characters")
        
        if "grounding_metadata" in result_without_grounding:
            print("⚠️ Unexpected: grounding metadata found when grounding disabled")
        else:
            print("✅ No grounding metadata (as expected when disabled)")
            
        # Parse non-grounded response
        try:
            parsed_no_grounding = json.loads(result_without_grounding['raw_text'])
            if "grounding_metadata" in parsed_no_grounding:
                print("⚠️ Unexpected: grounding_metadata in non-grounded response")
            else:
                print("✅ No grounding_metadata in non-grounded response (as expected)")
        except json.JSONDecodeError as e:
            print(f"❌ JSON parsing failed: {e}")
            
        print("\n🎉 Google Search grounding test completed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_grounding())