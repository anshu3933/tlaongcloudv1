"""
Pipeline Orchestrator API Routes
Complete end-to-end assessment pipeline endpoints
"""
import logging
from typing import List, Optional, Dict, Any
from uuid import UUID
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from fastapi.responses import JSONResponse

from assessment_pipeline_service.src.pipeline_orchestrator import AssessmentPipelineOrchestrator
from assessment_pipeline_service.schemas.assessment_schemas import (
    AssessmentUploadDTO, QuantifiedMetricsDTO
)
from assessment_pipeline_service.src.service_clients import special_education_client
from assessment_pipeline_service.src.auth_middleware import (
    get_current_user, require_teacher_or_above, require_coordinator_or_above,
    require_self_or_admin_access
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/assessment-pipeline/orchestrator", tags=["pipeline-orchestrator"])

# Global orchestrator instance (in production, would use proper state management)
orchestrator = AssessmentPipelineOrchestrator()

@router.post("/execute-complete", response_model=dict)
async def execute_complete_pipeline(
    request: Dict[str, Any],
    background_tasks: BackgroundTasks,
    current_user: Dict[str, Any] = Depends(require_teacher_or_above())
):
    """Execute the complete assessment pipeline from documents to IEP"""
    
    try:
        student_id = request.get("student_id")
        assessment_documents = request.get("assessment_documents", [])
        template_id = request.get("template_id")
        academic_year = request.get("academic_year", "2025-2026")
        generate_iep = request.get("generate_iep", True)
        
        if not student_id:
            raise HTTPException(status_code=400, detail="student_id is required")
        
        if not assessment_documents:
            raise HTTPException(status_code=400, detail="assessment_documents are required")
        
        logger.info(f"Starting complete pipeline for student {student_id} by user {current_user.get('sub', 'unknown')}")
        
        # Convert documents to DTOs
        document_dtos = [
            AssessmentUploadDTO(**doc) for doc in assessment_documents
        ]
        
        # Validate inputs
        validation = await orchestrator.validate_pipeline_inputs(student_id, document_dtos)
        if not validation["valid"]:
            return JSONResponse(
                status_code=400,
                content={
                    "status": "validation_failed",
                    "errors": validation["errors"],
                    "warnings": validation["warnings"]
                }
            )
        
        # Execute pipeline
        result = await orchestrator.execute_complete_pipeline(
            student_id=student_id,
            assessment_documents=document_dtos,
            template_id=template_id,
            academic_year=academic_year,
            generate_iep=generate_iep
        )
        
        return {
            "status": "success",
            "message": "Complete assessment pipeline executed successfully",
            "pipeline_result": result
        }
        
    except Exception as e:
        logger.error(f"Complete pipeline execution failed: {e}")
        raise HTTPException(status_code=500, detail=f"Pipeline execution failed: {str(e)}")

@router.post("/execute-partial", response_model=dict)
async def execute_partial_pipeline(
    request: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(require_teacher_or_above())
):
    """Execute a partial pipeline (specific stages only)"""
    
    try:
        student_id = request.get("student_id")
        start_stage = request.get("start_stage")
        end_stage = request.get("end_stage")
        input_data = request.get("input_data")
        
        if not all([student_id, start_stage, end_stage]):
            raise HTTPException(
                status_code=400, 
                detail="student_id, start_stage, and end_stage are required"
            )
        
        logger.info(f"Starting partial pipeline for student {student_id}: {start_stage} to {end_stage} by user {current_user.get('sub', 'unknown')}")
        
        result = await orchestrator.execute_partial_pipeline(
            student_id=student_id,
            start_stage=start_stage,
            end_stage=end_stage,
            input_data=input_data
        )
        
        return {
            "status": "success",
            "message": f"Partial pipeline ({start_stage} to {end_stage}) executed successfully",
            "pipeline_result": result
        }
        
    except Exception as e:
        logger.error(f"Partial pipeline execution failed: {e}")
        raise HTTPException(status_code=500, detail=f"Partial pipeline execution failed: {str(e)}")

@router.get("/status/{pipeline_id}", response_model=dict)
async def get_pipeline_status(
    pipeline_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get current status of a pipeline run"""
    
    try:
        status = await orchestrator.get_pipeline_status(pipeline_id)
        return {
            "status": "success",
            "pipeline_status": status
        }
        
    except Exception as e:
        logger.error(f"Pipeline status check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Status check failed: {str(e)}")

@router.post("/validate-inputs", response_model=dict)
async def validate_pipeline_inputs(
    request: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(require_teacher_or_above())
):
    """Validate inputs before starting pipeline"""
    
    try:
        student_id = request.get("student_id")
        assessment_documents = request.get("assessment_documents", [])
        
        if not student_id:
            raise HTTPException(status_code=400, detail="student_id is required")
        
        # Convert documents to DTOs
        document_dtos = [
            AssessmentUploadDTO(**doc) for doc in assessment_documents
        ]
        
        validation = await orchestrator.validate_pipeline_inputs(student_id, document_dtos)
        
        return {
            "status": "success",
            "validation_result": validation
        }
        
    except Exception as e:
        logger.error(f"Input validation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Validation failed: {str(e)}")


@router.get("/health", response_model=dict)
async def pipeline_orchestrator_health():
    """Health check for the pipeline orchestrator"""
    
    try:
        # Test orchestrator initialization
        test_orchestrator = AssessmentPipelineOrchestrator()
        pipeline_id = test_orchestrator.initialize_pipeline()
        
        # Test RAG integration health
        rag_service = RAGIntegrationService()
        rag_healthy = await rag_service.validate_rag_service_connection()
        
        return {
            "status": "healthy",
            "service": "assessment_pipeline_orchestrator",
            "version": "2.0.0",
            "components": {
                "orchestrator": "active",
                "intake_processor": "active", 
                "quantification_engine": "active",
                "rag_integration": "connected" if rag_healthy else "disconnected"
            },
            "capabilities": [
                "Complete end-to-end assessment processing",
                "Document AI integration (Google Cloud)",
                "Psychoeducational score extraction",
                "PLOP data quantification", 
                "RAG-enhanced IEP generation",
                "Pipeline status monitoring",
                "Performance analytics"
            ],
            "test_pipeline_id": pipeline_id,
            "ready_for_production": rag_healthy
        }
        
    except Exception as e:
        logger.error(f"Pipeline orchestrator health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "service": "assessment_pipeline_orchestrator",
                "error": str(e)
            }
        )