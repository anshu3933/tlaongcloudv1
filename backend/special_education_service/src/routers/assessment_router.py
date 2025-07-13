"""Assessment data management API endpoints"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, Any
from uuid import UUID
import logging

from ..database import get_db
from ..repositories.assessment_repository import AssessmentRepository
from ..schemas.assessment_schemas import (
    AssessmentDocumentCreate, AssessmentDocumentUpdate, AssessmentDocumentResponse,
    PsychoedScoreCreate, PsychoedScoreResponse,
    ExtractedAssessmentDataCreate, ExtractedAssessmentDataResponse,
    QuantifiedAssessmentDataCreate, QuantifiedAssessmentDataResponse
)
from ..schemas.common_schemas import PaginatedResponse, SuccessResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/assessments", tags=["Assessments"])

async def get_assessment_repository(db: AsyncSession = Depends(get_db)) -> AssessmentRepository:
    """Dependency to get Assessment repository"""
    return AssessmentRepository(db)

# Assessment Document endpoints
@router.post("/documents", response_model=AssessmentDocumentResponse, status_code=status.HTTP_201_CREATED)
async def create_assessment_document(
    document_data: AssessmentDocumentCreate,
    assessment_repo: AssessmentRepository = Depends(get_assessment_repository)
):
    """Create a new assessment document record"""
    try:
        document_dict = document_data.model_dump()
        created_document = await assessment_repo.create_assessment_document(document_dict)
        return AssessmentDocumentResponse(**created_document)
    except HTTPException:
        # Re-raise HTTPException from repository as-is (400, 422, etc)
        raise
    except Exception as e:
        logger.error(f"Unexpected error creating assessment document: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create assessment document"
        )

@router.get("/documents/{document_id}", response_model=AssessmentDocumentResponse)
async def get_assessment_document(
    document_id: UUID,
    assessment_repo: AssessmentRepository = Depends(get_assessment_repository)
):
    """Get assessment document by ID"""
    document = await assessment_repo.get_assessment_document(document_id)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Assessment document {document_id} not found"
        )
    return AssessmentDocumentResponse(**document)

@router.put("/documents/{document_id}", response_model=AssessmentDocumentResponse)
async def update_assessment_document(
    document_id: UUID,
    updates: AssessmentDocumentUpdate,
    assessment_repo: AssessmentRepository = Depends(get_assessment_repository)
):
    """Update an assessment document"""
    updates_dict = updates.model_dump(exclude_unset=True)
    updated_document = await assessment_repo.update_assessment_document(document_id, updates_dict)
    
    if not updated_document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Assessment document {document_id} not found"
        )
    
    return AssessmentDocumentResponse(**updated_document)

@router.get("/documents/student/{student_id}", response_model=List[AssessmentDocumentResponse])
async def get_student_assessment_documents(
    student_id: UUID,
    assessment_repo: AssessmentRepository = Depends(get_assessment_repository)
):
    """Get all assessment documents for a student"""
    documents = await assessment_repo.get_student_assessment_documents(student_id)
    return [AssessmentDocumentResponse(**doc) for doc in documents]

# Psychoeducational Scores endpoints
@router.post("/scores/batch", response_model=List[PsychoedScoreResponse], status_code=status.HTTP_201_CREATED)
async def create_psychoed_scores_batch(
    scores_request: Dict[str, List[Dict[str, Any]]],
    assessment_repo: AssessmentRepository = Depends(get_assessment_repository)
):
    """Create multiple psychoeducational scores"""
    try:
        scores_data = scores_request.get("scores", [])
        created_scores = await assessment_repo.create_psychoed_scores_batch(scores_data)
        return [PsychoedScoreResponse(**score) for score in created_scores]
    except Exception as e:
        logger.error(f"Error creating psychoed scores: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create psychoed scores"
        )

@router.get("/scores/document/{document_id}", response_model=List[PsychoedScoreResponse])
async def get_document_psychoed_scores(
    document_id: UUID,
    assessment_repo: AssessmentRepository = Depends(get_assessment_repository)
):
    """Get all psychoeducational scores for a document"""
    scores = await assessment_repo.get_document_psychoed_scores(document_id)
    return [PsychoedScoreResponse(**score) for score in scores]

@router.get("/scores/student/{student_id}", response_model=List[PsychoedScoreResponse])
async def get_student_psychoed_scores(
    student_id: UUID,
    test_name: Optional[str] = Query(None, description="Filter by test name"),
    assessment_repo: AssessmentRepository = Depends(get_assessment_repository)
):
    """Get all psychoeducational scores for a student"""
    scores = await assessment_repo.get_student_psychoed_scores(student_id, test_name=test_name)
    return [PsychoedScoreResponse(**score) for score in scores]

# Extracted Assessment Data endpoints
@router.post("/extracted-data", response_model=ExtractedAssessmentDataResponse, status_code=status.HTTP_201_CREATED)
async def create_extracted_assessment_data(
    extracted_data: ExtractedAssessmentDataCreate,
    assessment_repo: AssessmentRepository = Depends(get_assessment_repository)
):
    """Create extracted assessment data record"""
    try:
        data_dict = extracted_data.model_dump()
        created_data = await assessment_repo.create_extracted_assessment_data(data_dict)
        return ExtractedAssessmentDataResponse(**created_data)
    except Exception as e:
        logger.error(f"Error creating extracted assessment data: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create extracted assessment data"
        )

@router.get("/extracted-data/document/{document_id}", response_model=ExtractedAssessmentDataResponse)
async def get_document_extracted_data(
    document_id: UUID,
    assessment_repo: AssessmentRepository = Depends(get_assessment_repository)
):
    """Get extracted data for a document"""
    extracted_data = await assessment_repo.get_document_extracted_data(document_id)
    if not extracted_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No extracted data found for document {document_id}"
        )
    return ExtractedAssessmentDataResponse(**extracted_data)

# Quantified Assessment Data endpoints
@router.post("/quantified-data", response_model=QuantifiedAssessmentDataResponse, status_code=status.HTTP_201_CREATED)
async def create_quantified_assessment_data(
    quantified_data: QuantifiedAssessmentDataCreate,
    assessment_repo: AssessmentRepository = Depends(get_assessment_repository)
):
    """Create quantified assessment data record"""
    try:
        data_dict = quantified_data.model_dump()
        created_data = await assessment_repo.create_quantified_assessment_data(data_dict)
        return QuantifiedAssessmentDataResponse(**created_data)
    except Exception as e:
        logger.error(f"Error creating quantified assessment data: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create quantified assessment data"
        )

@router.get("/quantified-data/student/{student_id}", response_model=List[QuantifiedAssessmentDataResponse])
async def get_student_quantified_data(
    student_id: UUID,
    assessment_repo: AssessmentRepository = Depends(get_assessment_repository)
):
    """Get all quantified assessment data for a student"""
    quantified_data = await assessment_repo.get_student_quantified_data(student_id)
    return [QuantifiedAssessmentDataResponse(**data) for data in quantified_data]

@router.get("/quantified-data/{data_id}", response_model=QuantifiedAssessmentDataResponse)
async def get_quantified_assessment_data(
    data_id: UUID,
    assessment_repo: AssessmentRepository = Depends(get_assessment_repository)
):
    """Get quantified assessment data by ID"""
    quantified_data = await assessment_repo.get_quantified_assessment_data(data_id)
    if not quantified_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Quantified assessment data {data_id} not found"
        )
    return QuantifiedAssessmentDataResponse(**quantified_data)

# Consolidated endpoints
@router.get("/student/{student_id}", response_model=Dict[str, Any])
async def get_student_assessment_summary(
    student_id: UUID,
    assessment_repo: AssessmentRepository = Depends(get_assessment_repository)
):
    """Get comprehensive assessment summary for a student with graceful degradation"""
    from ..utils.safe_db_operations import safe_list_operation, get_database_health
    
    try:
        # Each operation wrapped individually - partial failure doesn't kill everything
        documents = await safe_list_operation(
            assessment_repo.get_student_assessment_documents, 
            student_id,
            operation_name="get_student_assessment_documents"
        )
        
        scores = await safe_list_operation(
            assessment_repo.get_student_psychoed_scores, 
            student_id,
            operation_name="get_student_psychoed_scores"
        )
        
        quantified_data = await safe_list_operation(
            assessment_repo.get_student_quantified_data, 
            student_id,
            operation_name="get_student_quantified_data"
        )
        
        # Get database health for monitoring
        db_health = get_database_health()
        
        return {
            "student_id": str(student_id),
            "assessment_documents": [AssessmentDocumentResponse(**doc) for doc in documents],
            "psychoed_scores": [PsychoedScoreResponse(**score) for score in scores] if scores else [],
            "quantified_data": [QuantifiedAssessmentDataResponse(**data) for data in quantified_data] if quantified_data else [],
            "summary": {
                "total_documents": len(documents),
                "total_scores": len(scores),
                "quantified_assessments": len(quantified_data),
                "latest_assessment": documents[0]["assessment_date"] if documents else None,
                "database_status": db_health["status"],
                "migration_needed": db_health["migration_needed"]
            }
        }
    except Exception as e:
        logger.error(f"Unexpected error in assessment summary: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve student assessment summary"
        )

# Pipeline integration endpoints
@router.post("/pipeline/process-document", response_model=Dict[str, Any])
async def trigger_document_processing(
    document_id: UUID,
    assessment_repo: AssessmentRepository = Depends(get_assessment_repository)
):
    """Trigger assessment pipeline processing for a document"""
    try:
        # Update document status to indicate processing started
        await assessment_repo.update_assessment_document(
            document_id, 
            {"processing_status": "processing"}
        )
        
        # In a full implementation, this would trigger the assessment pipeline
        # For now, we'll return a success response
        return {
            "message": "Document processing triggered",
            "document_id": str(document_id),
            "status": "processing"
        }
    except Exception as e:
        logger.error(f"Error triggering document processing: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to trigger document processing"
        )