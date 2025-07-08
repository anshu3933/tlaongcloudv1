"""
Pydantic schemas for assessment data transfer
"""
from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
from enum import Enum
from uuid import UUID

class AssessmentTypeEnum(str, Enum):
    """Assessment types matching database enum"""
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

class AssessmentUploadDTO(BaseModel):
    """Frontend -> Backend: Assessment document upload"""
    student_id: UUID
    document_type: AssessmentTypeEnum
    file_name: str
    file_data: Optional[bytes] = None  # Base64 encoded
    file_path: Optional[str] = None    # Alternative: path reference
    assessment_date: Optional[datetime] = None
    assessor_name: Optional[str] = None
    assessor_title: Optional[str] = None
    referral_reason: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)

class PsychoedScoreDTO(BaseModel):
    """Individual test score data"""
    test_name: str
    test_version: Optional[str] = None
    subtest_name: str
    
    # Score values
    raw_score: Optional[float] = None
    standard_score: Optional[float] = None
    scaled_score: Optional[float] = None
    t_score: Optional[float] = None
    percentile_rank: Optional[float] = None
    
    # Equivalents
    age_equivalent_years: Optional[float] = None
    age_equivalent_months: Optional[int] = None
    grade_equivalent: Optional[str] = None
    
    # Confidence interval
    confidence_interval: Optional[Tuple[float, float]] = None
    confidence_level: Optional[int] = 95
    
    # Interpretation
    qualitative_descriptor: Optional[str] = None
    score_classification: Optional[str] = None
    
    # Quality
    extraction_confidence: Optional[float] = Field(None, ge=0, le=1)
    
    model_config = ConfigDict(from_attributes=True)

class ExtractedDataDTO(BaseModel):
    """Extracted assessment data for frontend display"""
    document_id: UUID
    extraction_date: datetime
    
    # Cognitive data
    cognitive_scores: List[PsychoedScoreDTO] = []
    cognitive_indices: Dict[str, float] = {}
    
    # Academic data
    academic_scores: List[PsychoedScoreDTO] = []
    academic_composites: Dict[str, float] = {}
    
    # Behavioral data
    behavioral_ratings: Dict[str, float] = {}
    behavioral_observations: List[str] = []
    
    # Present levels
    present_levels: Dict[str, Any] = {}
    strengths: List[str] = []
    needs: List[str] = []
    
    # Recommendations
    recommendations: List[str] = []
    accommodations: List[str] = []
    
    # Quality metrics
    extraction_confidence: float = Field(ge=0.76, le=0.98)
    completeness_score: float = Field(ge=0, le=1)
    manual_review_required: bool = False
    
    model_config = ConfigDict(from_attributes=True)

class AssessmentIntakeRequestDTO(BaseModel):
    """Request to process assessment documents"""
    student_id: UUID
    documents: List[AssessmentUploadDTO]
    processing_priority: str = "standard"  # standard, urgent
    notify_on_completion: bool = True
    
    model_config = ConfigDict(from_attributes=True)

class AssessmentIntakeResponseDTO(BaseModel):
    """Response from assessment intake"""
    pipeline_id: UUID
    status: str
    documents_received: int
    estimated_completion_time: datetime
    initial_validation: Dict[str, Any]
    
    model_config = ConfigDict(from_attributes=True)

class QuantifiedMetricsDTO(BaseModel):
    """Quantified assessment metrics for frontend"""
    # Academic metrics
    reading_metrics: Dict[str, float] = {}
    math_metrics: Dict[str, float] = {}
    writing_metrics: Dict[str, float] = {}
    
    # Cognitive metrics
    cognitive_indices: Dict[str, float] = {}
    processing_strengths: List[str] = []
    processing_weaknesses: List[str] = []
    
    # Behavioral metrics
    attention_metrics: Dict[str, float] = {}
    social_emotional_metrics: Dict[str, float] = {}
    executive_function_metrics: Dict[str, float] = {}
    
    # Growth data
    growth_rates: Dict[str, float] = {}
    progress_indicators: List[Dict[str, Any]] = []
    
    # Learning profile
    learning_style: str = ""
    optimal_conditions: List[str] = []
    barriers: List[str] = []
    
    # Priority areas
    priority_goals: List[Dict[str, Any]] = []
    service_recommendations: List[Dict[str, Any]] = []
    
    model_config = ConfigDict(from_attributes=True)

class CognitiveProfileDTO(BaseModel):
    """Comprehensive cognitive profile"""
    assessment_date: datetime
    
    # IQ indices
    full_scale_iq: Optional[float] = None
    verbal_comprehension_index: Optional[float] = None
    visual_spatial_index: Optional[float] = None
    fluid_reasoning_index: Optional[float] = None
    working_memory_index: Optional[float] = None
    processing_speed_index: Optional[float] = None
    
    # Additional indices
    general_ability_index: Optional[float] = None
    cognitive_proficiency_index: Optional[float] = None
    
    # Analysis
    cognitive_strengths: List[str] = []
    cognitive_weaknesses: List[str] = []
    processing_patterns: Dict[str, Any] = {}
    
    # Confidence
    composite_confidence: float = Field(ge=0, le=1)
    
    model_config = ConfigDict(from_attributes=True)

class AcademicProfileDTO(BaseModel):
    """Comprehensive academic profile"""
    assessment_date: datetime
    
    # Reading
    basic_reading_skills: Optional[float] = None
    reading_comprehension: Optional[float] = None
    reading_fluency: Optional[float] = None
    reading_rate_wpm: Optional[float] = None
    
    # Math
    math_calculation: Optional[float] = None
    math_problem_solving: Optional[float] = None
    math_fluency: Optional[float] = None
    
    # Writing
    written_expression: Optional[float] = None
    spelling: Optional[float] = None
    writing_fluency: Optional[float] = None
    
    # Analysis
    academic_strengths: List[str] = []
    academic_needs: List[str] = []
    error_patterns: Dict[str, List[str]] = {}
    
    model_config = ConfigDict(from_attributes=True)

class BehavioralProfileDTO(BaseModel):
    """Comprehensive behavioral profile"""
    assessment_date: datetime
    
    # Composite scores
    externalizing_problems: Optional[float] = None
    internalizing_problems: Optional[float] = None
    behavioral_symptoms_index: Optional[float] = None
    adaptive_skills_composite: Optional[float] = None
    
    # Specific behaviors
    hyperactivity: Optional[float] = None
    aggression: Optional[float] = None
    anxiety: Optional[float] = None
    depression: Optional[float] = None
    attention_problems: Optional[float] = None
    
    # Executive function
    executive_function_scores: Dict[str, float] = {}
    
    # Functional data
    behavior_frequency_data: List[Dict[str, Any]] = []
    antecedent_patterns: List[str] = []
    effective_interventions: List[str] = []
    
    model_config = ConfigDict(from_attributes=True)

class AssessmentSummaryDTO(BaseModel):
    """Summary of all assessments for a student"""
    student_id: UUID
    total_assessments: int
    latest_assessment_date: Optional[datetime] = None
    
    # Available profiles
    has_cognitive_profile: bool = False
    has_academic_profile: bool = False
    has_behavioral_profile: bool = False
    
    # Summary metrics
    overall_functioning_level: Optional[str] = None
    primary_concerns: List[str] = []
    eligibility_determination: Optional[str] = None
    
    # Recent scores
    recent_cognitive_scores: Optional[CognitiveProfileDTO] = None
    recent_academic_scores: Optional[AcademicProfileDTO] = None
    recent_behavioral_scores: Optional[BehavioralProfileDTO] = None
    
    model_config = ConfigDict(from_attributes=True)