"""Assessment data schemas for API validation and serialization"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID
from enum import Enum

class AssessmentType(str, Enum):
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

# Assessment Document schemas
class AssessmentDocumentBase(BaseModel):
    """Base schema for assessment documents"""
    student_id: UUID
    document_type: AssessmentType
    file_name: str = Field(..., min_length=1, max_length=255)
    file_path: str
    gcs_path: Optional[str] = None
    assessment_date: Optional[datetime] = None
    assessor_name: Optional[str] = Field(None, max_length=255)
    assessor_title: Optional[str] = Field(None, max_length=255)
    assessment_location: Optional[str] = Field(None, max_length=255)

class AssessmentDocumentCreate(AssessmentDocumentBase):
    """Schema for creating assessment documents"""
    processing_status: str = "pending"
    extraction_confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    processing_duration: Optional[float] = None
    error_message: Optional[str] = None

class AssessmentDocumentUpdate(BaseModel):
    """Schema for updating assessment documents"""
    model_config = ConfigDict(extra="forbid")
    
    processing_status: Optional[str] = None
    extraction_confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    processing_duration: Optional[float] = None
    error_message: Optional[str] = None
    assessor_name: Optional[str] = Field(None, max_length=255)
    assessor_title: Optional[str] = Field(None, max_length=255)
    assessment_location: Optional[str] = Field(None, max_length=255)

class AssessmentDocumentResponse(AssessmentDocumentBase):
    """Schema for assessment document responses"""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    upload_date: datetime
    processing_status: str
    extraction_confidence: Optional[float] = None
    processing_duration: Optional[float] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

# Psychoeducational Score schemas
class PsychoedScoreBase(BaseModel):
    """Base schema for psychoeducational scores"""
    test_name: str = Field(..., max_length=100)
    subtest_name: str = Field(..., max_length=100)
    score_type: str = Field(..., max_length=50)
    raw_score: Optional[int] = None
    standard_score: Optional[int] = None
    percentile_rank: Optional[int] = Field(None, ge=1, le=99)
    scaled_score: Optional[int] = None
    grade_equivalent: Optional[str] = Field(None, max_length=10)
    age_equivalent: Optional[str] = Field(None, max_length=10)
    confidence_interval_lower: Optional[int] = None
    confidence_interval_upper: Optional[int] = None
    confidence_level: int = Field(95, ge=90, le=99)
    extraction_confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    normative_sample: Optional[str] = Field(None, max_length=100)
    test_date: Optional[datetime] = None
    basal_score: Optional[int] = None
    ceiling_score: Optional[int] = None

class PsychoedScoreCreate(PsychoedScoreBase):
    """Schema for creating psychoeducational scores"""
    document_id: UUID

class PsychoedScoreResponse(PsychoedScoreBase):
    """Schema for psychoeducational score responses"""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    document_id: UUID
    created_at: datetime

# Extracted Assessment Data schemas
class ExtractedAssessmentDataBase(BaseModel):
    """Base schema for extracted assessment data"""
    raw_text: Optional[str] = None
    structured_data: Optional[Dict[str, Any]] = None
    extraction_method: Optional[str] = Field(None, max_length=50)
    extraction_confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    completeness_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    pages_processed: Optional[int] = Field(None, ge=0)
    total_pages: Optional[int] = Field(None, ge=0)
    processing_errors: Optional[Dict[str, Any]] = None

class ExtractedAssessmentDataCreate(ExtractedAssessmentDataBase):
    """Schema for creating extracted assessment data"""
    document_id: UUID

class ExtractedAssessmentDataResponse(ExtractedAssessmentDataBase):
    """Schema for extracted assessment data responses"""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    document_id: UUID
    created_at: datetime

# Quantified Assessment Data schemas
class QuantifiedAssessmentDataBase(BaseModel):
    """Base schema for quantified assessment data"""
    assessment_date: datetime
    cognitive_composite: Optional[float] = Field(None, ge=0.0, le=100.0)
    academic_composite: Optional[float] = Field(None, ge=0.0, le=100.0)
    behavioral_composite: Optional[float] = Field(None, ge=0.0, le=100.0)
    social_emotional_composite: Optional[float] = Field(None, ge=0.0, le=100.0)
    adaptive_composite: Optional[float] = Field(None, ge=0.0, le=100.0)
    executive_composite: Optional[float] = Field(None, ge=0.0, le=100.0)
    reading_composite: Optional[float] = Field(None, ge=0.0, le=100.0)
    math_composite: Optional[float] = Field(None, ge=0.0, le=100.0)
    writing_composite: Optional[float] = Field(None, ge=0.0, le=100.0)
    language_composite: Optional[float] = Field(None, ge=0.0, le=100.0)
    standardized_plop: Optional[Dict[str, Any]] = None
    growth_rate: Optional[Dict[str, Any]] = None
    progress_indicators: Optional[Dict[str, Any]] = None
    learning_style_profile: Optional[Dict[str, Any]] = None
    cognitive_processing_profile: Optional[Dict[str, Any]] = None
    priority_goals: Optional[Dict[str, Any]] = None
    service_recommendations: Optional[Dict[str, Any]] = None
    accommodation_recommendations: Optional[Dict[str, Any]] = None
    eligibility_category: Optional[str] = Field(None, max_length=100)
    primary_disability: Optional[str] = Field(None, max_length=100)
    secondary_disabilities: Optional[Dict[str, Any]] = None
    confidence_metrics: Optional[Dict[str, Any]] = None
    source_documents: Optional[Dict[str, Any]] = None

class QuantifiedAssessmentDataCreate(QuantifiedAssessmentDataBase):
    """Schema for creating quantified assessment data"""
    student_id: UUID

class QuantifiedAssessmentDataResponse(QuantifiedAssessmentDataBase):
    """Schema for quantified assessment data responses"""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    student_id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None

# Composite schemas for comprehensive responses
class StudentAssessmentSummary(BaseModel):
    """Comprehensive assessment summary for a student"""
    student_id: UUID
    assessment_documents: List[AssessmentDocumentResponse]
    psychoed_scores: List[PsychoedScoreResponse]
    quantified_data: List[QuantifiedAssessmentDataResponse]
    summary: Dict[str, Any]

class AssessmentPipelineRequest(BaseModel):
    """Request schema for triggering assessment pipeline processing"""
    document_id: UUID
    processing_options: Optional[Dict[str, Any]] = None
    priority: str = Field("normal", pattern="^(low|normal|high|urgent)$")

class AssessmentPipelineResponse(BaseModel):
    """Response schema for assessment pipeline operations"""
    document_id: UUID
    status: str
    message: str
    processing_started_at: Optional[datetime] = None
    estimated_completion: Optional[datetime] = None