#!/usr/bin/env python3
"""
Test the response structure when Google Search grounding is enabled
to ensure enriched fields are properly included
"""

import os
import asyncio
import json
from src.utils.gemini_client import GeminiClient

async def test_grounding_response_structure():
    """Test that grounding produces enriched section fields"""
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ GEMINI_API_KEY not set")
        return
    
    print("🔍 Testing Google Search Grounding Response Structure")
    print("=" * 60)
    
    client = GeminiClient()
    
    # Test data
    student_data = {
        "student_id": "test-123",
        "student_name": "Test Student",
        "grade_level": "5",
        "disability_type": "Specific Learning Disability",
        "case_manager_name": "Ms. Test",
        "test_scores": [
            {
                "test_name": "WISC-V",
                "subtest_name": "Working Memory Index",
                "standard_score": 82,
                "percentile_rank": 12
            }
        ]
    }
    
    template_data = {
        "name": "Comprehensive Academic Areas IEP Template",
        "sections": {
            "reading": "Reading skills and comprehension",
            "spelling": "Spelling goals and strategies",
            "writing": "Writing skills and recommendations",
            "math": "Mathematics goals and interventions",
            "concept": "Concept development"
        }
    }
    
    print("🌐 Generating with Google Search grounding ENABLED...")
    
    try:
        result = await client.generate_iep_content(
            student_data=student_data,
            template_data=template_data,
            enable_google_search_grounding=True
        )
        
        print(f"✅ Generation completed")
        print(f"📊 Response has grounding metadata: {'grounding_metadata' in result}")
        
        # Parse the response
        response_data = json.loads(result['raw_text'])
        
        print("\n📋 Response Structure Analysis:")
        print("-" * 40)
        
        # Check for enriched fields in each section
        enriched_sections = []
        for section_name in ['reading', 'spelling', 'writing', 'math', 'concept']:
            if section_name in response_data:
                section = response_data[section_name]
                print(f"\n🔍 {section_name.upper()} section:")
                
                if isinstance(section, dict):
                    fields = list(section.keys())
                    print(f"   Fields: {fields}")
                    
                    # Check for enriched fields
                    has_current = 'current' in section
                    has_goals = 'goals' in section
                    has_recommendations = 'recommendations' in section
                    
                    if has_current or has_goals:
                        enriched_sections.append(section_name)
                        print(f"   ✅ ENRICHED: current={has_current}, goals={has_goals}")
                        
                        # Show sample content
                        if has_current:
                            print(f"   📝 Current: {section['current'][:100]}...")
                        if has_goals:
                            print(f"   🎯 Goals: {section['goals'][:100]}...")
                    else:
                        print(f"   ⚠️ NOT ENRICHED - standard fields only")
                else:
                    print(f"   ❌ Not a dict: {type(section)}")
        
        print(f"\n📊 Summary:")
        print(f"   Total enriched sections: {len(enriched_sections)}")
        print(f"   Enriched sections: {enriched_sections}")
        
        # Check if grounding_metadata is in the response
        if 'grounding_metadata' in response_data:
            gm = response_data['grounding_metadata']
            print(f"\n🌐 LLM Grounding Metadata:")
            print(f"   Google Search used: {gm.get('google_search_used', False)}")
            print(f"   Queries performed: {len(gm.get('search_queries_performed', []))}")
            print(f"   Improvements: {len(gm.get('evidence_based_improvements', []))}")
        
        # Check backend grounding metadata
        if 'grounding_metadata' in result:
            print(f"\n🔧 Backend Grounding Metadata:")
            print(f"   Queries: {len(result['grounding_metadata'].get('web_search_queries', []))}")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_grounding_response_structure())