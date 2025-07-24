#!/usr/bin/env python3
"""
Debug script to understand why grounding_metadata is not in the response
"""

import os
from google import genai
from google.genai import types
import json

def test_grounding_metadata():
    """Test to debug grounding metadata structure"""
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ GEMINI_API_KEY not set")
        return
    
    print("🔍 Debugging grounding metadata structure...")
    print("=" * 60)
    
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
        top_p=0.95,
        top_k=40,
        max_output_tokens=1000
    )
    
    # Simple test query
    print("🌐 Making grounded request...")
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents="What are evidence-based reading interventions for SLD students?",
        config=config,
    )
    
    print("✅ Response received!")
    
    # Debug response structure
    print("\n🔍 Response object structure:")
    print(f"   Type: {type(response)}")
    print(f"   Dir: {[attr for attr in dir(response) if not attr.startswith('_')]}")
    
    # Check for grounding metadata at response level
    print(f"\n   Has grounding_metadata: {hasattr(response, 'grounding_metadata')}")
    print(f"   Has candidates: {hasattr(response, 'candidates')}")
    print(f"   Has text: {hasattr(response, 'text')}")
    
    # Check candidates structure
    if hasattr(response, 'candidates') and response.candidates:
        print(f"\n🔍 Candidates structure:")
        print(f"   Number of candidates: {len(response.candidates)}")
        candidate = response.candidates[0]
        print(f"   Candidate type: {type(candidate)}")
        print(f"   Candidate dir: {[attr for attr in dir(candidate) if not attr.startswith('_')]}")
        print(f"   Candidate has grounding_metadata: {hasattr(candidate, 'grounding_metadata')}")
        
        # Check if grounding metadata is nested
        if hasattr(candidate, 'grounding_metadata'):
            gm = candidate.grounding_metadata
            print(f"\n🌐 Grounding metadata found at candidate level!")
            print(f"   Type: {type(gm)}")
            print(f"   Dir: {[attr for attr in dir(gm) if not attr.startswith('_')]}")
            
            # Try to convert to dict
            try:
                gm_dict = types.to_dict(gm)
                print(f"   As dict: {json.dumps(gm_dict, indent=2)[:500]}...")
            except Exception as e:
                print(f"   Error converting to dict: {e}")
    
    # Check usage metadata
    if hasattr(response, 'usage_metadata'):
        print(f"\n📊 Usage metadata:")
        um = response.usage_metadata
        print(f"   Type: {type(um)}")
        print(f"   Dir: {[attr for attr in dir(um) if not attr.startswith('_')]}")
    
    # Check if there's a to_dict method
    if hasattr(response, 'to_dict'):
        print(f"\n🔍 Response has to_dict method!")
        try:
            response_dict = response.to_dict()
            print(f"   Keys: {list(response_dict.keys())}")
            if 'grounding_metadata' in response_dict:
                print(f"   ✅ grounding_metadata found in to_dict()!")
        except Exception as e:
            print(f"   Error calling to_dict: {e}")
    
    # Try using types.to_dict
    print(f"\n🔍 Using types.to_dict on response:")
    try:
        response_dict = types.to_dict(response)
        print(f"   Keys: {list(response_dict.keys())}")
        if 'grounding_metadata' in response_dict:
            print(f"   ✅ grounding_metadata found via types.to_dict!")
            print(f"   Structure: {json.dumps(response_dict['grounding_metadata'], indent=2)[:500]}...")
    except Exception as e:
        print(f"   Error: {e}")

if __name__ == "__main__":
    test_grounding_metadata()