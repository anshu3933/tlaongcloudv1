#!/usr/bin/env python3
"""
Test Google Search Grounding with JSON response format constraint
This tests if JSON format requirements interfere with grounding
"""

from google import genai
from google.genai import types

def test_grounding_with_json():
    print("🧪 Testing Google Search Grounding with JSON format requirement")
    print("="*70)
    
    # Configure client
    client = genai.Client(api_key="AIzaSyDEmol7oGNgPose137dLA8MWtI1pyOAoVs")
    
    # Create grounding tool
    grounding_tool = types.Tool(google_search=types.GoogleSearch())
    
    # Test with JSON format requirement
    try:
        config = types.GenerateContentConfig(
            tools=[grounding_tool],
            temperature=1.0,
            response_mime_type="application/json"  # This might conflict with grounding
        )
        
        prompt = """
        You must respond with valid JSON in this exact format:
        {
            "answer": "your answer here",
            "confidence": "high/medium/low"
        }
        
        Question: Who won the most recent FIFA World Cup and what was the final score?
        """
        
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=config
        )
        
        print("✅ API call with JSON format completed")
        print("\n--- Response ---")
        print(response.text)
        
        # Check for grounding
        if hasattr(response, 'candidates') and response.candidates:
            candidate = response.candidates[0]
            if hasattr(candidate, 'grounding_metadata') and candidate.grounding_metadata:
                metadata = candidate.grounding_metadata
                queries = getattr(metadata, 'web_search_queries', [])
                print(f"\n🎉 SUCCESS: {len(queries)} search queries performed with JSON format!")
                for i, query in enumerate(queries):
                    print(f"   - Query {i+1}: {query}")
                return True
            else:
                print("\n❌ FAILURE: No grounding metadata with JSON format")
                return False
        
    except Exception as e:
        print(f"❌ Error with JSON format: {e}")
        return False

def test_grounding_without_json():
    print("\n🧪 Testing Google Search Grounding without JSON format requirement")
    print("="*70)
    
    # Configure client
    client = genai.Client(api_key="AIzaSyDEmol7oGNgPose137dLA8MWtI1pyOAoVs")
    
    # Create grounding tool
    grounding_tool = types.Tool(google_search=types.GoogleSearch())
    
    try:
        config = types.GenerateContentConfig(
            tools=[grounding_tool],
            temperature=1.0
            # No response_mime_type constraint
        )
        
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents="Who won the most recent FIFA World Cup and what was the final score?",
            config=config
        )
        
        print("✅ API call without JSON format completed")
        print("\n--- Response ---")
        print(response.text)
        
        # Check for grounding
        if hasattr(response, 'candidates') and response.candidates:
            candidate = response.candidates[0]
            if hasattr(candidate, 'grounding_metadata') and candidate.grounding_metadata:
                metadata = candidate.grounding_metadata
                queries = getattr(metadata, 'web_search_queries', [])
                print(f"\n🎉 SUCCESS: {len(queries)} search queries performed without JSON format!")
                for i, query in enumerate(queries):
                    print(f"   - Query {i+1}: {query}")
                return True
            else:
                print("\n❌ FAILURE: No grounding metadata without JSON format")
                return False
        
    except Exception as e:
        print(f"❌ Error without JSON format: {e}")
        return False

if __name__ == "__main__":
    json_success = test_grounding_with_json()
    no_json_success = test_grounding_without_json()
    
    print("\n" + "="*70)
    print("📊 RESULTS:")
    print(f"   JSON Format + Grounding: {'✅ WORKS' if json_success else '❌ FAILS'}")
    print(f"   No JSON Format + Grounding: {'✅ WORKS' if no_json_success else '❌ FAILS'}")
    
    if no_json_success and not json_success:
        print("\n💡 CONCLUSION: JSON format constraint conflicts with Google Search grounding")
        print("   Solution: Remove response_mime_type='application/json' when grounding is enabled")
    elif json_success:
        print("\n💡 CONCLUSION: JSON format works with grounding - issue is elsewhere")
    else:
        print("\n💡 CONCLUSION: Neither configuration works - deeper issue exists")