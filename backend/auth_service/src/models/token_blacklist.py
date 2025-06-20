"""Token blacklist model for invalidated JWT tokens."""

from sqlalchemy import Column, Integer, String, DateTime, Index
from sqlalchemy.sql import func
from datetime import datetime, timezone

from .base import Base

class TokenBlacklist(Base):
    """Model for blacklisted JWT tokens."""
    
    __tablename__ = "token_blacklist"
    
    id = Column(Integer, primary_key=True, index=True)
    token_hash = Column(String(64), unique=True, nullable=False, index=True)  # SHA256 hash of token
    user_id = Column(Integer, nullable=False, index=True)
    blacklisted_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)  # Original token expiration
    reason = Column(String(255), nullable=True)  # Reason for blacklisting (logout, security, etc.)
    
    # Index for efficient cleanup of expired blacklisted tokens
    __table_args__ = (
        Index('idx_token_blacklist_expires_at', 'expires_at'),
        Index('idx_token_blacklist_user_id_blacklisted_at', 'user_id', 'blacklisted_at'),
    )
    
    def __repr__(self):
        return f"<TokenBlacklist(id={self.id}, user_id={self.user_id}, blacklisted_at={self.blacklisted_at})>"