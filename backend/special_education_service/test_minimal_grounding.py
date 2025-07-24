#!/usr/bin/env python3
"""
Minimal Google Search Grounding Test
Tests grounding in isolation without complex application logic
"""

import os
import sys

def test_minimal_grounding():
    try:
        from google import genai
        from google.genai import types
        print("✅ Successfully imported google.genai modules")
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

    # --- Configuration using new GenAI client ---
    API_KEY = "AIzaSyDEmol7oGNgPose137dLA8MWtI1pyOAoVs"
    
    try:
        # Use the new GenAI client pattern
        client = genai.Client(api_key=API_KEY)
        print("✅ New GenAI client created successfully")
    except Exception as e:
        print(f"❌ Client creation error: {e}")
        return False

    # --- Define the Grounding Tool ---
    try:
        grounding_tool = types.Tool(
            google_search=types.GoogleSearch()
        )
        print("✅ Grounding tool created successfully")
    except Exception as e:
        print(f"❌ Tool creation error: {e}")
        return False

    # --- API Call ---
    try:
        print("\n🌐 Making API call with Google Search grounding...")
        
        config = types.GenerateContentConfig(
            tools=[grounding_tool],
            temperature=1.0  # Google's recommendation for grounding
        )
        
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents="Who won the most recent FIFA World Cup and what was the final score?",
            config=config
        )
        print("✅ API call completed successfully")

        # --- Verification ---
        print("\n--- Model Response ---")
        print(response.text)
        print("\n" + "="*50 + "\n")

        # Check for grounding metadata
        if hasattr(response, 'candidates') and response.candidates:
            candidate = response.candidates[0]
            if hasattr(candidate, 'grounding_metadata') and candidate.grounding_metadata:
                metadata = candidate.grounding_metadata
                print("🎉 SUCCESS: Grounding metadata was found!")
                
                # Try to access web search queries
                try:
                    queries = getattr(metadata, 'web_search_queries', [])
                    print(f"   Queries Performed: {len(queries)}")
                    for i, query in enumerate(queries):
                        print(f"     - Query {i+1}: {query}")
                except Exception as e:
                    print(f"   Error accessing queries: {e}")
                
                # Try to access grounding chunks
                try:
                    chunks = getattr(metadata, 'grounding_chunks', [])
                    print(f"   Sources Found: {len(chunks)}")
                    for i, chunk in enumerate(chunks[:3]):  # Show first 3
                        if hasattr(chunk, 'web') and chunk.web:
                            print(f"     - Source {i+1}: {getattr(chunk.web, 'title', 'No title')} ({getattr(chunk.web, 'uri', 'No URI')})")
                except Exception as e:
                    print(f"   Error accessing chunks: {e}")
                
                return True
            else:
                print("❌ FAILURE: No grounding_metadata attribute found in the response.")
                print("   This suggests either:")
                print("   1. API access is not enabled for Google Search grounding")
                print("   2. Model chose not to use the search tool")
                print("   3. Tool configuration issue")
                return False
        else:
            print("❌ FAILURE: No candidates found in response")
            return False

    except Exception as e:
        print(f"❌ API call error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🧪 Starting Minimal Google Search Grounding Test")
    print("="*60)
    
    success = test_minimal_grounding()
    
    print("\n" + "="*60)
    if success:
        print("🎉 TEST PASSED: Google Search grounding is working!")
        print("   The issue is likely conflicting instructions in the application.")
    else:
        print("❌ TEST FAILED: Google Search grounding is not working.")
        print("   This indicates an API access or configuration issue.")