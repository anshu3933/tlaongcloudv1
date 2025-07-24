#!/usr/bin/env python3
"""
Debug script to trace the grounding flow through the assessment pipeline
This will help identify where grounding metadata is being lost
"""

import requests
import json
import time

def debug_assessment_pipeline_grounding():
    """Test the exact request that assessment pipeline makes"""
    print("🔍 DEBUGGING ASSESSMENT PIPELINE GROUNDING FLOW")
    print("=" * 80)
    
    url = "http://localhost:8005/api/v1/ieps/advanced/create-with-rag"
    params = {
        "current_user_id": "1",
        "current_user_role": "teacher"
    }
    
    # Exact payload structure from assessment pipeline
    payload = {
        "student_id": "a5c65e54-29b2-4aaf-a0f2-805049b3169e",
        "template_id": "a2bde6bf-5793-4295-bc61-aea5415bcb36",
        "academic_year": "2025-2026",
        "meeting_date": "2025-01-22",
        "effective_date": "2025-01-22", 
        "review_date": "2026-01-22",
        "enable_google_search_grounding": True,  # THIS IS KEY
        "content": {
            "case_manager_name": "Test Case Manager",
            "student_name": "Test Student",
            "grade_level": "5th Grade",
            "disability_types": ["SLD"],
            "assessment_summary": "Testing grounding in assessment pipeline flow",
            "educational_content": {
                "objectives": [],
                "performance_levels": {},
                "recommendations": ["Test recommendation"],
                "areas_of_concern": ["Test concern"],
                "strengths": ["Test strength"]
            }
        }
    }
    
    print("📤 Sending Assessment Pipeline Request:")
    print(f"   URL: {url}")
    print(f"   Grounding Enabled: {payload['enable_google_search_grounding']}")
    print(f"   Student ID: {payload['student_id']}")
    print(f"   Template ID: {payload['template_id']}")
    
    try:
        start_time = time.time()
        response = requests.post(url, json=payload, params=params, timeout=30)
        duration = time.time() - start_time
        
        print(f"⏱️  Request completed in {duration:.2f} seconds")
        print(f"📋 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            print("✅ SUCCESS: IEP generated")
            print(f"📋 Response Keys: {list(data.keys())}")
            
            # Check for grounding metadata at top level
            if "grounding_metadata" in data:
                grounding = data["grounding_metadata"]
                print(f"🌐 TOP-LEVEL grounding_metadata: {type(grounding)}")
                if grounding:
                    print(f"   Queries: {len(grounding.get('web_search_queries', []))}")
                    print(f"   Chunks: {len(grounding.get('grounding_chunks', []))}")
                else:
                    print("   ⚠️ Empty grounding metadata")
            else:
                print("❌ NO top-level grounding_metadata in response")
            
            # Check for grounding metadata in content
            if "content" in data and data["content"]:
                content = data["content"]
                print(f"📝 Content field: {type(content)}")
                
                if isinstance(content, dict):
                    print(f"   Content keys: {list(content.keys())}")
                    
                    if "google_search_grounding" in content:
                        content_grounding = content["google_search_grounding"]
                        print(f"🌐 CONTENT-LEVEL google_search_grounding: {type(content_grounding)}")
                        if content_grounding:
                            print(f"   Queries: {len(content_grounding.get('web_search_queries', []))}")
                            print(f"   Chunks: {len(content_grounding.get('grounding_chunks', []))}")
                        else:
                            print("   ⚠️ Empty content-level grounding metadata")
                    else:
                        print("❌ NO google_search_grounding in content")
                else:
                    print("   ⚠️ Content is not a dictionary")
            else:
                print("❌ NO content field in response")
            
            # Analysis for frontend
            print("\n" + "=" * 60)
            print("📊 FRONTEND IMPACT ANALYSIS:")
            
            has_top_level = "grounding_metadata" in data and data["grounding_metadata"]
            has_content_level = False
            
            if "content" in data and isinstance(data["content"], dict):
                has_content_level = "google_search_grounding" in data["content"] and data["content"]["google_search_grounding"]
            
            print(f"   Assessment Pipeline stores: file.iepData = response")
            print(f"   StructuredIEPDisplay gets: file.iepData.content")
            print(f"   AISections metadata gets: content.google_search_grounding")
            print(f"   ")
            print(f"   Top-level metadata present: {'✅' if has_top_level else '❌'}")
            print(f"   Content-level metadata present: {'✅' if has_content_level else '❌'}")
            
            if has_content_level:
                print(f"   🎉 GROUNDING SHOULD BE VISIBLE in GenerationMetadata component")
            elif has_top_level:
                print(f"   ⚠️ Grounding metadata exists but won't be displayed (needs to be in content)")
            else:
                print(f"   ❌ NO GROUNDING METADATA - won't be displayed")
            
            return True
            
        else:
            print(f"❌ ERROR: HTTP {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Error: {error_data}")
            except:
                print(f"   Error: {response.text[:200]}")
            return False
            
    except requests.exceptions.Timeout:
        print("⏱️ Request timed out after 30 seconds")
        print("   This suggests grounding is being attempted but taking too long")
        return False
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

if __name__ == "__main__":
    debug_assessment_pipeline_grounding()