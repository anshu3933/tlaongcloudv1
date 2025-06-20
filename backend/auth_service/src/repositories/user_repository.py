from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func
from sqlalchemy.orm import selectinload
import logging

from ..models.user import User
from ..models.user_session import UserSession
from ..security import generate_token_hash

logger = logging.getLogger(__name__)

class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, user_id: int, include_sessions: bool = False) -> Optional[User]:
        """Get user by ID with optional session loading."""
        query = select(User).where(User.id == user_id)
        
        if include_sessions:
            query = query.options(selectinload(User.sessions))
        
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str, include_sessions: bool = False) -> Optional[User]:
        """Get user by email with optional session loading."""
        query = select(User).where(User.email == email)
        
        if include_sessions:
            query = query.options(selectinload(User.sessions))
        
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def create(self, user: User) -> User:
        """Create a new user."""
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        logger.info(f"Created user: {user.email}")
        return user

    async def update(self, user: User) -> User:
        """Update an existing user."""
        await self.session.commit()
        await self.session.refresh(user)
        logger.info(f"Updated user: {user.email}")
        return user

    async def delete(self, user_id: int) -> bool:
        """Delete a user by ID."""
        user = await self.get_by_id(user_id)
        if user:
            await self.session.delete(user)
            await self.session.commit()
            logger.info(f"Deleted user: {user.email}")
            return True
        return False

    async def list_all(self, active_only: bool = True) -> List[User]:
        """List all users, optionally filtering by active status."""
        query = select(User)
        if active_only:
            query = query.where(User.is_active == True)
        
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_users_by_role(self, role: str, active_only: bool = True) -> List[Dict[str, Any]]:
        """Get users by role."""
        query = select(User).where(User.role == role)
        if active_only:
            query = query.where(User.is_active == True)
        
        result = await self.session.execute(query)
        users = result.scalars().all()
        
        return [
            {
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role,
                "is_active": user.is_active,
                "last_login": user.last_login,
                "created_at": user.created_at
            }
            for user in users
        ]

    async def update_last_login(self, user_id: int) -> bool:
        """Update user's last login timestamp."""
        result = await self.session.execute(
            update(User)
            .where(User.id == user_id)
            .values(last_login=datetime.utcnow())
        )
        await self.session.commit()
        return result.rowcount > 0

    # Session Management Methods
    
    async def create_session(
        self, 
        user_id: int, 
        refresh_token: str, 
        expires_at: datetime
    ) -> UserSession:
        """Create a new user session."""
        # Clean up old sessions if user has too many
        await self._cleanup_old_sessions(user_id)
        
        token_hash = generate_token_hash(refresh_token)
        session = UserSession(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at
        )
        
        self.session.add(session)
        await self.session.commit()
        await self.session.refresh(session)
        
        logger.debug(f"Created session for user {user_id}")
        return session

    async def get_session_by_token_hash(self, token_hash: str) -> Optional[UserSession]:
        """Get session by token hash."""
        result = await self.session.execute(
            select(UserSession)
            .where(UserSession.token_hash == token_hash)
            .where(UserSession.expires_at > datetime.utcnow())
        )
        return result.scalar_one_or_none()

    async def validate_refresh_token(self, refresh_token: str) -> Optional[UserSession]:
        """Validate refresh token and return session if valid."""
        token_hash = generate_token_hash(refresh_token)
        return await self.get_session_by_token_hash(token_hash)

    async def delete_session(self, session_id: int) -> bool:
        """Delete a specific session."""
        result = await self.session.execute(
            delete(UserSession).where(UserSession.id == session_id)
        )
        await self.session.commit()
        return result.rowcount > 0

    async def delete_all_user_sessions(self, user_id: int) -> int:
        """Delete all sessions for a user."""
        result = await self.session.execute(
            delete(UserSession).where(UserSession.user_id == user_id)
        )
        await self.session.commit()
        count = result.rowcount
        logger.info(f"Deleted {count} sessions for user {user_id}")
        return count

    async def cleanup_expired_sessions(self) -> int:
        """Clean up all expired sessions."""
        result = await self.session.execute(
            delete(UserSession).where(UserSession.expires_at <= datetime.utcnow())
        )
        await self.session.commit()
        count = result.rowcount
        logger.info(f"Cleaned up {count} expired sessions")
        return count

    async def get_user_session_count(self, user_id: int) -> int:
        """Get count of active sessions for a user."""
        result = await self.session.execute(
            select(func.count(UserSession.id))
            .where(UserSession.user_id == user_id)
            .where(UserSession.expires_at > datetime.utcnow())
        )
        return result.scalar() or 0

    async def _cleanup_old_sessions(self, user_id: int, max_sessions: int = 5):
        """Clean up old sessions if user has too many."""
        # Get current session count
        session_count = await self.get_user_session_count(user_id)
        
        if session_count >= max_sessions:
            # Delete oldest sessions
            old_sessions = await self.session.execute(
                select(UserSession.id)
                .where(UserSession.user_id == user_id)
                .where(UserSession.expires_at > datetime.utcnow())
                .order_by(UserSession.created_at)
                .limit(session_count - max_sessions + 1)
            )
            
            session_ids = old_sessions.scalars().all()
            if session_ids:
                await self.session.execute(
                    delete(UserSession).where(UserSession.id.in_(session_ids))
                )
                logger.debug(f"Cleaned up {len(session_ids)} old sessions for user {user_id}")

    # User management helper methods
    
    async def activate_user(self, user_id: int) -> bool:
        """Activate a user account."""
        result = await self.session.execute(
            update(User)
            .where(User.id == user_id)
            .values(is_active=True, updated_at=datetime.utcnow())
        )
        await self.session.commit()
        return result.rowcount > 0

    async def deactivate_user(self, user_id: int) -> bool:
        """Deactivate a user account and clear all sessions."""
        # First deactivate the user
        result = await self.session.execute(
            update(User)
            .where(User.id == user_id)
            .values(is_active=False, updated_at=datetime.utcnow())
        )
        
        # Then clear all sessions
        await self.delete_all_user_sessions(user_id)
        await self.session.commit()
        
        return result.rowcount > 0

    async def change_user_password(self, user_id: int, new_hashed_password: str) -> bool:
        """Change user password and invalidate all sessions."""
        # Update password
        result = await self.session.execute(
            update(User)
            .where(User.id == user_id)
            .values(hashed_password=new_hashed_password, updated_at=datetime.utcnow())
        )
        
        # Invalidate all sessions
        await self.delete_all_user_sessions(user_id)
        await self.session.commit()
        
        return result.rowcount > 0
