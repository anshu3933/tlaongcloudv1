"""Authentication routes for login, registration, token management."""

from datetime import datetime, timedelta, timezone
from typing import Dict
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..dependencies import get_audit_repository, get_user_repository, get_client_ip
from ..dependencies.auth import get_current_user, get_optional_current_user
from ..repositories.user_repository import UserRepository
from ..repositories.audit_repository import AuditRepository
from ..models.user import User
from ..security import (
    hash_password, verify_password, create_access_token, create_refresh_token,
    verify_token, PasswordValidator
)
from ..schemas import (
    UserCreate, UserLogin, UserResponse, Token, TokenRefresh, 
    SuccessResponse, SessionCleanupResponse
)
from ..config import get_auth_settings
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["authentication"])
settings = get_auth_settings()

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user_repo: UserRepository = Depends(get_user_repository),
    audit_repo: AuditRepository = Depends(get_audit_repository)
):
    """
    Register a new user account.
    
    - **email**: Valid email address (must be unique)
    - **password**: Password meeting complexity requirements
    - **full_name**: User's full name
    - **role**: User role (defaults to 'user')
    """
    client_ip = get_client_ip(request)
    
    try:
        # Check if user already exists
        existing_user = await user_repo.get_by_email(user_data.email)
        if existing_user:
            await audit_repo.log_action(
                entity_type="user",
                entity_id=0,
                action="registration_failed",
                ip_address=client_ip,
                details={"reason": "email_already_exists", "email": user_data.email}
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists"
            )
        
        # Validate password
        is_valid, errors = PasswordValidator.validate_password(user_data.password)
        if not is_valid:
            await audit_repo.log_action(
                entity_type="user",
                entity_id=0,
                action="registration_failed",
                ip_address=client_ip,
                details={"reason": "invalid_password", "errors": errors}
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Password validation failed: {'; '.join(errors)}"
            )
        
        # Create user
        hashed_password = hash_password(user_data.password)
        user = User(
            email=user_data.email,
            hashed_password=hashed_password,
            full_name=user_data.full_name,
            role=user_data.role
        )
        
        created_user = await user_repo.create(user)
        
        # Log successful registration
        await audit_repo.log_action(
            entity_type="user",
            entity_id=created_user.id,
            action="user_registered",
            user_id=created_user.id,
            user_role=created_user.role,
            ip_address=client_ip,
            details={"email": created_user.email, "role": created_user.role}
        )
        
        logger.info(f"User registered: {created_user.email}")
        return UserResponse.from_orm(created_user)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {e}")
        await audit_repo.log_action(
            entity_type="user",
            entity_id=0,
            action="registration_error",
            ip_address=client_ip,
            details={"error": str(e)}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during registration"
        )

@router.post("/login", response_model=Token)
async def login(
    credentials: UserLogin,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user_repo: UserRepository = Depends(get_user_repository),
    audit_repo: AuditRepository = Depends(get_audit_repository)
):
    """
    Authenticate user and return JWT tokens.
    
    - **email**: User's email address
    - **password**: User's password
    
    Returns access token (60 min) and refresh token (7 days).
    """
    client_ip = get_client_ip(request)
    
    try:
        # Get user by email
        user = await user_repo.get_by_email(credentials.email)
        
        if not user:
            await audit_repo.log_action(
                entity_type="user",
                entity_id=0,
                action="login_failed",
                ip_address=client_ip,
                details={"reason": "user_not_found", "email": credentials.email}
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        # Check if user is active
        if not user.is_active:
            await audit_repo.log_action(
                entity_type="user",
                entity_id=user.id,
                action="login_failed",
                user_id=user.id,
                user_role=user.role,
                ip_address=client_ip,
                details={"reason": "account_disabled"}
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account is disabled"
            )
        
        # Verify password
        if not verify_password(credentials.password, user.hashed_password):
            await audit_repo.log_action(
                entity_type="user",
                entity_id=user.id,
                action="login_failed",
                user_id=user.id,
                user_role=user.role,
                ip_address=client_ip,
                details={"reason": "invalid_password"}
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        # Create tokens
        access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
        access_token = create_access_token(
            data={"sub": str(user.id), "email": user.email, "role": user.role},
            expires_delta=access_token_expires
        )
        
        refresh_token = create_refresh_token(user.id)
        refresh_expires_at = datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days)
        
        # Store refresh token session
        await user_repo.create_session(
            user_id=user.id,
            refresh_token=refresh_token,
            expires_at=refresh_expires_at
        )
        
        # Update last login
        await user_repo.update_last_login(user.id)
        
        # Log successful login
        await audit_repo.log_action(
            entity_type="user",
            entity_id=user.id,
            action="login_success",
            user_id=user.id,
            user_role=user.role,
            ip_address=client_ip,
            details={"login_method": "password"}
        )
        
        logger.info(f"User logged in: {user.email}")
        
        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.access_token_expire_minutes * 60,
            user=UserResponse.from_orm(user)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        await audit_repo.log_action(
            entity_type="user",
            entity_id=0,
            action="login_error",
            ip_address=client_ip,
            details={"error": str(e)}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during login"
        )

@router.post("/refresh", response_model=Token)
async def refresh_token(
    token_data: TokenRefresh,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user_repo: UserRepository = Depends(get_user_repository),
    audit_repo: AuditRepository = Depends(get_audit_repository)
):
    """
    Refresh access token using refresh token.
    
    - **refresh_token**: Valid refresh token
    
    Returns new access token with same refresh token.
    """
    client_ip = get_client_ip(request)
    
    try:
        # Verify refresh token
        payload = verify_token(token_data.refresh_token, token_type="refresh")
        if not payload:
            await audit_repo.log_action(
                entity_type="session",
                entity_id=0,
                action="token_refresh_failed",
                ip_address=client_ip,
                details={"reason": "invalid_token"}
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token"
            )
        
        user_id = int(payload.get("sub"))
        
        # Validate session in database
        session = await user_repo.validate_refresh_token(token_data.refresh_token)
        if not session or session.user_id != user_id:
            await audit_repo.log_action(
                entity_type="session",
                entity_id=0,
                action="token_refresh_failed",
                user_id=user_id,
                ip_address=client_ip,
                details={"reason": "session_not_found"}
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token session"
            )
        
        # Get user
        user = await user_repo.get_by_id(user_id)
        if not user or not user.is_active:
            await audit_repo.log_action(
                entity_type="session",
                entity_id=session.id,
                action="token_refresh_failed",
                user_id=user_id,
                ip_address=client_ip,
                details={"reason": "user_inactive"}
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is disabled"
            )
        
        # Create new access token
        access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
        access_token = create_access_token(
            data={"sub": str(user.id), "email": user.email, "role": user.role},
            expires_delta=access_token_expires
        )
        
        # Log token refresh
        await audit_repo.log_action(
            entity_type="session",
            entity_id=session.id,
            action="token_refreshed",
            user_id=user.id,
            user_role=user.role,
            ip_address=client_ip
        )
        
        logger.debug(f"Token refreshed for user: {user.email}")
        
        return Token(
            access_token=access_token,
            refresh_token=token_data.refresh_token,  # Keep same refresh token
            token_type="bearer",
            expires_in=settings.access_token_expire_minutes * 60,
            user=UserResponse.from_orm(user)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        await audit_repo.log_action(
            entity_type="session",
            entity_id=0,
            action="token_refresh_error",
            ip_address=client_ip,
            details={"error": str(e)}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during token refresh"
        )

@router.post("/logout", response_model=SuccessResponse)
async def logout(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    user_repo: UserRepository = Depends(get_user_repository),
    audit_repo: AuditRepository = Depends(get_audit_repository)
):
    """
    Logout user and invalidate all sessions.
    
    Requires valid JWT token in Authorization header.
    """
    client_ip = get_client_ip(request)
    
    try:
        
        # Delete all user sessions
        deleted_count = await user_repo.delete_all_user_sessions(current_user.id)
        
        # Log logout
        await audit_repo.log_action(
            entity_type="user",
            entity_id=current_user.id,
            action="logout",
            user_id=current_user.id,
            user_role=current_user.role,
            ip_address=client_ip,
            details={"sessions_cleared": deleted_count}
        )
        
        logger.info(f"User logged out: {current_user.email}, sessions cleared: {deleted_count}")
        
        return SuccessResponse(
            message="Successfully logged out",
            data={"sessions_cleared": deleted_count}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Logout error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during logout"
        )

@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user)
):
    """
    Get current user profile information.
    
    Requires valid JWT token in Authorization header.
    """
    return UserResponse.from_orm(current_user)

@router.post("/cleanup-sessions", response_model=SessionCleanupResponse)
async def cleanup_expired_sessions(
    db: AsyncSession = Depends(get_db),
    user_repo: UserRepository = Depends(get_user_repository),
    audit_repo: AuditRepository = Depends(get_audit_repository)
):
    """
    Clean up expired sessions (maintenance endpoint).
    
    This endpoint is typically called by a scheduled job.
    """
    try:
        cleaned_count = await user_repo.cleanup_expired_sessions()
        
        # Log cleanup
        await audit_repo.log_action(
            entity_type="session",
            entity_id=0,
            action="sessions_cleanup",
            details={"cleaned_count": cleaned_count}
        )
        
        logger.info(f"Cleaned up {cleaned_count} expired sessions")
        
        return SessionCleanupResponse(
            message=f"Successfully cleaned up {cleaned_count} expired sessions",
            cleaned_sessions=cleaned_count
        )
        
    except Exception as e:
        logger.error(f"Session cleanup error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during session cleanup"
        )

# Token verification endpoint for other services
@router.post("/verify-token", response_model=UserResponse)
async def verify_user_token(
    token_data: Dict[str, str],
    db: AsyncSession = Depends(get_db),
    user_repo: UserRepository = Depends(get_user_repository)
):
    """
    Verify JWT token and return user data.
    
    This endpoint is used by other services to validate tokens.
    """
    try:
        token = token_data.get("token")
        if not token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Token is required"
            )
        
        payload = verify_token(token, token_type="access")
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token"
            )
        
        user_id = int(payload.get("sub"))
        user = await user_repo.get_by_id(user_id)
        
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )
        
        return UserResponse.from_orm(user)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token verification error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during token verification"
        )