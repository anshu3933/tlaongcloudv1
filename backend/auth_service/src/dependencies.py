"""FastAPI dependencies for authentication and authorization."""

from typing import Optional, Dict, Any
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from .database import get_db
from .security import verify_token
from .repositories.user_repository import UserRepository
from .repositories.audit_repository import AuditRepository
from .models.user import User

# Security scheme
security = HTTPBearer(auto_error=False)

class AuthenticationError(HTTPException):
    """Custom authentication error."""
    def __init__(self, detail: str = "Authentication failed"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )

class AuthorizationError(HTTPException):
    """Custom authorization error."""
    def __init__(self, detail: str = "Insufficient permissions"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
        )

async def get_current_user_token(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Dict[str, Any]:
    """Extract and verify the current user's token."""
    if not credentials:
        raise AuthenticationError("Authorization header missing")
    
    token = credentials.credentials
    payload = verify_token(token, token_type="access")
    
    if not payload:
        raise AuthenticationError("Invalid or expired token")
    
    return payload

async def get_current_user(
    token_payload: Dict[str, Any] = Depends(get_current_user_token),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Get the current authenticated user."""
    try:
        user_id = int(token_payload.get("sub"))
    except (ValueError, TypeError):
        raise AuthenticationError("Invalid token payload")
    
    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(user_id)
    
    if not user:
        raise AuthenticationError("User not found")
    
    if not user.is_active:
        raise AuthenticationError("User account is disabled")
    
    return user

async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current active user (alias for clarity)."""
    return current_user

def require_role(required_role: str):
    """Dependency factory for role-based access control."""
    async def check_role(
        current_user: User = Depends(get_current_user)
    ) -> User:
        role_hierarchy = {
            "user": 1,
            "teacher": 2,
            "co_coordinator": 3,
            "coordinator": 4,
            "admin": 5,
            "superuser": 6
        }
        
        user_level = role_hierarchy.get(current_user.role, 0)
        required_level = role_hierarchy.get(required_role, 999)
        
        if user_level < required_level:
            raise AuthorizationError(
                f"Access denied. Required role: {required_role} or higher"
            )
        
        return current_user
    
    return check_role

def require_superuser():
    """Dependency for superuser-only access."""
    async def check_superuser(
        current_user: User = Depends(get_current_user)
    ) -> User:
        if not current_user.is_superuser:
            raise AuthorizationError("Superuser access required")
        return current_user
    
    return check_superuser

def require_self_or_admin(user_id_param: str = "user_id"):
    """Dependency factory for self-access or admin privileges."""
    async def check_self_or_admin(
        request: Request,
        current_user: User = Depends(get_current_user)
    ) -> User:
        # Get user_id from path parameters
        path_params = request.path_params
        target_user_id = path_params.get(user_id_param)
        
        if not target_user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User ID parameter missing"
            )
        
        try:
            target_user_id = int(target_user_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid user ID format"
            )
        
        # Allow if user is accessing their own data or is admin/superuser
        if (current_user.id == target_user_id or 
            current_user.role in ["admin", "coordinator"] or 
            current_user.is_superuser):
            return current_user
        
        raise AuthorizationError("Access denied. You can only access your own data")
    
    return check_self_or_admin

async def get_user_repository(db: AsyncSession = Depends(get_db)) -> UserRepository:
    """Get user repository instance."""
    return UserRepository(db)

async def get_audit_repository(db: AsyncSession = Depends(get_db)) -> AuditRepository:
    """Get audit repository instance."""
    return AuditRepository(db)

def get_client_ip(request: Request) -> str:
    """Extract client IP address from request."""
    # Check for forwarded headers (for reverse proxy setups)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    # Fallback to client host
    return request.client.host if request.client else "unknown"

class OptionalAuth:
    """Optional authentication dependency."""
    
    async def __call__(
        self,
        credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
        db: AsyncSession = Depends(get_db)
    ) -> Optional[User]:
        """Get current user if authenticated, otherwise return None."""
        if not credentials:
            return None
        
        try:
            token_payload = await get_current_user_token(credentials)
            user_repo = UserRepository(db)
            user_id = int(token_payload.get("sub"))
            user = await user_repo.get_by_id(user_id)
            
            if user and user.is_active:
                return user
        except Exception:
            pass  # Ignore authentication errors for optional auth
        
        return None

# Create instance for use
optional_auth = OptionalAuth()