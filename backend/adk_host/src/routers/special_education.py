from fastapi import APIRouter, Depends, HTTPException, Query, Body
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import date, datetime

from ..middleware.auth import get_current_user, require_role
from ..dependencies import get_iep_service, get_pl_service, get_approval_service
from common.src.models.special_education import (
    IEPCreate, IEPUpdate, IEPResponse, 
    PLAssessmentCreate, PLAssessmentResponse,
    IEPGoalCreate, IEPGoalResponse
)

router = APIRouter(prefix="/api/v1/special-education", tags=["special-education"])

# ============== IEP Management Endpoints ==============

@router.post("/ieps", response_model=IEPResponse)
async def create_iep(
    iep_data: IEPCreate,
    current_user: dict = Depends(require_role(["teacher", "co_coordinator", "coordinator"])),
    iep_service = Depends(get_iep_service)
):
    """Create new IEP with RAG assistance"""
    try:
        iep = await iep_service.create_iep_with_rag(
            student_id=iep_data.student_id,
            template_id=iep_data.template_id,
            academic_year=iep_data.academic_year,
            initial_data={
                "goals": [g.dict() for g in iep_data.goals],
                **iep_data.additional_data
            },
            user_id=UUID(current_user['id']),
            user_role=current_user['role']
        )
        return IEPResponse(**iep)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to create IEP")

@router.get("/ieps/{iep_id}", response_model=IEPResponse)
async def get_iep(
    iep_id: UUID,
    include_history: bool = Query(False, description="Include version history"),
    include_goals: bool = Query(True, description="Include IEP goals"),
    current_user: dict = Depends(get_current_user),
    iep_service = Depends(get_iep_service)
):
    """Get IEP by ID with optional version history"""
    iep = await iep_service.get_iep_with_details(
        iep_id=iep_id,
        include_history=include_history,
        include_goals=include_goals
    )
    
    if not iep:
        raise HTTPException(status_code=404, detail="IEP not found")
    
    return IEPResponse(**iep)

@router.post("/ieps/{iep_id}/submit-for-approval")
async def submit_iep_for_approval(
    iep_id: UUID,
    comments: Optional[str] = Body(None, description="Submission comments"),
    current_user: dict = Depends(require_role(["teacher"])),
    iep_service = Depends(get_iep_service)
):
    """Submit IEP for approval workflow"""
    try:
        result = await iep_service.submit_iep_for_approval(
            iep_id=iep_id,
            user_id=UUID(current_user['id']),
            user_role=current_user['role'],
            comments=comments
        )
        return {
            "message": "IEP submitted for approval successfully",
            "workflow_id": result['workflow']['id'],
            "current_step": result['workflow']['current_step']
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# ============== Approval Workflow Endpoints ==============

@router.get("/approvals/pending")
async def get_pending_approvals(
    document_type: Optional[str] = Query(None, description="Filter by document type"),
    current_user: dict = Depends(get_current_user),
    approval_service = Depends(get_approval_service)
):
    """Get pending approvals for current user"""
    approvals = await approval_service.get_pending_approvals(
        user_id=UUID(current_user['id']),
        user_role=current_user['role'],
        document_type=document_type
    )
    return {
        "pending_approvals": approvals,
        "total": len(approvals)
    }

@router.post("/approvals/{workflow_id}/steps/{step_id}/decision")
async def process_approval_decision(
    workflow_id: UUID,
    step_id: UUID,
    decision: str = Body(..., regex="^(approved|rejected|returned)$"),
    comments: Optional[str] = Body(None),
    current_user: dict = Depends(get_current_user),
    approval_service = Depends(get_approval_service)
):
    """Process approval decision for a workflow step"""
    try:
        result = await approval_service.process_approval_decision(
            workflow_id=workflow_id,
            step_id=step_id,
            decision=decision,
            comments=comments,
            user_id=UUID(current_user['id']),
            user_role=current_user['role']
        )
        return {
            "workflow_id": workflow_id,
            "step_id": step_id,
            "decision": decision,
            "workflow_status": result['workflow']['status'],
            "next_step": result.get('next_step')
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e)) 