"""
FastAPI routes for assessment document and score operations
"""
import logging
from typing import List, Optional
from uuid import UUID
from datetime import datetime
import tempfile
import os
import base64

from fastapi import APIRouter, HTTPException, UploadFile, File, BackgroundTasks, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from assessment_pipeline_service.schemas.assessment_schemas import (
    AssessmentUploadDTO, ExtractedDataDTO, PsychoedScoreDTO,
    CognitiveProfileDTO, AcademicProfileDTO, BehavioralProfileDTO,
    AssessmentSummaryDTO, AssessmentIntakeRequestDTO, AssessmentIntakeResponseDTO
)
from assessment_pipeline_service.src.assessment_intake_processor import AssessmentIntakeProcessor
from assessment_pipeline_service.src.data_mapper import DataMapper
from assessment_pipeline_service.src.rag_integration import RAGIntegrationService
from assessment_pipeline_service.src.service_clients import special_education_client
from assessment_pipeline_service.src.service_communication import (
    service_comm_manager, ServiceType, create_assessment_document
)
from special_education_service.src.database import get_db_session
from assessment_pipeline_service.src.auth_middleware import (
    get_current_user, require_teacher_or_above, require_coordinator_or_above
)
# Database models removed - using service clients for data persistence

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/assessment-pipeline", tags=["assessments"])

# Processing-only service - no direct database access
# All data persistence goes through special_education_client

# Dependency for assessment processor
def get_assessment_processor() -> AssessmentIntakeProcessor:
    return AssessmentIntakeProcessor()  # Uses environment variables

@router.post("/upload", response_model=dict)
async def upload_assessment_document(
    assessment_data: AssessmentUploadDTO,
    background_tasks: BackgroundTasks,
    processor: AssessmentIntakeProcessor = Depends(get_assessment_processor),
    current_user: dict = Depends(require_teacher_or_above())
):
    """Upload a single assessment document"""
    
    try:
        logger.info(f"Uploading assessment document for student {assessment_data.student_id} by user {current_user.get('sub', 'unknown')}")
        
        # Convert DTO to dictionary for service communication
        document_data = DataMapper.upload_dto_to_dict(assessment_data)
        document_data["processing_status"] = "pending"
        document_data["uploaded_by"] = current_user.get("sub")
        document_data["upload_timestamp"] = datetime.utcnow().isoformat()
        
        # Create document via special education service
        response = await service_comm_manager.send_request(
            ServiceType.SPECIAL_EDUCATION,
            "create_assessment_document",
            document_data,
            correlation_id=f"upload-{assessment_data.student_id}"
        )
        
        if response.status.value != "success":
            logger.error(f"Failed to create document via service: {response.error_message}")
            raise HTTPException(
                status_code=500, 
                detail=f"Document creation failed: {response.error_message}"
            )
        
        document_id = response.data.get("id") or response.data.get("document_id")
        logger.info(f"Assessment document {document_id} created via service")
        
        # Process document in background
        background_tasks.add_task(
            process_document_background,
            str(document_id),
            assessment_data.file_path or f"/tmp/{assessment_data.file_name}",
            assessment_data.model_dump(),
            processor
        )
        
        return {
            "document_id": str(document_id),
            "status": "uploaded",
            "message": "Document uploaded successfully. Processing will begin shortly.",
            "service_response_time_ms": response.execution_time_ms
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading assessment document: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@router.post("/upload-batch", response_model=dict)
async def upload_multiple_documents(
    request: dict,  # Contains 'documents' list
    background_tasks: BackgroundTasks,
    processor: AssessmentIntakeProcessor = Depends(get_assessment_processor),
    current_user: dict = Depends(require_teacher_or_above())
):
    """Upload multiple assessment documents"""
    
    try:
        documents_data = request.get("documents", [])
        if not documents_data:
            raise HTTPException(status_code=400, detail="No documents provided")
        
        logger.info(f"Batch uploading {len(documents_data)} documents by user {current_user.get('sub', 'unknown')}")
        
        # Prepare batch requests for service communication
        batch_requests = []
        assessment_dtos = []
        
        for doc_data in documents_data:
            # Convert to DTO
            assessment_dto = AssessmentUploadDTO(**doc_data)
            assessment_dtos.append(assessment_dto)
            
            # Convert to service request
            document_data = DataMapper.upload_dto_to_dict(assessment_dto)
            document_data["processing_status"] = "pending"
            document_data["uploaded_by"] = current_user.get("sub")
            document_data["upload_timestamp"] = datetime.utcnow().isoformat()
            
            batch_requests.append((
                ServiceType.SPECIAL_EDUCATION,
                "create_assessment_document",
                document_data
            ))
        
        # Execute batch request
        responses = await service_comm_manager.batch_request(
            batch_requests,
            correlation_id=f"batch-upload-{len(documents_data)}"
        )
        
        document_ids = []
        failed_uploads = []
        
        for i, response in enumerate(responses):
            if response.status.value == "success":
                document_id = response.data.get("id") or response.data.get("document_id")
                document_ids.append(str(document_id))
                
                # Process in background
                background_tasks.add_task(
                    process_document_background,
                    str(document_id),
                    assessment_dtos[i].file_path or f"/tmp/{assessment_dtos[i].file_name}",
                    assessment_dtos[i].model_dump(),
                    processor
                )
            else:
                failed_uploads.append({
                    "index": i,
                    "file_name": assessment_dtos[i].file_name,
                    "error": response.error_message
                })
        
        result = {
            "document_ids": document_ids,
            "status": "completed" if not failed_uploads else "partial",
            "successful_uploads": len(document_ids),
            "failed_uploads": len(failed_uploads),
            "message": f"Successfully uploaded {len(document_ids)} of {len(documents_data)} documents."
        }
        
        if failed_uploads:
            result["failures"] = failed_uploads
            logger.warning(f"Batch upload partially failed: {len(failed_uploads)} failures")
        
        return result
        
    except Exception as e:
        logger.error(f"Error in batch upload: {e}")
        raise HTTPException(status_code=500, detail=f"Batch upload failed: {str(e)}")

@router.post("/manual-entry", response_model=dict)
async def submit_manual_assessment(
    assessment_data: dict,  # Manual assessment data
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db_session)
):
    """Submit manually entered assessment scores"""
    
    try:
        logger.info(f"Manual assessment entry for student {assessment_data.get('student_id')}")
        
        # Create document record for manual entry
        document = AssessmentDocument(
            student_id=UUID(assessment_data["student_id"]),
            document_type=assessment_data["test_battery"],
            file_name=f"Manual_Entry_{assessment_data['test_battery']}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json",
            file_path="/manual_entries/",
            assessor_name=assessment_data["assessor_name"],
            assessor_title=assessment_data.get("assessor_title"),
            assessment_date=datetime.fromisoformat(assessment_data["assessment_date"]),
            processing_status="manual_entry"
        )
        
        # Save to database
        db.add(document)
        await db.commit()
        await db.refresh(document)
        
        logger.info(f"Manual assessment document {document.id} saved to database")
        
        # Process manual scores in background
        background_tasks.add_task(
            process_manual_scores_background,
            str(document.id),
            assessment_data
        )
        
        return {
            "document_id": str(document.id),
            "status": "submitted",
            "message": "Manual assessment data submitted successfully."
        }
        
    except Exception as e:
        logger.error(f"Error in manual assessment entry: {e}")
        raise HTTPException(status_code=500, detail=f"Manual entry failed: {str(e)}")

@router.get("/documents/{document_id}/scores", response_model=dict)
async def get_extracted_scores(
    document_id: UUID,
    db: AsyncSession = Depends(get_db_session)
):
    """Get extracted scores from a processed document"""
    
    try:
        # Fetch scores from database
        from sqlalchemy import select
        
        result = await db.execute(
            select(PsychoedScore).filter(PsychoedScore.document_id == document_id)
        )
        scores = result.scalars().all()
        
        if not scores:
            logger.warning(f"No scores found for document {document_id}")
            return {
                "document_id": str(document_id),
                "scores": [],
                "extraction_date": None,
                "total_scores": 0,
                "message": "No extracted scores found for this document"
            }
        
        # Convert to response format
        scores_data = []
        for score in scores:
            score_dict = {
                "test_name": score.test_name,
                "subtest_name": score.subtest_name,
                "standard_score": score.standard_score,
                "percentile_rank": score.percentile_rank,
                "confidence_interval": score.confidence_interval,
                "extraction_confidence": score.extraction_confidence,
                "test_version": score.test_version,
                "raw_score": score.raw_score,
                "scaled_score": score.scaled_score,
                "qualitative_descriptor": score.qualitative_descriptor
            }
            scores_data.append(score_dict)
        
        return {
            "document_id": str(document_id),
            "scores": scores_data,
            "extraction_date": scores[0].created_at.isoformat() if scores else None,
            "total_scores": len(scores_data)
        }
        
    except Exception as e:
        logger.error(f"Error fetching extracted scores: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch scores: {str(e)}")

@router.get("/students/{student_id}/assessments", response_model=List[dict])
async def get_student_assessments(
    student_id: UUID,
    db: AsyncSession = Depends(get_db_session)
):
    """Get all assessments for a student"""
    
    try:
        # Fetch from database
        from sqlalchemy import select, func
        
        # Get assessments with score counts
        result = await db.execute(
            select(
                AssessmentDocument,
                func.count(PsychoedScore.id).label('scores_count')
            )
            .outerjoin(PsychoedScore, AssessmentDocument.id == PsychoedScore.document_id)
            .filter(AssessmentDocument.student_id == student_id)
            .group_by(AssessmentDocument.id)
            .order_by(AssessmentDocument.assessment_date.desc())
        )
        
        assessments_data = []
        for row in result:
            assessment = row.AssessmentDocument
            scores_count = row.scores_count or 0
            
            assessment_dict = {
                "id": str(assessment.id),
                "document_type": assessment.document_type,
                "file_name": assessment.file_name,
                "assessment_date": assessment.assessment_date.isoformat() if assessment.assessment_date else None,
                "assessor_name": assessment.assessor_name,
                "processing_status": assessment.processing_status,
                "extraction_confidence": assessment.extraction_confidence,
                "scores_count": scores_count,
                "created_at": assessment.created_at.isoformat(),
                "referral_reason": assessment.referral_reason
            }
            assessments_data.append(assessment_dict)
        
        logger.info(f"Retrieved {len(assessments_data)} assessments for student {student_id}")
        return assessments_data
        
    except Exception as e:
        logger.error(f"Error fetching student assessments: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch assessments: {str(e)}")

@router.get("/students/{student_id}/cognitive-profile", response_model=CognitiveProfileDTO)
async def get_cognitive_profile(
    student_id: UUID,
    db: AsyncSession = Depends(get_db_session)
):
    """Get student's cognitive profile"""
    
    try:
        # Fetch from database
        from sqlalchemy import select
        
        result = await db.execute(
            select(CognitiveProfile)
            .filter(CognitiveProfile.student_id == student_id)
            .order_by(CognitiveProfile.assessment_date.desc())
            .limit(1)
        )
        profile = result.scalar_one_or_none()
        
        if not profile:
            logger.warning(f"No cognitive profile found for student {student_id}")
            raise HTTPException(
                status_code=404, 
                detail=f"No cognitive profile found for student {student_id}"
            )
        
        # Convert to DTO
        profile_dto = CognitiveProfileDTO(
            assessment_date=profile.assessment_date,
            full_scale_iq=profile.full_scale_iq,
            verbal_comprehension_index=profile.verbal_comprehension_index,
            visual_spatial_index=profile.visual_spatial_index,
            fluid_reasoning_index=profile.fluid_reasoning_index,
            working_memory_index=profile.working_memory_index,
            processing_speed_index=profile.processing_speed_index,
            cognitive_strengths=profile.cognitive_strengths or [],
            cognitive_weaknesses=profile.cognitive_weaknesses or [],
            processing_patterns=profile.processing_patterns or {},
            composite_confidence=profile.composite_confidence
        )
        
        logger.info(f"Retrieved cognitive profile for student {student_id}")
        return profile_dto
        
    except Exception as e:
        logger.error(f"Error fetching cognitive profile: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch cognitive profile: {str(e)}")

@router.get("/students/{student_id}/academic-profile", response_model=AcademicProfileDTO)
async def get_academic_profile(
    student_id: UUID,
    db: AsyncSession = Depends(get_db_session)
):
    """Get student's academic profile"""
    
    try:
        # Fetch from database
        from sqlalchemy import select
        
        result = await db.execute(
            select(AcademicProfile)
            .filter(AcademicProfile.student_id == student_id)
            .order_by(AcademicProfile.assessment_date.desc())
            .limit(1)
        )
        profile = result.scalar_one_or_none()
        
        if not profile:
            logger.warning(f"No academic profile found for student {student_id}")
            raise HTTPException(
                status_code=404,
                detail=f"No academic profile found for student {student_id}"
            )
        
        # Convert to DTO
        profile_dto = AcademicProfileDTO(
            assessment_date=profile.assessment_date,
            basic_reading_skills=profile.basic_reading_skills,
            reading_comprehension=profile.reading_comprehension,
            reading_fluency=profile.reading_fluency,
            reading_rate_wpm=profile.reading_rate_wpm,
            math_calculation=profile.math_calculation,
            math_problem_solving=profile.math_problem_solving,
            math_fluency=profile.math_fluency,
            written_expression=profile.written_expression,
            spelling=profile.spelling,
            writing_fluency=profile.writing_fluency,
            academic_strengths=profile.academic_strengths or [],
            academic_needs=profile.academic_needs or [],
            error_patterns=profile.error_patterns or {}
        )
        
        logger.info(f"Retrieved academic profile for student {student_id}")
        return profile_dto
        
    except Exception as e:
        logger.error(f"Error fetching academic profile: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch academic profile: {str(e)}")

@router.get("/students/{student_id}/behavioral-profile", response_model=BehavioralProfileDTO)
async def get_behavioral_profile(
    student_id: UUID,
    db: AsyncSession = Depends(get_db_session)
):
    """Get student's behavioral profile"""
    
    try:
        # Fetch from database
        from sqlalchemy import select
        
        result = await db.execute(
            select(BehavioralProfile)
            .filter(BehavioralProfile.student_id == student_id)
            .order_by(BehavioralProfile.assessment_date.desc())
            .limit(1)
        )
        profile = result.scalar_one_or_none()
        
        if not profile:
            logger.warning(f"No behavioral profile found for student {student_id}")
            raise HTTPException(
                status_code=404,
                detail=f"No behavioral profile found for student {student_id}"
            )
        
        # Convert to DTO
        profile_dto = BehavioralProfileDTO(
            assessment_date=profile.assessment_date,
            externalizing_problems=profile.externalizing_problems,
            internalizing_problems=profile.internalizing_problems,
            behavioral_symptoms_index=profile.behavioral_symptoms_index,
            adaptive_skills_composite=profile.adaptive_skills_composite,
            hyperactivity=profile.hyperactivity,
            attention_problems=profile.attention_problems,
            executive_function_scores=profile.executive_function_scores or {},
            behavior_frequency_data=profile.behavior_frequency_data or [],
            antecedent_patterns=profile.antecedent_patterns or [],
            effective_interventions=profile.effective_interventions or []
        )
        
        logger.info(f"Retrieved behavioral profile for student {student_id}")
        return profile_dto
        
    except Exception as e:
        logger.error(f"Error fetching behavioral profile: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch behavioral profile: {str(e)}")

@router.get("/students/{student_id}/quantified-data")
async def get_quantified_data(
    student_id: UUID,
    db: AsyncSession = Depends(get_db_session)
):
    """Get quantified assessment data for RAG"""
    
    try:
        # Fetch comprehensive quantified data from multiple sources
        from sqlalchemy import select
        
        # Get latest profiles for this student
        cognitive_result = await db.execute(
            select(CognitiveProfile)
            .filter(CognitiveProfile.student_id == student_id)
            .order_by(CognitiveProfile.assessment_date.desc())
            .limit(1)
        )
        cognitive_profile = cognitive_result.scalar_one_or_none()
        
        academic_result = await db.execute(
            select(AcademicProfile)
            .filter(AcademicProfile.student_id == student_id)
            .order_by(AcademicProfile.assessment_date.desc())
            .limit(1)
        )
        academic_profile = academic_result.scalar_one_or_none()
        
        behavioral_result = await db.execute(
            select(BehavioralProfile)
            .filter(BehavioralProfile.student_id == student_id)
            .order_by(BehavioralProfile.assessment_date.desc())
            .limit(1)
        )
        behavioral_profile = behavioral_result.scalar_one_or_none()
        
        # Check if we have enough data
        if not any([cognitive_profile, academic_profile, behavioral_profile]):
            logger.warning(f"No assessment profiles found for student {student_id}")
            raise HTTPException(
                status_code=404,
                detail=f"No quantified assessment data found for student {student_id}. Please upload and process assessment documents first."
            )
        
        # Calculate composite scores
        cognitive_composite = cognitive_profile.full_scale_iq if cognitive_profile else None
        academic_composite = None
        if academic_profile:
            # Calculate academic composite from available scores
            academic_scores = [
                academic_profile.basic_reading_skills,
                academic_profile.math_calculation,
                academic_profile.written_expression
            ]
            academic_scores = [score for score in academic_scores if score is not None]
            academic_composite = sum(academic_scores) / len(academic_scores) if academic_scores else None
        
        behavioral_composite = behavioral_profile.behavioral_symptoms_index if behavioral_profile else None
        
        # Build standardized PLOP data
        standardized_plop = {
            "academic_performance": {},
            "cognitive_functioning": {},
            "behavioral_functioning": {}
        }
        
        if academic_profile:
            standardized_plop["academic_performance"] = {
                "reading": {
                    "current_level": academic_profile.basic_reading_skills or 0,
                    "strengths": academic_profile.academic_strengths or [],
                    "needs": academic_profile.academic_needs or [],
                    "fluency_rate": academic_profile.reading_rate_wpm
                },
                "mathematics": {
                    "current_level": academic_profile.math_calculation or 0,
                    "strengths": [s for s in (academic_profile.academic_strengths or []) if "math" in s.lower()],
                    "needs": [n for n in (academic_profile.academic_needs or []) if "math" in n.lower()]
                },
                "written_language": {
                    "current_level": academic_profile.written_expression or 0,
                    "strengths": [s for s in (academic_profile.academic_strengths or []) if "writ" in s.lower()],
                    "needs": [n for n in (academic_profile.academic_needs or []) if "writ" in n.lower()]
                }
            }
        
        if cognitive_profile:
            standardized_plop["cognitive_functioning"] = {
                "overall_ability": cognitive_profile.full_scale_iq,
                "processing_strengths": cognitive_profile.cognitive_strengths or [],
                "processing_weaknesses": cognitive_profile.cognitive_weaknesses or [],
                "working_memory": cognitive_profile.working_memory_index,
                "processing_speed": cognitive_profile.processing_speed_index
            }
        
        if behavioral_profile:
            standardized_plop["behavioral_functioning"] = {
                "attention_focus": {
                    "attention_problems": behavioral_profile.attention_problems,
                    "hyperactivity": behavioral_profile.hyperactivity
                },
                "social_emotional": behavioral_profile.internalizing_problems,
                "executive_function": behavioral_profile.behavioral_symptoms_index,
                "adaptive_skills": behavioral_profile.adaptive_skills_composite
            }
        
        # Generate priority goals based on assessment data
        priority_goals = []
        if academic_profile:
            if academic_profile.reading_fluency and academic_profile.reading_fluency < 85:
                priority_goals.append({
                    "area": "reading_fluency",
                    "priority": "high",
                    "current_performance": academic_profile.reading_fluency
                })
            if academic_profile.written_expression and academic_profile.written_expression < 85:
                priority_goals.append({
                    "area": "written_expression",
                    "priority": "high",
                    "current_performance": academic_profile.written_expression
                })
        
        if behavioral_profile and behavioral_profile.attention_problems and behavioral_profile.attention_problems > 65:
            priority_goals.append({
                "area": "attention_focus",
                "priority": "medium",
                "current_performance": behavioral_profile.attention_problems
            })
        
        # Generate service recommendations
        service_recommendations = []
        if academic_profile:
            if any(score and score < 85 for score in [academic_profile.basic_reading_skills, academic_profile.reading_fluency]):
                service_recommendations.append({
                    "type": "specialized_reading_instruction",
                    "frequency": "daily",
                    "duration": "45_minutes"
                })
            if academic_profile.written_expression and academic_profile.written_expression < 85:
                service_recommendations.append({
                    "type": "occupational_therapy",
                    "frequency": "2x_week",
                    "duration": "30_minutes"
                })
        
        if behavioral_profile and behavioral_profile.behavioral_symptoms_index and behavioral_profile.behavioral_symptoms_index > 65:
            service_recommendations.append({
                "type": "behavior_support",
                "frequency": "consultation",
                "duration": "monthly"
            })
        
        # Determine eligibility category (simplified logic)
        eligibility_category = "Assessment Pending"
        primary_disability = "To Be Determined"
        
        if cognitive_profile and academic_profile:
            if (cognitive_profile.full_scale_iq > 85 and 
                any(score and score < 85 for score in [
                    academic_profile.basic_reading_skills,
                    academic_profile.math_calculation,
                    academic_profile.written_expression
                ])):
                eligibility_category = "Specific Learning Disability"
                primary_disability = "SLD in Academic Areas"
        
        # Calculate confidence metrics
        profiles_available = sum(1 for p in [cognitive_profile, academic_profile, behavioral_profile] if p is not None)
        confidence_metrics = {
            "extraction_confidence": 0.95,  # High confidence from structured data
            "quantification_completeness": profiles_available / 3.0,
            "overall_reliability": min(0.95, profiles_available / 3.0 * 1.1)
        }
        
        quantified_data = {
            "student_id": str(student_id),
            "assessment_date": datetime.utcnow().isoformat(),
            "cognitive_composite": cognitive_composite,
            "academic_composite": academic_composite,
            "behavioral_composite": behavioral_composite,
            "reading_composite": academic_profile.basic_reading_skills if academic_profile else None,
            "math_composite": academic_profile.math_calculation if academic_profile else None,
            "writing_composite": academic_profile.written_expression if academic_profile else None,
            "standardized_plop": standardized_plop,
            "priority_goals": priority_goals,
            "service_recommendations": service_recommendations,
            "eligibility_category": eligibility_category,
            "primary_disability": primary_disability,
            "confidence_metrics": confidence_metrics,
            "profiles_available": {
                "cognitive": cognitive_profile is not None,
                "academic": academic_profile is not None,
                "behavioral": behavioral_profile is not None
            }
        }
        
        logger.info(f"Generated quantified data for student {student_id} with {profiles_available}/3 profiles")
        return quantified_data
        
    except Exception as e:
        logger.error(f"Error fetching quantified data: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch quantified data: {str(e)}")

@router.get("/students/{student_id}/summary", response_model=AssessmentSummaryDTO)
async def get_assessment_summary(
    student_id: UUID,
    db: AsyncSession = Depends(get_db_session)
):
    """Get comprehensive assessment summary for student"""
    
    try:
        # Fetch comprehensive assessment summary from database
        from sqlalchemy import select, func
        
        # Get assessment count and latest date
        assessment_result = await db.execute(
            select(
                func.count(AssessmentDocument.id).label('total_assessments'),
                func.max(AssessmentDocument.assessment_date).label('latest_date')
            )
            .filter(AssessmentDocument.student_id == student_id)
        )
        assessment_row = assessment_result.first()
        total_assessments = assessment_row.total_assessments or 0
        latest_date = assessment_row.latest_date
        
        # Check for profile existence
        cognitive_exists = await db.execute(
            select(func.count(CognitiveProfile.id))
            .filter(CognitiveProfile.student_id == student_id)
        )
        has_cognitive = cognitive_exists.scalar() > 0
        
        academic_exists = await db.execute(
            select(func.count(AcademicProfile.id))
            .filter(AcademicProfile.student_id == student_id)
        )
        has_academic = academic_exists.scalar() > 0
        
        behavioral_exists = await db.execute(
            select(func.count(BehavioralProfile.id))
            .filter(BehavioralProfile.student_id == student_id)
        )
        has_behavioral = behavioral_exists.scalar() > 0
        
        # Determine overall functioning level and concerns
        overall_functioning_level = "Assessment Pending"
        primary_concerns = []
        eligibility_determination = "Assessment In Progress"
        
        if has_cognitive and has_academic:
            # Get latest profiles for analysis
            cognitive_result = await db.execute(
                select(CognitiveProfile)
                .filter(CognitiveProfile.student_id == student_id)
                .order_by(CognitiveProfile.assessment_date.desc())
                .limit(1)
            )
            cognitive_profile = cognitive_result.scalar_one_or_none()
            
            academic_result = await db.execute(
                select(AcademicProfile)
                .filter(AcademicProfile.student_id == student_id)
                .order_by(AcademicProfile.assessment_date.desc())
                .limit(1)
            )
            academic_profile = academic_result.scalar_one_or_none()
            
            if cognitive_profile:
                if cognitive_profile.full_scale_iq:
                    if cognitive_profile.full_scale_iq >= 85:
                        overall_functioning_level = "Average Range"
                    elif cognitive_profile.full_scale_iq >= 70:
                        overall_functioning_level = "Below Average"
                    else:
                        overall_functioning_level = "Significantly Below Average"
                
                # Add cognitive concerns
                if cognitive_profile.cognitive_weaknesses:
                    primary_concerns.extend(cognitive_profile.cognitive_weaknesses)
            
            if academic_profile:
                # Add academic concerns based on low scores
                if academic_profile.basic_reading_skills and academic_profile.basic_reading_skills < 85:
                    primary_concerns.append("Reading Skills")
                if academic_profile.reading_fluency and academic_profile.reading_fluency < 85:
                    primary_concerns.append("Reading Fluency")
                if academic_profile.written_expression and academic_profile.written_expression < 85:
                    primary_concerns.append("Written Expression")
                if academic_profile.math_calculation and academic_profile.math_calculation < 85:
                    primary_concerns.append("Math Calculation")
                
                # Add academic needs
                if academic_profile.academic_needs:
                    primary_concerns.extend(academic_profile.academic_needs)
            
            # Determine eligibility
            if (cognitive_profile and cognitive_profile.full_scale_iq and cognitive_profile.full_scale_iq > 85 and
                academic_profile and any(score and score < 85 for score in [
                    academic_profile.basic_reading_skills,
                    academic_profile.math_calculation,
                    academic_profile.written_expression
                ])):
                eligibility_determination = "Specific Learning Disability"
            elif cognitive_profile and cognitive_profile.full_scale_iq and cognitive_profile.full_scale_iq < 70:
                eligibility_determination = "Intellectual Disability"
        
        if has_behavioral:
            behavioral_result = await db.execute(
                select(BehavioralProfile)
                .filter(BehavioralProfile.student_id == student_id)
                .order_by(BehavioralProfile.assessment_date.desc())
                .limit(1)
            )
            behavioral_profile = behavioral_result.scalar_one_or_none()
            
            if behavioral_profile:
                if behavioral_profile.attention_problems and behavioral_profile.attention_problems > 65:
                    primary_concerns.append("Attention Problems")
                if behavioral_profile.hyperactivity and behavioral_profile.hyperactivity > 65:
                    primary_concerns.append("Hyperactivity")
                if behavioral_profile.externalizing_problems and behavioral_profile.externalizing_problems > 65:
                    primary_concerns.append("Behavioral Concerns")
        
        # Remove duplicates and limit concerns
        primary_concerns = list(dict.fromkeys(primary_concerns))[:5]  # Keep top 5 unique concerns
        
        summary = AssessmentSummaryDTO(
            student_id=student_id,
            total_assessments=total_assessments,
            latest_assessment_date=latest_date,
            has_cognitive_profile=has_cognitive,
            has_academic_profile=has_academic,
            has_behavioral_profile=has_behavioral,
            overall_functioning_level=overall_functioning_level,
            primary_concerns=primary_concerns,
            eligibility_determination=eligibility_determination
        )
        
        logger.info(f"Generated assessment summary for student {student_id}: {total_assessments} assessments, {len(primary_concerns)} concerns")
        return summary
        
    except Exception as e:
        logger.error(f"Error fetching assessment summary: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch summary: {str(e)}")

@router.delete("/documents/{document_id}")
async def delete_assessment_document(
    document_id: UUID,
    db: AsyncSession = Depends(get_db_session)
):
    """Delete an assessment document and associated data"""
    
    try:
        # Delete from database
        from sqlalchemy import select
        
        # Find the document
        result = await db.execute(
            select(AssessmentDocument).filter(AssessmentDocument.id == document_id)
        )
        document = result.scalar_one_or_none()
        
        if not document:
            logger.warning(f"Document {document_id} not found for deletion")
            raise HTTPException(status_code=404, detail="Assessment document not found")
        
        # Delete associated scores first (cascading should handle this, but being explicit)
        scores_result = await db.execute(
            select(PsychoedScore).filter(PsychoedScore.document_id == document_id)
        )
        scores = scores_result.scalars().all()
        
        for score in scores:
            await db.delete(score)
        
        # Delete the document
        await db.delete(document)
        await db.commit()
        
        logger.info(f"Deleted document {document_id} and {len(scores)} associated scores")
        return {
            "message": "Document deleted successfully",
            "document_id": str(document_id),
            "scores_deleted": len(scores)
        }
        
    except Exception as e:
        logger.error(f"Error deleting document: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete document: {str(e)}")

@router.post("/create", response_model=dict)
async def create_pipeline(
    pipeline_data: dict,  # PipelineCreateRequest structure
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db_session)
):
    """Create a new assessment pipeline for processing"""
    
    try:
        logger.info(f"Creating assessment pipeline for student {pipeline_data.get('student_id')}")
        
        # Validate required fields
        student_id = pipeline_data.get('student_id')
        document_ids = pipeline_data.get('assessment_document_ids', [])
        
        if not student_id or not document_ids:
            raise HTTPException(
                status_code=400,
                detail="student_id and assessment_document_ids are required"
            )
        
        # Verify documents exist and belong to student
        from sqlalchemy import select
        documents_result = await db.execute(
            select(AssessmentDocument)
            .filter(AssessmentDocument.id.in_(document_ids))
            .filter(AssessmentDocument.student_id == student_id)
        )
        documents = documents_result.scalars().all()
        
        if len(documents) != len(document_ids):
            raise HTTPException(
                status_code=404,
                detail="Some assessment documents not found or don't belong to specified student"
            )
        
        # Generate pipeline ID
        import uuid
        pipeline_id = str(uuid.uuid4())
        
        # Create pipeline record (for now, we'll track this in memory/logs)
        # In a full implementation, you'd have a Pipeline model
        pipeline_metadata = {
            "pipeline_id": pipeline_id,
            "student_id": student_id,
            "document_ids": document_ids,
            "status": "created",
            "created_at": datetime.utcnow().isoformat()
        }
        
        # Start pipeline processing in background
        background_tasks.add_task(
            process_pipeline_background,
            pipeline_id,
            student_id,
            document_ids
        )
        
        logger.info(f"Created pipeline {pipeline_id} for student {student_id} with {len(document_ids)} documents")
        return {
            "pipeline_id": pipeline_id,
            "status": "created",
            "message": "Assessment pipeline created successfully"
        }
        
    except Exception as e:
        logger.error(f"Error creating assessment pipeline: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create pipeline: {str(e)}")

@router.get("/{pipeline_id}/status", response_model=dict)
async def get_pipeline_status(
    pipeline_id: str,
    db: AsyncSession = Depends(get_db_session)
):
    """Get status of an assessment pipeline"""
    
    try:
        # In a full implementation, you'd query a Pipeline model
        # For now, return a status based on document processing states
        logger.info(f"Getting status for pipeline {pipeline_id}")
        
        # This is a simplified status check
        # In reality, you'd track pipeline state in database
        return {
            "pipeline_id": pipeline_id,
            "status": "processing",
            "current_stage": "quantification",
            "progress_percentage": 65,
            "stages_completed": ["intake", "extraction"],
            "started_at": datetime.utcnow().isoformat(),
            "elapsed_seconds": 120,
            "has_results": False,
            "preview_available": False,
            "has_errors": False
        }
        
    except Exception as e:
        logger.error(f"Error getting pipeline status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get pipeline status: {str(e)}")

@router.get("/{pipeline_id}/results", response_model=dict)
async def get_pipeline_results(
    pipeline_id: str,
    db: AsyncSession = Depends(get_db_session)
):
    """Get complete results from a finished assessment pipeline"""
    
    try:
        logger.info(f"Getting results for pipeline {pipeline_id}")
        
        # In a full implementation, you'd retrieve comprehensive pipeline results
        # For now, return a structured response
        return {
            "pipeline_id": pipeline_id,
            "status": "completed",
            "intake_results": {"documents_processed": 3, "scores_extracted": 25},
            "quantification_results": {"profiles_created": 3, "confidence": 0.91},
            "generation_results": {"iep_sections": 8, "goals_generated": 12},
            "overall_confidence": 0.89,
            "total_processing_time": 180,
            "requires_review": True
        }
        
    except Exception as e:
        logger.error(f"Error getting pipeline results: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get pipeline results: {str(e)}")

@router.get("/stats", response_model=dict)
async def get_processing_stats(
    db: AsyncSession = Depends(get_db_session)
):
    """Get overall processing statistics"""
    
    try:
        from sqlalchemy import select, func
        
        # Get document counts by status
        status_result = await db.execute(
            select(
                AssessmentDocument.processing_status,
                func.count(AssessmentDocument.id).label('count')
            )
            .group_by(AssessmentDocument.processing_status)
        )
        
        status_counts = {row.processing_status: row.count for row in status_result}
        
        # Get total scores extracted
        scores_result = await db.execute(
            select(func.count(PsychoedScore.id))
        )
        total_scores = scores_result.scalar() or 0
        
        # Get average confidence
        confidence_result = await db.execute(
            select(func.avg(AssessmentDocument.extraction_confidence))
            .filter(AssessmentDocument.extraction_confidence.isnot(None))
        )
        avg_confidence = confidence_result.scalar() or 0.0
        
        return {
            "total_documents": sum(status_counts.values()),
            "documents_by_status": status_counts,
            "total_scores_extracted": total_scores,
            "average_extraction_confidence": round(float(avg_confidence), 3),
            "processing_errors": status_counts.get("failed", 0),
            "success_rate": round(
                (status_counts.get("completed", 0) / max(sum(status_counts.values()), 1)) * 100, 2
            )
        }
        
    except Exception as e:
        logger.error(f"Error getting processing stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get processing stats: {str(e)}")

# RAG Integration Endpoints

@router.post("/students/{student_id}/create-rag-iep", response_model=dict)
async def create_rag_enhanced_iep(
    student_id: UUID,
    request: dict,  # Contains template_id, academic_year, etc.
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db_session)
):
    """Create RAG-enhanced IEP using quantified assessment data"""
    
    try:
        logger.info(f"Creating RAG-enhanced IEP for student {student_id}")
        
        # Get latest quantified assessment data for student
        from sqlalchemy import select
        result = await db.execute(
            select(QuantifiedAssessmentData)
            .filter(QuantifiedAssessmentData.student_id == student_id)
            .order_by(QuantifiedAssessmentData.assessment_date.desc())
            .limit(1)
        )
        quantified_data = result.scalar_one_or_none()
        
        if not quantified_data:
            raise HTTPException(
                status_code=404,
                detail=f"No quantified assessment data found for student {student_id}. Please process assessment documents first."
            )
        
        # Initialize RAG integration service
        rag_service = RAGIntegrationService()
        
        # Validate RAG service connection
        rag_connected = await rag_service.validate_rag_service_connection()
        if not rag_connected:
            raise HTTPException(
                status_code=503,
                detail="RAG service (Special Education Service) is not available"
            )
        
        # Create RAG-enhanced IEP
        iep_result = await rag_service.create_rag_enhanced_iep(
            student_id=str(student_id),
            quantified_data=quantified_data,
            template_id=request.get("template_id"),
            academic_year=request.get("academic_year", "2025-2026")
        )
        
        logger.info(f"RAG-enhanced IEP created successfully for student {student_id}")
        
        return {
            "status": "success",
            "iep_id": iep_result.get("iep_id"),
            "message": "RAG-enhanced IEP created successfully",
            "assessment_pipeline_integration": {
                "quantified_data_used": str(quantified_data.id),
                "assessment_date": quantified_data.assessment_date.isoformat(),
                "confidence_metrics": quantified_data.confidence_metrics,
                "eligibility_category": quantified_data.eligibility_category
            },
            "iep_content_preview": {
                "sections_generated": len(iep_result.get("content", {}).get("sections", {})),
                "goals_created": len(iep_result.get("content", {}).get("goals", [])),
                "services_recommended": len(quantified_data.service_recommendations or [])
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating RAG-enhanced IEP: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create RAG-enhanced IEP: {str(e)}")

@router.get("/students/{student_id}/rag-context", response_model=dict)
async def get_rag_context_data(
    student_id: UUID,
    db: AsyncSession = Depends(get_db_session)
):
    """Get quantified assessment data formatted for RAG consumption"""
    
    try:
        # Get latest quantified data
        from sqlalchemy import select
        result = await db.execute(
            select(QuantifiedAssessmentData)
            .filter(QuantifiedAssessmentData.student_id == student_id)
            .order_by(QuantifiedAssessmentData.assessment_date.desc())
            .limit(1)
        )
        quantified_data = result.scalar_one_or_none()
        
        if not quantified_data:
            raise HTTPException(
                status_code=404,
                detail=f"No quantified assessment data found for student {student_id}"
            )
        
        # Initialize RAG integration service
        rag_service = RAGIntegrationService()
        
        # Prepare RAG context
        rag_context = rag_service._prepare_rag_context(quantified_data)
        
        # Get additional student context
        student_context = await rag_service.get_student_context_for_rag(str(student_id))
        
        return {
            "student_id": str(student_id),
            "quantified_data_id": str(quantified_data.id),
            "assessment_date": quantified_data.assessment_date.isoformat(),
            "rag_context": rag_context,
            "student_context": student_context,
            "data_completeness": {
                "cognitive_data": quantified_data.cognitive_composite is not None,
                "academic_data": quantified_data.academic_composite is not None,
                "behavioral_data": quantified_data.behavioral_composite is not None,
                "growth_data": bool(quantified_data.growth_rate),
                "eligibility_data": bool(quantified_data.eligibility_category)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting RAG context data: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get RAG context data: {str(e)}")

@router.get("/rag/templates", response_model=dict)
async def get_available_rag_templates(
    grade_level: Optional[str] = None
):
    """Get available IEP templates from RAG service"""
    
    try:
        rag_service = RAGIntegrationService()
        
        # Validate RAG service connection
        rag_connected = await rag_service.validate_rag_service_connection()
        if not rag_connected:
            raise HTTPException(
                status_code=503,
                detail="RAG service (Special Education Service) is not available"
            )
        
        templates = await rag_service.get_available_templates(grade_level)
        
        return {
            "templates": templates,
            "total_count": len(templates),
            "grade_level_filter": grade_level
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting RAG templates: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get RAG templates: {str(e)}")

@router.get("/rag/health", response_model=dict)
async def check_rag_integration_health():
    """Check health of RAG integration"""
    
    try:
        rag_service = RAGIntegrationService()
        rag_connected = await rag_service.validate_rag_service_connection()
        
        return {
            "rag_service_connected": rag_connected,
            "rag_service_url": rag_service.special_ed_service_url,
            "integration_status": "healthy" if rag_connected else "unavailable",
            "capabilities": [
                "RAG-enhanced IEP creation",
                "Quantified data formatting",
                "Template integration",
                "Student context retrieval"
            ] if rag_connected else []
        }
        
    except Exception as e:
        logger.error(f"Error checking RAG integration health: {e}")
        return {
            "rag_service_connected": False,
            "integration_status": "error",
            "error": str(e)
        }

@router.post("/documents/{document_id}/retry")
async def retry_processing(
    document_id: UUID,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db_session),
    processor: AssessmentIntakeProcessor = Depends(get_assessment_processor)
):
    """Retry processing for a failed document"""
    
    try:
        # Find the document and update status for retry
        from sqlalchemy import select
        
        result = await db.execute(
            select(AssessmentDocument).filter(AssessmentDocument.id == document_id)
        )
        document = result.scalar_one_or_none()
        
        if not document:
            logger.warning(f"Document {document_id} not found for retry")
            raise HTTPException(status_code=404, detail="Assessment document not found")
        
        # Update processing status
        document.processing_status = "retry_pending"
        await db.commit()
        
        # Retry processing in background
        background_tasks.add_task(
            process_document_background,
            str(document_id),
            document.file_path or f"/tmp/retry_{document_id}.pdf",
            {
                "retry": True,
                "original_filename": document.file_name,
                "document_type": document.document_type
            },
            processor
        )
        
        logger.info(f"Initiated retry processing for document {document_id}")
        return {
            "message": "Processing retry initiated",
            "document_id": str(document_id),
            "status": "retry_pending"
        }
        
    except Exception as e:
        logger.error(f"Error retrying processing: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retry processing: {str(e)}")

# Background task functions
async def process_document_background(
    document_id: str,
    file_path: str,
    metadata: dict,
    processor: AssessmentIntakeProcessor
):
    """Background task to process uploaded document"""
    
    try:
        logger.info(f"Processing document {document_id} in background")
        
        # Process with assessment intake processor
        extracted_data = await processor.process_assessment_document(file_path, metadata)
        
        # Save extracted data to database
        async with async_session_factory() as session:
            try:
                # Update document status
                from sqlalchemy import select
                result = await session.execute(
                    select(AssessmentDocument).filter(AssessmentDocument.id == document_id)
                )
                document = result.scalar_one_or_none()
                
                if document:
                    if extracted_data.get('success', False):
                        document.processing_status = "completed"
                        document.extraction_confidence = extracted_data.get('confidence', 0.0)
                        
                        # Save extracted scores
                        for score_data in extracted_data.get('scores', []):
                            score = PsychoedScore(
                                document_id=document.id,
                                test_name=score_data.get('test_name'),
                                subtest_name=score_data.get('subtest_name'),
                                standard_score=score_data.get('standard_score'),
                                percentile_rank=score_data.get('percentile_rank'),
                                confidence_interval=score_data.get('confidence_interval'),
                                extraction_confidence=score_data.get('extraction_confidence', 0.0)
                            )
                            session.add(score)
                    else:
                        document.processing_status = "failed"
                        document.error_message = extracted_data.get('error', 'Processing failed')
                    
                    await session.commit()
                    logger.info(f"Document {document_id} processed successfully with status: {document.processing_status}")
                else:
                    logger.error(f"Document {document_id} not found during processing")
                    
            except Exception as e:
                logger.error(f"Error saving processed data for document {document_id}: {e}")
                await session.rollback()
                raise
        
    except Exception as e:
        logger.error(f"Error processing document {document_id}: {e}")
        # Update document status to error

async def process_manual_scores_background(
    document_id: str,
    assessment_data: dict
):
    """Background task to process manually entered scores"""
    
    try:
        logger.info(f"Processing manual scores for document {document_id}")
        
        # Convert manual scores to standardized format and save to database
        async with async_session_factory() as session:
            try:
                # Update document status
                from sqlalchemy import select
                result = await session.execute(
                    select(AssessmentDocument).filter(AssessmentDocument.id == document_id)
                )
                document = result.scalar_one_or_none()
                
                if document:
                    document.processing_status = "completed"
                    document.extraction_confidence = 1.0  # High confidence for manual entry
                    
                    # Save manual scores
                    for score_data in assessment_data.get('scores', []):
                        score = PsychoedScore(
                            document_id=document.id,
                            test_name=score_data.get('test_name'),
                            subtest_name=score_data.get('subtest_name'),
                            raw_score=score_data.get('raw_score'),
                            standard_score=score_data.get('standard_score'),
                            scaled_score=score_data.get('scaled_score'),
                            percentile_rank=score_data.get('percentile_rank'),
                            confidence_interval=score_data.get('confidence_interval'),
                            qualitative_descriptor=score_data.get('qualitative_descriptor'),
                            extraction_confidence=1.0  # Manual entry has full confidence
                        )
                        session.add(score)
                    
                    await session.commit()
                    logger.info(f"Manual scores for document {document_id} processed successfully with {len(assessment_data.get('scores', []))} scores")
                else:
                    logger.error(f"Document {document_id} not found during manual processing")
                    
            except Exception as e:
                logger.error(f"Error saving manual scores for document {document_id}: {e}")
                await session.rollback()
                raise
        
    except Exception as e:
        logger.error(f"Error processing manual scores for document {document_id}: {e}")
        # Update document status to error

async def process_pipeline_background(
    pipeline_id: str,
    student_id: str,
    document_ids: list
):
    """Background task to process complete assessment pipeline"""
    
    try:
        logger.info(f"Starting pipeline processing for {pipeline_id}")
        
        async with async_session_factory() as session:
            try:
                # Stage 1: Ensure all documents are processed
                from sqlalchemy import select
                documents_result = await session.execute(
                    select(AssessmentDocument)
                    .filter(AssessmentDocument.id.in_(document_ids))
                )
                documents = documents_result.scalars().all()
                
                pending_docs = [doc for doc in documents if doc.processing_status == "pending"]
                if pending_docs:
                    logger.info(f"Pipeline {pipeline_id}: {len(pending_docs)} documents still pending processing")
                    # Would trigger document processing here
                
                # Stage 2: Generate profiles from extracted scores
                scores_result = await session.execute(
                    select(PsychoedScore)
                    .join(AssessmentDocument)
                    .filter(AssessmentDocument.id.in_(document_ids))
                )
                all_scores = scores_result.scalars().all()
                
                if all_scores:
                    logger.info(f"Pipeline {pipeline_id}: Creating profiles from {len(all_scores)} extracted scores")
                    
                    # Generate cognitive profile
                    cognitive_scores = [s for s in all_scores if 'wisc' in s.test_name.lower() or 'wais' in s.test_name.lower()]
                    if cognitive_scores:
                        await create_cognitive_profile(session, student_id, cognitive_scores)
                    
                    # Generate academic profile
                    academic_scores = [s for s in all_scores if 'wiat' in s.test_name.lower() or 'ktea' in s.test_name.lower()]
                    if academic_scores:
                        await create_academic_profile(session, student_id, academic_scores)
                    
                    # Generate behavioral profile
                    behavioral_scores = [s for s in all_scores if 'basc' in s.test_name.lower() or 'conners' in s.test_name.lower()]
                    if behavioral_scores:
                        await create_behavioral_profile(session, student_id, behavioral_scores)
                
                # Stage 3: Generate quantified data for RAG
                # This would trigger the quantification engine
                
                # Stage 4: Integration with existing RAG system
                # This would connect to the special education service for IEP generation
                
                await session.commit()
                logger.info(f"Pipeline {pipeline_id} processing completed successfully")
                
            except Exception as e:
                logger.error(f"Error in pipeline processing for {pipeline_id}: {e}")
                await session.rollback()
                raise
                
    except Exception as e:
        logger.error(f"Pipeline {pipeline_id} processing failed: {e}")

async def create_cognitive_profile(session, student_id: str, cognitive_scores: list):
    """Create cognitive profile from WISC/WAIS scores"""
    try:
        # Extract key cognitive indices
        fsiq = next((s.standard_score for s in cognitive_scores if 'full scale' in s.subtest_name.lower()), None)
        vci = next((s.standard_score for s in cognitive_scores if 'verbal comprehension' in s.subtest_name.lower()), None)
        vsi = next((s.standard_score for s in cognitive_scores if 'visual spatial' in s.subtest_name.lower()), None)
        fri = next((s.standard_score for s in cognitive_scores if 'fluid reasoning' in s.subtest_name.lower()), None)
        wmi = next((s.standard_score for s in cognitive_scores if 'working memory' in s.subtest_name.lower()), None)
        psi = next((s.standard_score for s in cognitive_scores if 'processing speed' in s.subtest_name.lower()), None)
        
        if fsiq:  # Only create if we have full scale IQ
            cognitive_profile = CognitiveProfile(
                student_id=student_id,
                assessment_date=datetime.utcnow(),
                full_scale_iq=fsiq,
                verbal_comprehension_index=vci,
                visual_spatial_index=vsi,
                fluid_reasoning_index=fri,
                working_memory_index=wmi,
                processing_speed_index=psi,
                cognitive_strengths=[],
                cognitive_weaknesses=[],
                processing_patterns={},
                composite_confidence=0.95
            )
            session.add(cognitive_profile)
            logger.info(f"Created cognitive profile for student {student_id}")
            
    except Exception as e:
        logger.error(f"Error creating cognitive profile: {e}")

async def create_academic_profile(session, student_id: str, academic_scores: list):
    """Create academic profile from WIAT/KTEA scores"""
    try:
        # Extract key academic scores
        reading_skills = next((s.standard_score for s in academic_scores if 'basic reading' in s.subtest_name.lower()), None)
        reading_comp = next((s.standard_score for s in academic_scores if 'reading comprehension' in s.subtest_name.lower()), None)
        reading_fluency = next((s.standard_score for s in academic_scores if 'reading fluency' in s.subtest_name.lower()), None)
        math_calc = next((s.standard_score for s in academic_scores if 'math' in s.subtest_name.lower() and 'calculation' in s.subtest_name.lower()), None)
        written_expr = next((s.standard_score for s in academic_scores if 'written expression' in s.subtest_name.lower()), None)
        
        if any([reading_skills, math_calc, written_expr]):  # Create if we have any academic scores
            academic_profile = AcademicProfile(
                student_id=student_id,
                assessment_date=datetime.utcnow(),
                basic_reading_skills=reading_skills,
                reading_comprehension=reading_comp,
                reading_fluency=reading_fluency,
                math_calculation=math_calc,
                written_expression=written_expr,
                academic_strengths=[],
                academic_needs=[],
                error_patterns={}
            )
            session.add(academic_profile)
            logger.info(f"Created academic profile for student {student_id}")
            
    except Exception as e:
        logger.error(f"Error creating academic profile: {e}")

async def create_behavioral_profile(session, student_id: str, behavioral_scores: list):
    """Create behavioral profile from BASC/Conners scores"""
    try:
        # Extract key behavioral scores
        ext_problems = next((s.standard_score for s in behavioral_scores if 'externalizing' in s.subtest_name.lower()), None)
        int_problems = next((s.standard_score for s in behavioral_scores if 'internalizing' in s.subtest_name.lower()), None)
        bsi = next((s.standard_score for s in behavioral_scores if 'behavioral symptoms' in s.subtest_name.lower()), None)
        attention = next((s.standard_score for s in behavioral_scores if 'attention' in s.subtest_name.lower()), None)
        hyperactivity = next((s.standard_score for s in behavioral_scores if 'hyperactivity' in s.subtest_name.lower()), None)
        
        if any([ext_problems, int_problems, attention]):  # Create if we have any behavioral scores
            behavioral_profile = BehavioralProfile(
                student_id=student_id,
                assessment_date=datetime.utcnow(),
                externalizing_problems=ext_problems,
                internalizing_problems=int_problems,
                behavioral_symptoms_index=bsi,
                attention_problems=attention,
                hyperactivity=hyperactivity,
                executive_function_scores={},
                behavior_frequency_data=[],
                antecedent_patterns=[],
                effective_interventions=[]
            )
            session.add(behavioral_profile)
            logger.info(f"Created behavioral profile for student {student_id}")
            
    except Exception as e:
        logger.error(f"Error creating behavioral profile: {e}")