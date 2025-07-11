"""
Authentication middleware for Assessment Pipeline Service
Integrates with existing auth_service (:8003) JWT system
"""
import logging
from typing import Optional, Dict, Any, List
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import httpx
import os
from enum import Enum

from assessment_pipeline_service.src.service_clients import auth_client, ServiceUnavailableError, ServiceValidationError

logger = logging.getLogger(__name__)

# HTTP Bearer token extraction
security = HTTPBearer()

class UserRole(Enum):
    """User roles from auth service (maintains consistency)"""
    USER = "user"
    TEACHER = "teacher"
    CO_COORDINATOR = "co_coordinator"
    COORDINATOR = "coordinator"
    ADMIN = "admin"
    SUPERUSER = "superuser"

class AuthMiddleware:
    """Authentication middleware for assessment pipeline service"""
    
    def __init__(self):
        self.auth_service_url = os.getenv("AUTH_SERVICE_URL", "http://localhost:8003")
        
    async def get_current_user(
        self, 
        credentials: HTTPAuthorizationCredentials = Depends(security)
    ) -> Dict[str, Any]:
        """
        Validate JWT token and return current user information
        
        Raises:
            HTTPException: 401 if token invalid, 503 if auth service unavailable
        """
        try:
            logger.debug(f"Validating token for assessment pipeline access")
            
            # Use the enhanced auth client with circuit breaker
            user_info = await auth_client.validate_token(credentials.credentials)
            
            if not user_info:
                logger.warning("Token validation failed - invalid or expired token")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or expired token",
                    headers={"WWW-Authenticate": "Bearer"}
                )
            
            logger.debug(f"Token validated for user {user_info.get('sub', 'unknown')}")
            return user_info
            
        except ServiceUnavailableError:
            logger.error("Auth service unavailable during token validation")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Authentication service temporarily unavailable"
            )
        except ServiceValidationError as e:
            logger.warning(f"Token validation error: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token format",
                headers={"WWW-Authenticate": "Bearer"}
            )
        except Exception as e:
            logger.error(f"Unexpected error during token validation: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal authentication error"
            )
    
    async def get_optional_current_user(
        self, 
        credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
    ) -> Optional[Dict[str, Any]]:
        """
        Validate JWT token if provided, return None if not provided or invalid
        Used for endpoints that work with or without authentication
        """
        if not credentials:
            return None
            
        try:
            return await self.get_current_user(credentials)
        except HTTPException:
            # Don't raise for optional auth - just return None
            return None
    
    def require_role(self, required_roles: List[UserRole]) -> callable:
        """
        Dependency factory for role-based access control
        
        Args:
            required_roles: List of acceptable user roles
            
        Returns:
            Dependency function that validates user has required role
        """
        role_values = [role.value for role in required_roles]
        
        async def role_dependency(
            current_user: Dict[str, Any] = Depends(self.get_current_user)
        ) -> Dict[str, Any]:
            user_role = current_user.get("role")
            
            if user_role not in role_values:
                logger.warning(
                    f"Access denied for user {current_user.get('sub')} "
                    f"with role {user_role}, required: {role_values}"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Insufficient permissions. Required role: {role_values}"
                )
            
            logger.debug(f"Role check passed for user {current_user.get('sub')} with role {user_role}")
            return current_user
        
        return role_dependency
    
    async def require_self_or_admin(
        self,
        student_id: str,
        current_user: Dict[str, Any] = Depends(get_current_user)
    ) -> Dict[str, Any]:
        """
        Ensure user can only access their own student data or is admin/coordinator
        
        Args:
            student_id: ID of student being accessed
            current_user: Current authenticated user
            
        Returns:
            Current user if access is allowed
            
        Raises:
            HTTPException: 403 if access denied
        """
        user_role = current_user.get("role", "")
        user_id = current_user.get("sub", "")
        
        # Admin and coordinator roles can access any student
        if user_role in [UserRole.ADMIN.value, UserRole.COORDINATOR.value, UserRole.SUPERUSER.value]:
            logger.debug(f"Admin/coordinator access granted for student {student_id}")
            return current_user
        
        # Teachers can access students they're associated with (this would need service integration)
        # For now, allow teacher role but log for audit
        if user_role == UserRole.TEACHER.value:
            logger.info(f"Teacher {user_id} accessing student {student_id} - verify association in production")
            return current_user
        
        # Regular users need additional validation (parent/guardian relationship)
        # This would require integration with student management service
        logger.warning(f"Access attempt by user {user_id} to student {student_id} - insufficient permissions")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only access your own associated student records"
        )

# Global auth middleware instance
auth_middleware = AuthMiddleware()

# Common dependency functions for use in routes
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """Get current authenticated user - raises 401 if not authenticated"""
    return await auth_middleware.get_current_user(credentials)

async def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[Dict[str, Any]]:
    """Get current user if authenticated, None otherwise"""
    return await auth_middleware.get_optional_current_user(credentials)

def require_teacher_or_above() -> callable:
    """Require teacher role or higher (teacher, coordinator, admin, superuser)"""
    return auth_middleware.require_role([
        UserRole.TEACHER, UserRole.CO_COORDINATOR, UserRole.COORDINATOR, 
        UserRole.ADMIN, UserRole.SUPERUSER
    ])

def require_coordinator_or_above() -> callable:
    """Require coordinator role or higher (coordinator, admin, superuser)"""
    return auth_middleware.require_role([
        UserRole.COORDINATOR, UserRole.ADMIN, UserRole.SUPERUSER
    ])

def require_admin() -> callable:
    """Require admin role or superuser"""
    return auth_middleware.require_role([UserRole.ADMIN, UserRole.SUPERUSER])

async def require_self_or_admin_access(
    student_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Ensure user can access the specified student data"""
    return await auth_middleware.require_self_or_admin(student_id, current_user)

# Health check dependency for monitoring (no auth required)
async def health_check_access() -> bool:
    """Allow health check access without authentication"""
    return True