from sqlalchemy import Column, Integer, String, JSON, DateTime
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    entity_type = Column(String, nullable=False)
    entity_id = Column(Integer, nullable=False)
    action = Column(String, nullable=False)
    user_id = Column(Integer, nullable=False)
    user_role = Column(String, nullable=False)
    ip_address = Column(String, nullable=False)
    details = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now()) 