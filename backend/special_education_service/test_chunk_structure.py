#!/usr/bin/env python3
"""
Test to understand the structure of grounding chunks
"""

import os
from google import genai
from google.genai import types
import json

def test_chunk_structure():
    """Test the structure of grounding chunks"""
    
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
        contents="What are evidence-based reading interventions for SLD?",
        config=config,
    )
    
    print("✅ Response received!")
    
    # Get grounding metadata from candidate
    if hasattr(response, 'candidates') and response.candidates:
        candidate = response.candidates[0]
        if hasattr(candidate, 'grounding_metadata') and candidate.grounding_metadata:
            gm = candidate.grounding_metadata
            print("🌐 Grounding metadata found!")
            
            # Get the raw dict
            gm_dict = gm.model_dump()
            
            print(f"\n🔍 Grounding metadata structure:")
            print(f"   Web search queries: {gm_dict.get('web_search_queries', [])}")
            print(f"   Number of chunks: {len(gm_dict.get('grounding_chunks', []))}")
            
            # Examine chunk structure
            chunks = gm_dict.get('grounding_chunks', [])
            if chunks:
                print(f"\n🔍 Examining first chunk:")
                chunk = chunks[0]
                print(f"   Type: {type(chunk)}")
                print(f"   Keys: {list(chunk.keys()) if isinstance(chunk, dict) else 'Not a dict'}")
                
                # Print full chunk structure
                print(f"\n   Full chunk structure:")
                print(json.dumps(chunk, indent=2, default=str)[:1000])
                
                # Check if web is nested differently
                if 'web' in chunk:
                    web = chunk['web']
                    print(f"\n   Web structure:")
                    print(f"   Type: {type(web)}")
                    if isinstance(web, dict):
                        print(f"   Keys: {list(web.keys())}")
                        print(f"   Content: {json.dumps(web, indent=2, default=str)}")

if __name__ == "__main__":
    test_chunk_structure()