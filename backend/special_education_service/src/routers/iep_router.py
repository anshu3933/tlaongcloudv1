"""IEP management API endpoints"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from uuid import UUID
import logging

from ..database import get_db
from ..repositories.iep_repository import IEPRepository
from ..repositories.student_repository import StudentRepository
from ..services.user_adapter import UserAdapter
from ..schemas.iep_schemas import (
    IEPCreate, IEPUpdate, IEPResponse, IEPSearch, IEPSubmitForApproval,
    IEPGenerateSection, IEPVersionHistory, GoalProgressUpdate,
    IEPGoalCreate, IEPGoalResponse
)
from ..schemas.common_schemas import PaginatedResponse, SuccessResponse
from common.src.config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/ieps", tags=["IEPs"])
settings = get_settings()

# Initialize user adapter
user_adapter = UserAdapter(
    auth_service_url=getattr(settings, 'auth_service_url', 'http://localhost:8080'),
    cache_ttl_seconds=300
)

async def get_iep_repository(db: AsyncSession = Depends(get_db)) -> IEPRepository:
    """Dependency to get IEP repository"""
    return IEPRepository(db)

async def get_student_repository(db: AsyncSession = Depends(get_db)) -> StudentRepository:
    """Dependency to get Student repository"""
    return StudentRepository(db)

async def enrich_iep_response(iep_data: dict) -> IEPResponse:
    """Enrich IEP data with user information"""
    # Collect auth IDs for user resolution
    auth_ids = []
    if iep_data.get("created_by_auth_id"):
        auth_ids.append(iep_data["created_by_auth_id"])
    if iep_data.get("approved_by_auth_id"):
        auth_ids.append(iep_data["approved_by_auth_id"])
    
    # Resolve users
    users = {}
    if auth_ids:
        users = await user_adapter.resolve_users(auth_ids)
    
    # Enrich response
    enriched_data = iep_data.copy()
    if iep_data.get("created_by_auth_id"):
        enriched_data["created_by_user"] = users.get(iep_data["created_by_auth_id"])
    if iep_data.get("approved_by_auth_id"):
        enriched_data["approved_by_user"] = users.get(iep_data["approved_by_auth_id"])
    
    return IEPResponse(**enriched_data)

@router.post("", response_model=IEPResponse, status_code=status.HTTP_201_CREATED)
async def create_iep(
    iep_data: IEPCreate,
    current_user_id: int = Query(..., description="Current user's auth ID"),
    iep_repo: IEPRepository = Depends(get_iep_repository),
    student_repo: StudentRepository = Depends(get_student_repository)
):
    """Create a new IEP"""
    try:
        # Verify student exists
        student = await student_repo.get_student(iep_data.student_id)
        if not student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Student {iep_data.student_id} not found"
            )
        
        # Prepare IEP data
        iep_dict = iep_data.model_dump()
        iep_dict["created_by"] = current_user_id
        
        # Create IEP
        created_iep = await iep_repo.create_iep(iep_dict)
        
        # Enrich and return response
        return await enrich_iep_response(created_iep)
        
    except Exception as e:
        logger.error(f"Error creating IEP: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create IEP"
        )

@router.get("/{iep_id}", response_model=IEPResponse)
async def get_iep(
    iep_id: UUID,
    include_goals: bool = Query(True, description="Include IEP goals in response"),
    iep_repo: IEPRepository = Depends(get_iep_repository)
):
    """Get IEP by ID"""
    iep = await iep_repo.get_iep(iep_id, include_goals=include_goals)
    if not iep:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"IEP {iep_id} not found"
        )
    
    return await enrich_iep_response(iep)

@router.put("/{iep_id}", response_model=IEPResponse)
async def update_iep(
    iep_id: UUID,
    iep_updates: IEPUpdate,
    iep_repo: IEPRepository = Depends(get_iep_repository)
):
    """Update an existing IEP"""
    # Get existing IEP to check status
    existing_iep = await iep_repo.get_iep(iep_id, include_goals=False)
    if not existing_iep:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"IEP {iep_id} not found"
        )
    
    # Check if IEP can be edited
    if existing_iep["status"] not in ["draft", "returned"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot edit IEP in {existing_iep['status']} status"
        )
    
    # Update IEP
    updates_dict = iep_updates.model_dump(exclude_unset=True)
    updated_iep = await iep_repo.update_iep(iep_id, updates_dict)
    
    if not updated_iep:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update IEP"
        )
    
    return await enrich_iep_response(updated_iep)

@router.delete("/{iep_id}", response_model=SuccessResponse)
async def delete_iep(
    iep_id: UUID,
    iep_repo: IEPRepository = Depends(get_iep_repository)
):
    """Soft delete an IEP"""
    success = await iep_repo.delete_iep(iep_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"IEP {iep_id} not found"
        )
    
    return SuccessResponse(
        message=f"IEP {iep_id} deleted successfully"
    )

@router.get("/student/{student_id}", response_model=List[IEPResponse])
async def get_student_ieps(
    student_id: UUID,
    academic_year: Optional[str] = Query(None, description="Filter by academic year"),
    status: Optional[str] = Query(None, description="Filter by IEP status"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of IEPs to return"),
    student_repo: StudentRepository = Depends(get_student_repository),
    iep_repo: IEPRepository = Depends(get_iep_repository)
):
    """Get all IEPs for a student"""
    # Verify student exists
    student = await student_repo.get_student(student_id)
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student {student_id} not found"
        )
    
    # Get IEPs
    ieps = await iep_repo.get_student_ieps(
        student_id=student_id,
        academic_year=academic_year,
        status=status,
        limit=limit
    )
    
    # Enrich responses
    enriched_ieps = []
    for iep in ieps:
        enriched_iep = await enrich_iep_response(iep)
        enriched_ieps.append(enriched_iep)
    
    return enriched_ieps

@router.post("/{iep_id}/submit", response_model=SuccessResponse)
async def submit_iep_for_approval(
    iep_id: UUID,
    submission: IEPSubmitForApproval,
    current_user_id: int = Query(..., description="Current user's auth ID"),
    iep_repo: IEPRepository = Depends(get_iep_repository)
):
    """Submit IEP for approval workflow"""
    # Get IEP to validate status
    iep = await iep_repo.get_iep(iep_id, include_goals=False)
    if not iep:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"IEP {iep_id} not found"
        )
    
    if iep["status"] != "draft":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"IEP must be in draft status to submit for approval, currently {iep['status']}"
        )
    
    # Update status to under_review
    success = await iep_repo.update_iep_status(iep_id, "under_review")
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit IEP for approval"
        )
    
    # TODO: Integrate with workflow service for approval process
    
    return SuccessResponse(
        message=f"IEP {iep_id} submitted for approval successfully",
        data={"comments": submission.comments}
    )

@router.post("/{iep_id}/goals", response_model=IEPGoalResponse, status_code=status.HTTP_201_CREATED)
async def create_iep_goal(
    iep_id: UUID,
    goal_data: IEPGoalCreate,
    iep_repo: IEPRepository = Depends(get_iep_repository)
):
    """Add a new goal to an IEP"""
    # Verify IEP exists and can be edited
    iep = await iep_repo.get_iep(iep_id, include_goals=False)
    if not iep:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"IEP {iep_id} not found"
        )
    
    if iep["status"] not in ["draft", "returned"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot add goals to IEP in {iep['status']} status"
        )
    
    # Create goal
    goal_dict = goal_data.model_dump()
    goal_dict["iep_id"] = iep_id
    
    created_goal = await iep_repo.create_iep_goal(goal_dict)
    return IEPGoalResponse(**created_goal)

@router.get("/{iep_id}/goals", response_model=List[IEPGoalResponse])
async def get_iep_goals(
    iep_id: UUID,
    iep_repo: IEPRepository = Depends(get_iep_repository)
):
    """Get all goals for an IEP"""
    # Verify IEP exists
    iep = await iep_repo.get_iep(iep_id, include_goals=False)
    if not iep:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"IEP {iep_id} not found"
        )
    
    goals = await iep_repo.get_iep_goals(iep_id)
    return [IEPGoalResponse(**goal) for goal in goals]

@router.put("/{iep_id}/goals/{goal_id}/progress", response_model=SuccessResponse)
async def update_goal_progress(
    iep_id: UUID,
    goal_id: UUID,
    progress_update: GoalProgressUpdate,
    iep_repo: IEPRepository = Depends(get_iep_repository)
):
    """Update progress for a specific goal"""
    # Verify IEP exists
    iep = await iep_repo.get_iep(iep_id, include_goals=False)
    if not iep:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"IEP {iep_id} not found"
        )
    
    # Update goal progress
    success = await iep_repo.update_goal_progress(
        goal_id=goal_id,
        progress_status=progress_update.progress_status.value,
        progress_note=progress_update.progress_note
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Goal {goal_id} not found"
        )
    
    return SuccessResponse(
        message=f"Goal progress updated successfully",
        data={
            "goal_id": str(goal_id),
            "new_status": progress_update.progress_status.value
        }
    )

@router.get("/{iep_id}/versions", response_model=List[IEPVersionHistory])
async def get_iep_version_history(
    iep_id: UUID,
    iep_repo: IEPRepository = Depends(get_iep_repository)
):
    """Get version history for an IEP"""
    # Get current IEP to extract student and academic year
    iep = await iep_repo.get_iep(iep_id, include_goals=False)
    if not iep:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"IEP {iep_id} not found"
        )
    
    # Get version history
    versions = await iep_repo.get_iep_version_history(
        student_id=UUID(iep["student_id"]),
        academic_year=iep["academic_year"]
    )
    
    # Enrich with user information
    enriched_versions = []
    for version in versions:
        enriched_version = IEPVersionHistory(**version)
        if version.get("created_by_auth_id"):
            user = await user_adapter.resolve_user(version["created_by_auth_id"])
            enriched_version.created_by_user = user
        enriched_versions.append(enriched_version)
    
    return enriched_versions

@router.get("/pending-approval", response_model=List[IEPResponse])
async def get_pending_approvals(
    limit: int = Query(50, ge=1, le=100, description="Maximum number of IEPs to return"),
    iep_repo: IEPRepository = Depends(get_iep_repository)
):
    """Get IEPs pending approval"""
    ieps = await iep_repo.get_ieps_for_approval(
        status="under_review",
        limit=limit
    )
    
    # Enrich responses
    enriched_ieps = []
    for iep in ieps:
        enriched_iep = await enrich_iep_response(iep)
        enriched_ieps.append(enriched_iep)
    
    return enriched_ieps