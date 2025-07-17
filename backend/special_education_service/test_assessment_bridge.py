#!/usr/bin/env python3
"""
🔗 Assessment Data Bridge Test

This test verifies that the assessment data bridge correctly:
1. Fetches real assessment data using document_id
2. Formats test scores, composite scores, and educational objectives
3. Includes specific data in the LLM prompt
4. Generates evidence-based IEP content instead of hallucinated content
"""

import asyncio
import logging
import sys
import os
import json
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.services.iep_service import IEPService
from src.repositories.iep_repository import IEPRepository
from src.repositories.assessment_repository import AssessmentRepository
from src.utils.gemini_client import GeminiClient
from src.database import engine, create_tables, get_db_session
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import uuid4, UUID
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_assessment_bridge():
    """Test the complete assessment data bridge flow"""
    
    logger.info("🔗 Starting Assessment Data Bridge Test")
    
    # Initialize database
    await create_tables()
    
    async with get_db_session() as session:
        # Initialize repositories and services
        iep_repo = IEPRepository(session)
        assessment_repo = AssessmentRepository(session)
        
        # Create a test student (or use existing one)
        test_student_id = UUID("c6f74363-c1fb-4b0f-bd6b-0ae5c8a6f826")  # From your existing tests
        test_document_id = str(uuid4())
        
        logger.info(f"📋 Test setup - Student ID: {test_student_id}")
        logger.info(f"📄 Test setup - Document ID: {test_document_id}")
        
        # 1. Create mock assessment data to simulate Document AI results
        logger.info("🧪 Creating mock assessment data...")
        
        # Create extracted assessment data (simulating Document AI output)
        mock_extracted_data = {
            "document_id": UUID(test_document_id),
            "structured_data": {
                "educational_objectives": [
                    {
                        "area": "Reading Comprehension",
                        "current_performance": "Currently reading at 2nd grade level with difficulty understanding main ideas",
                        "goal": "Will improve reading comprehension to 3rd grade level",
                        "measurable_outcome": "80% accuracy on grade-level passages",
                        "support_needed": "Small group instruction and graphic organizers"
                    },
                    {
                        "area": "Mathematics",
                        "current_performance": "Struggles with multi-step word problems, strong in computation",
                        "goal": "Will solve 2-step word problems with 75% accuracy",
                        "measurable_outcome": "Correct solution with work shown",
                        "support_needed": "Visual supports and step-by-step guides"
                    }
                ],
                "performance_levels": {
                    "reading": {
                        "current_level": "Student reads at early 2nd grade level, requires support for comprehension"
                    },
                    "mathematics": {
                        "current_level": "Grade-level computation skills, below grade level in problem solving"
                    },
                    "writing": {
                        "current_level": "Writes simple sentences, needs support for organization"
                    }
                },
                "strengths": [
                    "Strong mathematical computation skills",
                    "Good visual processing abilities", 
                    "Responds well to structured instruction",
                    "Motivated to learn when given appropriate supports"
                ],
                "areas_of_concern": [
                    "Reading comprehension below grade level",
                    "Difficulty with multi-step problem solving",
                    "Written expression organization challenges",
                    "Attention and focus during independent work"
                ],
                "recommendations": [
                    "Provide small group reading instruction with explicit comprehension strategies",
                    "Use visual supports and graphic organizers for problem solving",
                    "Implement structured writing framework with sentence starters",
                    "Break complex tasks into smaller, manageable steps",
                    "Provide frequent breaks and movement opportunities"
                ]
            },
            "extraction_confidence": 0.87,
            "extraction_method": "google_document_ai",
            "completeness_score": 0.92
        }
        
        # Save mock extracted data
        try:
            created_extracted = await assessment_repo.create_extracted_assessment_data(mock_extracted_data)
            logger.info(f"✅ Created mock extracted data: {created_extracted['id']}")
        except Exception as e:
            logger.error(f"❌ Error creating extracted data: {e}")
            return
        
        # Create mock test scores (simulating Document AI score extraction)
        mock_scores = [
            {
                "document_id": UUID(test_document_id),
                "test_name": "WISC-V",
                "subtest_name": "Verbal Comprehension Index",
                "standard_score": 85,
                "percentile_rank": 16,
                "score_type": "composite",
                "extraction_confidence": 0.91
            },
            {
                "document_id": UUID(test_document_id), 
                "test_name": "WIAT-IV",
                "subtest_name": "Reading Comprehension",
                "standard_score": 78,
                "percentile_rank": 7,
                "score_type": "subtest",
                "extraction_confidence": 0.88
            },
            {
                "document_id": UUID(test_document_id),
                "test_name": "WIAT-IV", 
                "subtest_name": "Mathematical Problem Solving",
                "standard_score": 82,
                "percentile_rank": 12,
                "score_type": "subtest",
                "extraction_confidence": 0.85
            }
        ]
        
        # Save mock test scores
        for score_data in mock_scores:
            try:
                created_score = await assessment_repo.create_psychoed_score(score_data)
                logger.info(f"✅ Created mock test score: {created_score['id']}")
            except Exception as e:
                logger.error(f"❌ Error creating test score: {e}")
        
        # Create mock quantified data
        mock_quantified = {
            "student_id": test_student_id,
            "assessment_date": "2025-01-15",
            "cognitive_composite": 68.5,  # Based on WISC-V VCI of 85
            "academic_composite": 62.0,   # Based on WIAT-IV scores
            "reading_composite": 58.7,    # Based on reading comprehension score
            "math_composite": 65.3,       # Based on math problem solving
            "standardized_plop": {
                "reading_level": "2.1",
                "math_level": "2.8", 
                "writing_level": "2.0"
            },
            "priority_goals": {
                "reading": "Improve comprehension to grade level",
                "math": "Develop problem-solving strategies",
                "writing": "Increase organization and length"
            },
            "eligibility_category": "Specific Learning Disability",
            "primary_disability": "SLD"
        }
        
        try:
            created_quantified = await assessment_repo.create_quantified_assessment_data(mock_quantified)
            logger.info(f"✅ Created mock quantified data: {created_quantified['id']}")
        except Exception as e:
            logger.error(f"❌ Error creating quantified data: {e}")
        
        await session.commit()
        logger.info("🗃️ All mock assessment data saved successfully")
        
        # 2. Test the IEP service with assessment bridge
        logger.info("🚀 Testing IEP generation with assessment data bridge...")
        
        # Initialize IEP service
        gemini_client = GeminiClient()
        iep_service = IEPService(iep_repo, gemini_client)
        
        # Create IEP request with document_id (this triggers the bridge)
        iep_request_data = {
            "content": {
                "assessment_summary": "Assessment data processed through Document AI pipeline",
                "document_id": test_document_id  # 🔑 This is the key - triggers the bridge!
            },
            "meeting_date": "2025-01-20",
            "effective_date": "2025-01-20", 
            "review_date": "2026-01-20"
        }
        
        # Generate IEP with real assessment data
        start_time = time.time()
        
        try:
            logger.info("🤖 Calling create_iep_with_rag with assessment bridge...")
            generated_iep = await iep_service.create_iep_with_rag(
                student_id=test_student_id,
                template_id=None,  # Will use default template
                academic_year="2025-2026",
                initial_data=iep_request_data,
                user_id=UUID("12345678-1234-5678-9012-123456789012"),
                user_role="teacher"
            )
            
            end_time = time.time()
            logger.info(f"✅ IEP generation completed in {end_time - start_time:.2f} seconds")
            
            # 3. Analyze the generated content
            logger.info("🔍 Analyzing generated IEP content...")
            
            content = generated_iep.get("content", {})
            if isinstance(content, dict):
                # Check if the content includes specific assessment data
                content_str = json.dumps(content, indent=2)
                
                # Look for evidence of real assessment data usage
                evidence_found = []
                
                if "85" in content_str or "78" in content_str or "82" in content_str:
                    evidence_found.append("✅ Specific test scores referenced")
                
                if "2nd grade level" in content_str or "reading comprehension" in content_str.lower():
                    evidence_found.append("✅ Specific performance levels referenced") 
                
                if "visual processing" in content_str.lower() or "computation skills" in content_str.lower():
                    evidence_found.append("✅ Identified strengths referenced")
                
                if "multi-step" in content_str.lower() or "problem solving" in content_str.lower():
                    evidence_found.append("✅ Areas of concern referenced")
                
                if "graphic organizers" in content_str.lower() or "small group" in content_str.lower():
                    evidence_found.append("✅ Specific recommendations included")
                
                logger.info("📊 Assessment Data Bridge Results:")
                if evidence_found:
                    for evidence in evidence_found:
                        logger.info(f"  {evidence}")
                    logger.info(f"🎯 SUCCESS: Assessment bridge working! {len(evidence_found)}/5 evidence types found")
                else:
                    logger.warning("⚠️  No specific assessment data found in generated content")
                    logger.warning("❌ Assessment bridge may not be working properly")
                
                # Show sample content
                logger.info("📄 Sample generated content sections:")
                for section_name, section_content in list(content.items())[:3]:
                    if isinstance(section_content, str):
                        preview = section_content[:200] + "..." if len(section_content) > 200 else section_content
                        logger.info(f"  {section_name}: {preview}")
                
            else:
                logger.error("❌ Generated content is not in expected dict format")
                
        except Exception as e:
            logger.error(f"❌ Error during IEP generation: {e}")
            import traceback
            traceback.print_exc()
        
        # 4. Test summary
        logger.info("🏁 Assessment Data Bridge Test Complete")
        logger.info("Expected outcome: IEP content should reference specific test scores,")
        logger.info("performance levels, strengths, and recommendations from the assessment data")
        logger.info("instead of generating generic content.")

if __name__ == "__main__":
    asyncio.run(test_assessment_bridge())