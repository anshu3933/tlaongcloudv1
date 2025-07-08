"""
Migration script to create assessment pipeline tables in the shared database
"""
import asyncio
import sys
import os
from pathlib import Path
import logging

# Add the backend directory to Python path
backend_dir = Path(__file__).parent.parent
sys.path.append(str(backend_dir))

# Load environment variables
env_file = Path('/Users/anshu/Documents/GitHub/tlaongcloudv1/.env')
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            if line.strip() and not line.startswith('#'):
                key, _, value = line.partition('=')
                os.environ[key.strip()] = value.strip()

from special_education_service.src.database import get_db_session
from special_education_service.src.models.special_education_models import (
    Base, AssessmentDocument, PsychoedScore, ExtractedAssessmentData, 
    QuantifiedAssessmentData, AssessmentType
)
from sqlalchemy import text

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def create_assessment_tables():
    """Create assessment pipeline tables in the shared database"""
    
    try:
        logger.info("Creating assessment pipeline tables in shared database...")
        
        async with get_db_session() as session:
            # Create all tables including new assessment tables
            engine = session.bind
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            
            logger.info("Assessment tables created successfully")
            
            # Test the integration with a sample document
            # Get an existing student ID
            result = await session.execute(text("SELECT id, first_name, last_name FROM students LIMIT 1"))
            student_row = result.fetchone()
            
            if student_row:
                student_id, first_name, last_name = student_row
                logger.info(f"Testing with student: {first_name} {last_name}")
                
                # Create a test assessment document
                test_doc = AssessmentDocument(
                    student_id=student_id,
                    document_type=AssessmentType.WISC_V,
                    file_name="test_wisc_v_report.pdf",
                    file_path="/tmp/test_report.pdf",
                    processing_status="completed",
                    assessor_name="Dr. Test Psychologist",
                    assessor_title="School Psychologist"
                )
                
                session.add(test_doc)
                await session.commit()
                await session.refresh(test_doc)
                
                logger.info(f"Created test assessment document: {test_doc.id}")
                
                # Create a test psychoed score
                test_score = PsychoedScore(
                    document_id=test_doc.id,
                    test_name="WISC-V",
                    subtest_name="Full Scale IQ",
                    score_type="standard_score",
                    standard_score=95,
                    percentile_rank=37,
                    confidence_interval_lower=90,
                    confidence_interval_upper=100,
                    extraction_confidence=0.95
                )
                
                session.add(test_score)
                await session.commit()
                await session.refresh(test_score)
                
                logger.info(f"Created test psychoed score: {test_score.id}")
                
                # Create quantified assessment data
                test_quantified = QuantifiedAssessmentData(
                    student_id=student_id,
                    assessment_date=test_doc.upload_date,
                    cognitive_composite=45.0,  # Below average
                    academic_composite=35.0,   # Significantly below average
                    reading_composite=30.0,
                    math_composite=40.0,
                    writing_composite=32.0,
                    standardized_plop={
                        "academic_performance": {
                            "reading": {
                                "current_level": 2.5,
                                "strengths": ["phonemic awareness"],
                                "needs": ["comprehension", "fluency"]
                            }
                        }
                    },
                    eligibility_category="Specific Learning Disability",
                    primary_disability="SLD in Reading",
                    confidence_metrics={"extraction_confidence": 0.95}
                )
                
                session.add(test_quantified)
                await session.commit()
                await session.refresh(test_quantified)
                
                logger.info(f"Created test quantified data: {test_quantified.id}")
                
                # Verify relationships work
                await session.refresh(test_doc, ["student", "psychoed_scores"])
                logger.info(f"Document belongs to student: {test_doc.student.first_name} {test_doc.student.last_name}")
                logger.info(f"Document has {len(test_doc.psychoed_scores)} scores")
                
                return {
                    "status": "success",
                    "message": "Assessment pipeline tables created and tested successfully",
                    "test_document_id": str(test_doc.id),
                    "test_score_id": str(test_score.id),
                    "test_quantified_id": str(test_quantified.id),
                    "student_name": f"{first_name} {last_name}"
                }
            else:
                return {
                    "status": "success",
                    "message": "Assessment pipeline tables created (no students available for testing)",
                    "tables_created": True
                }
                
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        raise

async def verify_integration():
    """Verify the assessment pipeline integration"""
    
    try:
        async with get_db_session() as session:
            # Count assessment documents
            doc_count = await session.execute(text("SELECT COUNT(*) FROM assessment_documents"))
            doc_total = doc_count.scalar()
            
            # Count psychoed scores
            score_count = await session.execute(text("SELECT COUNT(*) FROM psychoed_scores"))
            score_total = score_count.scalar()
            
            # Count quantified data
            quant_count = await session.execute(text("SELECT COUNT(*) FROM quantified_assessment_data"))
            quant_total = quant_count.scalar()
            
            # Get student count
            student_count = await session.execute(text("SELECT COUNT(*) FROM students"))
            student_total = student_count.scalar()
            
            logger.info(f"Integration verification:")
            logger.info(f"  Students: {student_total}")
            logger.info(f"  Assessment Documents: {doc_total}")
            logger.info(f"  Psychoed Scores: {score_total}")
            logger.info(f"  Quantified Data: {quant_total}")
            
            return {
                "students": student_total,
                "assessment_documents": doc_total,
                "psychoed_scores": score_total,
                "quantified_data": quant_total,
                "integration_successful": doc_total > 0 or score_total > 0 or quant_total > 0
            }
            
    except Exception as e:
        logger.error(f"Verification failed: {e}")
        raise

if __name__ == "__main__":
    async def main():
        print("🔄 Assessment Pipeline Database Integration")
        print("=" * 50)
        
        # Create tables
        result = await create_assessment_tables()
        print(f"✅ {result['message']}")
        
        # Verify integration
        verification = await verify_integration()
        print(f"📊 Database Status:")
        print(f"   Students: {verification['students']}")
        print(f"   Assessment Documents: {verification['assessment_documents']}")
        print(f"   Psychoed Scores: {verification['psychoed_scores']}")
        print(f"   Quantified Data: {verification['quantified_data']}")
        
        if verification['integration_successful']:
            print("🎉 Assessment Pipeline Successfully Integrated!")
        else:
            print("⚠️ Integration completed but no test data created")
    
    asyncio.run(main())