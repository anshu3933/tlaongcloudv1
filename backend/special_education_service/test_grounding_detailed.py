#!/usr/bin/env python3
"""
Test Google Search grounding with detailed response analysis
"""
import os
import json
import asyncio
import logging
from src.utils.gemini_client import GeminiClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_grounding_detailed():
    """Test grounding with detailed response examination"""
    
    print("🔍 TESTING GOOGLE SEARCH GROUNDING - DETAILED ANALYSIS")
    print("=" * 80)
    
    # Initialize client
    client = GeminiClient()
    
    # Simple test data
    student_data = {
        'student_name': 'Test Student',
        'date_of_birth': '2015-03-15',
        'disability_type': 'Specific Learning Disability',
        'case_manager_name': 'Test Manager'
    }
    
    template_data = {
        'name': 'Standard IEP Template',
        'sections': ['student_info', 'goals', 'services']
    }
    
    print(f"📊 Student Data: {json.dumps(student_data, indent=2)}")
    print(f"📋 Template Data: {json.dumps(template_data, indent=2)}")
    print("\n" + "="*80)
    
    try:
        print("🌐 Testing WITH Google Search Grounding...")
        result_with_grounding = await client.generate_iep_content(
            student_data=student_data,
            template_data=template_data,
            enable_google_search_grounding=True
        )
        
        print(f"✅ Generation completed in {result_with_grounding['duration_seconds']:.2f}s")
        print(f"📊 Token usage: {result_with_grounding['usage']['total_tokens']}")
        
        # Examine grounding metadata
        if 'grounding_metadata' in result_with_grounding:
            gm = result_with_grounding['grounding_metadata']
            print(f"\n🔍 GROUNDING METADATA FOUND:")
            print(f"  - Web search queries: {len(gm.get('web_search_queries', []))}")
            print(f"  - Grounding chunks: {len(gm.get('grounding_chunks', []))}")
            print(f"  - Grounding supports: {len(gm.get('grounding_supports', []))}")
            
            # Print queries
            queries = gm.get('web_search_queries', [])
            if queries:
                print(f"\n🔍 SEARCH QUERIES PERFORMED:")
                for i, query in enumerate(queries, 1):
                    print(f"  {i}. {query}")
            
            # Print chunks (sources)
            chunks = gm.get('grounding_chunks', [])
            if chunks:
                print(f"\n📚 SOURCES FOUND:")
                for i, chunk in enumerate(chunks, 1):
                    print(f"  {i}. {chunk.get('title', 'No title')} - {chunk.get('uri', 'No URI')}")
            else:
                print(f"\n⚠️ NO SOURCES FOUND - This is the issue!")
            
            # Print supports
            supports = gm.get('grounding_supports', [])
            if supports:
                print(f"\n🎯 GROUNDING SUPPORTS:")
                for i, support in enumerate(supports, 1):
                    print(f"  {i}. {support.get('segment_text', 'No text')[:100]}...")
            else:
                print(f"\n⚠️ NO GROUNDING SUPPORTS FOUND")
                
        else:
            print(f"\n❌ NO GROUNDING METADATA FOUND IN RESPONSE")
        
        # Parse the JSON response to check for google_search_grounding field
        try:
            raw_text = result_with_grounding['raw_text']
            parsed_json = json.loads(raw_text)
            
            if 'google_search_grounding' in parsed_json:
                gsg = parsed_json['google_search_grounding']
                print(f"\n🌐 GOOGLE_SEARCH_GROUNDING FIELD FOUND IN JSON:")
                print(f"  - Type: {type(gsg)}")
                print(f"  - Value: {gsg}")
                
                if gsg is None:
                    print(f"  ❌ ISSUE IDENTIFIED: google_search_grounding is null in JSON response")
                elif isinstance(gsg, dict):
                    print(f"  - Web queries: {len(gsg.get('web_search_queries', []))}")
                    print(f"  - Chunks: {len(gsg.get('grounding_chunks', []))}")
                    print(f"  - Supports: {len(gsg.get('grounding_supports', []))}")
            else:
                print(f"\n❌ NO google_search_grounding FIELD IN JSON RESPONSE")
                print(f"Available keys: {list(parsed_json.keys())}")
                
        except json.JSONDecodeError as e:
            print(f"\n❌ Failed to parse JSON response: {e}")
            print(f"Raw response (first 500 chars): {result_with_grounding['raw_text'][:500]}")
    
    except Exception as e:
        print(f"❌ Grounding test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_grounding_detailed())