from .user import User, Base as UserBase
from .user_session import UserSession, Base as UserSessionBase
from .audit_log import AuditLog, Base as AuditLogBase

# Unified base for all models
from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()

# Import all models to ensure they're registered
__all__ = ["User", "UserSession", "AuditLog", "Base"]