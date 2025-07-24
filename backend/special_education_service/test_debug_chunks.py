#!/usr/bin/env python3
"""
Debug why chunks are not being extracted
"""

import os
import asyncio
from src.utils.gemini_client import GeminiClient
import json

async def debug_chunks():
    """Debug chunk extraction"""
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ GEMINI_API_KEY not set")
        return
    
    print("🔍 Debugging chunk extraction...")
    
    # Initialize client  
    client = GeminiClient()
    
    # Test data
    student_data = {
        "student_name": "Test Student", 
        "grade_level": "5",
        "disability_type": "Specific Learning Disability"
    }
    
    template_data = {
        "name": "Test Template",
        "sections": {"student_info": "Info"}
    }
    
    # Make request with grounding
    result = await client.generate_iep_content(
        student_data=student_data,
        template_data=template_data,
        enable_google_search_grounding=True
    )
    
    print(f"✅ Request completed")
    
    # Check grounding metadata
    if "grounding_metadata" in result:
        gm = result["grounding_metadata"]
        print(f"\n🌐 Backend grounding metadata:")
        print(f"   Web search queries: {gm.get('web_search_queries', [])}")
        print(f"   Grounding chunks: {gm.get('grounding_chunks', [])}")
        print(f"   Grounding supports: {gm.get('grounding_supports', [])}")
        
        # Debug empty chunks
        if not gm.get('grounding_chunks'):
            print("\n⚠️ No chunks found - this might indicate:")
            print("   1. The API didn't return web search results")
            print("   2. The search didn't find relevant content")
            print("   3. The chunk extraction logic needs adjustment")
    else:
        print("❌ No grounding metadata in result")

if __name__ == "__main__":
    asyncio.run(debug_chunks())