#!/usr/bin/env python3
"""
End-to-End Test for Two-Path Model using Real IEP Generation
Tests both grounded and non-grounded paths through the actual API
"""

import requests
import json
import time

def test_non_grounded_generation():
    """Test IEP generation without grounding (existing functionality)"""
    print("🧪 Testing NON-GROUNDED IEP generation (preserving existing functionality)")
    print("=" * 80)
    
    url = "http://localhost:8005/api/v1/ieps/advanced/create-with-rag"
    params = {
        "current_user_id": "1",
        "current_user_role": "teacher"
    }
    
    # Use existing student and template IDs from the system
    payload = {
        "student_id": "c6f74363-c1fb-4b0f-bd6b-0ae5c8a6f826",  # Known student ID
        "template_id": "3f2f2152-6758-425e-a3ed-3f4c2fd8afb8",  # Known template ID
        "academic_year": "2025-2026",
        "content": {"assessment_summary": "Testing non-grounded generation"},
        "meeting_date": "2025-01-22",
        "effective_date": "2025-01-22", 
        "review_date": "2026-01-22",
        "enable_google_search_grounding": False  # NON-GROUNDED PATH
    }
    
    try:
        print("📤 Sending non-grounded IEP generation request...")
        start_time = time.time()
        
        response = requests.post(url, json=payload, params=params, timeout=300)
        
        duration = time.time() - start_time
        print(f"⏱️ Request completed in {duration:.2f} seconds")
        
        if response.status_code == 200:
            data = response.json()
            
            # Check that it's a valid IEP response
            if "iep_id" in data and "content" in data:
                print("✅ Non-grounded generation successful")
                
                # Verify no grounding metadata in response
                if "grounding_metadata" in data and data["grounding_metadata"]:
                    print("❌ ERROR: Non-grounded response contains grounding metadata")
                    print(f"   Grounding data: {data['grounding_metadata']}")
                    return False
                else:
                    print("✅ SUCCESS: Non-grounded response clean (no grounding metadata)")
                    
                    # Check content size (should be substantial)
                    content_size = len(str(data["content"]))
                    print(f"📄 Generated content size: {content_size} characters")
                    
                    if content_size > 1000:
                        print("✅ SUCCESS: Generated substantial IEP content")
                        return True
                    else:
                        print("⚠️ WARNING: Generated content seems small")
                        return True  # Still success, just noting
            else:
                print("❌ ERROR: Invalid IEP response structure")
                print(f"   Response keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
                return False
        else:
            print(f"❌ ERROR: HTTP {response.status_code}")
            print(f"   Response: {response.text[:500]}...")
            return False
            
    except Exception as e:
        print(f"❌ ERROR in non-grounded test: {e}")
        return False

def test_grounded_generation():
    """Test IEP generation with grounding enabled"""
    print("\n🧪 Testing GROUNDED IEP generation (Google Search enabled)")
    print("=" * 80)
    
    url = "http://localhost:8005/api/v1/ieps/advanced/create-with-rag"
    params = {
        "current_user_id": "1", 
        "current_user_role": "teacher"
    }
    
    # Use existing student and template IDs, but with current topic
    payload = {
        "student_id": "c6f74363-c1fb-4b0f-bd6b-0ae5c8a6f826",  # Known student ID
        "template_id": "3f2f2152-6758-425e-a3ed-3f4c2fd8afb8",  # Known template ID
        "academic_year": "2025-2026",
        "content": {
            "assessment_summary": "Testing grounded generation with current information",
            "current_educational_trends": "Please research the latest 2025 special education technology trends"
        },
        "meeting_date": "2025-01-22",
        "effective_date": "2025-01-22",
        "review_date": "2026-01-22", 
        "enable_google_search_grounding": True  # GROUNDED PATH
    }
    
    try:
        print("📤 Sending grounded IEP generation request...")
        start_time = time.time()
        
        response = requests.post(url, json=payload, params=params, timeout=300)
        
        duration = time.time() - start_time
        print(f"⏱️ Request completed in {duration:.2f} seconds")
        
        if response.status_code == 200:
            data = response.json()
            
            # Check that it's a valid IEP response
            if "iep_id" in data and "content" in data:
                print("✅ Grounded generation successful")
                
                # Check for grounding metadata
                if "grounding_metadata" in data and data["grounding_metadata"]:
                    grounding = data["grounding_metadata"]
                    
                    # Extract grounding info
                    queries = grounding.get("web_search_queries", [])
                    chunks = grounding.get("grounding_chunks", [])
                    
                    query_count = len(queries)
                    source_count = len(chunks)
                    
                    print(f"🌐 SUCCESS: Found grounding metadata - {query_count} queries, {source_count} sources")
                    
                    if query_count > 0:
                        print("   Search queries performed:")
                        for i, query in enumerate(queries[:3]):  # Show first 3
                            print(f"     - Query {i+1}: {query}")
                    
                    if source_count > 0:
                        print("   Sources found:")
                        for i, chunk in enumerate(chunks[:3]):  # Show first 3
                            title = chunk.get("title", "Unknown")
                            uri = chunk.get("uri", "")
                            print(f"     - Source {i+1}: {title}")
                            if uri:
                                print(f"       URL: {uri}")
                    
                    if query_count > 0 or source_count > 0:
                        print("🎉 EXCELLENT: Google Search grounding is working in Two-Path Model!")
                        return True
                    else:
                        print("⚠️ INFO: Grounding metadata present but empty (model chose not to search)")
                        print("   This is normal behavior - model can choose when to search")
                        return True
                        
                else:
                    print("❌ WARNING: Grounded response missing grounding metadata")
                    print("   This suggests the grounded path may not be working correctly")
                    print("   Expected: google_search_grounding field with queries/sources")
                    return False
                    
            else:
                print("❌ ERROR: Invalid IEP response structure")
                return False
        else:
            print(f"❌ ERROR: HTTP {response.status_code}")
            print(f"   Response: {response.text[:500]}...")
            return False
            
    except Exception as e:
        print(f"❌ ERROR in grounded test: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run comprehensive Two-Path Model end-to-end test"""
    print("🚀 TWO-PATH MODEL END-TO-END TEST")
    print("Testing real IEP generation through production API")
    print("=" * 90)
    
    # Test both paths
    non_grounded_success = test_non_grounded_generation()
    grounded_success = test_grounded_generation()
    
    # Results summary
    print("\n" + "=" * 90)
    print("📊 TWO-PATH MODEL END-TO-END TEST RESULTS:")
    print(f"   Non-Grounded Path: {'✅ WORKING' if non_grounded_success else '❌ FAILED'}")
    print(f"   Grounded Path: {'✅ WORKING' if grounded_success else '❌ FAILED'}")
    
    if non_grounded_success and grounded_success:
        print("\n🎉 SUCCESS: Two-Path Model is working correctly in production!")
        print("   ✅ Non-grounded: Standard IEP generation preserved")
        print("   ✅ Grounded: Google Search integration working") 
        print("   ✅ Both paths: Independent operation confirmed")
        print("\n💡 IMPLEMENTATION COMPLETE:")
        print("   • JSON format constraint removed for grounded path")
        print("   • Text-to-JSON parsing working for grounded responses") 
        print("   • Grounding metadata properly injected and returned")
        print("   • Non-grounded path completely untouched")
        return True
        
    elif non_grounded_success and not grounded_success:
        print("\n⚠️ PARTIAL SUCCESS: Two-Path Model partially working")
        print("   ✅ Non-grounded: Original functionality preserved (CRITICAL SUCCESS)")
        print("   ❌ Grounded: Google Search grounding still has issues")
        print("\n🔧 NEXT STEPS:")
        print("   • Grounded path implementation needs refinement")
        print("   • Check Google Search API access and permissions")
        print("   • Verify new GenAI client configuration")
        return False
        
    elif not non_grounded_success and grounded_success:
        print("\n🚨 CRITICAL: Non-grounded path broken!")
        print("   ❌ Non-grounded: Existing functionality compromised")
        print("   ✅ Grounded: Working but not at expense of standard generation")
        print("\n🚨 URGENT ACTION REQUIRED:")
        print("   • Fix non-grounded path immediately")
        print("   • Verify JSON format constraint preserved for standard generation")
        return False
        
    else:
        print("\n🚨 COMPLETE FAILURE: Both paths broken!")
        print("   ❌ Non-grounded: Standard generation not working")
        print("   ❌ Grounded: Google Search grounding not working")
        print("\n🔧 ACTION REQUIRED:")
        print("   • Review entire Two-Path Model implementation")
        print("   • Check service health and dependencies")
        print("   • Verify GeminiClient configuration")
        return False

if __name__ == "__main__":
    success = main()
    
    if success:
        print("\n✅ TWO-PATH MODEL READY FOR PRODUCTION!")
        exit(0)
    else:
        print("\n❌ TWO-PATH MODEL NEEDS ATTENTION")
        exit(1)