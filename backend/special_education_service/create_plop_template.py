#!/usr/bin/env python3
"""
Create a new PLOP (Present Levels of Performance) and Goals template
following the exact format provided by the user.
"""

import asyncio
import sys
import os
from datetime import datetime

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

async def create_plop_template():
    from src.database import get_db_session
    from src.models.special_education_models import IEPTemplate, DisabilityType
    from sqlalchemy import select
    
    print("Creating new PLOP (Present Levels of Performance) and Goals template...")
    
    async with get_db_session() as session:
        # Get the SLD disability type (most common for this template format)
        sld_result = await session.execute(
            select(DisabilityType).where(DisabilityType.code == "SLD")
        )
        sld_disability = sld_result.scalar_one_or_none()
        
        if not sld_disability:
            print("ERROR: SLD disability type not found. Please run database initialization first.")
            return
        
        # Check if this template already exists
        existing_template = await session.execute(
            select(IEPTemplate).where(IEPTemplate.name == "PLOP and Goals Comprehensive Template (K-5)")
        )
        if existing_template.scalar_one_or_none():
            print("Template already exists, skipping creation")
            return
        
        # Define the comprehensive template structure based on the user's example
        template_sections = {
            "oral_language": {
                "required": True,
                "description": "Oral Language – Receptive and Expressive",
                "fields": {
                    "current_grade": "Current grade level for this domain",
                    "present_level": "Detailed present level of performance description",
                    "goals": "Specific measurable goals for improvement",
                    "recommendations": "Evidence-based recommendations for instruction"
                },
                "example_format": {
                    "current_grade": "Grade 4",
                    "present_level": "Has age-appropriate vocabulary and can speak in complete sentences. Commits grammatical mistakes during sentence construction. Can understand 2-step instructions, but follows one-step and task-based instructions with reminders...",
                    "goals": "Student will improve grammatical accuracy in sentence construction and general conversation. Student will consistently follow multi-step instructions without frequent reminders...",
                    "recommendations": "Focus on structured grammar exercises, practice following multi-step instructions, and encourage verbal expression in complete sentences."
                }
            },
            "reading_familiar": {
                "required": True,
                "description": "Reading – Familiar",
                "fields": {
                    "current_grade": "Current grade level for this domain",
                    "present_level": "Detailed present level of performance description",
                    "goals": "Specific measurable goals for improvement",
                    "recommendations": "Evidence-based recommendations for instruction"
                },
                "example_format": {
                    "current_grade": "Grade 4",
                    "present_level": "Able to read Grade 4 level text with 90% accuracy.",
                    "goals": "Student will maintain 90% accuracy in reading Grade 4 level familiar texts.",
                    "recommendations": "Continue providing Grade 4 level familiar texts for practice to maintain current reading proficiency."
                }
            },
            "reading_unfamiliar": {
                "required": True,
                "description": "Reading - Unfamiliar",
                "fields": {
                    "current_grade": "Current grade level for this domain",
                    "present_level": "Detailed present level of performance description",
                    "goals": "Specific measurable goals for improvement",
                    "recommendations": "Evidence-based recommendations for instruction"
                },
                "example_format": {
                    "current_grade": "Grade 2",
                    "present_level": "Shows difficulty reading multisyllabic words. Can do sound-letter association for most consonants (80% accuracy). Can identify initial/final sounds of words (80% accuracy)...",
                    "goals": "Student will improve reading accuracy for multisyllabic words. Student will develop word attack skills, including syllabication and using context clues...",
                    "recommendations": "Provide targeted instruction and practice on decoding multisyllabic words, explicitly teach syllabication and context clues, and continue practicing sight words."
                }
            },
            "reading_comprehension": {
                "required": True,
                "description": "Reading Comprehension",
                "fields": {
                    "current_grade": "Current grade level for this domain",
                    "present_level": "Detailed present level of performance description",
                    "goals": "Specific measurable goals for improvement",
                    "recommendations": "Evidence-based recommendations for instruction"
                },
                "example_format": {
                    "current_grade": "Grade 4",
                    "present_level": "Able to answer 100% factual questions and 50% inferential questions. Can answer factual questions in 1-2 sentences with help...",
                    "goals": "Student will increase accuracy in answering inferential questions to 80% independently. Student will improve the ability to answer knowledge-based, comprehension-based, and application-based questions with less prompting...",
                    "recommendations": "Focus on strategies for inferential thinking, provide opportunities for independent comprehension tasks, and encourage elaboration when expressing opinions."
                }
            },
            "spelling": {
                "required": True,
                "description": "Spelling",
                "fields": {
                    "current_grade": "Current grade level for this domain",
                    "present_level": "Detailed present level of performance description",
                    "goals": "Specific measurable goals for improvement",
                    "recommendations": "Evidence-based recommendations for instruction"
                },
                "example_format": {
                    "current_grade": "Grade 3",
                    "present_level": "Able to spell up to List 6 of Dolch sight words with 90% accuracy and lists 7 to 11 with 70% accuracy. Can spell CVC words with 80% accuracy...",
                    "goals": "Student will achieve 90% accuracy in spelling sight words from lists 7 to 11. Student will improve spelling accuracy for blends and keywords from curriculum lessons to 80%...",
                    "recommendations": "Provide targeted practice for sight words (lists 7-11), blends, and curriculum keywords. Incorporate regular spelling checks in written assignments."
                }
            },
            "writing": {
                "required": True,
                "description": "Writing",
                "fields": {
                    "current_grade": "Current grade level for this domain",
                    "present_level": "Detailed present level of performance description",
                    "goals": "Specific measurable goals for improvement",
                    "recommendations": "Evidence-based recommendations for instruction"
                },
                "example_format": {
                    "current_grade": "Grade 3",
                    "present_level": "Can write 3-4 sentences on a familiar topic but needs keywords/assistance for unfamiliar topics. Handwriting is illegible...",
                    "goals": "Student will improve handwriting legibility. Student will be able to write 3-4 sentences on unfamiliar topics with minimal assistance...",
                    "recommendations": "Implement specific handwriting practice, provide graphic organizers or sentence starters for unfamiliar topics, and reinforce punctuation rules through explicit instruction and practice."
                }
            },
            "handwriting": {
                "required": True,
                "description": "Handwriting",
                "fields": {
                    "present_level": "Detailed present level of performance description",
                    "goals": "Specific measurable goals for improvement",
                    "recommendations": "Evidence-based recommendations for instruction"
                },
                "example_format": {
                    "present_level": "Handwriting is illegible. While letter formation, conforming to lines, and spacing between letters are generally good, Student joins words. Can perform far point and near point copying.",
                    "goals": "Student will improve the legibility of handwriting. Student will increase spacing between words to improve overall readability.",
                    "recommendations": "Provide regular handwriting practice focusing on appropriate spacing between words."
                }
            },
            "grammar": {
                "required": True,
                "description": "Grammar",
                "fields": {
                    "present_level": "Detailed present level of performance description",
                    "goals": "Specific measurable goals for improvement",
                    "recommendations": "Evidence-based recommendations for instruction"
                },
                "example_format": {
                    "present_level": "Can identify nouns, verbs, prepositions, adjectives, pronouns, and articles with help. Can handle word order but struggles with singular/plural and tense.",
                    "goals": "Student will improve understanding and application of singular/plural and tense in sentences. Student will identify different parts of speech independently.",
                    "recommendations": "Provide explicit instruction and targeted practice on singular/plural forms and verb tenses. Use interactive activities to reinforce identification of parts of speech."
                }
            },
            "concept": {
                "required": True,
                "description": "Concept",
                "fields": {
                    "current_grade": "Current grade level for this domain",
                    "present_level": "Detailed present level of performance description",
                    "goals": "Specific measurable goals for improvement",
                    "recommendations": "Evidence-based recommendations for instruction"
                },
                "example_format": {
                    "current_grade": "Grade 3",
                    "present_level": "Has general awareness of things around him but is unable to generalize learned concepts. Can recall 60% of keywords with practice...",
                    "goals": "Student will improve the ability to generalize learned concepts to new situations. Student will increase recall of keywords from curriculum lessons to 90% independently...",
                    "recommendations": "Provide opportunities for applying concepts in real-world scenarios. Use flashcards and repeated exposure for keyword recall. Encourage writing complete sentences for answers."
                }
            },
            "math": {
                "required": True,
                "description": "Math",
                "fields": {
                    "current_grade": "Current grade level for this domain",
                    "present_level": "Detailed present level of performance description",
                    "goals": "Specific measurable goals for improvement",
                    "recommendations": "Evidence-based recommendations for instruction"
                },
                "example_format": {
                    "current_grade": "Grade 2",
                    "present_level": "No awareness of ascending or descending order and place value. Can add and subtract 2-digit numbers without carryover/borrowing. Can read up to 3-digit numbers...",
                    "goals": "Student will develop an understanding of ascending/descending order and place value. Student will improve proficiency in addition and subtraction with carryover/borrowing for 2-digit numbers...",
                    "recommendations": "Provide explicit instruction on place value, ascending/descending order, and advanced addition/subtraction. Integrate word problem-solving strategies, including writing statements. Practice multiplication tables regularly. Use visual aids and prompts for time and calendar concepts."
                }
            },
            "behaviour": {
                "required": True,
                "description": "Behaviour",
                "fields": {
                    "present_level": "Detailed present level of performance description",
                    "goals": "Specific measurable goals for improvement",
                    "recommendations": "Evidence-based recommendations for instruction"
                },
                "example_format": {
                    "present_level": "Student is a visual learner. Has a sitting tolerance of 15-20 minutes and an attention span of 5 minutes. Completes homework 60% of the time and tasks within stipulated time with minimal reminders...",
                    "goals": "Student will increase sitting tolerance and attention span during academic tasks. Student will improve homework completion rate. Student will demonstrate increased independent participation in all school activities...",
                    "recommendations": "Implement strategies to gradually increase sitting tolerance and attention span (e.g., timed activities, breaks). Provide visual schedules and checklists for organizational tasks. Encourage participation in a wider range of activities."
                }
            }
        }
        
        # Default goals specific to this PLOP format
        plop_goals = [
            {
                "domain": "Oral Language",
                "goal_template": "Student will improve grammatical accuracy in sentence construction and follow multi-step instructions without frequent reminders as measured by [measurement]",
                "measurement_suggestions": ["teacher observation", "language sampling", "structured tasks"]
            },
            {
                "domain": "Reading - Familiar",
                "goal_template": "Student will maintain or improve reading accuracy for familiar texts at grade level as measured by [measurement]",
                "measurement_suggestions": ["oral reading fluency", "running records", "comprehension assessments"]
            },
            {
                "domain": "Reading - Unfamiliar",
                "goal_template": "Student will improve decoding skills and word attack strategies for unfamiliar texts as measured by [measurement]",
                "measurement_suggestions": ["phonics assessments", "word reading tests", "syllabication tasks"]
            },
            {
                "domain": "Reading Comprehension",
                "goal_template": "Student will increase accuracy in answering inferential and higher-order thinking questions as measured by [measurement]",
                "measurement_suggestions": ["comprehension assessments", "question response accuracy", "discussion participation"]
            },
            {
                "domain": "Spelling",
                "goal_template": "Student will improve spelling accuracy for sight words, blends, and curriculum vocabulary as measured by [measurement]",
                "measurement_suggestions": ["spelling tests", "written work samples", "dictation tasks"]
            },
            {
                "domain": "Writing",
                "goal_template": "Student will improve handwriting legibility and written expression with proper punctuation as measured by [measurement]",
                "measurement_suggestions": ["writing samples", "handwriting assessments", "teacher rubrics"]
            },
            {
                "domain": "Grammar",
                "goal_template": "Student will improve understanding and application of grammatical concepts including parts of speech and verb tenses as measured by [measurement]",
                "measurement_suggestions": ["grammar assessments", "language usage in writing", "structured exercises"]
            },
            {
                "domain": "Concept Development",
                "goal_template": "Student will improve ability to generalize learned concepts and increase keyword recall as measured by [measurement]",
                "measurement_suggestions": ["concept mapping", "transfer tasks", "vocabulary assessments"]
            },
            {
                "domain": "Mathematics",
                "goal_template": "Student will improve mathematical concepts including place value, operations, and problem-solving as measured by [measurement]",
                "measurement_suggestions": ["math assessments", "problem-solving tasks", "computational fluency measures"]
            },
            {
                "domain": "Behavior",
                "goal_template": "Student will improve attention span, task completion, and organizational skills as measured by [measurement]",
                "measurement_suggestions": ["behavior tracking sheets", "task completion data", "organizational checklists"]
            }
        ]
        
        # Create the new template
        new_template = IEPTemplate(
            name="PLOP and Goals Comprehensive Template (K-5)",
            disability_type_id=sld_disability.id,
            grade_level="K-5",
            sections=template_sections,
            default_goals=plop_goals,
            version=1,
            is_active=True,
            created_by_auth_id=1  # System user
        )
        
        session.add(new_template)
        await session.commit()
        await session.refresh(new_template)
        
        print(f"✅ Successfully created PLOP template with ID: {new_template.id}")
        print(f"Template name: {new_template.name}")
        print(f"Sections included: {list(template_sections.keys())}")
        print(f"Default goals: {len(plop_goals)} goal templates")
        print(f"Grade level: {new_template.grade_level}")
        print(f"Disability type: SLD")
        
        return new_template.id

async def verify_template_creation(template_id):
    """Verify the template was created and is accessible via API"""
    from src.database import get_db_session
    from src.models.special_education_models import IEPTemplate
    from sqlalchemy import select
    
    async with get_db_session() as session:
        template = await session.execute(
            select(IEPTemplate).where(IEPTemplate.id == template_id)
        )
        template = template.scalar_one_or_none()
        
        if template:
            print(f"\n✅ Template verification successful:")
            print(f"   ID: {template.id}")
            print(f"   Name: {template.name}")
            print(f"   Sections: {len(template.sections)} sections")
            print(f"   Active: {template.is_active}")
            print(f"   Created: {template.created_at}")
            
            # Show section structure
            print(f"\n📋 Template sections:")
            for section_name, section_data in template.sections.items():
                print(f"   • {section_name}: {section_data['description']}")
                
            return True
        else:
            print(f"❌ Template verification failed - template {template_id} not found")
            return False

async def test_template_api_access(template_id):
    """Test that the template is accessible via the API endpoints"""
    import aiohttp
    import json
    
    try:
        # Test the templates API endpoint
        async with aiohttp.ClientSession() as session:
            # Test list templates
            async with session.get('http://localhost:8005/api/v1/templates') as response:
                if response.status == 200:
                    templates = await response.json()
                    template_found = any(t['id'] == template_id for t in templates.get('items', []))
                    if template_found:
                        print(f"✅ Template {template_id} found in API list")
                    else:
                        print(f"⚠️ Template {template_id} not found in API list")
                else:
                    print(f"⚠️ API list endpoint returned status {response.status}")
            
            # Test get specific template
            async with session.get(f'http://localhost:8005/api/v1/templates/{template_id}') as response:
                if response.status == 200:
                    template_data = await response.json()
                    print(f"✅ Template {template_id} accessible via API")
                    print(f"   Sections: {len(template_data.get('sections', {}))}")
                    print(f"   Goals: {len(template_data.get('default_goals', []))}")
                else:
                    print(f"⚠️ API get endpoint returned status {response.status}")
                    
    except Exception as e:
        print(f"⚠️ API test failed: {e}")
        print("Make sure the Special Education Service is running on port 8005")

async def main():
    print("🚀 Creating PLOP and Goals Comprehensive Template")
    print("=" * 60)
    
    try:
        # Create the template
        template_id = await create_plop_template()
        
        if template_id:
            # Verify creation
            await verify_template_creation(template_id)
            
            # Test API access
            print(f"\n🔍 Testing API access...")
            await test_template_api_access(template_id)
            
            print(f"\n🎉 Template creation complete!")
            print(f"Template ID: {template_id}")
            print(f"API URL: http://localhost:8005/api/v1/templates/{template_id}")
            print(f"Frontend URL: http://localhost:3002/templates/{template_id}")
            
            print(f"\n📝 Template Usage:")
            print(f"1. Access template via API: GET /api/v1/templates/{template_id}")
            print(f"2. Use in IEP generation: POST /api/v1/ieps/advanced/create-with-rag")
            print(f"3. View in frontend at: http://localhost:3002/templates")
            
        else:
            print("❌ Template creation failed")
            
    except Exception as e:
        print(f"❌ Error creating template: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())