"""
Observability endpoints for monitoring, health checks, and performance metrics
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List
import logging
from datetime import datetime, timedelta
import psutil
import sys
import os
from pathlib import Path

from ..database import get_db, check_database_connection
from common.src.config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/observability", tags=["Observability"])
settings = get_settings()

@router.get("/health", response_model=Dict[str, Any])
async def basic_health_check():
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "special-education-service",
        "version": "1.0.0"
    }

@router.get("/health/detailed", response_model=Dict[str, Any])
async def detailed_health_check(db: AsyncSession = Depends(get_db)):
    """
    Detailed health check with dependency status and system metrics
    """
    try:
        # Check database connectivity
        db_healthy = await check_database_connection()
        
        # Get system metrics
        memory_info = psutil.virtual_memory()
        disk_info = psutil.disk_usage('/')
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # Check if vector store is accessible (if applicable)
        vector_store_healthy = True  # Default to true, update if ChromaDB is configured
        
        # Calculate overall health
        dependencies_healthy = db_healthy and vector_store_healthy
        system_healthy = (
            memory_info.percent < 90 and 
            disk_info.percent < 90 and 
            cpu_percent < 95
        )
        
        overall_status = "healthy" if dependencies_healthy and system_healthy else "degraded"
        
        health_data = {
            "status": overall_status,
            "timestamp": datetime.now().isoformat(),
            "service": "special-education-service",
            "version": "1.0.0",
            "dependencies": {
                "database": {
                    "status": "healthy" if db_healthy else "unhealthy",
                    "response_time_ms": None  # Could add actual timing
                },
                "vector_store": {
                    "status": "healthy" if vector_store_healthy else "unhealthy",
                    "response_time_ms": None
                },
                "auth_service": {
                    "status": "unknown",  # Would need to ping auth service
                    "response_time_ms": None
                }
            },
            "system_metrics": {
                "memory": {
                    "total_gb": round(memory_info.total / (1024**3), 2),
                    "available_gb": round(memory_info.available / (1024**3), 2),
                    "used_percent": memory_info.percent
                },
                "disk": {
                    "total_gb": round(disk_info.total / (1024**3), 2),
                    "free_gb": round(disk_info.free / (1024**3), 2),
                    "used_percent": round((disk_info.used / disk_info.total) * 100, 1)
                },
                "cpu": {
                    "usage_percent": cpu_percent,
                    "load_average": os.getloadavg() if hasattr(os, 'getloadavg') else None
                }
            },
            "application_metrics": {
                "python_version": sys.version.split()[0],
                "process_id": os.getpid(),
                "working_directory": str(Path.cwd()),
                "environment": getattr(settings, 'environment', 'unknown')
            }
        }
        
        # Return appropriate status code
        if overall_status == "healthy":
            return health_data
        else:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=health_data
            )
            
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        error_response = {
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "error": str(e),
            "service": "special-education-service"
        }
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=error_response
        )

@router.get("/metrics", response_model=Dict[str, Any])
async def get_metrics():
    """
    Prometheus-style metrics endpoint for monitoring
    """
    try:
        # Basic system metrics
        memory_info = psutil.virtual_memory()
        disk_info = psutil.disk_usage('/')
        cpu_percent = psutil.cpu_percent(interval=0.1)
        
        # Application metrics (would be enhanced with real metrics)
        metrics = {
            "system_memory_usage_percent": memory_info.percent,
            "system_memory_total_bytes": memory_info.total,
            "system_memory_available_bytes": memory_info.available,
            "system_disk_usage_percent": round((disk_info.used / disk_info.total) * 100, 1),
            "system_disk_total_bytes": disk_info.total,
            "system_disk_free_bytes": disk_info.free,
            "system_cpu_usage_percent": cpu_percent,
            "application_process_id": os.getpid(),
            "application_uptime_seconds": None,  # Would track actual uptime
            "http_requests_total": None,  # Would track request count
            "http_request_duration_seconds": None,  # Would track latency
            "database_connections_active": None,  # Would track DB connections
            "database_query_duration_seconds": None,  # Would track query performance
        }
        
        return {
            "timestamp": datetime.now().isoformat(),
            "metrics": metrics
        }
        
    except Exception as e:
        logger.error(f"Metrics collection failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to collect metrics: {str(e)}"
        )

@router.get("/info", response_model=Dict[str, Any])
async def get_service_info():
    """
    Service information endpoint
    """
    return {
        "service": "special-education-service",
        "version": "1.0.0",
        "description": "Special Education IEP Management Service with AI capabilities",
        "build_info": {
            "python_version": sys.version.split()[0],
            "platform": sys.platform,
            "architecture": os.uname().machine if hasattr(os, 'uname') else 'unknown'
        },
        "capabilities": [
            "IEP Management",
            "Student Records",
            "Goal Tracking",
            "AI-Powered Content Generation",
            "Vector Similarity Search",
            "Dashboard BFF Endpoints"
        ],
        "api_endpoints": {
            "health": "/health",
            "detailed_health": "/health/detailed",
            "metrics": "/api/v1/observability/metrics",
            "dashboard_bff": "/api/v1/dashboard/*",
            "students": "/api/v1/students",
            "ieps": "/api/v1/ieps",
            "documentation": "/docs"
        },
        "environment": getattr(settings, 'environment', 'unknown'),
        "timestamp": datetime.now().isoformat()
    }

@router.post("/logs", response_model=Dict[str, Any])
async def get_recent_logs(lines: int = 100):
    """
    Get recent application logs (if log file exists)
    Note: In production, this should be secured and limited
    """
    try:
        # This is a simplified version - in production you'd read from actual log files
        # or integrate with a logging service
        logs = [
            {
                "timestamp": (datetime.now() - timedelta(minutes=i)).isoformat(),
                "level": "INFO" if i % 3 != 0 else "WARNING",
                "message": f"Sample log message {i}",
                "service": "special-education-service"
            }
            for i in range(min(lines, 100))
        ]
        
        return {
            "logs": logs,
            "total_lines": len(logs),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Log retrieval failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve logs: {str(e)}"
        )