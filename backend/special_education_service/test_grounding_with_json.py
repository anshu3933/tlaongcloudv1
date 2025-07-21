#!/usr/bin/env python3
"""
Test Google Search grounding with JSON output requirement
"""

import os
import json
from google import genai
from google.genai import types

def test_grounding_with_json():
    """Test Google Search grounding with JSON response requirement"""
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ GEMINI_API_KEY not set")
        return
    
    print("🔧 Testing Google Search grounding with JSON output...")
    
    try:
        # Configure the client
        client = genai.Client()
        
        # Define the grounding tool
        grounding_tool = types.Tool(
            google_search=types.GoogleSearch()
        )
        
        # Configure generation settings (no JSON mime type due to grounding limitation)
        config = types.GenerateContentConfig(
            tools=[grounding_tool]
        )
        
        # Prompt that requests JSON output
        prompt = """Based on current research and evidence-based practices, create a simplified IEP recommendation for a Grade 5 student with Specific Learning Disability.

CRITICAL: You MUST respond with valid JSON in this exact format:
{
  "reading_goal": "A specific, measurable reading goal based on current research",
  "math_goal": "A specific, measurable math goal based on current research", 
  "accommodations": ["accommodation1", "accommodation2"],
  "grounding_info": {
    "google_search_used": true,
    "research_applied": "Brief description of how current research influenced these recommendations"
  }
}

Use Google Search to find the latest evidence-based interventions for Grade 5 students with SLD and incorporate that research into your recommendations."""
        
        print("🌐 Making grounded request with JSON requirement...")
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=config,
        )
        
        print("✅ Response received!")
        print(f"📄 Full response: {response.text}")
        
        # Try to extract JSON
        response_text = response.text.strip()
        
        # Look for JSON in the response
        json_start = response_text.find('{')
        json_end = response_text.rfind('}') + 1
        
        if json_start != -1 and json_end > json_start:
            potential_json = response_text[json_start:json_end]
            try:
                parsed_json = json.loads(potential_json)
                print("✅ JSON extraction successful!")
                print(f"📋 Parsed response: {json.dumps(parsed_json, indent=2)}")
                
                # Check if grounding info is included
                if "grounding_info" in parsed_json:
                    grounding_info = parsed_json["grounding_info"]
                    print(f"🌐 LLM reported Google Search used: {grounding_info.get('google_search_used', False)}")
                    print(f"📚 Research applied: {grounding_info.get('research_applied', 'None')}")
                
            except json.JSONDecodeError as e:
                print(f"❌ JSON parsing failed: {e}")
                print(f"🔍 Attempted to parse: {potential_json[:200]}...")
        else:
            print("⚠️ No JSON found in response")
        
        # Check for grounding metadata
        if hasattr(response, 'candidates') and response.candidates:
            candidate = response.candidates[0]
            if hasattr(candidate, 'grounding_metadata') and candidate.grounding_metadata:
                gm = candidate.grounding_metadata
                print("🌐 Google grounding metadata found!")
                
                if hasattr(gm, 'web_search_queries'):
                    print(f"   - Search queries: {gm.web_search_queries}")
                    
                if hasattr(gm, 'grounding_chunks'):
                    print(f"   - Sources found: {len(gm.grounding_chunks)}")
            else:
                print("⚠️ No grounding metadata in response")
                
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_grounding_with_json()