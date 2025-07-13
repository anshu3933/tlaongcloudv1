"""
Safe database operation wrappers for graceful degradation
Handles schema mismatch errors without crashing the API
"""
import logging
from typing import Any, Callable, List, Optional, TypeVar, Union
from sqlalchemy.exc import OperationalError, StatementError
import time

logger = logging.getLogger(__name__)

T = TypeVar('T')

class DatabaseMetrics:
    """Simple metrics tracking for database operations"""
    def __init__(self):
        self.partial_failures = 0
        self.total_calls = 0
        self.last_failure_time = None
    
    def increment_failure(self):
        self.partial_failures += 1
        self.last_failure_time = time.time()
        logger.warning(f"Database partial failure count: {self.partial_failures}")
    
    def increment_call(self):
        self.total_calls += 1
    
    def get_failure_rate(self) -> float:
        if self.total_calls == 0:
            return 0.0
        return self.partial_failures / self.total_calls

# Global metrics instance
db_metrics = DatabaseMetrics()

async def safe_db_operation(
    operation: Callable[..., T], 
    *args, 
    default_return: Any = None,
    operation_name: str = "unknown",
    **kwargs
) -> Union[T, Any]:
    """
    Safely execute a database operation with graceful degradation
    
    Args:
        operation: The async database operation to execute
        *args: Arguments to pass to the operation
        default_return: What to return if operation fails (default: [] for lists, None for single items)
        operation_name: Name of the operation for logging
        **kwargs: Keyword arguments to pass to the operation
    
    Returns:
        Operation result on success, default_return on schema mismatch
    
    Raises:
        Non-schema related exceptions are re-raised
    """
    db_metrics.increment_call()
    
    try:
        result = await operation(*args, **kwargs)
        logger.debug(f"✅ Safe DB operation '{operation_name}' succeeded")
        return result
        
    except (OperationalError, StatementError) as exc:
        error_msg = str(exc).lower()
        
        # Check for schema-related errors
        if any(phrase in error_msg for phrase in [
            "no such column", 
            "column does not exist", 
            "relation does not exist",
            "column not found"
        ]):
            db_metrics.increment_failure()
            logger.warning(
                f"⚠️ Schema mismatch in operation '{operation_name}': {exc}. "
                f"Returning default value. Migration needed."
            )
            
            # Return appropriate default based on type hint or explicit default
            if default_return is not None:
                return default_return
            
            # Smart defaults based on common patterns
            if "get_" in operation.__name__ and "list" in operation.__name__.lower():
                return []
            elif "get_" in operation.__name__:
                return None
            else:
                return []
        else:
            # Re-raise non-schema errors
            logger.error(f"❌ Non-schema database error in '{operation_name}': {exc}")
            raise
            
    except Exception as exc:
        # Re-raise all other exceptions
        logger.error(f"❌ Unexpected error in safe DB operation '{operation_name}': {exc}")
        raise

async def safe_list_operation(operation: Callable[..., List[T]], *args, **kwargs) -> List[T]:
    """Convenience wrapper for operations that return lists"""
    return await safe_db_operation(operation, *args, default_return=[], **kwargs)

async def safe_single_operation(operation: Callable[..., Optional[T]], *args, **kwargs) -> Optional[T]:
    """Convenience wrapper for operations that return single items or None"""
    return await safe_db_operation(operation, *args, default_return=None, **kwargs)

def get_database_health() -> dict:
    """Get current database health metrics"""
    failure_rate = db_metrics.get_failure_rate()
    
    return {
        "total_calls": db_metrics.total_calls,
        "partial_failures": db_metrics.partial_failures,
        "failure_rate": failure_rate,
        "last_failure_time": db_metrics.last_failure_time,
        "status": "degraded" if failure_rate > 0.1 else "healthy",
        "migration_needed": db_metrics.partial_failures > 0
    }