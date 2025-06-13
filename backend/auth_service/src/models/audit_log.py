from sqlalchemy import Column, Integer, String, JSON, DateTime, Index
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    entity_type = Column(String, nullable=False, index=True)
    entity_id = Column(Integer, nullable=False, index=True)
    action = Column(String, nullable=False, index=True)
    user_id = Column(Integer, nullable=True, index=True)
    user_role = Column(String, nullable=True)
    ip_address = Column(String, nullable=True)
    details = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Composite indexes for common queries
    __table_args__ = (
        Index('ix_audit_logs_entity_type_id', 'entity_type', 'entity_id'),
        Index('ix_audit_logs_user_created', 'user_id', 'created_at'),
    ) 