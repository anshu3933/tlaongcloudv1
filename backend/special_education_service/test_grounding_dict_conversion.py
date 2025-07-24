#!/usr/bin/env python3
"""
Test proper way to convert grounding metadata to dict
"""

import os
from google import genai
from google.genai import types
import json

def test_dict_conversion():
    """Test proper dict conversion for grounding metadata"""
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ GEMINI_API_KEY not set")
        return
    
    # Configure the client
    client = genai.Client()
    
    # Define the grounding tool
    grounding_tool = types.Tool(
        google_search=types.GoogleSearch()
    )
    
    # Configure generation settings
    config = types.GenerateContentConfig(
        tools=[grounding_tool],
        temperature=0.8,
        max_output_tokens=500
    )
    
    # Simple test query
    print("🌐 Making grounded request...")
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents="What are evidence-based reading interventions?",
        config=config,
    )
    
    print("✅ Response received!")
    
    # Get grounding metadata from candidate
    if hasattr(response, 'candidates') and response.candidates:
        candidate = response.candidates[0]
        if hasattr(candidate, 'grounding_metadata') and candidate.grounding_metadata:
            gm = candidate.grounding_metadata
            print("🌐 Grounding metadata found!")
            
            # Test different conversion methods
            print("\n🔍 Testing conversion methods:")
            
            # Method 1: model_dump()
            if hasattr(gm, 'model_dump'):
                print("\n1. Using model_dump():")
                try:
                    gm_dict = gm.model_dump()
                    print(f"   ✅ Success! Type: {type(gm_dict)}")
                    print(f"   Keys: {list(gm_dict.keys())}")
                    if 'web_search_queries' in gm_dict:
                        print(f"   Web search queries: {gm_dict['web_search_queries']}")
                    if 'grounding_chunks' in gm_dict:
                        print(f"   Grounding chunks: {len(gm_dict['grounding_chunks'])}")
                except Exception as e:
                    print(f"   ❌ Error: {e}")
            
            # Method 2: to_json_dict()
            if hasattr(gm, 'to_json_dict'):
                print("\n2. Using to_json_dict():")
                try:
                    gm_dict = gm.to_json_dict()
                    print(f"   ✅ Success! Type: {type(gm_dict)}")
                    print(f"   Keys: {list(gm_dict.keys())}")
                except Exception as e:
                    print(f"   ❌ Error: {e}")
            
            # Method 3: dict()
            print("\n3. Using dict():")
            try:
                gm_dict = dict(gm)
                print(f"   ✅ Success! Type: {type(gm_dict)}")
                print(f"   Keys: {list(gm_dict.keys())}")
            except Exception as e:
                print(f"   ❌ Error: {e}")
            
            # Method 4: Direct attribute access
            print("\n4. Direct attribute access:")
            try:
                gm_dict = {
                    "web_search_queries": gm.web_search_queries if hasattr(gm, 'web_search_queries') else [],
                    "grounding_chunks": gm.grounding_chunks if hasattr(gm, 'grounding_chunks') else [],
                    "grounding_supports": gm.grounding_supports if hasattr(gm, 'grounding_supports') else [],
                    "search_entry_point": gm.search_entry_point if hasattr(gm, 'search_entry_point') else None,
                }
                print(f"   ✅ Success!")
                print(f"   Web search queries: {gm_dict['web_search_queries']}")
                print(f"   Grounding chunks: {len(gm_dict['grounding_chunks'])}")
                
                # Print sample chunk structure
                if gm_dict['grounding_chunks']:
                    chunk = gm_dict['grounding_chunks'][0]
                    print(f"\n   Sample chunk structure:")
                    if hasattr(chunk, 'model_dump'):
                        print(f"   {json.dumps(chunk.model_dump(), indent=2)[:500]}...")
                    else:
                        print(f"   Type: {type(chunk)}")
                        print(f"   Dir: {[attr for attr in dir(chunk) if not attr.startswith('_')]}")
                        
            except Exception as e:
                print(f"   ❌ Error: {e}")
                import traceback
                traceback.print_exc()

if __name__ == "__main__":
    test_dict_conversion()