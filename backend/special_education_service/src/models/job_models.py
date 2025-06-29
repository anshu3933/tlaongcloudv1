"""Job tracking models for async IEP generation"""

from sqlalchemy import Column, String, Text, DateTime, Integer, Index, Boolean
from sqlalchemy.sql import func
from .special_education_models import Base


class IEPGenerationJob(Base):
    """Combined job tracking and queue functionality"""
    __tablename__ = 'iep_generation_jobs'
    
    # Identity
    id = Column(String(36), primary_key=True)  # UUID as string for SQLite
    student_id = Column(String(36), nullable=False, index=True)
    academic_year = Column(String(10), nullable=False)
    template_id = Column(String(36), nullable=True)
    
    # Status and queue fields
    status = Column(String(20), default="PENDING", nullable=False, index=True)
    queue_status = Column(String(20), default="PENDING", nullable=False, index=True)
    priority = Column(Integer, default=0, nullable=False)
    claimed_at = Column(DateTime, nullable=True)  # For worker claim tracking
    claim_worker_id = Column(String(50), nullable=True)  # Track which worker claimed
    
    # Data
    input_data = Column(Text, nullable=False)  # JSON as text
    result_id = Column(String(36), nullable=True)
    
    # Gemini-specific fields
    gemini_request_id = Column(String(100), nullable=True)
    gemini_response_raw = Column(Text, nullable=True)  # Consider compression for large responses
    gemini_response_compressed = Column(Boolean, default=False)
    gemini_tokens_used = Column(Integer, nullable=True)
    
    # Error handling
    retry_count = Column(Integer, default=0, nullable=False)
    next_retry_at = Column(DateTime, nullable=True, index=True)
    error_message = Column(Text, nullable=True)
    error_details = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    failed_at = Column(DateTime, nullable=True)
    
    # Audit
    created_by = Column(String(36), nullable=False)
    
    __table_args__ = (
        # Composite index for job identity lookups
        Index('idx_job_identity', 'student_id', 'academic_year', 'template_id'),
        # Index for queue processing - optimized for SQLite
        Index('idx_queue_claim', 'queue_status', 'next_retry_at', 'claimed_at'),
        # Separate index for priority since SQLite may not use composite efficiently
        Index('idx_queue_priority', 'priority', 'created_at'),
        # Index for status queries
        Index('idx_job_status', 'status', 'created_at'),
    )