#!/usr/bin/env python3
"""
Test Two-Path Generation Model for Google Search Grounding
This verifies that grounded and non-grounded paths work independently
"""

import asyncio
import json
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from utils.gemini_client import GeminiClient

async def test_non_grounded_path():
    """Test the non-grounded path (should remain unchanged)"""
    print("🧪 Testing NON-GROUNDED PATH (standard JSON generation)")
    print("=" * 70)
    
    client = GeminiClient()
    
    # Simple prompt that should return JSON
    prompt = """
    Generate a simple IEP present level summary in JSON format:
    {
        "student_name": "Test Student",
        "grade": "5",
        "strengths": ["reading comprehension", "math facts"],
        "concerns": ["written expression", "attention"],
        "needs": ["writing support", "behavior plan"]
    }
    """
    
    try:
        result = await client.generate_iep_content(
            prompt=prompt,
            enable_google_search_grounding=False  # NON-GROUNDED PATH
        )
        
        print("✅ Non-grounded generation completed")
        
        # Verify JSON structure
        if isinstance(result, str):
            parsed = json.loads(result)
            print(f"📝 JSON fields: {list(parsed.keys())}")
            if "google_search_grounding" in parsed:
                print("❌ ERROR: Non-grounded response contains grounding metadata")
                return False
            else:
                print("✅ SUCCESS: Non-grounded response clean (no grounding metadata)")
                return True
        else:
            print("❌ ERROR: Non-grounded response is not string")
            return False
            
    except Exception as e:
        print(f"❌ ERROR in non-grounded path: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_grounded_path():
    """Test the grounded path (should use new GenAI client)"""
    print("\n🧪 Testing GROUNDED PATH (Google Search enabled)")
    print("=" * 70)
    
    client = GeminiClient()
    
    # Prompt that requires current information
    prompt = """
    Generate an IEP section about current educational technology trends in JSON format:
    {
        "section_title": "Educational Technology Resources",
        "current_trends": ["list of current tech trends"],
        "recommended_tools": ["specific tools for special education"],
        "implementation_date": "2025-01-15"
    }
    
    Please research current educational technology trends for 2025.
    """
    
    try:
        result = await client.generate_iep_content(
            prompt=prompt,
            enable_google_search_grounding=True  # GROUNDED PATH
        )
        
        print("✅ Grounded generation completed")
        
        # Verify JSON structure and grounding metadata
        if isinstance(result, str):
            parsed = json.loads(result)
            print(f"📝 JSON fields: {list(parsed.keys())}")
            
            if "google_search_grounding" in parsed:
                grounding = parsed["google_search_grounding"]
                query_count = len(grounding.get("web_search_queries", []))
                source_count = len(grounding.get("grounding_chunks", []))
                print(f"🌐 SUCCESS: Found grounding metadata - {query_count} queries, {source_count} sources")
                
                if query_count > 0 or source_count > 0:
                    print("🎉 EXCELLENT: Google Search grounding appears to be working!")
                    return True
                else:
                    print("⚠️ WARNING: Grounding metadata present but empty (model chose not to search)")
                    return True  # Still success - model can choose not to search
            else:
                print("❌ WARNING: Grounded response missing grounding metadata")
                print("   This could mean:")
                print("   1. Google Search API access not available")
                print("   2. Model chose not to search")
                print("   3. Two-path model not working correctly")
                return False
        else:
            print("❌ ERROR: Grounded response is not string")
            return False
            
    except Exception as e:
        print(f"❌ ERROR in grounded path: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run comprehensive Two-Path Model test"""
    print("🚀 STARTING TWO-PATH MODEL COMPREHENSIVE TEST")
    print("=" * 80)
    
    # Test both paths
    non_grounded_success = await test_non_grounded_path()
    grounded_success = await test_grounded_path()
    
    # Results summary
    print("\n" + "=" * 80)
    print("📊 TWO-PATH MODEL TEST RESULTS:")
    print(f"   Non-Grounded Path: {'✅ WORKING' if non_grounded_success else '❌ FAILED'}")
    print(f"   Grounded Path: {'✅ WORKING' if grounded_success else '❌ FAILED'}")
    
    if non_grounded_success and grounded_success:
        print("\n🎉 SUCCESS: Two-Path Model is working correctly!")
        print("   ✅ Non-grounded path preserves existing functionality")
        print("   ✅ Grounded path enables Google Search without JSON conflicts")
        return True
    elif non_grounded_success and not grounded_success:
        print("\n⚠️ PARTIAL SUCCESS: Non-grounded path works, grounded path has issues")
        print("   ✅ Non-grounded path: Original functionality preserved")
        print("   ❌ Grounded path: Google Search grounding not working")
        print("   💡 RECOMMENDATION: Check Google Search API access and configuration")
        return False
    elif not non_grounded_success and grounded_success:
        print("\n❌ CRITICAL: Non-grounded path broken!")
        print("   ❌ Non-grounded path: Existing functionality compromised")
        print("   ✅ Grounded path: Working but at cost of breaking standard generation")
        print("   🚨 URGENT: Fix non-grounded path immediately")
        return False
    else:
        print("\n🚨 COMPLETE FAILURE: Both paths are broken!")
        print("   ❌ Non-grounded path: Standard generation not working")
        print("   ❌ Grounded path: Google Search grounding not working")
        print("   🔧 ACTION REQUIRED: Review Two-Path Model implementation")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    
    if success:
        print("\n✅ ALL TESTS PASSED - Two-Path Model ready for production!")
        sys.exit(0)
    else:
        print("\n❌ TESTS FAILED - Two-Path Model needs fixes")
        sys.exit(1)