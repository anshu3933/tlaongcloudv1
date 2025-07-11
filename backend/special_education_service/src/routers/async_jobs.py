"""API routes for async job management"""

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime
import logging

from ..services.async_job_service import (
    AsyncJobService, 
    JobRequest, 
    IEPGenerationRequest, 
    SectionGenerationRequest, 
    JobStatus
)
from ..middleware.session_middleware import get_request_session
from ..utils.safe_json import safe_json_response
from fastapi import Request

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/jobs", tags=["Async Jobs"])


@router.post("/iep-generation", response_model=Dict[str, Any])
async def submit_iep_generation_job(
    job_request: IEPGenerationRequest,
    request: Request,
    current_user_id: int = Query(..., description="Current user's auth ID")
):
    """Submit an IEP generation job for async processing"""
    try:
        db = await get_request_session(request)
        service = AsyncJobService(db)
        job_id = await service.submit_iep_generation_job(
            request=job_request,
            created_by_auth_id=str(current_user_id)
        )
        
        return safe_json_response({
            "job_id": job_id,
            "status": "pending",
            "message": "IEP generation job submitted successfully"
        }, status_code=202)
        
    except ValueError as e:
        logger.warning(f"Invalid IEP generation request: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error submitting IEP generation job: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to submit job")


@router.post("/section-generation", response_model=Dict[str, Any])
async def submit_section_generation_job(
    job_request: SectionGenerationRequest,
    request: Request,
    current_user_id: int = Query(..., description="Current user's auth ID")
):
    """Submit a section generation job for async processing"""
    try:
        db = await get_request_session(request)
        service = AsyncJobService(db)
        job_id = await service.submit_section_generation_job(
            request=job_request,
            created_by_auth_id=str(current_user_id)
        )
        
        return safe_json_response({
            "job_id": job_id,
            "status": "pending", 
            "message": "Section generation job submitted successfully"
        }, status_code=202)
        
    except ValueError as e:
        logger.warning(f"Invalid section generation request: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error submitting section generation job: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to submit job")


@router.get("/{job_id}", response_model=Dict[str, Any])
async def get_job_status(
    job_id: str,
    request: Request,
    current_user_id: int = Query(..., description="Current user's auth ID")
):
    """Get job status by ID"""
    try:
        db = await get_request_session(request)
        service = AsyncJobService(db)
        job_status = await service.get_job_status(job_id)
        
        if not job_status:
            raise HTTPException(status_code=404, detail="Job not found")
        
        return safe_json_response(job_status.model_dump())
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting job status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get job status")


@router.get("", response_class=None)
async def list_user_jobs(
    request: Request,
    status: Optional[str] = Query(None, description="Filter by job status"),
    limit: int = Query(50, ge=1, le=100, description="Number of jobs to return"),
    offset: int = Query(0, ge=0, description="Number of jobs to skip"),
    current_user_id: int = Query(..., description="Current user's auth ID")
):
    """List jobs for the current user"""
    try:
        db = await get_request_session(request)
        service = AsyncJobService(db)
        jobs = await service.list_user_jobs(
            created_by_auth_id=str(current_user_id),
            status_filter=status,
            limit=limit,
            offset=offset
        )
        
        return safe_json_response({
            "jobs": [job.model_dump() for job in jobs],
            "total_returned": len(jobs),
            "filters": {
                "status": status,
                "limit": limit,
                "offset": offset
            }
        })
        
    except Exception as e:
        logger.error(f"Error listing user jobs: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to list jobs")


@router.patch("/{job_id}/cancel", response_class=None)
async def cancel_job(
    job_id: str,
    request: Request,
    current_user_id: int = Query(..., description="Current user's auth ID")
):
    """Cancel a pending or processing job"""
    try:
        db = await get_request_session(request)
        service = AsyncJobService(db)
        success = await service.cancel_job(
            job_id=job_id,
            user_auth_id=str(current_user_id)
        )
        
        if not success:
            raise HTTPException(
                status_code=404, 
                detail="Job not found or cannot be cancelled"
            )
        
        return safe_json_response({
            "job_id": job_id,
            "status": "cancelled",
            "message": "Job cancelled successfully"
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling job: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to cancel job")


@router.get("/admin/queue-stats", response_class=None)
async def get_queue_stats(
    request: Request,
    current_user_id: int = Query(..., description="Current user's auth ID"),
    current_user_role: str = Query("teacher", description="Current user's role")
):
    """Get queue statistics (admin only)"""
    try:
        # Check admin permissions
        if current_user_role != "admin":
            raise HTTPException(
                status_code=403, 
                detail="Admin access required"
            )
        
        db = await get_request_session(request)
        service = AsyncJobService(db)
        stats = await service.get_queue_stats()
        
        return safe_json_response(stats)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting queue stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get queue stats")


@router.post("/admin/cleanup", response_class=None)
async def cleanup_old_jobs(
    request: Request,
    days_old: int = Query(30, ge=1, le=365, description="Days old threshold"),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    current_user_id: int = Query(..., description="Current user's auth ID"),
    current_user_role: str = Query("teacher", description="Current user's role")
):
    """Clean up old completed/failed jobs (admin only)"""
    try:
        # Check admin permissions
        if current_user_role != "admin":
            raise HTTPException(
                status_code=403,
                detail="Admin access required"
            )
        
        db = await get_request_session(request)
        service = AsyncJobService(db)
        
        # Run cleanup in background
        background_tasks.add_task(
            service.cleanup_old_jobs,
            days_old=days_old
        )
        
        return safe_json_response({
            "message": f"Cleanup of jobs older than {days_old} days started",
            "status": "background_task_submitted"
        }, status_code=202)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting cleanup: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to start cleanup")


# Health check endpoint specific to async jobs
@router.get("/health", response_class=None)
async def job_health_check(
    request: Request
):
    """Health check for async job system"""
    try:
        db = await get_request_session(request)
        service = AsyncJobService(db)
        stats = await service.get_queue_stats()
        
        # Determine health status
        health_status = "healthy"
        issues = []
        
        pending_jobs = stats.get('pending_jobs', 0)
        if pending_jobs > 100:
            health_status = "degraded"
            issues.append(f"High pending job count: {pending_jobs}")
        
        wait_time = stats.get('oldest_pending_wait_minutes', 0)
        if wait_time and wait_time > 60:
            health_status = "degraded"
            issues.append(f"Long queue wait time: {wait_time} minutes")
        
        return safe_json_response({
            "status": health_status,
            "timestamp": str(datetime.utcnow()),
            "queue_stats": stats,
            "issues": issues
        })
        
    except Exception as e:
        logger.error(f"Error in job health check: {e}", exc_info=True)
        return safe_json_response({
            "status": "unhealthy",
            "timestamp": str(datetime.utcnow()),
            "error": "Failed to check job system health"
        }, status_code=500)


# Polling endpoint for job completion
@router.get("/{job_id}/poll", response_class=None)
async def poll_job_completion(
    job_id: str,
    request: Request,
    timeout_seconds: int = Query(30, ge=1, le=300, description="Polling timeout"),
    current_user_id: int = Query(..., description="Current user's auth ID")
):
    """Poll for job completion with timeout"""
    import asyncio
    from datetime import datetime, timedelta
    
    try:
        db = await get_request_session(request)
        service = AsyncJobService(db)
        start_time = datetime.utcnow()
        timeout = timedelta(seconds=timeout_seconds)
        
        while datetime.utcnow() - start_time < timeout:
            job_status = await service.get_job_status(job_id)
            
            if not job_status:
                raise HTTPException(status_code=404, detail="Job not found")
            
            # Return if job is completed, failed, or cancelled
            if job_status.status in ['completed', 'failed', 'cancelled']:
                return safe_json_response(job_status.model_dump())
            
            # Wait before next poll
            await asyncio.sleep(2)
        
        # Timeout reached, return current status
        job_status = await service.get_job_status(job_id)
        return safe_json_response({
            **job_status.model_dump(),
            "polling_timeout": True,
            "message": f"Polling timeout after {timeout_seconds} seconds"
        }, status_code=202)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error polling job: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to poll job")