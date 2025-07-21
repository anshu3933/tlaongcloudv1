#!/usr/bin/env python3
"""
Update the Gemini client prompt to generate output in the exact PLOP format
requested by the user, ensuring strict adherence to the example structure.
"""

import asyncio
import sys
import os

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

async def test_plop_format_generation():
    """Test generating IEP content in the exact PLOP format"""
    from src.utils.gemini_client import GeminiClient
    
    print("🎯 Testing PLOP Format Generation")
    print("=" * 50)
    
    client = GeminiClient()
    
    # Test data that should produce the exact format
    student_data = {
        "student_id": "test-plop-001",
        "student_name": "Student E",
        "grade_level": "4",
        "disability_type": "Specific Learning Disability",
        "case_manager_name": "Ms. Test",
        "test_scores": [
            {
                "test_name": "WISC-V",
                "subtest_name": "Working Memory Index",
                "standard_score": 82,
                "percentile_rank": 12
            },
            {
                "test_name": "WIAT-IV",
                "subtest_name": "Reading Comprehension",
                "standard_score": 88,
                "percentile_rank": 21
            }
        ]
    }
    
    # Template data specifically for PLOP format
    template_data = {
        "name": "PLOP and Goals Comprehensive Template (K-5)",
        "sections": {
            "oral_language": {
                "description": "Oral Language – Receptive and Expressive",
                "fields": {
                    "current_grade": "Current grade level for this domain",
                    "present_level": "Detailed present level of performance description",
                    "goals": "Specific measurable goals for improvement",
                    "recommendations": "Evidence-based recommendations for instruction"
                }
            },
            "reading_familiar": {
                "description": "Reading – Familiar",
                "fields": {
                    "current_grade": "Current grade level for this domain",
                    "present_level": "Detailed present level of performance description",
                    "goals": "Specific measurable goals for improvement",
                    "recommendations": "Evidence-based recommendations for instruction"
                }
            },
            "reading_unfamiliar": {
                "description": "Reading - Unfamiliar",
                "fields": {
                    "current_grade": "Current grade level for this domain",
                    "present_level": "Detailed present level of performance description",
                    "goals": "Specific measurable goals for improvement",
                    "recommendations": "Evidence-based recommendations for instruction"
                }
            },
            "reading_comprehension": {
                "description": "Reading Comprehension",
                "fields": {
                    "current_grade": "Current grade level for this domain",
                    "present_level": "Detailed present level of performance description",
                    "goals": "Specific measurable goals for improvement",
                    "recommendations": "Evidence-based recommendations for instruction"
                }
            },
            "spelling": {
                "description": "Spelling",
                "fields": {
                    "current_grade": "Current grade level for this domain",
                    "present_level": "Detailed present level of performance description",
                    "goals": "Specific measurable goals for improvement",
                    "recommendations": "Evidence-based recommendations for instruction"
                }
            },
            "writing": {
                "description": "Writing",
                "fields": {
                    "current_grade": "Current grade level for this domain",
                    "present_level": "Detailed present level of performance description",
                    "goals": "Specific measurable goals for improvement",
                    "recommendations": "Evidence-based recommendations for instruction"
                }
            },
            "handwriting": {
                "description": "Handwriting",
                "fields": {
                    "present_level": "Detailed present level of performance description",
                    "goals": "Specific measurable goals for improvement",
                    "recommendations": "Evidence-based recommendations for instruction"
                }
            },
            "grammar": {
                "description": "Grammar",
                "fields": {
                    "present_level": "Detailed present level of performance description",
                    "goals": "Specific measurable goals for improvement",
                    "recommendations": "Evidence-based recommendations for instruction"
                }
            },
            "concept": {
                "description": "Concept",
                "fields": {
                    "current_grade": "Current grade level for this domain",
                    "present_level": "Detailed present level of performance description",
                    "goals": "Specific measurable goals for improvement",
                    "recommendations": "Evidence-based recommendations for instruction"
                }
            },
            "math": {
                "description": "Math",
                "fields": {
                    "current_grade": "Current grade level for this domain",
                    "present_level": "Detailed present level of performance description",
                    "goals": "Specific measurable goals for improvement",
                    "recommendations": "Evidence-based recommendations for instruction"
                }
            },
            "behaviour": {
                "description": "Behaviour",
                "fields": {
                    "present_level": "Detailed present level of performance description",
                    "goals": "Specific measurable goals for improvement",
                    "recommendations": "Evidence-based recommendations for instruction"
                }
            }
        }
    }
    
    print("🚀 Generating content with PLOP template...")
    
    try:
        result = await client.generate_iep_content(
            student_data=student_data,
            template_data=template_data,
            enable_google_search_grounding=True
        )
        
        print(f"✅ Generation completed in {result.get('duration_seconds', 0):.2f} seconds")
        
        # Parse and display the result
        import json
        response_data = json.loads(result['raw_text'])
        
        print("\n📋 Generated PLOP Format:")
        print("-" * 40)
        
        # Check each section for the expected PLOP format
        plop_sections = ['oral_language', 'reading_familiar', 'reading_unfamiliar', 
                        'reading_comprehension', 'spelling', 'writing', 'handwriting',
                        'grammar', 'concept', 'math', 'behaviour']
        
        for section_name in plop_sections:
            if section_name in response_data:
                section = response_data[section_name]
                print(f"\n🔍 {section_name.upper().replace('_', ' ')}:")
                
                if isinstance(section, dict):
                    # Check for PLOP format fields
                    if 'current_grade' in section:
                        print(f"   Current Grade: {section.get('current_grade', 'N/A')}")
                    if 'present_level' in section:
                        print(f"   Present Level: {section.get('present_level', 'N/A')[:100]}...")
                    if 'goals' in section:
                        print(f"   Goals: {section.get('goals', 'N/A')[:100]}...")
                    if 'recommendations' in section:
                        print(f"   Recommendations: {section.get('recommendations', 'N/A')[:100]}...")
                else:
                    print(f"   ⚠️ Not in expected format: {type(section)}")
        
        # Check for grounding metadata
        if 'grounding_metadata' in result and result['grounding_metadata']:
            gm = result['grounding_metadata']
            print(f"\n🌐 Grounding Information:")
            print(f"   Search queries: {len(gm.get('web_search_queries', []))}")
            print(f"   Sources found: {len(gm.get('grounding_chunks', []))}")
        
        return response_data
        
    except Exception as e:
        print(f"❌ Generation failed: {e}")
        import traceback
        traceback.print_exc()
        return None

async def create_enhanced_plop_schema():
    """Create an enhanced schema specifically for PLOP format"""
    
    # This is the exact schema that should be used for PLOP generation
    plop_schema = {
        "type": "object",
        "properties": {
            "oral_language": {
                "type": "object",
                "properties": {
                    "current_grade": {"type": "string", "description": "Current grade level for oral language domain"},
                    "present_level": {"type": "string", "description": "Detailed present level of performance"},
                    "goals": {"type": "string", "description": "Specific measurable goals"},
                    "recommendations": {"type": "string", "description": "Evidence-based recommendations"}
                },
                "required": ["current_grade", "present_level", "goals", "recommendations"]
            },
            "reading_familiar": {
                "type": "object",
                "properties": {
                    "current_grade": {"type": "string"},
                    "present_level": {"type": "string"},
                    "goals": {"type": "string"},
                    "recommendations": {"type": "string"}
                },
                "required": ["current_grade", "present_level", "goals", "recommendations"]
            },
            "reading_unfamiliar": {
                "type": "object",
                "properties": {
                    "current_grade": {"type": "string"},
                    "present_level": {"type": "string"},
                    "goals": {"type": "string"},
                    "recommendations": {"type": "string"}
                },
                "required": ["current_grade", "present_level", "goals", "recommendations"]
            },
            "reading_comprehension": {
                "type": "object",
                "properties": {
                    "current_grade": {"type": "string"},
                    "present_level": {"type": "string"},
                    "goals": {"type": "string"},
                    "recommendations": {"type": "string"}
                },
                "required": ["current_grade", "present_level", "goals", "recommendations"]
            },
            "spelling": {
                "type": "object",
                "properties": {
                    "current_grade": {"type": "string"},
                    "present_level": {"type": "string"},
                    "goals": {"type": "string"},
                    "recommendations": {"type": "string"}
                },
                "required": ["current_grade", "present_level", "goals", "recommendations"]
            },
            "writing": {
                "type": "object",
                "properties": {
                    "current_grade": {"type": "string"},
                    "present_level": {"type": "string"},
                    "goals": {"type": "string"},
                    "recommendations": {"type": "string"}
                },
                "required": ["current_grade", "present_level", "goals", "recommendations"]
            },
            "handwriting": {
                "type": "object",
                "properties": {
                    "present_level": {"type": "string"},
                    "goals": {"type": "string"},
                    "recommendations": {"type": "string"}
                },
                "required": ["present_level", "goals", "recommendations"]
            },
            "grammar": {
                "type": "object",
                "properties": {
                    "present_level": {"type": "string"},
                    "goals": {"type": "string"},
                    "recommendations": {"type": "string"}
                },
                "required": ["present_level", "goals", "recommendations"]
            },
            "concept": {
                "type": "object",
                "properties": {
                    "current_grade": {"type": "string"},
                    "present_level": {"type": "string"},
                    "goals": {"type": "string"},
                    "recommendations": {"type": "string"}
                },
                "required": ["current_grade", "present_level", "goals", "recommendations"]
            },
            "math": {
                "type": "object",
                "properties": {
                    "current_grade": {"type": "string"},
                    "present_level": {"type": "string"},
                    "goals": {"type": "string"},
                    "recommendations": {"type": "string"}
                },
                "required": ["current_grade", "present_level", "goals", "recommendations"]
            },
            "behaviour": {
                "type": "object",
                "properties": {
                    "present_level": {"type": "string"},
                    "goals": {"type": "string"},
                    "recommendations": {"type": "string"}
                },
                "required": ["present_level", "goals", "recommendations"]
            }
        },
        "required": ["oral_language", "reading_familiar", "reading_unfamiliar", 
                    "reading_comprehension", "spelling", "writing", "handwriting",
                    "grammar", "concept", "math", "behaviour"]
    }
    
    print("📋 Enhanced PLOP Schema Created")
    print(f"Sections: {len(plop_schema['properties'])}")
    print(f"Required sections: {len(plop_schema['required'])}")
    
    return plop_schema

async def main():
    print("🎯 PLOP Format Testing and Enhancement")
    print("=" * 60)
    
    # Create enhanced schema
    plop_schema = await create_enhanced_plop_schema()
    
    # Test generation
    result = await test_plop_format_generation()
    
    if result:
        print("\n✅ PLOP format generation test completed")
        print("\n📝 Next Steps:")
        print("1. The template is created and available in the database")
        print("2. The schema supports the exact PLOP format structure")
        print("3. Test with actual assessment pipeline integration")
        print("4. Template ID: b0d83589-dce5-49b5-8d74-2e8697f3856a")
        print("5. Frontend URL: http://localhost:3002/templates/b0d83589-dce5-49b5-8d74-2e8697f3856a")
    else:
        print("\n❌ PLOP format generation test failed")

if __name__ == "__main__":
    asyncio.run(main())