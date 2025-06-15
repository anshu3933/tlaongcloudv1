"""Shared models for cross-service consistency"""
from sqlalchemy import Column, String, Boolean, DateTime, Integer, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base
import uuid

Base = declarative_base()

class User(Base):
    """Shared user model with UUID primary key for cross-service consistency"""
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    legacy_id = Column(Integer, unique=True, nullable=True, index=True)  # For migration from auth service
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    roles = Column(JSON, default=list)  # Support multiple roles: ["teacher", "admin", "case_manager"]
    permissions = Column(JSON, default=dict)  # Role-specific permissions
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    last_login = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, roles={self.roles})>"
    
    def has_role(self, role: str) -> bool:
        """Check if user has specific role"""
        return role in (self.roles or [])
    
    def can_perform(self, permission: str) -> bool:
        """Check if user has specific permission"""
        return permission in (self.permissions or {})