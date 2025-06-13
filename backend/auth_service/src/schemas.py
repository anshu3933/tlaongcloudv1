"""Pydantic schemas for request/response validation."""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, validator
from enum import Enum

# Base schemas
class TimestampMixin(BaseModel):
    """Mixin for timestamp fields."""
    created_at: datetime
    updated_at: Optional[datetime] = None

# Enums
class UserRole(str, Enum):
    """User role enumeration."""
    USER = "user"
    TEACHER = "teacher"
    CO_COORDINATOR = "co_coordinator"
    COORDINATOR = "coordinator"
    ADMIN = "admin"
    SUPERUSER = "superuser"

class TokenType(str, Enum):
    """Token type enumeration."""
    ACCESS = "access"
    REFRESH = "refresh"

# User schemas
class UserBase(BaseModel):
    """Base user schema."""
    email: EmailStr
    full_name: Optional[str] = None
    role: Optional[UserRole] = UserRole.USER

class UserCreate(UserBase):
    """Schema for user creation."""
    password: str = Field(..., min_length=8, max_length=128)
    
    @validator('password')
    def validate_password(cls, v):
        """Validate password complexity."""
        try:
            from .security import PasswordValidator
        except ImportError:
            from security import PasswordValidator
        is_valid, errors = PasswordValidator.validate_password(v)
        if not is_valid:
            raise ValueError("; ".join(errors))
        return v

class UserUpdate(BaseModel):
    """Schema for user updates."""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None

class UserResponse(UserBase, TimestampMixin):
    """Schema for user responses."""
    id: int
    is_active: bool
    is_superuser: bool
    last_login: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class UserSummary(BaseModel):
    """Schema for user summary responses."""
    id: int
    email: EmailStr
    full_name: Optional[str]
    role: Optional[UserRole]
    is_active: bool
    last_login: Optional[datetime]
    created_at: datetime

# Authentication schemas
class UserLogin(BaseModel):
    """Schema for user login."""
    email: EmailStr
    password: str = Field(..., min_length=1)

class Token(BaseModel):
    """Schema for JWT token response."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse

class TokenRefresh(BaseModel):
    """Schema for token refresh request."""
    refresh_token: str

class TokenVerify(BaseModel):
    """Schema for token verification."""
    token: str

class PasswordChange(BaseModel):
    """Schema for password change request."""
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=128)
    
    @validator('new_password')
    def validate_new_password(cls, v):
        """Validate new password complexity."""
        try:
            from .security import PasswordValidator
        except ImportError:
            from security import PasswordValidator
        is_valid, errors = PasswordValidator.validate_password(v)
        if not is_valid:
            raise ValueError("; ".join(errors))
        return v

# Session schemas
class UserSessionResponse(BaseModel):
    """Schema for user session response."""
    id: int
    user_id: int
    expires_at: datetime
    created_at: datetime
    
    class Config:
        from_attributes = True

# Audit log schemas
class AuditLogResponse(BaseModel):
    """Schema for audit log response."""
    id: int
    entity_type: str
    entity_id: int
    action: str
    user_id: Optional[int]
    user_role: Optional[str]
    ip_address: Optional[str]
    details: Optional[Dict[str, Any]]
    created_at: datetime
    
    class Config:
        from_attributes = True

class AuditLogQuery(BaseModel):
    """Schema for audit log queries."""
    entity_type: Optional[str] = None
    entity_id: Optional[int] = None
    action: Optional[str] = None
    user_id: Optional[int] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    limit: int = Field(default=100, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)

class AuditStatistics(BaseModel):
    """Schema for audit statistics response."""
    total_logs: int
    action_counts: Dict[str, int]
    period: Dict[str, Optional[str]]

class UserActivitySummary(BaseModel):
    """Schema for user activity summary."""
    user_id: int
    period_days: int
    action_counts: Dict[str, int]
    total_actions: int
    last_activity: Dict[str, Optional[str]]

# Error schemas
class ErrorDetail(BaseModel):
    """Schema for error details."""
    type: str
    message: str
    field: Optional[str] = None

class ErrorResponse(BaseModel):
    """Schema for error responses."""
    detail: str
    errors: Optional[List[ErrorDetail]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

# Health check schema
class HealthResponse(BaseModel):
    """Schema for health check response."""
    status: str
    service: str
    version: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    database: Optional[str] = None

# Pagination schemas
class PaginationMeta(BaseModel):
    """Schema for pagination metadata."""
    total: int
    page: int
    per_page: int
    total_pages: int
    has_next: bool
    has_prev: bool

class PaginatedResponse(BaseModel):
    """Generic paginated response schema."""
    data: List[Any]
    meta: PaginationMeta

class PaginatedUserResponse(BaseModel):
    """Paginated user response schema."""
    data: List[UserResponse]
    meta: PaginationMeta

class PaginatedAuditLogResponse(BaseModel):
    """Paginated audit log response schema."""
    data: List[AuditLogResponse]
    meta: PaginationMeta

# Success response schemas
class SuccessResponse(BaseModel):
    """Schema for success responses."""
    message: str
    data: Optional[Dict[str, Any]] = None

class SessionCleanupResponse(BaseModel):
    """Schema for session cleanup response."""
    message: str
    cleaned_sessions: int

class UserDeactivationResponse(BaseModel):
    """Schema for user deactivation response."""
    message: str
    user_id: int
    sessions_cleared: int

class UserActivationResponse(BaseModel):
    """Schema for user activation response."""
    message: str
    user_id: int

class PasswordChangeResponse(BaseModel):
    """Schema for password change response."""
    message: str
    sessions_invalidated: int

# Query parameter schemas
class UserListQuery(BaseModel):
    """Schema for user list query parameters."""
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    search: Optional[str] = None
    limit: int = Field(default=50, ge=1, le=100)
    offset: int = Field(default=0, ge=0)

class DateRangeQuery(BaseModel):
    """Schema for date range queries."""
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

# Validation helpers
def validate_user_id(v: int) -> int:
    """Validate user ID."""
    if v <= 0:
        raise ValueError("User ID must be positive")
    return v

def validate_limit(v: int) -> int:
    """Validate limit parameter."""
    if v <= 0 or v > 1000:
        raise ValueError("Limit must be between 1 and 1000")
    return v

def validate_offset(v: int) -> int:
    """Validate offset parameter."""
    if v < 0:
        raise ValueError("Offset must be non-negative")
    return v

# Custom validators for common use cases
class IDValidationMixin(BaseModel):
    """Mixin for ID validation."""
    
    @validator('*', pre=True)
    def validate_ids(cls, v, field):
        """Validate ID fields."""
        if field.name.endswith('_id') and isinstance(v, int):
            if v <= 0:
                raise ValueError(f"{field.name} must be positive")
        return v

# Configuration schemas
class AuthSettings(BaseModel):
    """Schema for authentication settings."""
    access_token_expire_minutes: int
    refresh_token_expire_days: int
    max_sessions_per_user: int
    password_min_length: int
    require_password_complexity: bool

# Rate limiting schemas
class RateLimitInfo(BaseModel):
    """Schema for rate limit information."""
    requests_remaining: int
    reset_time: datetime
    limit: int
    window_seconds: int