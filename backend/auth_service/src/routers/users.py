"""User management routes for CRUD operations and administration."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..dependencies import (
    get_audit_repository, get_user_repository, get_client_ip,
    require_superuser, require_self_or_admin
)
from ..repositories.user_repository import UserRepository
from ..repositories.audit_repository import AuditRepository
from ..models.user import User
from ..security import hash_password, PasswordValidator
from ..schemas import (
    UserResponse, UserUpdate, PasswordChange, UserSummary,
    PaginatedUserResponse, PaginationMeta, UserDeactivationResponse, UserActivationResponse,
    PasswordChangeResponse, AuditLogResponse
)
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/users", tags=["user management"])

@router.get("/", response_model=PaginatedUserResponse)
async def list_users(
    request: Request,
    role: Optional[str] = Query(None, description="Filter by user role"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    search: Optional[str] = Query(None, description="Search in email and name"),
    limit: int = Query(50, ge=1, le=100, description="Number of users per page"),
    offset: int = Query(0, ge=0, description="Number of users to skip"),
    current_user: User = Depends(require_superuser()),
    db: AsyncSession = Depends(get_db),
    user_repo: UserRepository = Depends(get_user_repository),
    audit_repo: AuditRepository = Depends(get_audit_repository)
):
    """
    List all users (superuser only).
    
    Supports filtering by role, active status, and text search.
    Returns paginated results.
    """
    client_ip = get_client_ip(request)
    
    try:
        # Get users with filters
        users = await user_repo.list_all(active_only=False)
        
        # Apply filters
        if role:
            users = [u for u in users if u.role == role]
        
        if is_active is not None:
            users = [u for u in users if u.is_active == is_active]
        
        if search:
            search_lower = search.lower()
            users = [
                u for u in users 
                if (search_lower in u.email.lower() or 
                    (u.full_name and search_lower in u.full_name.lower()))
            ]
        
        # Calculate pagination
        total = len(users)
        paginated_users = users[offset:offset + limit]
        total_pages = (total + limit - 1) // limit
        
        # Convert to response models
        user_responses = [UserResponse.from_orm(user) for user in paginated_users]
        
        # Log access
        await audit_repo.log_action(
            entity_type="user",
            entity_id=0,
            action="users_listed",
            user_id=current_user.id,
            user_role=current_user.role,
            ip_address=client_ip,
            details={
                "filters": {"role": role, "is_active": is_active, "search": search},
                "pagination": {"limit": limit, "offset": offset, "total": total}
            }
        )
        
        return PaginatedUserResponse(
            data=user_responses,
            meta=PaginationMeta(
                total=total,
                page=(offset // limit) + 1,
                per_page=limit,
                total_pages=total_pages,
                has_next=offset + limit < total,
                has_prev=offset > 0
            )
        )
        
    except Exception as e:
        logger.error(f"List users error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    request: Request,
    current_user: User = Depends(require_self_or_admin()),
    db: AsyncSession = Depends(get_db),
    user_repo: UserRepository = Depends(get_user_repository),
    audit_repo: AuditRepository = Depends(get_audit_repository)
):
    """
    Get user by ID.
    
    Users can view their own profile, superusers can view any user.
    """
    client_ip = get_client_ip(request)
    
    try:
        user = await user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Log access
        await audit_repo.log_action(
            entity_type="user",
            entity_id=user.id,
            action="user_viewed",
            user_id=current_user.id,
            user_role=current_user.role,
            ip_address=client_ip,
            details={"viewed_user": user.email}
        )
        
        return UserResponse.from_orm(user)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get user error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    request: Request,
    current_user: User = Depends(require_self_or_admin()),
    db: AsyncSession = Depends(get_db),
    user_repo: UserRepository = Depends(get_user_repository),
    audit_repo: AuditRepository = Depends(get_audit_repository)
):
    """
    Update user information.
    
    Users can update their own profile, superusers can update any user.
    """
    client_ip = get_client_ip(request)
    
    try:
        user = await user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Track changes for audit
        changes = {}
        
        # Update fields
        if user_update.email is not None and user_update.email != user.email:
            # Check if email is already taken
            existing_user = await user_repo.get_by_email(user_update.email)
            if existing_user and existing_user.id != user.id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already in use"
                )
            changes["email"] = {"old": user.email, "new": user_update.email}
            user.email = user_update.email
        
        if user_update.full_name is not None and user_update.full_name != user.full_name:
            changes["full_name"] = {"old": user.full_name, "new": user_update.full_name}
            user.full_name = user_update.full_name
        
        if user_update.role is not None and user_update.role != user.role:
            # Only superusers can change roles
            if not current_user.is_superuser:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Only superusers can change user roles"
                )
            changes["role"] = {"old": user.role, "new": user_update.role}
            user.role = user_update.role
        
        if user_update.is_active is not None and user_update.is_active != user.is_active:
            # Only superusers can change active status
            if not current_user.is_superuser:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Only superusers can change user active status"
                )
            changes["is_active"] = {"old": user.is_active, "new": user_update.is_active}
            user.is_active = user_update.is_active
        
        if changes:
            updated_user = await user_repo.update(user)
            
            # Log update
            await audit_repo.log_action(
                entity_type="user",
                entity_id=user.id,
                action="user_updated",
                user_id=current_user.id,
                user_role=current_user.role,
                ip_address=client_ip,
                details={"changes": changes, "updated_user": user.email}
            )
            
            logger.info(f"User updated: {user.email} by {current_user.email}")
            return UserResponse.from_orm(updated_user)
        else:
            # No changes made
            return UserResponse.from_orm(user)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update user error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.post("/{user_id}/change-password", response_model=PasswordChangeResponse)
async def change_password(
    user_id: int,
    password_data: PasswordChange,
    request: Request,
    current_user: User = Depends(require_self_or_admin()),
    db: AsyncSession = Depends(get_db),
    user_repo: UserRepository = Depends(get_user_repository),
    audit_repo: AuditRepository = Depends(get_audit_repository)
):
    """
    Change user password.
    
    Users can change their own password, superusers can change any password.
    """
    client_ip = get_client_ip(request)
    
    try:
        user = await user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # For self-password change, verify current password
        if current_user.id == user.id:
            from ..security import verify_password
            if not verify_password(password_data.current_password, user.hashed_password):
                await audit_repo.log_action(
                    entity_type="user",
                    entity_id=user.id,
                    action="password_change_failed",
                    user_id=current_user.id,
                    user_role=current_user.role,
                    ip_address=client_ip,
                    details={"reason": "invalid_current_password"}
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Current password is incorrect"
                )
        
        # Validate new password
        is_valid, errors = PasswordValidator.validate_password(password_data.new_password)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Password validation failed: {'; '.join(errors)}"
            )
        
        # Hash new password and update
        new_hashed_password = hash_password(password_data.new_password)
        success = await user_repo.change_user_password(user.id, new_hashed_password)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update password"
            )
        
        # Log password change
        await audit_repo.log_action(
            entity_type="user",
            entity_id=user.id,
            action="password_changed",
            user_id=current_user.id,
            user_role=current_user.role,
            ip_address=client_ip,
            details={"target_user": user.email, "changed_by_self": current_user.id == user.id}
        )
        
        logger.info(f"Password changed for user: {user.email} by {current_user.email}")
        
        return PasswordChangeResponse(
            message="Password changed successfully. All sessions have been invalidated.",
            sessions_invalidated=await user_repo.get_user_session_count(user.id)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Change password error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.post("/{user_id}/deactivate", response_model=UserDeactivationResponse)
async def deactivate_user(
    user_id: int,
    request: Request,
    current_user: User = Depends(require_superuser()),
    db: AsyncSession = Depends(get_db),
    user_repo: UserRepository = Depends(get_user_repository),
    audit_repo: AuditRepository = Depends(get_audit_repository)
):
    """
    Deactivate user account (superuser only).
    
    Deactivates the account and clears all active sessions.
    """
    client_ip = get_client_ip(request)
    
    try:
        user = await user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is already deactivated"
            )
        
        # Prevent self-deactivation
        if current_user.id == user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot deactivate your own account"
            )
        
        # Get session count before deactivation
        session_count = await user_repo.get_user_session_count(user.id)
        
        # Deactivate user and clear sessions
        success = await user_repo.deactivate_user(user.id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to deactivate user"
            )
        
        # Log deactivation
        await audit_repo.log_action(
            entity_type="user",
            entity_id=user.id,
            action="user_deactivated",
            user_id=current_user.id,
            user_role=current_user.role,
            ip_address=client_ip,
            details={"deactivated_user": user.email, "sessions_cleared": session_count}
        )
        
        logger.info(f"User deactivated: {user.email} by {current_user.email}")
        
        return UserDeactivationResponse(
            message=f"User {user.email} has been deactivated",
            user_id=user.id,
            sessions_cleared=session_count
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Deactivate user error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.post("/{user_id}/activate", response_model=UserActivationResponse)
async def activate_user(
    user_id: int,
    request: Request,
    current_user: User = Depends(require_superuser()),
    db: AsyncSession = Depends(get_db),
    user_repo: UserRepository = Depends(get_user_repository),
    audit_repo: AuditRepository = Depends(get_audit_repository)
):
    """
    Activate user account (superuser only).
    """
    client_ip = get_client_ip(request)
    
    try:
        user = await user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        if user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is already active"
            )
        
        # Activate user
        success = await user_repo.activate_user(user.id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to activate user"
            )
        
        # Log activation
        await audit_repo.log_action(
            entity_type="user",
            entity_id=user.id,
            action="user_activated",
            user_id=current_user.id,
            user_role=current_user.role,
            ip_address=client_ip,
            details={"activated_user": user.email}
        )
        
        logger.info(f"User activated: {user.email} by {current_user.email}")
        
        return UserActivationResponse(
            message=f"User {user.email} has been activated",
            user_id=user.id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Activate user error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get("/role/{role}", response_model=List[UserSummary])
async def get_users_by_role(
    role: str,
    request: Request,
    current_user: User = Depends(require_superuser()),
    db: AsyncSession = Depends(get_db),
    user_repo: UserRepository = Depends(get_user_repository),
    audit_repo: AuditRepository = Depends(get_audit_repository)
):
    """
    Get users by role (superuser only).
    """
    client_ip = get_client_ip(request)
    
    try:
        users_data = await user_repo.get_users_by_role(role)
        
        # Log access
        await audit_repo.log_action(
            entity_type="user",
            entity_id=0,
            action="users_by_role_viewed",
            user_id=current_user.id,
            user_role=current_user.role,
            ip_address=client_ip,
            details={"role": role, "count": len(users_data)}
        )
        
        return [UserSummary(**user_data) for user_data in users_data]
        
    except Exception as e:
        logger.error(f"Get users by role error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get("/{user_id}/audit-logs", response_model=List[AuditLogResponse])
async def get_user_audit_logs(
    user_id: int,
    request: Request,
    limit: int = Query(100, ge=1, le=1000, description="Number of logs to return"),
    offset: int = Query(0, ge=0, description="Number of logs to skip"),
    current_user: User = Depends(require_self_or_admin()),
    db: AsyncSession = Depends(get_db),
    user_repo: UserRepository = Depends(get_user_repository),
    audit_repo: AuditRepository = Depends(get_audit_repository)
):
    """
    Get audit logs for a user.
    
    Users can view their own logs, superusers can view any user's logs.
    """
    client_ip = get_client_ip(request)
    
    try:
        # Verify user exists
        user = await user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Get audit logs
        logs = await audit_repo.get_logs_by_user(user_id, limit=limit, offset=offset)
        
        # Log access to audit logs
        await audit_repo.log_action(
            entity_type="audit_log",
            entity_id=user_id,
            action="audit_logs_viewed",
            user_id=current_user.id,
            user_role=current_user.role,
            ip_address=client_ip,
            details={"target_user": user.email, "logs_count": len(logs)}
        )
        
        return [AuditLogResponse.from_orm(log) for log in logs]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get user audit logs error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )