import time
import logging
from typing import Callable, Any
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from .metrics_collector import metrics_collector
from .health_monitor import health_monitor

logger = logging.getLogger(__name__)


class MonitoringMiddleware(BaseHTTPMiddleware):
    """Middleware to automatically track API performance and errors"""
    
    def __init__(self, app, track_all_endpoints: bool = True):
        super().__init__(app)
        self.track_all_endpoints = track_all_endpoints
        
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip health check endpoints to avoid noise
        if request.url.path in ["/health", "/metrics", "/monitoring"]:
            return await call_next(request)
        
        # Start tracking the operation
        start_time = time.time()
        operation_id = metrics_collector.start_operation()
        
        # Track session if it's a database operation
        if any(path in request.url.path for path in ["/api/v1/", "/students", "/ieps"]):
            health_monitor.track_session_start()
        
        try:
            # Process the request
            response = await call_next(request)
            
            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000
            
            # Determine if operation was successful
            success = 200 <= response.status_code < 400
            error_type = None if success else f"HTTP_{response.status_code}"
            
            # Record performance metric
            operation_name = f"{request.method} {request.url.path}"
            metrics_collector.record_performance_metric(
                operation_name=operation_name,
                duration_ms=duration_ms,
                success=success,
                error_type=error_type
            )
            
            # Log slow operations
            if duration_ms > 1000:  # Log operations slower than 1 second
                logger.warning(
                    f"Slow operation: {operation_name} took {duration_ms:.2f}ms"
                )
            
            return response
            
        except Exception as e:
            # Calculate duration for failed operations
            duration_ms = (time.time() - start_time) * 1000
            
            # Record the failure
            operation_name = f"{request.method} {request.url.path}"
            error_type = type(e).__name__
            
            metrics_collector.record_performance_metric(
                operation_name=operation_name,
                duration_ms=duration_ms,
                success=False,
                error_type=error_type
            )
            
            logger.error(
                f"Operation failed: {operation_name} after {duration_ms:.2f}ms - {error_type}: {str(e)}"
            )
            
            # Re-raise the exception
            raise
            
        finally:
            # End operation tracking
            metrics_collector.end_operation()
            
            # End session tracking if applicable
            if any(path in request.url.path for path in ["/api/v1/", "/students", "/ieps"]):
                health_monitor.track_session_end()


def track_operation(operation_name: str):
    """Decorator to track specific operations with detailed metrics"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            operation_id = metrics_collector.start_operation()
            retry_count = 0
            
            try:
                # Check if this is a retry operation
                if hasattr(func, '_retry_count'):
                    retry_count = getattr(func, '_retry_count', 0)
                
                result = await func(*args, **kwargs)
                
                # Calculate duration
                duration_ms = (time.time() - start_time) * 1000
                
                # Record successful operation
                metrics_collector.record_performance_metric(
                    operation_name=operation_name,
                    duration_ms=duration_ms,
                    success=True,
                    retry_count=retry_count
                )
                
                return result
                
            except Exception as e:
                # Calculate duration for failed operations
                duration_ms = (time.time() - start_time) * 1000
                error_type = type(e).__name__
                
                # Record failed operation
                metrics_collector.record_performance_metric(
                    operation_name=operation_name,
                    duration_ms=duration_ms,
                    success=False,
                    retry_count=retry_count,
                    error_type=error_type
                )
                
                # If this is a version conflict, record it specifically
                if "version" in str(e).lower() or "conflict" in str(e).lower():
                    # Try to extract student info from args
                    student_id = "unknown"
                    academic_year = "unknown"
                    attempted_version = 0
                    
                    # Look for student_id and academic_year in function arguments
                    for arg in args:
                        if hasattr(arg, 'student_id'):
                            student_id = str(arg.student_id)
                        if hasattr(arg, 'academic_year'):
                            academic_year = str(arg.academic_year)
                    
                    # Look in kwargs
                    if 'student_id' in kwargs:
                        student_id = str(kwargs['student_id'])
                    if 'academic_year' in kwargs:
                        academic_year = str(kwargs['academic_year'])
                    
                    conflict_type = "database_error"
                    if "retryable" in error_type.lower():
                        conflict_type = "version_conflict"
                    elif retry_count >= 3:
                        conflict_type = "retry_exhausted"
                    
                    metrics_collector.record_conflict_event(
                        student_id=student_id,
                        academic_year=academic_year,
                        attempted_version=attempted_version,
                        conflict_type=conflict_type,
                        retry_count=retry_count,
                        resolution_time_ms=duration_ms,
                        error_message=str(e)
                    )
                
                raise
                
            finally:
                metrics_collector.end_operation()
        
        return wrapper
    return decorator


def track_conflict(
    student_id: str,
    academic_year: str,
    attempted_version: int,
    conflict_type: str,
    retry_count: int,
    resolution_time_ms: float,
    error_message: str = None
):
    """Manually track a version conflict event"""
    metrics_collector.record_conflict_event(
        student_id=student_id,
        academic_year=academic_year,
        attempted_version=attempted_version,
        conflict_type=conflict_type,
        retry_count=retry_count,
        resolution_time_ms=resolution_time_ms,
        error_message=error_message
    )