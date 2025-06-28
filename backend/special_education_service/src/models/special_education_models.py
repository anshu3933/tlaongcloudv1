"""Database models for Special Education Service"""
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Date, JSON, ForeignKey, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import uuid
from enum import Enum

Base = declarative_base()

class IEPStatus(str, Enum):
    DRAFT = "draft"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    ACTIVE = "active"
    EXPIRED = "expired"
    RETURNED = "returned"

class GoalStatus(str, Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    MASTERED = "mastered"
    DISCONTINUED = "discontinued"

class Student(Base):
    """Core student entity for special education"""
    __tablename__ = "students"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(String(50), unique=True, nullable=False, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    middle_name = Column(String(100), nullable=True)
    date_of_birth = Column(Date, nullable=False)
    grade_level = Column(String(20), nullable=False)
    disability_codes = Column(JSON, nullable=False, default=list)  # List of disability type codes
    
    # User relationships (stored as auth service IDs)
    case_manager_auth_id = Column(Integer, nullable=True)
    primary_teacher_auth_id = Column(Integer, nullable=True)
    parent_guardian_auth_ids = Column(JSON, default=list)
    
    # Educational data
    school_district = Column(String(200), nullable=True)
    school_name = Column(String(200), nullable=True)
    enrollment_date = Column(Date, nullable=True)
    
    # Current IEP reference
    active_iep_id = Column(UUID(as_uuid=True), ForeignKey("ieps.id"), nullable=True)
    
    # Metadata
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    ieps = relationship("IEP", back_populates="student", foreign_keys="IEP.student_id")
    active_iep = relationship("IEP", foreign_keys=[active_iep_id])
    present_levels = relationship("PresentLevel", back_populates="student")
    
    def __repr__(self):
        return f"<Student(id={self.id}, name={self.first_name} {self.last_name}, student_id={self.student_id})>"

class DisabilityType(Base):
    __tablename__ = "disability_types"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    description = Column(String, nullable=True)
    accommodation_defaults = Column(JSON, nullable=True)
    federal_category = Column(String(100), nullable=True)  # IDEA categories
    state_category = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    iep_templates = relationship("IEPTemplate", back_populates="disability_type")
    pl_templates = relationship("PLAssessmentTemplate", back_populates="disability_type")

class IEPTemplate(Base):
    __tablename__ = "iep_templates"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False)
    disability_type_id = Column(UUID(as_uuid=True), ForeignKey("disability_types.id"))
    grade_level = Column(String(20))
    sections = Column(JSON, nullable=False)  # Template structure
    default_goals = Column(JSON, default=list)  # Pre-defined goal templates
    version = Column(Integer, default=1)
    is_active = Column(Boolean, default=True)
    created_by_auth_id = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    disability_type = relationship("DisabilityType", back_populates="iep_templates")
    ieps = relationship("IEP", back_populates="template")

class IEP(Base):
    __tablename__ = "ieps"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id"), nullable=False, index=True)
    template_id = Column(UUID(as_uuid=True), ForeignKey("iep_templates.id"), nullable=True)
    academic_year = Column(String(9), nullable=False)  # Format: "2023-2024"
    status = Column(String(50), default=IEPStatus.DRAFT.value)
    
    # IEP Content
    content = Column(JSON, nullable=False, default=dict)
    meeting_date = Column(Date, nullable=True)
    effective_date = Column(Date, nullable=True)
    review_date = Column(Date, nullable=True)
    
    # Versioning
    version = Column(Integer, default=1)
    parent_version_id = Column(UUID(as_uuid=True), ForeignKey("ieps.id"), nullable=True)
    
    # Audit fields
    created_by_auth_id = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    approved_at = Column(DateTime(timezone=True), nullable=True)
    approved_by_auth_id = Column(Integer, nullable=True)
    
    # Relationships
    student = relationship("Student", back_populates="ieps", foreign_keys=[student_id])
    template = relationship("IEPTemplate", back_populates="ieps")
    goals = relationship("IEPGoal", back_populates="iep", cascade="all, delete-orphan")
    present_levels = relationship("PresentLevel", back_populates="iep")
    parent_version = relationship("IEP", remote_side=[id])
    
    # Constraints and Indexes
    __table_args__ = (
        Index('ix_iep_student_year', 'student_id', 'academic_year'),
        Index('ix_iep_status', 'status'),
        UniqueConstraint('student_id', 'academic_year', 'version', name='uq_student_year_version'),
    )
    
    def __repr__(self):
        return f"<IEP(id={self.id}, student_id={self.student_id}, year={self.academic_year}, status={self.status})>"

class IEPGoal(Base):
    __tablename__ = "iep_goals"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    iep_id = Column(UUID(as_uuid=True), ForeignKey("ieps.id", ondelete="CASCADE"), nullable=False)
    
    # Goal definition
    domain = Column(String(100), nullable=False)  # Academic, Behavioral, Social, Communication, etc.
    goal_text = Column(String, nullable=False)
    baseline = Column(String, nullable=True)
    target_criteria = Column(String, nullable=False)
    measurement_method = Column(String, nullable=False)
    measurement_frequency = Column(String, nullable=True)  # Weekly, Monthly, etc.
    
    # Timeline
    target_date = Column(Date, nullable=True)
    start_date = Column(Date, nullable=True)
    
    # Progress tracking
    progress_status = Column(String(50), default=GoalStatus.NOT_STARTED.value)
    progress_notes = Column(JSON, default=list)  # List of progress entries
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    iep = relationship("IEP", back_populates="goals")

class PLAssessmentTemplate(Base):
    __tablename__ = "pl_assessment_templates"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False)
    disability_type_id = Column(UUID(as_uuid=True), ForeignKey("disability_types.id"))
    skill_domains = Column(JSON, nullable=False)  # Assessment domains and criteria
    assessment_type = Column(String(50), nullable=False)  # Formal, Informal, Observational
    version = Column(Integer, default=1)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    disability_type = relationship("DisabilityType", back_populates="pl_templates")
    present_levels = relationship("PresentLevel", back_populates="template")

class PresentLevel(Base):
    __tablename__ = "present_levels"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id"), nullable=False, index=True)
    iep_id = Column(UUID(as_uuid=True), ForeignKey("ieps.id"), nullable=True)
    template_id = Column(UUID(as_uuid=True), ForeignKey("pl_assessment_templates.id"))
    
    # Assessment details
    assessment_date = Column(Date, nullable=False)
    assessment_type = Column(String(50), nullable=False)
    assessor_auth_id = Column(Integer, nullable=False)
    
    # Assessment content
    content = Column(JSON, nullable=False, default=dict)  # Assessment results and observations
    strengths = Column(JSON, default=list)
    needs = Column(JSON, default=list)
    recommendations = Column(JSON, default=list)
    
    # Versioning
    version = Column(Integer, default=1)
    parent_version_id = Column(UUID(as_uuid=True), ForeignKey("present_levels.id"), nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    student = relationship("Student", back_populates="present_levels")
    iep = relationship("IEP", back_populates="present_levels")
    template = relationship("PLAssessmentTemplate", back_populates="present_levels")
    parent_version = relationship("PresentLevel", remote_side=[id])
    
    # Indexes
    __table_args__ = (
        Index('ix_pl_student_date', 'student_id', 'assessment_date'),
        Index('ix_pl_assessor', 'assessor_auth_id'),
    )

class WizardSession(Base):
    """Tracks multi-step IEP creation wizard sessions"""
    __tablename__ = "wizard_sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id"), nullable=False)
    template_id = Column(UUID(as_uuid=True), ForeignKey("iep_templates.id"), nullable=False)
    created_by_auth_id = Column(Integer, nullable=False)
    
    # Session state
    current_step = Column(Integer, default=1)
    total_steps = Column(Integer, nullable=False)
    session_data = Column(JSON, default=dict)  # Stores step data
    is_completed = Column(Boolean, default=False)
    completed_iep_id = Column(UUID(as_uuid=True), ForeignKey("ieps.id"), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)  # Session expiration
    
    def __repr__(self):
        return f"<WizardSession(id={self.id}, student_id={self.student_id}, step={self.current_step}/{self.total_steps})>"