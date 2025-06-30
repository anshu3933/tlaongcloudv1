"""Custom SQLAlchemy type decorators for safe data type handling"""
from sqlalchemy import TypeDecorator, Date
from datetime import date, datetime
from typing import Optional, Union


class SafeDate(TypeDecorator):
    """A Date type that safely converts strings and datetime objects to date objects.
    
    This decorator handles the common SQLite issue where date strings leak through
    the application layers and cause "SQLite Date type only accepts Python date objects"
    errors at the database binding layer.
    
    Usage:
        meeting_date = Column(SafeDate(), nullable=True)
    """
    impl = Date
    cache_ok = True  # SQLAlchemy 2.x performance optimization
    
    def process_bind_param(self, value: Optional[Union[str, date, datetime]], dialect) -> Optional[date]:
        """Convert input value to a date object before database binding.
        
        Args:
            value: The input value (string, date, datetime, or None)
            dialect: The SQL dialect in use
            
        Returns:
            A Python date object or None
            
        Raises:
            ValueError: If the date string format is invalid
            TypeError: If the value type is not supported
        """
        if value is None:
            return None
            
        if isinstance(value, date):
            return value
            
        if isinstance(value, datetime):
            return value.date()
            
        if isinstance(value, str):
            # Try common date formats
            for fmt in ["%Y-%m-%d", "%Y/%m/%d", "%m-%d-%Y", "%m/%d/%Y"]:
                try:
                    return datetime.strptime(value, fmt).date()
                except ValueError:
                    continue
            raise ValueError(f"Invalid date string format: {value}")
            
        raise TypeError(f"SafeDate cannot convert type {type(value).__name__} to date")
    
    def process_result_value(self, value: Optional[date], dialect) -> Optional[date]:
        """Process value from database (no conversion needed for dates)."""
        return value