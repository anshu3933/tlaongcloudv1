#!/usr/bin/env python3
"""
Direct API test to understand grounding response
"""

import os
from google import genai
from google.genai import types
import json

def test_direct():
    """Direct API test"""
    
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
    
    # Configure generation WITHOUT JSON response (not supported with tools)
    config = types.GenerateContentConfig(
        tools=[grounding_tool],
        temperature=0.8
        # response_mime_type="application/json"  # NOT SUPPORTED with tools!
    )
    
    # Test with JSON response format
    print("🌐 Making grounded request with JSON response...")
    
    prompt = """Generate a simple JSON response with this structure:
{
  "message": "test response",
  "search_performed": true
}

Also search for: evidence-based reading interventions for SLD"""
    
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=config,
    )
    
    print("✅ Response received!")
    print(f"📄 Response text: {response.text}")
    
    # Check grounding metadata
    if hasattr(response, 'candidates') and response.candidates:
        candidate = response.candidates[0]
        if hasattr(candidate, 'grounding_metadata') and candidate.grounding_metadata:
            gm = candidate.grounding_metadata
            gm_dict = gm.model_dump()
            
            print(f"\n🌐 Grounding metadata:")
            print(f"   Queries: {gm_dict.get('web_search_queries', [])}")
            print(f"   Chunks: {len(gm_dict.get('grounding_chunks', []))}")
            
            # Print chunk details
            for i, chunk in enumerate(gm_dict.get('grounding_chunks', [])[:3]):
                if 'web' in chunk:
                    print(f"   Chunk {i+1}: {chunk['web'].get('title', 'No title')} - {chunk['web'].get('uri', '')[:50]}...")

if __name__ == "__main__":
    test_direct()