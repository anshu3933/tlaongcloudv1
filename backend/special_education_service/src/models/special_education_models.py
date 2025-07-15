"""Database models for Special Education Service"""
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Date, JSON, ForeignKey, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import uuid
from enum import Enum
from .type_decorators import SafeDate

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
    date_of_birth = Column(SafeDate(), nullable=False)
    grade_level = Column(String(20), nullable=False)
    disability_codes = Column(JSON, nullable=False, default=list)  # List of disability type codes
    
    # User relationships (stored as auth service IDs)
    case_manager_auth_id = Column(Integer, nullable=True)
    primary_teacher_auth_id = Column(Integer, nullable=True)
    parent_guardian_auth_ids = Column(JSON, default=list)
    
    # Educational data
    school_district = Column(String(200), nullable=True)
    school_name = Column(String(200), nullable=True)
    enrollment_date = Column(SafeDate(), nullable=True)
    
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
    
    # Assessment pipeline relationships
    assessment_documents = relationship("AssessmentDocument", back_populates="student")
    quantified_assessments = relationship("QuantifiedAssessmentData", back_populates="student")
    
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
    meeting_date = Column(SafeDate(), nullable=True)
    effective_date = Column(SafeDate(), nullable=True)
    review_date = Column(SafeDate(), nullable=True)
    
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
    target_date = Column(SafeDate(), nullable=True)
    start_date = Column(SafeDate(), nullable=True)
    
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
    assessment_date = Column(SafeDate(), nullable=False)
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


# =============================================================================
# ASSESSMENT PIPELINE MODELS - Integrated into shared database
# =============================================================================

from sqlalchemy import Text, Float, Enum as SQLEnum
from ..common.enums import AssessmentType

class AssessmentDocument(Base):
    """Stores uploaded assessment documents"""
    __tablename__ = "assessment_documents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id"), nullable=False)
    document_type = Column(SQLEnum(AssessmentType, native_enum=False), nullable=False)
    file_path = Column(Text, nullable=False)
    file_name = Column(String(255), nullable=False)
    gcs_path = Column(Text)  # Google Cloud Storage path
    upload_date = Column(DateTime(timezone=True), server_default=func.now())
    processing_status = Column(String(50), default="pending")  # pending, processing, completed, failed
    
    # Document metadata
    assessment_date = Column(DateTime(timezone=True))
    assessor_name = Column(String(255))
    assessor_title = Column(String(255))
    assessment_location = Column(String(255))
    
    # Processing metadata
    extraction_confidence = Column(Float)  # 0-1 confidence score
    processing_duration = Column(Float)  # seconds
    error_message = Column(Text)
    
    # Relationships
    student = relationship("Student", back_populates="assessment_documents")
    psychoed_scores = relationship("PsychoedScore", back_populates="document", cascade="all, delete-orphan")
    extracted_data = relationship("ExtractedAssessmentData", back_populates="document", cascade="all, delete-orphan")
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<AssessmentDocument(id={self.id}, student_id={self.student_id}, type={self.document_type})>"

class PsychoedScore(Base):
    """Individual test scores extracted from assessments"""
    __tablename__ = "psychoed_scores"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("assessment_documents.id"), nullable=False)
    
    # Test information
    test_name = Column(String(100), nullable=False)  # WISC-V, WIAT-IV, etc.
    subtest_name = Column(String(100), nullable=False)  # Verbal Comprehension, Block Design, etc.
    score_type = Column(String(50), nullable=False)  # standard_score, percentile, scaled_score, etc.
    
    # Score values
    raw_score = Column(Integer)
    standard_score = Column(Integer)
    percentile_rank = Column(Integer)
    scaled_score = Column(Integer)
    grade_equivalent = Column(String(10))  # "3.5", "K.2", etc.
    age_equivalent_years = Column(Integer)  # Years component
    age_equivalent_months = Column(Integer)  # Months component
    
    # Confidence and reliability
    confidence_interval_lower = Column(Integer)
    confidence_interval_upper = Column(Integer)
    confidence_level = Column(Integer, default=95)  # 90, 95, 99
    extraction_confidence = Column(Float)  # How confident we are in the extraction
    
    # Metadata
    normative_sample = Column(String(100))  # Which norm was used
    test_date = Column(DateTime(timezone=True))
    basal_score = Column(Integer)
    ceiling_score = Column(Integer)
    
    # Relationships
    document = relationship("AssessmentDocument", back_populates="psychoed_scores")
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<PsychoedScore(test={self.test_name}, subtest={self.subtest_name}, score={self.standard_score})>"

class QuantifiedAssessmentData(Base):
    """Quantified and synthesized assessment data ready for RAG"""
    __tablename__ = "quantified_assessment_data"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id"), nullable=False)
    assessment_date = Column(DateTime(timezone=True), nullable=False)
    
    # Composite scores (normalized to 0-100 scale)
    cognitive_composite = Column(Float)
    academic_composite = Column(Float)
    behavioral_composite = Column(Float)
    social_emotional_composite = Column(Float)
    adaptive_composite = Column(Float)
    executive_composite = Column(Float)
    
    # Domain-specific composites
    reading_composite = Column(Float)
    math_composite = Column(Float)
    writing_composite = Column(Float)
    language_composite = Column(Float)
    
    # Standardized Present Levels of Performance (PLOP) data
    standardized_plop = Column(JSON)
    
    # Growth and progress data
    growth_rate = Column(JSON)  # Domain-specific growth rates
    progress_indicators = Column(JSON)  # Structured progress data
    
    # Learning profiles
    learning_style_profile = Column(JSON)
    cognitive_processing_profile = Column(JSON)
    
    # Goals and recommendations
    priority_goals = Column(JSON)
    service_recommendations = Column(JSON)
    accommodation_recommendations = Column(JSON)
    
    # Eligibility determination
    eligibility_category = Column(String(100))
    primary_disability = Column(String(100))
    secondary_disabilities = Column(JSON)
    
    # Confidence and source tracking
    confidence_metrics = Column(JSON)
    source_documents = Column(JSON)  # List of source document IDs
    
    # Relationships
    student = relationship("Student", back_populates="quantified_assessments")
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<QuantifiedAssessmentData(id={self.id}, student_id={self.student_id}, date={self.assessment_date})>"

class ExtractedAssessmentData(Base):
    """Raw extracted data from assessment documents before quantification"""
    __tablename__ = "extracted_assessment_data"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("assessment_documents.id"), nullable=False)
    
    # Raw extracted content
    raw_text = Column(Text)
    structured_data = Column(JSON)  # Structured extraction results
    
    # Extraction metadata
    extraction_method = Column(String(50))  # document_ai, manual, ocr
    extraction_confidence = Column(Float)
    completeness_score = Column(Float)  # How complete is the extraction
    
    # Quality indicators
    pages_processed = Column(Integer)
    total_pages = Column(Integer)
    processing_errors = Column(JSON)
    
    # Relationships
    document = relationship("AssessmentDocument", back_populates="extracted_data")
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<ExtractedAssessmentData(id={self.id}, confidence={self.extraction_confidence})>"