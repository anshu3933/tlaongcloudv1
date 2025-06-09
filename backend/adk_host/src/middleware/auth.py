from fastapi import Request, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List, Optional
import httpx

from common.src.config import get_settings

security = HTTPBearer()
settings = get_settings()

class AuthMiddleware:
    def __init__(self):
        self.auth_service_url = settings.auth_service_url or "http://auth-service:8003"
    
    async def get_current_user(
        self,
        credentials: HTTPAuthorizationCredentials = Depends(security)
    ) -> dict:
        """Validate JWT token and return current user"""
        token = credentials.credentials
        
        # Call auth service to verify token
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.auth_service_url}/verify-token",
                    json={"token": token}
                )
                
                if response.status_code != 200:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Invalid authentication credentials",
                        headers={"WWW-Authenticate": "Bearer"},
                    )
                
                user_data = response.json()
                return user_data
                
            except httpx.RequestError:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Authentication service unavailable"
                )

# Create singleton instance
auth_middleware = AuthMiddleware()

# Dependency functions
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    return await auth_middleware.get_current_user(credentials)

def require_role(allowed_roles: List[str]):
    """Create a dependency that checks if user has required role"""
    async def role_checker(current_user: dict = Depends(get_current_user)):
        if current_user.get('role') not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"User role '{current_user.get('role')}' not authorized for this action"
            )
        return current_user
    return role_checker 