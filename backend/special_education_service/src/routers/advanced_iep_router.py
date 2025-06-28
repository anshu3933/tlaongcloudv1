"""Advanced IEP operations with RAG integration"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, Any
from uuid import UUID
import logging

from ..database import get_db, get_request_scoped_db
from ..middleware.session_middleware import get_request_session
from ..repositories.iep_repository import IEPRepository
from ..repositories.pl_repository import PLRepository
from ..services.iep_service import IEPService
from ..services.user_adapter import UserAdapter
from ..rag.iep_generator import IEPGenerator
from ..schemas.iep_schemas import (
    IEPCreate, IEPCreateWithRAG, IEPResponse, IEPGenerateSection
)
from common.src.config import get_settings
from common.src.vector_store import VectorStore

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/ieps/advanced", tags=["Advanced IEPs"])
settings = get_settings()

# Initialize services
user_adapter = UserAdapter(
    auth_service_url=getattr(settings, 'auth_service_url', 'http://localhost:8080'),
    cache_ttl_seconds=300
)

# Initialize vector store based on environment
import os
if os.getenv("ENVIRONMENT") == "development":
    # Development: Use ChromaDB with collection_name
    vector_store = VectorStore(
        project_id=getattr(settings, 'gcp_project_id', 'default-project'),
        collection_name="rag_documents"
    )
else:
    # Production: Use VertexVectorStore with proper factory method
    try:
        from common.src.vector_store.vertex_vector_store import VertexVectorStore
        vector_store = VertexVectorStore.from_settings(settings)
    except (ValueError, AttributeError) as e:
        # Fallback to ChromaDB if Vertex is not configured
        print(f"Warning: Vertex AI not configured ({e}), falling back to ChromaDB")
        from common.src.vector_store.chroma_vector_store import VectorStore as ChromaVectorStore
        vector_store = ChromaVectorStore(
            project_id=getattr(settings, 'gcp_project_id', 'default-project'),
            collection_name="rag_documents"
        )

iep_generator = IEPGenerator(vector_store=vector_store, settings=settings)

async def get_iep_service(request: Request) -> IEPService:
    """Dependency to get IEP service with request-scoped session"""
    db = await get_request_session(request)
    iep_repo = IEPRepository(db)
    pl_repo = PLRepository(db)
    
    # Create mock clients for now - TODO: integrate with actual services
    workflow_client = None
    audit_client = None
    
    return IEPService(
        repository=iep_repo,
        pl_repository=pl_repo,
        vector_store=vector_store,
        iep_generator=iep_generator,
        workflow_client=workflow_client,
        audit_client=audit_client
    )

@router.post("/create-with-rag", response_model=IEPResponse, status_code=status.HTTP_201_CREATED)
async def create_iep_with_rag(
    iep_data: IEPCreateWithRAG,
    current_user_id: int = Query(..., description="Current user's auth ID"),
    current_user_role: str = Query("teacher", description="Current user's role"),
    iep_service: IEPService = Depends(get_iep_service)
):
    """Create IEP using RAG-powered generation"""
    try:
        # Prepare initial data from request
        initial_data = {
            "content": iep_data.content,
            "meeting_date": iep_data.meeting_date,
            "effective_date": iep_data.effective_date,
            "review_date": iep_data.review_date
        }
        
        # Add goals if provided
        if iep_data.goals:
            initial_data["goals"] = [goal.model_dump() for goal in iep_data.goals]
        
        # Create IEP with RAG
        created_iep = await iep_service.create_iep_with_rag(
            student_id=iep_data.student_id,
            template_id=iep_data.template_id,
            academic_year=iep_data.academic_year,
            initial_data=initial_data,
            user_id=current_user_id,
            user_role=current_user_role
        )
        
        # Return IEP response without user enrichment to avoid greenlet issues
        # User enrichment can be done by frontend via separate API calls if needed
        return IEPResponse(**created_iep)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating IEP with RAG: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create IEP with RAG"
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
        # Use the IEP generator's retrieval capability
        similar_ieps = await iep_generator._retrieve_similar_ieps(
            query=query_text,
            top_k=top_k
        )
        
        return similar_ieps
        
    except Exception as e:
        logger.error(f"Error finding similar IEPs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to find similar IEPs"
        )