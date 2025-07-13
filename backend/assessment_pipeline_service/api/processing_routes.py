"""
Processing-Only API Routes for Assessment Pipeline Service
Service-oriented endpoints that use special_education_client for data persistence
"""
import logging
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime
import tempfile
import os
import base64

from fastapi import APIRouter, HTTPException, UploadFile, File, BackgroundTasks, Depends
from fastapi.responses import JSONResponse

from assessment_pipeline_service.schemas.assessment_schemas import (
    AssessmentUploadDTO, ExtractedDataDTO, PsychoedScoreDTO,
    CognitiveProfileDTO, AcademicProfileDTO, BehavioralProfileDTO,
    AssessmentSummaryDTO, AssessmentIntakeRequestDTO, AssessmentIntakeResponseDTO
)
from assessment_pipeline_service.src.assessment_intake_processor import AssessmentIntakeProcessor
from assessment_pipeline_service.src.data_mapper import DataMapper
from assessment_pipeline_service.src.rag_integration import RAGIntegrationService
from assessment_pipeline_service.src.service_communication import (
    service_comm_manager, ServiceType, CommunicationStatus
)
from assessment_pipeline_service.src.auth_middleware import (
    get_current_user, require_teacher_or_above, require_coordinator_or_above
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/assessment-pipeline/processing", tags=["assessment-processing"])

# Dependency for assessment processor
def get_assessment_processor() -> AssessmentIntakeProcessor:
    return AssessmentIntakeProcessor()

async def process_document_background(
    document_id: str,
    file_path: str,
    assessment_data: Dict[str, Any],
    processor: AssessmentIntakeProcessor
):
    """Background task for document processing"""
    try:
        logger.info(f"Background processing started for document {document_id}")
        
        # Process the document
        result = await processor.process_assessment_document(
            file_path=file_path,
            document_id=document_id,
            assessment_type=assessment_data.get("assessment_type"),
            student_id=assessment_data.get("student_id")
        )
        
        # Update document status via service
        update_data = {
            "processing_status": "completed" if result.get("success") else "failed",
            "processing_notes": result.get("notes", ""),
            "confidence_score": result.get("confidence_score", 0.0)
        }
        
        await service_comm_manager.send_request(
            ServiceType.SPECIAL_EDUCATION,
            "update_assessment_document",
            {"document_id": document_id, **update_data},
            correlation_id=f"background-{document_id}"
        )
        
        logger.info(f"Background processing completed for document {document_id}")
        
    except Exception as e:
        logger.error(f"Background processing failed for document {document_id}: {e}")
        
        # Update status to failed
        await service_comm_manager.send_request(
            ServiceType.SPECIAL_EDUCATION,
            "update_assessment_document",
            {"document_id": document_id, "processing_status": "failed", "processing_notes": str(e)},
            correlation_id=f"background-error-{document_id}"
        )

# ===== DOCUMENT UPLOAD ENDPOINTS =====

@router.post("/upload", response_model=dict)
async def upload_assessment_document(
    assessment_data: AssessmentUploadDTO,
    background_tasks: BackgroundTasks,
    processor: AssessmentIntakeProcessor = Depends(get_assessment_processor),
    current_user: dict = Depends(require_teacher_or_above())
):
    """Upload a single assessment document"""
    
    try:
        logger.info(f"Processing upload for student {assessment_data.student_id} by user {current_user.get('sub', 'unknown')}")
        
        # Convert DTO to dictionary for service communication
        document_data = DataMapper.upload_dto_to_dict(assessment_data)
        document_data.update({
            "processing_status": "pending",
            "uploaded_by": current_user.get("sub"),
            "upload_timestamp": datetime.utcnow().isoformat()
        })
        
        # Create document via special education service
        response = await service_comm_manager.send_request(
            ServiceType.SPECIAL_EDUCATION,
            "create_assessment_document",
            document_data,
            correlation_id=f"upload-{assessment_data.student_id}"
        )
        
        if response.status != CommunicationStatus.SUCCESS:
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
        
        logger.info(f"Batch processing {len(documents_data)} documents by user {current_user.get('sub', 'unknown')}")
        
        # Prepare batch requests for service communication
        batch_requests = []
        assessment_dtos = []
        
        for doc_data in documents_data:
            assessment_dto = AssessmentUploadDTO(**doc_data)
            assessment_dtos.append(assessment_dto)
            
            document_data = DataMapper.upload_dto_to_dict(assessment_dto)
            document_data.update({
                "processing_status": "pending",
                "uploaded_by": current_user.get("sub"),
                "upload_timestamp": datetime.utcnow().isoformat()
            })
            
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
            if response.status == CommunicationStatus.SUCCESS:
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

# ===== DOCUMENT PROCESSING ENDPOINTS =====

@router.post("/extract/{document_id}", response_model=dict)
async def extract_assessment_data(
    document_id: UUID,
    processor: AssessmentIntakeProcessor = Depends(get_assessment_processor),
    current_user: dict = Depends(require_teacher_or_above())
):
    """Extract data from an uploaded assessment document"""
    
    try:
        logger.info(f"Extracting data from document {document_id} by user {current_user.get('sub', 'unknown')}")
        
        # Get document info from special education service
        doc_response = await service_comm_manager.send_request(
            ServiceType.SPECIAL_EDUCATION,
            "get_assessment_document",
            {"document_id": str(document_id)},
            correlation_id=f"extract-{document_id}"
        )
        
        if doc_response.status != CommunicationStatus.SUCCESS:
            raise HTTPException(status_code=404, detail="Document not found")
        
        document_data = doc_response.data
        
        # Extract data using processor
        extraction_result = await processor.extract_assessment_scores(
            document_data.get("file_path"),
            document_data.get("document_type", "unknown")
        )
        
        if not extraction_result.get("success"):
            raise HTTPException(
                status_code=500, 
                detail=f"Extraction failed: {extraction_result.get('error')}"
            )
        
        # Save extracted data via service
        extracted_data = DataMapper.extraction_result_to_dict(extraction_result, str(document_id))
        
        save_response = await service_comm_manager.send_request(
            ServiceType.SPECIAL_EDUCATION,
            "create_extracted_data",
            extracted_data,
            correlation_id=f"save-extract-{document_id}"
        )
        
        if save_response.status != CommunicationStatus.SUCCESS:
            logger.error(f"Failed to save extracted data: {save_response.error_message}")
        
        return {
            "document_id": str(document_id),
            "extraction_status": "success",
            "confidence_score": extraction_result.get("confidence_score", 0.0),
            "extracted_scores": extraction_result.get("scores", []),
            "processing_notes": extraction_result.get("notes", ""),
            "service_response_time_ms": save_response.execution_time_ms if save_response.status == CommunicationStatus.SUCCESS else 0
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error extracting data from document {document_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Extraction failed: {str(e)}")

@router.post("/quantify/{document_id}", response_model=dict)
async def quantify_assessment_metrics(
    document_id: UUID,
    current_user: dict = Depends(require_teacher_or_above())
):
    """Quantify assessment metrics for RAG integration"""
    
    try:
        logger.info(f"Quantifying metrics for document {document_id} by user {current_user.get('sub', 'unknown')}")
        
        # Get extracted data from special education service
        data_response = await service_comm_manager.send_request(
            ServiceType.SPECIAL_EDUCATION,
            "get_extracted_data",
            {"document_id": str(document_id)},
            correlation_id=f"quantify-{document_id}"
        )
        
        if data_response.status != CommunicationStatus.SUCCESS:
            raise HTTPException(status_code=404, detail="Extracted data not found")
        
        extracted_data = data_response.data
        
        # Import quantification engine
        from assessment_pipeline_service.src.quantification_engine import QuantificationEngine
        quantifier = QuantificationEngine()
        
        # Quantify the data
        quantified_result = await quantifier.quantify_assessment_data(extracted_data)
        
        if not quantified_result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=f"Quantification failed: {quantified_result.get('error')}"
            )
        
        # Save quantified data via service
        quantified_data = DataMapper.quantified_result_to_dict(quantified_result, str(document_id))
        
        save_response = await service_comm_manager.send_request(
            ServiceType.SPECIAL_EDUCATION,
            "create_quantified_data",
            quantified_data,
            correlation_id=f"save-quantify-{document_id}"
        )
        
        return {
            "document_id": str(document_id),
            "quantification_status": "success",
            "metrics": quantified_result.get("metrics", {}),
            "grade_level_analysis": quantified_result.get("grade_analysis", {}),
            "service_response_time_ms": save_response.execution_time_ms if save_response.status == CommunicationStatus.SUCCESS else 0
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error quantifying metrics for document {document_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Quantification failed: {str(e)}")

# ===== STATUS AND MONITORING ENDPOINTS =====

@router.get("/status/{document_id}", response_model=dict)
async def get_processing_status(
    document_id: UUID,
    current_user: dict = Depends(get_current_user)
):
    """Get processing status for a document"""
    
    try:
        # Get document status from special education service
        response = await service_comm_manager.send_request(
            ServiceType.SPECIAL_EDUCATION,
            "get_assessment_document",
            {"document_id": str(document_id)},
            correlation_id=f"status-{document_id}"
        )
        
        if response.status != CommunicationStatus.SUCCESS:
            raise HTTPException(status_code=404, detail="Document not found")
        
        document_data = response.data
        
        return {
            "document_id": str(document_id),
            "processing_status": document_data.get("processing_status", "unknown"),
            "confidence_score": document_data.get("confidence_score", 0.0),
            "processing_notes": document_data.get("processing_notes", ""),
            "created_at": document_data.get("created_at"),
            "updated_at": document_data.get("updated_at"),
            "service_response_time_ms": response.execution_time_ms
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting status for document {document_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Status check failed: {str(e)}")

@router.get("/health", response_model=dict)
async def processing_health_check():
    """Health check for processing endpoints"""
    
    try:
        # Check dependent services
        service_health = await service_comm_manager.batch_request([
            (ServiceType.SPECIAL_EDUCATION, "health_check", {}),
            (ServiceType.AUTH_SERVICE, "health_check", {})
        ], correlation_id="processing-health")
        
        special_ed_healthy = service_health[0].status == CommunicationStatus.SUCCESS
        auth_healthy = service_health[1].status == CommunicationStatus.SUCCESS
        
        # Test processor initialization
        try:
            processor = AssessmentIntakeProcessor()
            processor_healthy = True
        except Exception:
            processor_healthy = False
        
        overall_healthy = special_ed_healthy and auth_healthy and processor_healthy
        
        return {
            "status": "healthy" if overall_healthy else "unhealthy",
            "service": "assessment_pipeline_processing",
            "version": "2.0.0",
            "timestamp": datetime.utcnow().isoformat(),
            "dependencies": {
                "special_education_service": "connected" if special_ed_healthy else "disconnected",
                "auth_service": "connected" if auth_healthy else "disconnected",
                "assessment_processor": "active" if processor_healthy else "failed"
            },
            "capabilities": [
                "Document upload and processing",
                "Score extraction with 76-98% confidence",
                "Data quantification for RAG integration",
                "Background processing with status tracking",
                "Service-oriented architecture (no direct database access)"
            ]
        }
        
    except Exception as e:
        logger.error(f"Processing health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "service": "assessment_pipeline_processing",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        )

@router.get("/metrics", response_model=dict)
async def get_processing_metrics(
    current_user: dict = Depends(require_coordinator_or_above())
):
    """Get processing metrics and communication statistics"""
    
    try:
        # Get communication metrics
        metrics = service_comm_manager.get_all_metrics()
        
        # Get recent processing history
        history = service_comm_manager.get_recent_communication_history(limit=20)
        
        return {
            "service": "assessment_pipeline_processing",
            "timestamp": datetime.utcnow().isoformat(),
            "communication_metrics": metrics,
            "recent_activity": history,
            "user": current_user.get("sub", "unknown")
        }
        
    except Exception as e:
        logger.error(f"Error getting processing metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Metrics retrieval failed: {str(e)}")