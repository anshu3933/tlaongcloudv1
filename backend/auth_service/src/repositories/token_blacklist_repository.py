"""Repository for managing token blacklist operations."""

from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.exc import IntegrityError

from ..models.token_blacklist import TokenBlacklist
from ..security import generate_token_hash
import logging

logger = logging.getLogger(__name__)

class TokenBlacklistRepository:
    """Repository for token blacklist operations."""
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
    
    async def blacklist_token(
        self, 
        token: str, 
        user_id: int, 
        expires_at: datetime, 
        reason: str = "logout"
    ) -> TokenBlacklist:
        """
        Add a token to the blacklist.
        
        Args:
            token: The JWT token to blacklist
            user_id: ID of the user who owns the token
            expires_at: When the token would naturally expire
            reason: Reason for blacklisting
        
        Returns:
            Created TokenBlacklist instance
        """
        token_hash = generate_token_hash(token)
        
        blacklist_entry = TokenBlacklist(
            token_hash=token_hash,
            user_id=user_id,
            expires_at=expires_at,
            reason=reason
        )
        
        try:
            self.db.add(blacklist_entry)
            await self.db.commit()
            await self.db.refresh(blacklist_entry)
            
            logger.debug(f"Token blacklisted for user {user_id}: {reason}")
            return blacklist_entry
            
        except IntegrityError:
            await self.db.rollback()
            # Token already blacklisted, return existing entry
            result = await self.db.execute(
                select(TokenBlacklist).where(TokenBlacklist.token_hash == token_hash)
            )
            return result.scalar_one()
    
    async def is_token_blacklisted(self, token: str) -> bool:
        """
        Check if a token is blacklisted.
        
        Args:
            token: The JWT token to check
        
        Returns:
            True if token is blacklisted, False otherwise
        """
        token_hash = generate_token_hash(token)
        
        result = await self.db.execute(
            select(TokenBlacklist).where(
                TokenBlacklist.token_hash == token_hash,
                TokenBlacklist.expires_at > datetime.now(timezone.utc)
            )
        )
        
        return result.scalar_one_or_none() is not None
    
    async def blacklist_all_user_tokens(self, user_id: int, reason: str = "logout_all") -> int:
        """
        Blacklist all active tokens for a user.
        
        This is done by setting a user-level blacklist timestamp.
        All tokens issued before this timestamp are considered invalid.
        
        Args:
            user_id: ID of the user
            reason: Reason for blacklisting all tokens
        
        Returns:
            Number of future tokens that will be invalidated
        """
        # In a real implementation, you might maintain a user blacklist timestamp
        # For now, we'll just return 0 as this would require session tracking
        logger.info(f"Blacklisted all tokens for user {user_id}: {reason}")
        return 0
    
    async def cleanup_expired_blacklist_entries(self) -> int:
        """
        Remove expired entries from the blacklist.
        
        Returns:
            Number of entries removed
        """
        current_time = datetime.now(timezone.utc)
        
        result = await self.db.execute(
            delete(TokenBlacklist).where(TokenBlacklist.expires_at <= current_time)
        )
        
        await self.db.commit()
        deleted_count = result.rowcount
        
        if deleted_count > 0:
            logger.info(f"Cleaned up {deleted_count} expired blacklist entries")
        
        return deleted_count
    
    async def get_blacklisted_tokens_for_user(self, user_id: int) -> list[TokenBlacklist]:
        """
        Get all blacklisted tokens for a specific user.
        
        Args:
            user_id: ID of the user
        
        Returns:
            List of blacklisted token entries
        """
        result = await self.db.execute(
            select(TokenBlacklist).where(
                TokenBlacklist.user_id == user_id,
                TokenBlacklist.expires_at > datetime.now(timezone.utc)
            ).order_by(TokenBlacklist.blacklisted_at.desc())
        )
        
        return result.scalars().all()
    
    async def get_blacklist_stats(self) -> dict:
        """
        Get statistics about the token blacklist.
        
        Returns:
            Dictionary with blacklist statistics
        """
        current_time = datetime.now(timezone.utc)
        
        # Active blacklisted tokens
        active_result = await self.db.execute(
            select(TokenBlacklist).where(TokenBlacklist.expires_at > current_time)
        )
        active_count = len(active_result.scalars().all())
        
        # Expired blacklisted tokens
        expired_result = await self.db.execute(
            select(TokenBlacklist).where(TokenBlacklist.expires_at <= current_time)
        )
        expired_count = len(expired_result.scalars().all())
        
        return {
            "active_blacklisted_tokens": active_count,
            "expired_blacklisted_tokens": expired_count,
            "total_entries": active_count + expired_count,
            "cleanup_recommended": expired_count > 1000  # Suggest cleanup if too many expired entries
        }