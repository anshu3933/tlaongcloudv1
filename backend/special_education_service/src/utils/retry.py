"""Retry utilities for handling temporary conflicts and database issues"""
import asyncio
import random
import logging
import time
from typing import Callable, TypeVar, Any, Optional
from functools import wraps

logger = logging.getLogger(__name__)

T = TypeVar('T')

class RetryableError(Exception):
    """Base class for errors that should trigger retries"""
    pass

class VersionConflictError(RetryableError):
    """Raised when IEP version conflicts occur"""
    pass

class DatabaseLockError(RetryableError):
    """Raised when database lock conflicts occur"""
    pass

async def retry_with_exponential_backoff(
    func: Callable[..., T],
    max_retries: int = 3,
    base_delay: float = 0.1,
    max_delay: float = 5.0,
    backoff_factor: float = 2.0,
    jitter: bool = True,
    retryable_exceptions: tuple = (RetryableError,)
) -> T:
    """
    Retry a function with exponential backoff.
    
    Args:
        func: The async function to retry
        max_retries: Maximum number of retry attempts
        base_delay: Base delay in seconds
        max_delay: Maximum delay in seconds
        backoff_factor: Exponential backoff multiplier
        jitter: Add random jitter to prevent thundering herd
        retryable_exceptions: Tuple of exception types that should trigger retries
    
    Returns:
        The result of the successful function call
    
    Raises:
        The last exception if all retries are exhausted
    """
    last_exception = None
    
    for attempt in range(max_retries + 1):
        try:
            if hasattr(func, '__call__'):
                # Direct function call
                return await func()
            else:
                # Should not happen, but handle gracefully
                raise ValueError("func must be callable")
                
        except retryable_exceptions as e:
            last_exception = e
            
            if attempt == max_retries:
                logger.error(f"Retry exhausted after {max_retries} attempts: {e}")
                raise e
            
            # Calculate delay with exponential backoff
            delay = min(base_delay * (backoff_factor ** attempt), max_delay)
            
            # Add jitter to prevent thundering herd
            if jitter:
                jitter_amount = delay * 0.1  # 10% jitter
                delay += random.uniform(-jitter_amount, jitter_amount)
            
            logger.warning(f"Attempt {attempt + 1} failed, retrying in {delay:.3f}s: {e}")
            await asyncio.sleep(delay)
            
        except Exception as e:
            # Non-retryable exception, fail immediately
            logger.error(f"Non-retryable error occurred: {e}")
            raise e
    
    # Should never reach here, but handle gracefully
    if last_exception:
        raise last_exception
    else:
        raise RuntimeError("Unexpected retry loop termination")

def retry_on_conflict(
    max_retries: int = 3,
    base_delay: float = 0.1,
    max_delay: float = 2.0
):
    """
    Decorator for automatically retrying functions that may encounter conflicts.
    
    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Base delay in seconds
        max_delay: Maximum delay in seconds
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            async def retry_func():
                return await func(*args, **kwargs)
            
            return await retry_with_exponential_backoff(
                retry_func,
                max_retries=max_retries,
                base_delay=base_delay,
                max_delay=max_delay,
                retryable_exceptions=(
                    RetryableError,
                    # Add SQLAlchemy specific exceptions that indicate conflicts
                    # These will be imported conditionally
                )
            )
        return wrapper
    return decorator

class ConflictDetector:
    """Utility for detecting database conflicts and converting them to retryable errors"""
    
    @staticmethod
    def is_version_conflict(exception: Exception) -> bool:
        """Check if exception indicates an IEP version conflict"""
        error_str = str(exception).lower()
        return any(phrase in error_str for phrase in [
            'uq_student_year_version',
            'duplicate key value violates unique constraint',
            'version conflict',
            'constraint violation'
        ])
    
    @staticmethod
    def is_lock_conflict(exception: Exception) -> bool:
        """Check if exception indicates a database lock conflict"""
        error_str = str(exception).lower()
        return any(phrase in error_str for phrase in [
            'lock timeout',
            'deadlock detected',
            'could not obtain lock',
            'advisory lock',
            'lock wait timeout'
        ])
    
    @staticmethod
    def convert_to_retryable_error(exception: Exception) -> Exception:
        """Convert database exceptions to retryable errors when appropriate"""
        if ConflictDetector.is_version_conflict(exception):
            return VersionConflictError(f"IEP version conflict detected: {exception}")
        elif ConflictDetector.is_lock_conflict(exception):
            return DatabaseLockError(f"Database lock conflict detected: {exception}")
        else:
            # Return original exception (non-retryable)
            return exception

# Convenience function for common retry patterns
async def retry_iep_operation(operation: Callable[..., T], *args, **kwargs) -> T:
    """
    Convenience function for retrying IEP operations with appropriate settings.
    
    Args:
        operation: The async operation to retry
        *args: Arguments to pass to the operation
        **kwargs: Keyword arguments to pass to the operation
    
    Returns:
        The result of the successful operation
    """
    start_time = time.time()
    retry_count = 0
    last_exception = None
    
    # Try to import monitoring (optional dependency)
    try:
        from ..monitoring.middleware import track_conflict
        monitoring_available = True
    except ImportError:
        monitoring_available = False
    
    async def retry_func():
        nonlocal retry_count, last_exception
        try:
            result = await operation(*args, **kwargs)
            
            # If we had retries, log the successful resolution
            if retry_count > 0 and monitoring_available:
                resolution_time_ms = (time.time() - start_time) * 1000
                
                # Extract student info for monitoring (best effort)
                student_id = "unknown"
                academic_year = "unknown"
                
                # Look for student_id and academic_year in operation arguments
                for arg in args:
                    if hasattr(arg, 'student_id'):
                        student_id = str(arg.student_id)
                    if hasattr(arg, 'academic_year'):
                        academic_year = str(arg.academic_year)
                
                if 'student_id' in kwargs:
                    student_id = str(kwargs['student_id'])
                if 'academic_year' in kwargs:
                    academic_year = str(kwargs['academic_year'])
                
                track_conflict(
                    student_id=student_id,
                    academic_year=academic_year,
                    attempted_version=0,  # Unknown at this level
                    conflict_type="resolved_after_retry",
                    retry_count=retry_count,
                    resolution_time_ms=resolution_time_ms,
                    error_message=str(last_exception) if last_exception else None
                )
            
            return result
            
        except Exception as e:
            last_exception = e
            retry_count += 1
            
            # Convert database exceptions to retryable errors when appropriate
            converted_exception = ConflictDetector.convert_to_retryable_error(e)
            if isinstance(converted_exception, RetryableError):
                raise converted_exception
            else:
                raise e
    
    try:
        return await retry_with_exponential_backoff(
            retry_func,
            max_retries=3,
            base_delay=0.1,
            max_delay=1.0,
            retryable_exceptions=(RetryableError,)
        )
    except Exception as e:
        # If all retries failed, record the final failure
        if monitoring_available and retry_count > 0:
            resolution_time_ms = (time.time() - start_time) * 1000
            
            # Extract student info for monitoring (best effort)
            student_id = "unknown"
            academic_year = "unknown"
            
            for arg in args:
                if hasattr(arg, 'student_id'):
                    student_id = str(arg.student_id)
                if hasattr(arg, 'academic_year'):
                    academic_year = str(arg.academic_year)
            
            if 'student_id' in kwargs:
                student_id = str(kwargs['student_id'])
            if 'academic_year' in kwargs:
                academic_year = str(kwargs['academic_year'])
            
            track_conflict(
                student_id=student_id,
                academic_year=academic_year,
                attempted_version=0,  # Unknown at this level
                conflict_type="retry_exhausted",
                retry_count=retry_count,
                resolution_time_ms=resolution_time_ms,
                error_message=str(e)
            )
        
        raise