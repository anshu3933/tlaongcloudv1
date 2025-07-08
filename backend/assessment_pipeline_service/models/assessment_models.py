"""
Database models for assessment pipeline with psychoeducational testing structures
"""
from sqlalchemy import Column, String, Text, JSON, DateTime, Float, Boolean, ForeignKey, Index, Integer, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

Base = declarative_base()

class AssessmentType(enum.Enum):
    """Standardized assessment types"""
    WISC_V = "wisc_v"
    WIAT_IV = "wiat_iv"
    WJ_IV = "wj_iv"
    BASC_3 = "basc_3"
    CONNERS_3 = "conners_3"
    CTOPP_2 = "ctopp_2"
    KTEA_3 = "ktea_3"
    DAS_II = "das_ii"
    GORT_5 = "gort_5"
    TOWL_4 = "towl_4"
    BRIEF_2 = "brief_2"
    VINELAND_3 = "vineland_3"
    FBA = "functional_behavior_assessment"
    CBM = "curriculum_based_measure"
    OBSERVATION = "teacher_observation"
    PROGRESS_MONITORING = "progress_monitoring"

class AssessmentDocument(Base):
    """Stores uploaded assessment documents"""
    __tablename__ = "assessment_documents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id"), nullable=False)
    document_type = Column(SQLEnum(AssessmentType), nullable=False)
    file_path = Column(Text, nullable=False)
    file_name = Column(String(255), nullable=False)
    gcs_path = Column(Text)  # Google Cloud Storage path
    upload_date = Column(DateTime, default=datetime.utcnow)
    processing_status = Column(String(50), default="pending")  # pending, processing, completed, failed
    
    # Document metadata
    assessment_date = Column(DateTime)
    assessor_name = Column(String(255))
    assessor_title = Column(String(255))
    assessment_location = Column(String(255))
    referral_reason = Column(Text)
    
    # Processing metadata
    extraction_confidence = Column(Float)  # 76-98% range
    processing_errors = Column(JSON)
    processing_duration_seconds = Column(Float)
    
    # Relationships
    extracted_data = relationship("ExtractedAssessmentData", back_populates="document", cascade="all, delete-orphan")
    psychoed_scores = relationship("PsychoedScore", back_populates="document", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_student_document', 'student_id', 'document_type'),
        Index('idx_processing_status', 'processing_status'),
        Index('idx_assessment_date', 'assessment_date'),
    )

class PsychoedScore(Base):
    """Stores individual psychoeducational test scores"""
    __tablename__ = "psychoed_scores"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("assessment_documents.id"), nullable=False)
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id"), nullable=False)
    
    # Test identification
    test_name = Column(String(100), nullable=False)  # e.g., "WISC-V"
    test_version = Column(String(50))
    subtest_name = Column(String(100), nullable=False)  # e.g., "Verbal Comprehension Index"
    
    # Score data
    raw_score = Column(Float)
    standard_score = Column(Float)  # Usually mean=100, SD=15
    scaled_score = Column(Float)    # Usually mean=10, SD=3
    t_score = Column(Float)         # Usually mean=50, SD=10
    z_score = Column(Float)         # Mean=0, SD=1
    percentile_rank = Column(Float)
    stanine = Column(Integer)       # 1-9 scale
    
    # Age/Grade equivalents
    age_equivalent_years = Column(Float)
    age_equivalent_months = Column(Integer)
    grade_equivalent = Column(String(20))
    
    # Confidence intervals
    confidence_interval_lower = Column(Float)
    confidence_interval_upper = Column(Float)
    confidence_level = Column(Integer, default=95)  # 90 or 95 typically
    
    # Descriptors and interpretations
    qualitative_descriptor = Column(String(50))  # e.g., "Average", "Below Average"
    score_classification = Column(String(50))    # e.g., "Low", "Low Average", "Average"
    
    # Test-specific metadata
    test_specific_data = Column(JSON)  # For unique test properties
    
    # Quality and extraction metadata
    extraction_confidence = Column(Float)
    manually_verified = Column(Boolean, default=False)
    
    # Relationships
    document = relationship("AssessmentDocument", back_populates="psychoed_scores")
    
    # Indexes
    __table_args__ = (
        Index('idx_student_test_scores', 'student_id', 'test_name', 'subtest_name'),
        Index('idx_score_types', 'test_name', 'subtest_name'),
    )

class ExtractedAssessmentData(Base):
    """Stores structured data extracted from assessments"""
    __tablename__ = "extracted_assessment_data"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("assessment_documents.id"), nullable=False)
    extraction_date = Column(DateTime, default=datetime.utcnow)
    
    # Cognitive/Academic Composite Data
    cognitive_data = Column(JSON)  # Composite scores, indices
    academic_data = Column(JSON)   # Achievement areas
    processing_data = Column(JSON) # Processing speed, working memory
    
    # Behavioral/Social-Emotional Data
    behavioral_data = Column(JSON)       # Behavior rating scales
    social_emotional_data = Column(JSON) # Social skills, emotional regulation
    adaptive_data = Column(JSON)         # Adaptive behavior scales
    executive_function_data = Column(JSON) # Executive function measures
    
    # Present Levels of Performance
    present_levels = Column(JSON)  # Structured PLOP data
    
    # Clinical observations
    observations = Column(JSON)
    test_behavior = Column(JSON)  # Behavior during testing
    
    # Strengths and Needs
    strengths = Column(JSON)       # List of identified strengths
    needs = Column(JSON)           # List of identified needs
    
    # Recommendations
    recommendations = Column(JSON)  # Professional recommendations
    accommodations = Column(JSON)   # Testing accommodations used
    
    # Diagnostic impressions
    diagnostic_impressions = Column(JSON)
    eligibility_determinations = Column(JSON)
    
    # Quality metrics
    extraction_confidence = Column(Float)  # 0-1 confidence score
    completeness_score = Column(Float)     # How complete the extraction is
    manual_review_required = Column(Boolean, default=False)
    review_notes = Column(Text)
    reviewer_id = Column(UUID(as_uuid=True))
    review_timestamp = Column(DateTime)
    
    # Relationship
    document = relationship("AssessmentDocument", back_populates="extracted_data")

class CognitiveProfile(Base):
    """Stores comprehensive cognitive assessment profiles"""
    __tablename__ = "cognitive_profiles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id"), nullable=False)
    assessment_date = Column(DateTime, nullable=False)
    
    # WISC-V / DAS-II Index Scores
    full_scale_iq = Column(Float)
    verbal_comprehension_index = Column(Float)
    visual_spatial_index = Column(Float)
    fluid_reasoning_index = Column(Float)
    working_memory_index = Column(Float)
    processing_speed_index = Column(Float)
    
    # Additional cognitive measures
    general_ability_index = Column(Float)
    cognitive_proficiency_index = Column(Float)
    nonverbal_index = Column(Float)
    
    # Pattern of strengths and weaknesses
    psw_analysis = Column(JSON)  # Pattern analysis data
    cognitive_strengths = Column(JSON)
    cognitive_weaknesses = Column(JSON)
    
    # Cross-battery assessment data
    cross_battery_data = Column(JSON)
    
    # Source assessments
    source_assessments = Column(JSON)  # List of assessment IDs used
    composite_confidence = Column(Float)

class AcademicProfile(Base):
    """Stores comprehensive academic achievement profiles"""
    __tablename__ = "academic_profiles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id"), nullable=False)
    assessment_date = Column(DateTime, nullable=False)
    
    # Reading domain
    basic_reading_skills = Column(Float)
    reading_comprehension = Column(Float)
    reading_fluency = Column(Float)
    phonological_processing = Column(Float)
    
    # Mathematics domain
    math_calculation = Column(Float)
    math_problem_solving = Column(Float)
    math_fluency = Column(Float)
    
    # Written language domain
    written_expression = Column(Float)
    spelling = Column(Float)
    writing_fluency = Column(Float)
    
    # Oral language
    listening_comprehension = Column(Float)
    oral_expression = Column(Float)
    
    # Academic fluency measures
    reading_rate = Column(Float)  # Words per minute
    math_facts_fluency = Column(Float)
    
    # Error analysis
    error_patterns = Column(JSON)
    
    # Academic strengths/needs
    academic_strengths = Column(JSON)
    academic_needs = Column(JSON)
    
    # Source assessments
    source_assessments = Column(JSON)

class BehavioralProfile(Base):
    """Stores behavioral assessment data"""
    __tablename__ = "behavioral_profiles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id"), nullable=False)
    assessment_date = Column(DateTime, nullable=False)
    
    # BASC-3 / Conners scales
    externalizing_problems = Column(Float)
    internalizing_problems = Column(Float)
    behavioral_symptoms_index = Column(Float)
    adaptive_skills_composite = Column(Float)
    
    # Specific behavior domains
    hyperactivity = Column(Float)
    aggression = Column(Float)
    anxiety = Column(Float)
    depression = Column(Float)
    attention_problems = Column(Float)
    social_skills = Column(Float)
    
    # Executive function (BRIEF-2)
    inhibit = Column(Float)
    shift = Column(Float)
    emotional_control = Column(Float)
    working_memory_behavior = Column(Float)
    plan_organize = Column(Float)
    
    # Functional behavior data
    behavior_frequency_data = Column(JSON)
    antecedent_data = Column(JSON)
    consequence_data = Column(JSON)
    setting_events = Column(JSON)
    
    # Multi-informant data
    teacher_ratings = Column(JSON)
    parent_ratings = Column(JSON)
    self_ratings = Column(JSON)

class QuantifiedAssessmentData(Base):
    """Stores quantified/normalized assessment data for RAG"""
    __tablename__ = "quantified_assessment_data"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id"), nullable=False)
    assessment_date = Column(DateTime, default=datetime.utcnow)
    
    # Quantified composite scores (normalized 0-100)
    cognitive_composite = Column(Float)
    academic_composite = Column(Float)
    behavioral_composite = Column(Float)
    social_emotional_composite = Column(Float)
    adaptive_composite = Column(Float)
    executive_composite = Column(Float)
    
    # Domain-specific quantified scores
    reading_composite = Column(Float)
    math_composite = Column(Float)
    writing_composite = Column(Float)
    language_composite = Column(Float)
    
    # Growth metrics
    growth_rate = Column(JSON)  # Subject-specific growth rates
    progress_indicators = Column(JSON)  # Trending data
    response_to_intervention = Column(JSON)  # RTI data
    
    # Learning profile
    learning_style_profile = Column(JSON)
    cognitive_processing_profile = Column(JSON)
    
    # Standardized present levels
    standardized_plop = Column(JSON)  # Normalized PLOP for RAG
    
    # Priority rankings
    priority_goals = Column(JSON)  # Top priority goal areas
    service_recommendations = Column(JSON)  # Quantified service needs
    accommodation_recommendations = Column(JSON)
    
    # Eligibility and classification
    eligibility_category = Column(String(100))
    primary_disability = Column(String(100))
    secondary_disabilities = Column(JSON)
    
    # Source tracking
    source_documents = Column(JSON)  # List of document IDs used
    source_scores = Column(JSON)     # List of score IDs used
    calculation_metadata = Column(JSON)  # How scores were calculated
    confidence_metrics = Column(JSON)
    
    __table_args__ = (
        Index('idx_student_assessment_date', 'student_id', 'assessment_date'),
        Index('idx_eligibility', 'eligibility_category'),
    )

class AssessmentPipeline(Base):
    """Tracks assessment processing pipeline runs"""
    __tablename__ = "assessment_pipelines"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(UUID(as_uuid=True))  # User ID
    
    # Pipeline configuration
    pipeline_version = Column(String(20), default="2.0")
    pipeline_config = Column(JSON)  # Settings used
    
    # Pipeline status
    status = Column(String(50), default="initiated")  # initiated, intake, quantifying, generating, review, completed, failed
    current_stage = Column(String(50))
    
    # Stage results with psychoed data
    intake_results = Column(JSON)  # Document processing results
    extraction_results = Column(JSON)  # Score extraction results
    quantification_results = Column(JSON)  # Quantified metrics
    rag_generation_results = Column(JSON)  # Generated IEP content
    review_results = Column(JSON)  # Professional review feedback
    
    # Quality metrics
    overall_confidence = Column(Float)
    extraction_confidence = Column(Float)
    quantification_completeness = Column(Float)
    generation_quality_score = Column(Float)
    
    # Error tracking
    error_message = Column(Text)
    error_stage = Column(String(50))
    error_details = Column(JSON)
    
    # Audit trail
    pipeline_metadata = Column(JSON)  # Detailed processing log
    processing_time_seconds = Column(Float)
    stage_timings = Column(JSON)  # Time per stage
    
    # Review and approval
    review_status = Column(String(50))  # pending, in_review, approved, rejected
    reviewer_id = Column(UUID(as_uuid=True))
    review_comments = Column(Text)
    review_timestamp = Column(DateTime)
    
    __table_args__ = (
        Index('idx_pipeline_status', 'status'),
        Index('idx_pipeline_student', 'student_id'),
        Index('idx_pipeline_created', 'created_at'),
    )