"""Advanced IEP operations with RAG integration"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime
import logging

from ..database import get_db, get_request_scoped_db
from ..middleware.session_middleware import get_request_session
from ..repositories.iep_repository import IEPRepository
from ..repositories.pl_repository import PLRepository
from ..services.iep_service import IEPService
from ..services.user_adapter import UserAdapter
from ..services.async_job_service import AsyncJobService
from ..rag.metadata_aware_iep_generator import MetadataAwareIEPGenerator
from ..schemas.iep_schemas import (
    IEPCreate, IEPCreateWithRAG, IEPResponse, IEPGenerateSection
)
from ..config import get_settings
from ..vector_store_enhanced import EnhancedVectorStore

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/ieps/advanced", tags=["Advanced IEPs"])
settings = get_settings()

# Initialize services
user_adapter = UserAdapter(
    auth_service_url=getattr(settings, 'auth_service_url', 'http://localhost:8080'),
    cache_ttl_seconds=300
)

# Initialize enhanced vector store and metadata-aware IEP generator
import os
logger.info("🔄 Initializing Enhanced RAG System with Metadata Intelligence...")

try:
    # Use enhanced vector store with metadata capabilities
    enhanced_vector_store = EnhancedVectorStore(
        persist_directory="./chromadb",
        collection_name="enhanced_educational_docs"
    )
    logger.info("✅ Enhanced vector store initialized successfully")
    
    # Initialize metadata-aware IEP generator
    metadata_aware_iep_generator = MetadataAwareIEPGenerator(
        vector_store=enhanced_vector_store
    )
    logger.info("✅ Metadata-aware IEP generator initialized successfully")
    logger.info("🚀 Enhanced RAG system ready with metadata intelligence, quality filtering, and evidence attribution")
    
except Exception as e:
    logger.error(f"❌ Failed to initialize enhanced RAG system: {e}")
    logger.warning("🔄 Falling back to basic vector store for compatibility")
    
    # Fallback to basic system if enhanced fails
    from ..vector_store import VectorStore
    from ..rag.iep_generator import IEPGenerator
    
    vector_store = VectorStore(collection_name="rag_documents")
    metadata_aware_iep_generator = IEPGenerator(vector_store=vector_store, settings=settings)
    logger.warning("⚠️ Using deprecated basic RAG system as fallback")

async def get_iep_service(request: Request) -> IEPService:
    """Dependency to get IEP service with request-scoped session"""
    db = await get_request_session(request)
    iep_repo = IEPRepository(db)
    pl_repo = PLRepository(db)
    
    # Workflow and audit clients - TODO: integrate with actual services when available
    workflow_client = None
    audit_client = None
    
    return IEPService(
        repository=iep_repo,
        pl_repository=pl_repo,
        vector_store=enhanced_vector_store,
        iep_generator=metadata_aware_iep_generator,
        workflow_client=workflow_client,
        audit_client=audit_client
    )

@router.post("/create-with-rag", response_model=Dict[str, Any])
async def create_iep_with_rag(
    iep_data: IEPCreateWithRAG,
    request: Request,
    current_user_id: int = Query(..., description="Current user's auth ID"),
    current_user_role: str = Query("teacher", description="Current user's role"),
    async_processing: bool = Query(False, description="Use async processing for large jobs")
):
    """Create IEP using RAG-powered generation"""
    
    import time
    start_time = time.time()
    logger.info(f"🎯 [BACKEND-ROUTER] RAG IEP creation started: student_id={iep_data.student_id}, user_id={current_user_id}, academic_year={iep_data.academic_year}")
    logger.info(f"📊 [BACKEND-ROUTER] Request details: template_id={iep_data.template_id}, async={async_processing}, content_keys={list(iep_data.content.keys()) if iep_data.content else []}")
    
    # DETAILED REQUEST DATA LOGGING FOR ROOT CAUSE ANALYSIS
    logger.error(f"🔍 [DEBUG] FULL REQUEST DATA RECEIVED:")
    logger.error(f"🔍 [DEBUG] iep_data.student_id: {iep_data.student_id}")
    logger.error(f"🔍 [DEBUG] iep_data.academic_year: {iep_data.academic_year}")
    logger.error(f"🔍 [DEBUG] iep_data.template_id: {iep_data.template_id}")
    logger.error(f"🔍 [DEBUG] iep_data.meeting_date: {iep_data.meeting_date}")
    logger.error(f"🔍 [DEBUG] iep_data.effective_date: {iep_data.effective_date}")
    logger.error(f"🔍 [DEBUG] iep_data.review_date: {iep_data.review_date}")
    logger.error(f"🔍 [DEBUG] iep_data.content: {iep_data.content}")
    if iep_data.content:
        logger.error(f"🔍 [DEBUG] content.student_name: {iep_data.content.get('student_name', 'NOT_SET')}")
        logger.error(f"🔍 [DEBUG] content.grade_level: {iep_data.content.get('grade_level', 'NOT_SET')}")
        logger.error(f"🔍 [DEBUG] content.case_manager_name: {iep_data.content.get('case_manager_name', 'NOT_SET')}")
        logger.error(f"🔍 [DEBUG] content.assessment_summary: {iep_data.content.get('assessment_summary', 'NOT_SET')}")
        if 'assessment_summary' in iep_data.content and isinstance(iep_data.content['assessment_summary'], dict):
            assessment = iep_data.content['assessment_summary']
            logger.error(f"🔍 [DEBUG] assessment.current_achievement: {assessment.get('current_achievement', 'NOT_SET')}")
            logger.error(f"🔍 [DEBUG] assessment.strengths: {assessment.get('strengths', 'NOT_SET')}")
            logger.error(f"🔍 [DEBUG] assessment.areas_for_growth: {assessment.get('areas_for_growth', 'NOT_SET')}")
            logger.error(f"🔍 [DEBUG] assessment.learning_profile: {assessment.get('learning_profile', 'NOT_SET')}")
            logger.error(f"🔍 [DEBUG] assessment.interests: {assessment.get('interests', 'NOT_SET')}")
    
    # Check if async processing is requested
    if async_processing:
        logger.info(f"Using async processing for IEP generation for student {iep_data.student_id}")
        
        try:
            # Import async job service
            from ..services.async_job_service import AsyncJobService, IEPGenerationRequest
            
            # Use request-scoped session instead of creating new one
            db = await get_request_session(request)
            service = AsyncJobService(db)
            
            # Convert IEPCreateWithRAG to IEPGenerationRequest
            job_request = IEPGenerationRequest(
                student_id=str(iep_data.student_id),
                template_id=str(iep_data.template_id) if iep_data.template_id else None,
                academic_year=iep_data.academic_year,
                include_previous_ieps=True,
                include_assessments=True,
                priority=8  # High priority for user-initiated requests
            )
            
            # Submit async job
            job_id = await service.submit_iep_generation_job(
                request=job_request,
                created_by_auth_id=str(current_user_id)
            )
            
            # Return job tracking response
            return {
                "async_job": True,
                "job_id": job_id,
                "status": "pending",
                "message": "IEP generation job submitted for async processing",
                "poll_url": f"/api/v1/jobs/{job_id}",
                "estimated_completion": "2-5 minutes"
            }
            
        except Exception as e:
            logger.error(f"Error submitting async job: {e}")
            # Fall back to synchronous processing
            logger.info("Falling back to synchronous processing")
    
    # Use synchronous real LLM implementation
    try:
        logger.info(f"🤖 [BACKEND-ROUTER] Creating IEP with RAG/LLM for student {iep_data.student_id}")
        
        # Get the service dependency
        logger.info(f"🔧 [BACKEND-ROUTER] Initializing IEP service...")
        iep_service = await get_iep_service(request)
        logger.info(f"✅ [BACKEND-ROUTER] IEP service initialized successfully")
        
        # Prepare initial data from request
        initial_data = {
            "content": iep_data.content if iep_data.content else {},
            "meeting_date": iep_data.meeting_date,
            "effective_date": iep_data.effective_date,
            "review_date": iep_data.review_date
        }
        
        # Add goals if provided
        if iep_data.goals:
            initial_data["goals"] = [goal.model_dump() for goal in iep_data.goals]
        
        # Create IEP with RAG
        logger.info(f"📞 [BACKEND-ROUTER] Calling IEP service create_iep_with_rag...")
        created_iep = await iep_service.create_iep_with_rag(
            student_id=iep_data.student_id,
            template_id=iep_data.template_id,
            academic_year=iep_data.academic_year,
            initial_data=initial_data,
            user_id=current_user_id,
            user_role=current_user_role
        )
        
        elapsed_time = time.time() - start_time
        logger.info(f"✅ [BACKEND-ROUTER] IEP created successfully in {elapsed_time:.2f}s: {created_iep.get('id')}")
        
        # Ensure the response is JSON serializable
        # Convert any UUID objects to strings
        import json
        from uuid import UUID
        from ..utils.response_flattener import SimpleIEPFlattener
        
        def make_json_serializable(obj):
            if isinstance(obj, dict):
                return {k: make_json_serializable(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [make_json_serializable(item) for item in obj]
            elif isinstance(obj, UUID):
                return str(obj)
            else:
                return obj
        
        # Step 1: Make JSON serializable
        serializable_iep = make_json_serializable(created_iep)
        
        # Step 2: Apply flattening to prevent [object Object] errors
        logger.info(f"🔧 [BACKEND-ROUTER] Applying response flattening for frontend compatibility")
        flattened_iep = SimpleIEPFlattener.flatten_for_frontend(serializable_iep)
        
        final_elapsed = time.time() - start_time
        logger.info(f"🎉 [BACKEND-ROUTER] RAG IEP creation completed successfully in {final_elapsed:.2f}s")
        logger.info(f"📄 [BACKEND-ROUTER] Response summary: id={flattened_iep.get('id')}, content_sections={len(flattened_iep.get('content', {}))}, response_size={len(str(flattened_iep))} chars")
        
        return flattened_iep
        
    except ValueError as e:
        elapsed_time = time.time() - start_time
        logger.error(f"❌ [BACKEND-ROUTER] ValueError creating IEP with RAG after {elapsed_time:.2f}s: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        import traceback
        elapsed_time = time.time() - start_time
        logger.error(f"💥 [BACKEND-ROUTER] Critical error creating IEP with RAG after {elapsed_time:.2f}s: {e}")
        logger.error(f"🔍 [BACKEND-ROUTER] Full traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create IEP with RAG: {str(e)}"
        )

@router.post("/{iep_id}/generate-section", response_model=Dict[str, Any])
async def generate_iep_section(
    iep_id: UUID,
    section_request: IEPGenerateSection,
    current_user_id: int = Query(..., description="Current user's auth ID"),
    iep_service: IEPService = Depends(get_iep_service)
):
    """Generate specific IEP section using RAG"""
    try:
        section_content = await iep_service.generate_section(
            iep_id=iep_id,
            section_name=section_request.section_name,
            additional_context=section_request.additional_context,
            user_id=current_user_id
        )
        
        return {
            "section_name": section_request.section_name,
            "generated_content": section_content,
            "iep_id": str(iep_id)
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error generating IEP section: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate IEP section"
        )

@router.post("/{iep_id}/update-with-versioning", response_model=IEPResponse)
async def update_iep_with_versioning(
    iep_id: UUID,
    updates: Dict[str, Any],
    current_user_id: int = Query(..., description="Current user's auth ID"),
    current_user_role: str = Query("teacher", description="Current user's role"),
    iep_service: IEPService = Depends(get_iep_service)
):
    """Update IEP with automatic versioning"""
    try:
        updated_iep = await iep_service.update_iep_with_versioning(
            iep_id=iep_id,
            updates=updates,
            user_id=current_user_id,
            user_role=current_user_role
        )
        
        # Enrich with user information
        enriched_data = updated_iep.copy()
        if updated_iep.get("created_by_auth_id"):
            user = await user_adapter.resolve_user(updated_iep["created_by_auth_id"])
            enriched_data["created_by_user"] = user
        
        return IEPResponse(**enriched_data)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error updating IEP with versioning: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update IEP with versioning"
        )

@router.post("/{iep_id}/submit-for-approval", response_model=Dict[str, Any])
async def submit_iep_for_approval_advanced(
    iep_id: UUID,
    current_user_id: int = Query(..., description="Current user's auth ID"),
    current_user_role: str = Query("teacher", description="Current user's role"),
    comments: Optional[str] = Query(None, description="Submission comments"),
    iep_service: IEPService = Depends(get_iep_service)
):
    """Submit IEP for approval workflow with advanced features"""
    try:
        result = await iep_service.submit_iep_for_approval(
            iep_id=iep_id,
            user_id=current_user_id,
            user_role=current_user_role,
            comments=comments
        )
        
        return result
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error submitting IEP for approval: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit IEP for approval"
        )

@router.get("/{iep_id}/with-details", response_model=IEPResponse)
async def get_iep_with_details(
    iep_id: UUID,
    include_history: bool = Query(False, description="Include version history"),
    include_goals: bool = Query(True, description="Include goals"),
    iep_service: IEPService = Depends(get_iep_service)
):
    """Get IEP with comprehensive details"""
    try:
        iep = await iep_service.get_iep_with_details(
            iep_id=iep_id,
            include_history=include_history,
            include_goals=include_goals
        )
        
        if not iep:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"IEP {iep_id} not found"
            )
        
        # Enrich with user information
        enriched_data = iep.copy()
        auth_ids = []
        
        if iep.get("created_by_auth_id"):
            auth_ids.append(iep["created_by_auth_id"])
        if iep.get("approved_by_auth_id"):
            auth_ids.append(iep["approved_by_auth_id"])
        
        if auth_ids:
            users = await user_adapter.resolve_users(auth_ids)
            if iep.get("created_by_auth_id"):
                enriched_data["created_by_user"] = users.get(iep["created_by_auth_id"])
            if iep.get("approved_by_auth_id"):
                enriched_data["approved_by_user"] = users.get(iep["approved_by_auth_id"])
        
        return IEPResponse(**enriched_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting IEP with details: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve IEP details"
        )

@router.get("/similar-ieps/{student_id}", response_model=List[Dict[str, Any]])
async def find_similar_ieps(
    student_id: UUID,
    query_text: str = Query(..., description="Text to find similar IEPs for"),
    top_k: int = Query(5, ge=1, le=20, description="Number of similar IEPs to return"),
    iep_service: IEPService = Depends(get_iep_service)
):
    """Find similar IEPs using vector search"""
    try:
        # Use the enhanced metadata-aware generator's retrieval capability
        # Note: This method needs to be implemented in MetadataAwareIEPGenerator
        # For now, use enhanced search directly
        from ..schemas.rag_metadata_schemas import SearchContext, IEPSection
        
        search_context = SearchContext(
            target_iep_section=IEPSection.PRESENT_LEVELS,
            quality_threshold=0.3,
            max_results=top_k,
            student_context={'student_id': str(student_id)},
            boost_recent=True
        )
        
        similar_results = await enhanced_vector_store.enhanced_search(
            query_text=query_text,
            search_context=search_context,
            n_results=top_k
        )
        
        # Convert enhanced results to legacy format for compatibility
        similar_ieps = [
            {
                "chunk_id": result.chunk_id,
                "content": result.content,
                "relevance_score": result.relevance_score,
                "quality_score": result.quality_score,
                "source_attribution": result.source_attribution
            }
            for result in similar_results
        ]
        
        return similar_ieps
        
    except Exception as e:
        logger.error(f"Error finding similar IEPs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to find similar IEPs"
        )


@router.get("/async-job/{job_id}", response_model=Dict[str, Any])
async def get_async_iep_job_status(
    job_id: str,
    request: Request,
    current_user_id: int = Query(..., description="Current user's auth ID")
):
    """Get status of async IEP generation job with results"""
    try:
        # Get request-scoped database session
        db = await get_request_session(request)
        service = AsyncJobService(db)
        
        # Get job status
        job_status = await service.get_job_status(job_id)
        
        if not job_status:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Return job status with IEP-specific formatting
        response = {
            "job_id": job_status.job_id,
            "status": job_status.status,
            "progress_percentage": job_status.progress_percentage,
            "status_message": job_status.status_message,
            "created_at": job_status.created_at,
            "completed_at": job_status.completed_at,
            "failed_at": job_status.failed_at
        }
        
        # If completed, include the IEP data
        if job_status.status == 'completed' and job_status.result:
            iep_data = job_status.result.get('iep_data')
            if iep_data:
                response['iep'] = iep_data
                response['message'] = "IEP generation completed successfully"
            else:
                response['message'] = "Job completed but no IEP data found"
        
        # If failed, include error details
        elif job_status.status == 'failed' and job_status.error_details:
            response['error'] = job_status.error_details
            response['message'] = "IEP generation failed"
        
        return response
                
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in async job status endpoint: {e}")
        raise HTTPException(
            status_code=500, 
            detail="Failed to get job status"
        )

@router.get("/health/flattener", response_model=Dict[str, Any])
async def get_flattener_health():
    """Get flattener health status and statistics"""
    try:
        from ..utils.response_flattener import get_flattener_statistics
        
        stats = get_flattener_statistics()
        
        # Determine health status based on error rate
        if stats['total_operations'] == 0:
            status = "idle"
        elif stats['error_rate'] > 0.05:  # More than 5% error rate
            status = "degraded"
        elif stats['error_rate'] > 0.01:  # More than 1% error rate
            status = "warning"
        else:
            status = "healthy"
        
        return {
            "status": status,
            "flattener_enabled": True,
            "statistics": stats,
            "configuration": {
                "detailed_logging": True,
                "max_log_length": 500
            },
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0"
        }
        
    except Exception as e:
        logger.error(f"Error getting flattener health: {e}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }