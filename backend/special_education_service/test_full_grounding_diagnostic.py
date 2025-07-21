#!/usr/bin/env python3
"""
Full Google Search grounding diagnostic test
Root cause analysis of assessment pipeline grounding failure
"""

import os
import asyncio
import json
import sys
import logging
from datetime import datetime

# Set up logging to see everything
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.utils.gemini_client import GeminiClient

async def test_full_grounding_diagnostic():
    """Complete diagnostic test of Google Search grounding functionality"""
    
    # Set up environment
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ GEMINI_API_KEY not set")
        return
    
    print("🔍 FULL GOOGLE SEARCH GROUNDING DIAGNOSTIC")
    print("=" * 60)
    print(f"🕐 Started at: {datetime.now()}")
    print(f"🔑 API Key: {api_key[:10]}..." if api_key else "❌ No API key")
    print()
    
    # Initialize client
    print("🔧 Initializing Gemini client...")
    client = GeminiClient()
    print(f"✅ Client initialized")
    print(f"   - Old model: {client.model.model_name if hasattr(client.model, 'model_name') else 'Unknown'}")
    print(f"   - New client available: {client.new_genai_client is not None}")
    print()
    
    # Test data representative of assessment pipeline
    student_data = {
        "student_id": "test-student-123",
        "student_name": "Test Student Assessment Pipeline",
        "grade_level": "5",
        "disability_type": "Specific Learning Disability",
        "case_manager_name": "Ms. Assessment",
        "test_scores": [
            {
                "test_name": "WISC-V",
                "subtest_name": "Verbal Comprehension Index",
                "standard_score": 88,
                "percentile_rank": 21,
                "score_interpretation": "Low Average"
            },
            {
                "test_name": "WISC-V",
                "subtest_name": "Working Memory Index",
                "standard_score": 82,
                "percentile_rank": 12,
                "score_interpretation": "Below Average"
            }
        ],
        "strengths": ["Visual learning", "Creative problem solving"],
        "areas_for_growth": ["Reading comprehension", "Math fluency"],
        "assessment_confidence": 0.95
    }
    
    template_data = {
        "name": "Comprehensive Academic Areas IEP Template",
        "sections": {
            "student_info": "Basic student information",
            "long_term_goal": "Annual academic goals",
            "short_term_goals": "Quarterly objectives",
            "oral_language": "Receptive and expressive language",
            "reading": "Reading skills assessment",
            "spelling": "Spelling goals",
            "writing": "Writing recommendations",
            "concept": "Concept development",
            "math": "Mathematics goals",
            "services": "Special education services"
        }
    }
    
    print("📋 Test Data Prepared:")
    print(f"   - Student: {student_data['student_name']}")
    print(f"   - Grade: {student_data['grade_level']}")
    print(f"   - Disability: {student_data['disability_type']}")
    print(f"   - Test scores: {len(student_data['test_scores'])}")
    print(f"   - Template: {template_data['name']}")
    print(f"   - Template sections: {len(template_data['sections'])}")
    print()
    
    # TEST 1: Standard generation (no grounding)
    print("📝 TEST 1: Standard generation (grounding=False)")
    print("-" * 50)
    try:
        start_time = datetime.now()
        result_no_grounding = await client.generate_iep_content(
            student_data=student_data,
            template_data=template_data,
            enable_google_search_grounding=False
        )
        duration1 = (datetime.now() - start_time).total_seconds()
        
        print(f"✅ Standard generation completed in {duration1:.2f}s")
        print(f"📄 Response size: {len(result_no_grounding['raw_text'])} characters")
        print(f"🎯 Has grounding metadata: {'grounding_metadata' in result_no_grounding}")
        print()
        
    except Exception as e:
        print(f"❌ Standard generation failed: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # TEST 2: Grounded generation
    print("🌐 TEST 2: Google Search grounded generation (grounding=True)")
    print("-" * 50)
    try:
        start_time = datetime.now()
        result_with_grounding = await client.generate_iep_content(
            student_data=student_data,
            template_data=template_data,
            enable_google_search_grounding=True  # ENABLED
        )
        duration2 = (datetime.now() - start_time).total_seconds()
        
        print(f"✅ Grounded generation completed in {duration2:.2f}s")
        print(f"📄 Response size: {len(result_with_grounding['raw_text'])} characters")
        print(f"🎯 Has grounding metadata: {'grounding_metadata' in result_with_grounding}")
        print(f"⏱️ Duration difference: +{duration2 - duration1:.2f}s for grounding")
        print()
        
        # Detailed grounding analysis
        if 'grounding_metadata' in result_with_grounding:
            gm = result_with_grounding['grounding_metadata']
            print("🌐 BACKEND GROUNDING METADATA FOUND:")
            print(f"   - Search queries: {len(gm.get('web_search_queries', []))}")
            print(f"   - Grounding chunks: {len(gm.get('grounding_chunks', []))}")
            print(f"   - Grounding supports: {len(gm.get('grounding_supports', []))}")
            
            # Show search queries
            queries = gm.get('web_search_queries', [])
            if queries:
                print("   - Search queries performed:")
                for i, query in enumerate(queries[:3]):
                    print(f"     {i+1}. {query}")
            
            # Show sources
            chunks = gm.get('grounding_chunks', [])
            if chunks:
                print("   - Sources found:")
                for i, chunk in enumerate(chunks[:3]):
                    print(f"     {i+1}. {chunk.get('title', 'Unknown')[:50]}...")
            print()
        else:
            print("⚠️ NO BACKEND GROUNDING METADATA FOUND")
            print("   This indicates Google Search is not being invoked")
            print()
        
        # Check LLM response content for grounding acknowledgment
        try:
            parsed_response = json.loads(result_with_grounding['raw_text'])
            
            # Check for grounding_metadata in LLM response
            if "grounding_metadata" in parsed_response:
                llm_gm = parsed_response["grounding_metadata"]
                print("🎯 LLM GROUNDING ACKNOWLEDGMENT FOUND:")
                print(f"   - Google Search used: {llm_gm.get('google_search_used', False)}")
                print(f"   - Search queries reported: {len(llm_gm.get('search_queries_performed', []))}")
                print(f"   - Improvements reported: {len(llm_gm.get('evidence_based_improvements', []))}")
                
                # Show LLM-reported search queries
                llm_queries = llm_gm.get('search_queries_performed', [])
                if llm_queries:
                    print("   - LLM reported search queries:")
                    for i, query in enumerate(llm_queries[:3]):
                        print(f"     {i+1}. {query}")
                
                print()
            else:
                print("⚠️ NO LLM GROUNDING ACKNOWLEDGMENT IN RESPONSE CONTENT")
                print("   The LLM did not include grounding_metadata section")
                print()
            
            # Check for enhanced content from grounding
            enhanced_indicators = []
            for section_name, section_data in parsed_response.items():
                if isinstance(section_data, dict):
                    for field_name, field_content in section_data.items():
                        if field_name in ["current", "goals"] and isinstance(field_content, str):
                            if len(field_content) > 200:  # Rich content indicator
                                enhanced_indicators.append(f"{section_name}.{field_name}")
            
            if enhanced_indicators:
                print(f"📋 ENHANCED CONTENT DETECTED: {len(enhanced_indicators)} rich fields")
                for indicator in enhanced_indicators[:3]:
                    print(f"   - {indicator}")
                print()
            else:
                print("⚠️ NO ENHANCED CONTENT DETECTED")
                print("   Content appears similar to non-grounded generation")
                print()
                
        except json.JSONDecodeError as e:
            print(f"❌ JSON parsing failed: {e}")
            print(f"🔍 Raw response sample:")
            print(result_with_grounding['raw_text'][:500])
            print("...")
            print()
        
    except Exception as e:
        print(f"❌ Grounded generation failed: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # DIAGNOSTIC SUMMARY
    print("📊 DIAGNOSTIC SUMMARY")
    print("=" * 50)
    
    # Compare response sizes
    size_diff = len(result_with_grounding['raw_text']) - len(result_no_grounding['raw_text'])
    print(f"📏 Response size difference: {size_diff:+} characters")
    
    # Check if grounding is actually working
    has_backend_grounding = 'grounding_metadata' in result_with_grounding
    
    try:
        grounded_parsed = json.loads(result_with_grounding['raw_text'])
        has_llm_grounding = 'grounding_metadata' in grounded_parsed
    except:
        has_llm_grounding = False
    
    print(f"🌐 Backend grounding detected: {'✅ YES' if has_backend_grounding else '❌ NO'}")
    print(f"🤖 LLM grounding acknowledgment: {'✅ YES' if has_llm_grounding else '❌ NO'}")
    
    # Root cause analysis
    print()
    print("🔍 ROOT CAUSE ANALYSIS")
    print("-" * 30)
    
    if not has_backend_grounding and not has_llm_grounding:
        print("❌ GROUNDING COMPLETELY NON-FUNCTIONAL")
        print("   - Google Search API is not being invoked")
        print("   - LLM is not acknowledging grounding requests")
        print("   - Possible causes:")
        print("     1. New GenAI client initialization failure")
        print("     2. API key permissions issues")
        print("     3. Grounding tool configuration problems")
        print("     4. Request routing to wrong model/API")
        
    elif has_backend_grounding and not has_llm_grounding:
        print("⚠️ PARTIAL GROUNDING FUNCTION")
        print("   - Google Search API is working")
        print("   - But LLM is not incorporating results into response")
        print("   - Possible causes:")
        print("     1. Prompt instructions not clear enough")
        print("     2. Schema validation issues")
        print("     3. Model not following grounding instructions")
        
    elif not has_backend_grounding and has_llm_grounding:
        print("⚠️ FALSE GROUNDING ACKNOWLEDGMENT")
        print("   - LLM claims to use grounding but no actual searches performed")
        print("   - This is confabulation/hallucination")
        
    else:
        print("✅ GROUNDING APPEARS FUNCTIONAL")
        print("   - Backend search API working")
        print("   - LLM acknowledging and incorporating results")
        print("   - This suggests the feature is working in isolation")
        
    print()
    print(f"🏁 Diagnostic completed at: {datetime.now()}")

if __name__ == "__main__":
    asyncio.run(test_full_grounding_diagnostic())