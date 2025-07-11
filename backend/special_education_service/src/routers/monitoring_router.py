from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import HTMLResponse
from typing import Dict, Any, Optional
import logging
import os
from pathlib import Path

from ..monitoring.metrics_collector import metrics_collector
from ..monitoring.health_monitor import health_monitor

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/monitoring", tags=["monitoring"])


@router.get("/dashboard", response_class=HTMLResponse)
async def get_monitoring_dashboard():
    """Serve the monitoring dashboard HTML page"""
    try:
        dashboard_path = Path(__file__).parent.parent / "monitoring" / "dashboard.html"
        
        if not dashboard_path.exists():
            raise HTTPException(status_code=404, detail="Dashboard file not found")
        
        with open(dashboard_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        return HTMLResponse(content=html_content)
        
    except Exception as e:
        logger.error(f"Failed to serve dashboard: {e}")
        raise HTTPException(status_code=500, detail="Failed to load monitoring dashboard")


@router.get("/health", response_model=Dict[str, Any])
async def get_health_status():
    """Get current system health status"""
    try:
        return await health_monitor.get_comprehensive_health()
    except Exception as e:
        logger.error(f"Failed to get health status: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve health status")


@router.get("/health/simple", response_model=Dict[str, Any])
async def get_simple_health():
    """Simple health check endpoint"""
    try:
        health_status = metrics_collector.get_health_status()
        return {
            "status": health_status["status"],
            "message": health_status["message"],
            "timestamp": health_status["last_update"]
        }
    except Exception as e:
        logger.error(f"Failed to get simple health: {e}")
        return {
            "status": "error",
            "message": f"Health check failed: {str(e)}",
            "timestamp": None
        }


@router.get("/metrics", response_model=Dict[str, Any])
async def get_metrics():
    """Get comprehensive metrics dashboard"""
    try:
        return metrics_collector.get_dashboard_data()
    except Exception as e:
        logger.error(f"Failed to get metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve metrics")


@router.get("/metrics/conflicts", response_model=Dict[str, Any])
async def get_conflict_metrics(
    hours: int = Query(default=1, ge=1, le=168, description="Time period in hours (1-168)")
):
    """Get version conflict metrics for specified time period"""
    try:
        return metrics_collector.get_conflict_summary(hours=hours)
    except Exception as e:
        logger.error(f"Failed to get conflict metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve conflict metrics")


@router.get("/metrics/performance", response_model=Dict[str, Any])
async def get_performance_metrics(
    hours: int = Query(default=1, ge=1, le=168, description="Time period in hours (1-168)")
):
    """Get performance metrics for specified time period"""
    try:
        return metrics_collector.get_performance_summary(hours=hours)
    except Exception as e:
        logger.error(f"Failed to get performance metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve performance metrics")


@router.get("/alerts", response_model=Dict[str, Any])
async def get_alerts():
    """Get current system alerts"""
    try:
        health_data = await health_monitor.get_comprehensive_health()
        return {
            "alerts": health_data.get("alerts", []),
            "alert_count": len(health_data.get("alerts", [])),
            "status": health_data.get("overall_status", "unknown")
        }
    except Exception as e:
        logger.error(f"Failed to get alerts: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve alerts")


@router.get("/status", response_model=Dict[str, Any])
async def get_monitoring_status():
    """Get monitoring system status and statistics"""
    try:
        return {
            "monitoring_active": True,
            "metrics_collector": {
                "total_operations": metrics_collector.total_operations,
                "total_conflicts": metrics_collector.total_conflicts,
                "total_retries": metrics_collector.total_retries,
                "active_operations": metrics_collector.active_operations,
                "conflict_events_stored": len(metrics_collector.conflict_events),
                "performance_metrics_stored": len(metrics_collector.performance_metrics),
                "health_snapshots_stored": len(metrics_collector.health_snapshots)
            },
            "health_monitor": {
                "is_running": health_monitor.is_running,
                "check_interval": health_monitor.check_interval
            }
        }
    except Exception as e:
        logger.error(f"Failed to get monitoring status: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve monitoring status")


@router.post("/cleanup", response_model=Dict[str, Any])
async def cleanup_old_data():
    """Manually trigger cleanup of old monitoring data"""
    try:
        metrics_collector.cleanup_old_data()
        return {
            "status": "success",
            "message": "Old monitoring data cleaned up successfully"
        }
    except Exception as e:
        logger.error(f"Failed to cleanup old data: {e}")
        raise HTTPException(status_code=500, detail="Failed to cleanup old data")


@router.get("/database/health", response_model=Dict[str, Any])
async def get_database_health():
    """Get database health status"""
    try:
        return await health_monitor.get_database_health()
    except Exception as e:
        logger.error(f"Failed to get database health: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve database health")


@router.get("/summary/hourly", response_model=Dict[str, Any])
async def get_hourly_summary():
    """Get hourly summary statistics"""
    try:
        return {
            "hourly_stats": dict(metrics_collector.hourly_stats),
            "data_points": len(metrics_collector.hourly_stats)
        }
    except Exception as e:
        logger.error(f"Failed to get hourly summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve hourly summary")


@router.get("/conflicts/recent", response_model=Dict[str, Any])
async def get_recent_conflicts(
    limit: int = Query(default=10, ge=1, le=100, description="Number of recent conflicts to return")
):
    """Get recent conflict events"""
    try:
        recent_conflicts = list(metrics_collector.conflict_events)[-limit:]
        return {
            "conflicts": [
                {
                    "timestamp": event.timestamp.isoformat(),
                    "student_id": event.student_id,
                    "academic_year": event.academic_year,
                    "attempted_version": event.attempted_version,
                    "conflict_type": event.conflict_type,
                    "retry_count": event.retry_count,
                    "resolution_time_ms": event.resolution_time_ms,
                    "error_message": event.error_message
                }
                for event in recent_conflicts
            ],
            "count": len(recent_conflicts)
        }
    except Exception as e:
        logger.error(f"Failed to get recent conflicts: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve recent conflicts")


@router.get("/performance/slowest", response_model=Dict[str, Any])
async def get_slowest_operations(
    limit: int = Query(default=10, ge=1, le=100, description="Number of slowest operations to return")
):
    """Get slowest operations"""
    try:
        all_metrics = list(metrics_collector.performance_metrics)
        slowest = sorted(all_metrics, key=lambda x: x.duration_ms, reverse=True)[:limit]
        
        return {
            "slowest_operations": [
                {
                    "operation_name": metric.operation_name,
                    "duration_ms": metric.duration_ms,
                    "timestamp": metric.timestamp.isoformat(),
                    "success": metric.success,
                    "retry_count": metric.retry_count,
                    "error_type": metric.error_type
                }
                for metric in slowest
            ],
            "count": len(slowest)
        }
    except Exception as e:
        logger.error(f"Failed to get slowest operations: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve slowest operations")