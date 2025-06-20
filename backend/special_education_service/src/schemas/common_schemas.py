"""Common Pydantic schemas used across the application"""
from pydantic import BaseModel, Field
from typing import Optional, Any, List, Generic, TypeVar
from datetime import datetime, timezone

# Generic type for paginated responses
T = TypeVar('T')

class UserInfo(BaseModel):
    """User information from auth service"""
    id: int
    email: Optional[str] = None
    full_name: Optional[str] = None
    role: Optional[str] = None
    is_active: bool = True

class ResponseMetadata(BaseModel):
    """Standard response metadata"""
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    request_id: Optional[str] = None
    version: str = "1.0.0"

class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response wrapper"""
    items: List[T]
    total: int
    page: int = Field(ge=1)
    size: int = Field(ge=1, le=100)
    pages: int
    has_next: bool
    has_prev: bool
    metadata: ResponseMetadata = Field(default_factory=ResponseMetadata)

class ErrorDetail(BaseModel):
    """Error detail structure"""
    field: Optional[str] = None
    message: str
    code: Optional[str] = None

class ErrorResponse(BaseModel):
    """Standard error response"""
    error: bool = True
    message: str
    details: Optional[List[ErrorDetail]] = None
    metadata: ResponseMetadata = Field(default_factory=ResponseMetadata)

class SuccessResponse(BaseModel):
    """Standard success response"""
    success: bool = True
    message: str
    data: Optional[Any] = None
    metadata: ResponseMetadata = Field(default_factory=ResponseMetadata)