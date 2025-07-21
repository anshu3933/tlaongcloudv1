#!/usr/bin/env python3
"""
Simple test for Google Search grounding
"""

import os
from google import genai
from google.genai import types

def test_simple_grounding():
    """Test basic Google Search grounding"""
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ GEMINI_API_KEY not set")
        return
    
    print("🔧 Testing basic Google Search grounding...")
    
    try:
        # Configure the client
        client = genai.Client()
        
        # Define the grounding tool
        grounding_tool = types.Tool(
            google_search=types.GoogleSearch()
        )
        
        # Configure generation settings
        config = types.GenerateContentConfig(
            tools=[grounding_tool]
        )
        
        # Simple test query
        print("🌐 Making grounded request...")
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents="What are the latest evidence-based reading interventions for students with specific learning disabilities in 2024-2025?",
            config=config,
        )
        
        print("✅ Response received!")
        print(f"📄 Response text: {response.text[:200]}...")
        
        # Check for grounding metadata
        if hasattr(response, 'candidates') and response.candidates:
            candidate = response.candidates[0]
            if hasattr(candidate, 'grounding_metadata') and candidate.grounding_metadata:
                gm = candidate.grounding_metadata
                print("🌐 Grounding metadata found!")
                
                if hasattr(gm, 'web_search_queries'):
                    print(f"   - Search queries: {gm.web_search_queries}")
                    
                if hasattr(gm, 'grounding_chunks'):
                    print(f"   - Sources found: {len(gm.grounding_chunks)}")
                    for i, chunk in enumerate(gm.grounding_chunks[:3]):
                        if hasattr(chunk, 'web'):
                            print(f"     {i+1}. {chunk.web.title} - {chunk.web.uri}")
            else:
                print("⚠️ No grounding metadata in response")
        else:
            print("⚠️ No candidates in response")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_simple_grounding()