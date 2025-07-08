"""
Pydantic schemas for pipeline operations
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID

class PipelineStatusEnum(str):
    """Pipeline status values"""
    INITIATED = "initiated"
    INTAKE = "intake"
    EXTRACTING = "extracting"
    QUANTIFYING = "quantifying"
    GENERATING = "generating"
    REVIEW = "review"
    COMPLETED = "completed"
    FAILED = "failed"

class PipelineCreateRequestDTO(BaseModel):
    """Request to create assessment pipeline"""
    student_id: UUID
    assessment_document_ids: List[UUID]
    template_id: Optional[UUID] = None
    processing_config: Dict[str, Any] = Field(default_factory=dict)
    
    model_config = ConfigDict(from_attributes=True)

class PipelineStatusResponseDTO(BaseModel):
    """Pipeline status for frontend polling"""
    pipeline_id: UUID
    status: str
    current_stage: Optional[str] = None
    progress_percentage: float = Field(ge=0, le=100)
    
    # Stage completion status
    stages_completed: List[str] = []
    current_stage_progress: Optional[float] = None
    
    # Time estimates
    started_at: datetime
    estimated_completion: Optional[datetime] = None
    elapsed_seconds: float
    
    # Results preview
    has_results: bool = False
    preview_available: bool = False
    
    # Errors
    has_errors: bool = False
    error_message: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)

class StageResultDTO(BaseModel):
    """Result from a pipeline stage"""
    stage_name: str
    status: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    
    # Results
    output_summary: Dict[str, Any] = {}
    quality_metrics: Dict[str, float] = {}
    warnings: List[str] = []
    
    model_config = ConfigDict(from_attributes=True)

class IntakeResultDTO(BaseModel):
    """Stage 1: Intake results"""
    documents_processed: int
    extraction_results: List[Dict[str, Any]]
    average_confidence: float
    psychoed_scores_extracted: int
    review_required_count: int
    
    model_config = ConfigDict(from_attributes=True)

class QuantificationResultDTO(BaseModel):
    """Stage 2: Quantification results"""
    domains_quantified: List[str]
    completeness_score: float
    academic_metrics_generated: int
    behavioral_matrices_generated: int
    composite_profile_complete: bool
    missing_data_areas: List[str] = []
    
    model_config = ConfigDict(from_attributes=True)

class GenerationResultDTO(BaseModel):
    """Stage 3: IEP generation results"""
    sections_generated: List[str]
    goals_created: int
    quality_score: float
    regurgitation_check_passed: bool
    smart_compliance_rate: float
    professional_terminology_count: int
    
    model_config = ConfigDict(from_attributes=True)

class ReviewPackageDTO(BaseModel):
    """Stage 4: Review package"""
    review_interface_ready: bool
    side_by_side_comparison: bool
    quality_dashboard: Dict[str, Any]
    compliance_checklist: List[Dict[str, bool]]
    parent_version_available: bool
    
    model_config = ConfigDict(from_attributes=True)

class AssessmentPipelineResponseDTO(BaseModel):
    """Complete pipeline results"""
    pipeline_id: UUID
    status: str
    
    # Stage results
    intake_results: Optional[IntakeResultDTO] = None
    quantification_results: Optional[QuantificationResultDTO] = None
    generation_results: Optional[GenerationResultDTO] = None
    review_package: Optional[ReviewPackageDTO] = None
    
    # Overall metrics
    overall_confidence: float = Field(ge=0, le=1)
    total_processing_time: float
    
    # Final outputs
    iep_content: Optional[Dict[str, Any]] = None
    supporting_documents: List[Dict[str, Any]] = []
    
    # Quality summary
    quality_summary: Dict[str, Any] = {}
    requires_review: bool = False
    
    model_config = ConfigDict(from_attributes=True)

class IEPSectionDTO(BaseModel):
    """Individual IEP section"""
    section_name: str
    content: str
    data_sources: List[str] = []
    confidence_score: float = Field(ge=0, le=1)
    
    # Alternatives for goals
    alternatives: Optional[List[Dict[str, Any]]] = None
    
    # Quality metrics
    terminology_score: int
    specificity_score: float
    evidence_citations: List[str] = []
    
    model_config = ConfigDict(from_attributes=True)

class GeneratedIEPDTO(BaseModel):
    """Complete generated IEP"""
    student_id: UUID
    pipeline_id: UUID
    generation_timestamp: datetime
    
    # Sections
    present_levels: Dict[str, IEPSectionDTO]
    annual_goals: List[IEPSectionDTO]
    short_term_objectives: List[IEPSectionDTO]
    services: IEPSectionDTO
    accommodations: IEPSectionDTO
    
    # Metadata
    template_used: Optional[str] = None
    quality_metrics: Dict[str, float]
    data_sources_summary: Dict[str, int]
    
    model_config = ConfigDict(from_attributes=True)

class PipelineErrorDTO(BaseModel):
    """Error response"""
    error_code: str
    error_message: str
    error_stage: Optional[str] = None
    error_details: Optional[Dict[str, Any]] = None
    suggested_actions: List[str] = []
    
    model_config = ConfigDict(from_attributes=True)

class BatchProcessingRequestDTO(BaseModel):
    """Request to process multiple students"""
    student_ids: List[UUID]
    document_types: Optional[List[str]] = None
    processing_priority: str = "standard"
    
    model_config = ConfigDict(from_attributes=True)

class BatchProcessingResponseDTO(BaseModel):
    """Batch processing status"""
    batch_id: UUID
    total_students: int
    pipelines_created: int
    estimated_completion: datetime
    
    model_config = ConfigDict(from_attributes=True)