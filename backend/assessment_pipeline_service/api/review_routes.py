"""
Stage 4: Professional Review API Routes
Provides endpoints for review workflows, collaboration, and approval processes
"""
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, HTTPException, Depends, Query, Body
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import httpx

from assessment_pipeline_service.src.professional_review import (
    ProfessionalReviewEngine, ReviewerRole, ReviewStatus, ApprovalLevel
)

logger = logging.getLogger(__name__)

# Initialize router and review engine
router = APIRouter(prefix="/review", tags=["Professional Review"])
review_engine = ProfessionalReviewEngine()

# Pydantic models for API
class CreateReviewPackageRequest(BaseModel):
    iep_id: str = Field(..., description="IEP ID to create review package for")
    student_id: str = Field(..., description="Student ID")
    reviewer_id: str = Field(..., description="Requesting reviewer ID")
    priority: str = Field(default="normal", description="Review priority level")
    deadline: Optional[datetime] = Field(None, description="Review deadline")
    special_instructions: Optional[str] = Field(None, description="Special review instructions")

class ReviewDecisionRequest(BaseModel):
    decision: str = Field(..., description="Approval decision: approved, rejected, revision_requested")
    rationale: str = Field(..., description="Rationale for the decision")
    reviewer_id: str = Field(..., description="Reviewer making the decision")
    reviewer_name: str = Field(..., description="Reviewer name")
    reviewer_role: str = Field(..., description="Reviewer role")
    digital_signature: Optional[str] = Field(None, description="Digital signature if required")
    comments: Optional[List[Dict[str, Any]]] = Field(None, description="Additional review comments")

class AddCommentRequest(BaseModel):
    package_id: str = Field(..., description="Review package ID")
    reviewer_id: str = Field(..., description="Reviewer ID")
    reviewer_name: str = Field(..., description="Reviewer name")
    reviewer_role: str = Field(..., description="Reviewer role")
    section: str = Field(..., description="Section being commented on")
    content: str = Field(..., description="Comment content")
    suggestion: Optional[str] = Field(None, description="Suggested improvement")
    priority: str = Field(default="medium", description="Comment priority: low, medium, high, critical")

class ResolveCommentRequest(BaseModel):
    comment_id: str = Field(..., description="Comment ID to resolve")
    resolver_id: str = Field(..., description="ID of person resolving comment")
    resolution_note: Optional[str] = Field(None, description="Resolution explanation")

# API Endpoints

@router.post("/create-package")
async def create_review_package(
    request: CreateReviewPackageRequest
) -> Dict[str, Any]:
    """Create comprehensive review package for an IEP"""
    
    try:
        logger.info(f"Creating review package for IEP {request.iep_id}")
        
        # Get IEP data from special education service
        iep_data = await _fetch_iep_data(request.iep_id)
        if not iep_data:
            raise HTTPException(status_code=404, detail="IEP not found")
        
        # Get associated assessment data
        assessment_data = await _fetch_assessment_data(request.student_id)
        
        # Create review package
        review_package = await review_engine.create_review_package(
            iep_id=request.iep_id,
            student_id=request.student_id,
            generated_content=iep_data.get("content", {}),
            source_data=assessment_data.get("source_data", {}),
            quality_assessment=iep_data.get("quality_assessment", {}),
            created_by=request.reviewer_id
        )
        
        # Store review package (in production, this would go to database)
        package_data = {
            "package_id": review_package.id,
            "status": review_package.status.value,
            "created_date": review_package.created_date.isoformat(),
            "expiration_date": review_package.expiration_date.isoformat(),
            "metadata": review_package.metadata,
            "estimated_review_time": review_package.metadata.get("estimated_review_time", 30),
            "quality_score": review_package.metadata.get("quality_score", 0),
            "passes_quality_gates": review_package.metadata.get("passes_quality_gates", False)
        }
        
        logger.info(f"Review package {review_package.id} created successfully")
        
        return {
            "success": True,
            "package": package_data,
            "next_steps": [
                "Assign reviewers to the package",
                "Begin professional review process",
                "Monitor review progress and quality metrics"
            ]
        }
        
    except Exception as e:
        logger.error(f"Error creating review package: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create review package: {str(e)}")

@router.get("/package/{package_id}")
async def get_review_package(
    package_id: str,
    reviewer_id: str = Query(..., description="Reviewer ID"),
    reviewer_role: str = Query(..., description="Reviewer role")
) -> Dict[str, Any]:
    """Get comprehensive review package data for reviewer interface"""
    
    try:
        logger.info(f"Fetching review package {package_id} for reviewer {reviewer_id}")
        
        # Convert role string to enum
        try:
            role_enum = ReviewerRole(reviewer_role.lower())
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid reviewer role: {reviewer_role}")
        
        # Get review interface data
        interface_data = await review_engine.get_review_interface_data(
            package_id=package_id,
            reviewer_id=reviewer_id,
            reviewer_role=role_enum
        )
        
        return {
            "success": True,
            "interface_data": interface_data,
            "reviewer_context": interface_data["reviewer_context"],
            "last_updated": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching review package: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch review package: {str(e)}")

@router.get("/quality-dashboard/{package_id}")
async def get_quality_dashboard(package_id: str) -> Dict[str, Any]:
    """Get visual quality dashboard for review package"""
    
    try:
        logger.info(f"Generating quality dashboard for package {package_id}")
        
        dashboard = await review_engine.dashboard_generator.generate_dashboard(package_id)
        
        return {
            "success": True,
            "dashboard": dashboard,
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error generating quality dashboard: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate dashboard: {str(e)}")

@router.get("/comparison/{package_id}")
async def get_side_by_side_comparison(package_id: str) -> Dict[str, Any]:
    """Get side-by-side comparison view of source data vs generated content"""
    
    try:
        logger.info(f"Generating comparison view for package {package_id}")
        
        comparison_view = await review_engine.comparison_analyzer.generate_comparison_view(package_id)
        
        return {
            "success": True,
            "comparison": comparison_view,
            "navigation_help": {
                "sections": "Use section navigation to jump between IEP components",
                "differences": "Highlighted differences show content vs source data alignment",
                "bookmarks": "Save important sections for easy reference"
            }
        }
        
    except Exception as e:
        logger.error(f"Error generating comparison view: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate comparison: {str(e)}")

@router.post("/submit-decision")
async def submit_review_decision(request: ReviewDecisionRequest) -> Dict[str, Any]:
    """Submit comprehensive review decision with approval/rejection"""
    
    try:
        logger.info(f"Processing review decision: {request.decision}")
        
        # Convert role string to enum
        try:
            role_enum = ReviewerRole(request.reviewer_role.lower())
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid reviewer role: {request.reviewer_role}")
        
        # Validate decision
        valid_decisions = ["approved", "rejected", "revision_requested"]
        if request.decision not in valid_decisions:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid decision. Must be one of: {', '.join(valid_decisions)}"
            )
        
        # Process the review decision
        result = await review_engine.submit_review_decision(
            package_id="",  # This would come from request in production
            reviewer_id=request.reviewer_id,
            reviewer_name=request.reviewer_name,
            reviewer_role=role_enum,
            decision=request.decision,
            rationale=request.rationale,
            comments=request.comments
        )
        
        return {
            "success": True,
            "result": result,
            "next_steps": _get_next_steps_for_decision(request.decision, result)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing review decision: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process decision: {str(e)}")

@router.post("/add-comment")
async def add_review_comment(request: AddCommentRequest) -> Dict[str, Any]:
    """Add comment to specific section of review package"""
    
    try:
        logger.info(f"Adding comment to package {request.package_id}")
        
        # Convert role string to enum
        try:
            role_enum = ReviewerRole(request.reviewer_role.lower())
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid reviewer role: {request.reviewer_role}")
        
        # Validate priority
        valid_priorities = ["low", "medium", "high", "critical"]
        if request.priority not in valid_priorities:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid priority. Must be one of: {', '.join(valid_priorities)}"
            )
        
        # Create comment (in production, this would be stored in database)
        comment_id = f"comment_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{request.reviewer_id[:8]}"
        
        comment_data = {
            "comment_id": comment_id,
            "package_id": request.package_id,
            "reviewer_id": request.reviewer_id,
            "reviewer_name": request.reviewer_name,
            "reviewer_role": request.reviewer_role,
            "section": request.section,
            "content": request.content,
            "suggestion": request.suggestion,
            "priority": request.priority,
            "timestamp": datetime.utcnow().isoformat(),
            "resolved": False
        }
        
        return {
            "success": True,
            "comment": comment_data,
            "notification_sent": True,
            "follow_up_required": request.priority in ["high", "critical"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding comment: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to add comment: {str(e)}")

@router.post("/resolve-comment")
async def resolve_comment(request: ResolveCommentRequest) -> Dict[str, Any]:
    """Resolve a review comment"""
    
    try:
        logger.info(f"Resolving comment {request.comment_id}")
        
        # Update comment resolution (in production, this would update database)
        resolution_data = {
            "comment_id": request.comment_id,
            "resolved": True,
            "resolved_by": request.resolver_id,
            "resolved_timestamp": datetime.utcnow().isoformat(),
            "resolution_note": request.resolution_note
        }
        
        return {
            "success": True,
            "resolution": resolution_data,
            "notification_sent": True
        }
        
    except Exception as e:
        logger.error(f"Error resolving comment: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to resolve comment: {str(e)}")

@router.get("/collaboration/{package_id}")
async def get_collaboration_data(
    package_id: str,
    reviewer_id: str = Query(..., description="Reviewer ID")
) -> Dict[str, Any]:
    """Get collaboration data for multi-user review"""
    
    try:
        collaboration_data = await review_engine.collaboration_manager.get_collaboration_data(
            package_id, reviewer_id
        )
        
        return {
            "success": True,
            "collaboration": collaboration_data,
            "real_time_features": {
                "active_users": True,
                "live_comments": True,
                "edit_tracking": True,
                "notifications": True
            }
        }
        
    except Exception as e:
        logger.error(f"Error fetching collaboration data: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch collaboration data: {str(e)}")

@router.get("/workflow-status/{package_id}")
async def get_workflow_status(package_id: str) -> Dict[str, Any]:
    """Get current approval workflow status"""
    
    try:
        workflow_status = await review_engine.approval_workflow.get_workflow_status(package_id)
        
        return {
            "success": True,
            "workflow": workflow_status,
            "estimated_completion": _calculate_estimated_completion(workflow_status)
        }
        
    except Exception as e:
        logger.error(f"Error fetching workflow status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch workflow status: {str(e)}")

@router.get("/history/{package_id}")
async def get_review_history(package_id: str) -> Dict[str, Any]:
    """Get complete review and approval history"""
    
    try:
        # This would fetch from database in production
        history = {
            "package_id": package_id,
            "timeline": [],
            "decisions": [],
            "comments": [],
            "versions": [],
            "audit_trail": []
        }
        
        return {
            "success": True,
            "history": history
        }
        
    except Exception as e:
        logger.error(f"Error fetching review history: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch review history: {str(e)}")

@router.get("/pending-reviews")
async def get_pending_reviews(
    reviewer_id: str = Query(..., description="Reviewer ID"),
    reviewer_role: str = Query(..., description="Reviewer role"),
    limit: int = Query(10, description="Maximum number of reviews to return")
) -> Dict[str, Any]:
    """Get pending reviews for a specific reviewer"""
    
    try:
        # This would query database for pending reviews assigned to reviewer
        pending_reviews = [
            {
                "package_id": f"pkg_{i}",
                "student_name": f"Student {i}",
                "iep_id": f"iep_{i}",
                "priority": "normal",
                "deadline": (datetime.utcnow() + timedelta(days=3)).isoformat(),
                "estimated_time": f"{15 + i*5} minutes",
                "quality_score": 0.8 + (i * 0.02)
            }
            for i in range(min(limit, 5))  # Mock data
        ]
        
        return {
            "success": True,
            "pending_reviews": pending_reviews,
            "total_count": len(pending_reviews),
            "reviewer_workload": {
                "current_reviews": len(pending_reviews),
                "estimated_total_time": f"{sum(15 + i*5 for i in range(len(pending_reviews)))} minutes",
                "urgent_reviews": 0
            }
        }
        
    except Exception as e:
        logger.error(f"Error fetching pending reviews: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch pending reviews: {str(e)}")

# Helper functions

async def _fetch_iep_data(iep_id: str) -> Optional[Dict[str, Any]]:
    """Fetch IEP data from special education service"""
    
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(f"http://localhost:8005/api/v1/ieps/{iep_id}")
            if response.status_code == 200:
                return response.json()
            return None
    except Exception as e:
        logger.error(f"Error fetching IEP data: {e}")
        return None

async def _fetch_assessment_data(student_id: str) -> Optional[Dict[str, Any]]:
    """Fetch assessment data for student"""
    
    # This would fetch from assessment database in production
    return {
        "source_data": {
            "academic_metrics": {},
            "behavioral_metrics": {},
            "quantified_data": {}
        }
    }

def _get_next_steps_for_decision(decision: str, result: Dict[str, Any]) -> List[str]:
    """Get next steps based on review decision"""
    
    if decision == "approved":
        if result.get("workflow_complete", False):
            return [
                "IEP approved and ready for implementation",
                "Notify all stakeholders of approval",
                "Begin service delivery planning"
            ]
        else:
            return [
                "Additional approvals required",
                "Route to next approval level",
                "Monitor approval progress"
            ]
    elif decision == "rejected":
        return [
            "IEP rejected - requires major revisions",
            "Review rejection rationale with team",
            "Schedule revision planning meeting"
        ]
    elif decision == "revision_requested":
        return [
            "Address specific revision requests",
            "Update IEP content based on feedback", 
            "Resubmit for review when ready"
        ]
    
    return ["Continue review process"]

def _calculate_estimated_completion(workflow_status: Dict[str, Any]) -> str:
    """Calculate estimated completion time for workflow"""
    
    pending_approvals = workflow_status.get("pending_approvals", [])
    if not pending_approvals:
        return "Complete"
    
    total_days = sum(
        int(approval.get("estimated_time", "2 days").split()[0]) 
        for approval in pending_approvals
    )
    
    completion_date = datetime.utcnow() + timedelta(days=total_days)
    return completion_date.strftime("%Y-%m-%d")