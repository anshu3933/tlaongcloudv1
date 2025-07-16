"""
Enhanced Metadata Schemas for RAG Pipeline
===========================================

Comprehensive metadata schemas for document processing, chunk annotation,
and relationship mapping in the TLA Educational Platform RAG system.

Created: 2025-07-16
Task: TASK-001 - Enhanced Metadata Schema Definitions
"""

from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import List, Dict, Optional, Any, Union
from datetime import datetime
from enum import Enum
import re


class DocumentType(str, Enum):
    """Standard document types in educational context"""
    IEP = "iep"
    ASSESSMENT_REPORT = "assessment_report"
    PROGRESS_REPORT = "progress_report"
    BEHAVIORAL_ASSESSMENT = "behavioral_assessment"
    SPEECH_LANGUAGE_EVAL = "speech_language_eval"
    OCCUPATIONAL_THERAPY = "occupational_therapy"
    PHYSICAL_THERAPY = "physical_therapy"
    PSYCHOLOGICAL_EVAL = "psychological_eval"
    EDUCATIONAL_EVAL = "educational_eval"
    TRANSITION_PLAN = "transition_plan"
    MEETING_NOTES = "meeting_notes"
    OTHER = "other"


class AssessmentType(str, Enum):
    """Standardized assessment types"""
    WISC_V = "wisc_v"
    WIAT_IV = "wiat_iv"
    WJ_IV = "wj_iv"
    BASC_3 = "basc_3"
    CONNERS_3 = "conners_3"
    KTEA_3 = "ktea_3"
    DAS_II = "das_ii"
    BRIEF_2 = "brief_2"
    CTOPP_2 = "ctopp_2"
    GARS_3 = "gars_3"
    VINELAND_3 = "vineland_3"
    OTHER = "other"


class IEPSection(str, Enum):
    """Standard IEP sections for relevance scoring"""
    STUDENT_INFO = "student_info"
    PRESENT_LEVELS = "present_levels"
    ANNUAL_GOALS = "annual_goals"
    SHORT_TERM_OBJECTIVES = "short_term_objectives"
    SPECIAL_EDUCATION_SERVICES = "special_education_services"
    RELATED_SERVICES = "related_services"
    ACCOMMODATIONS = "accommodations"
    MODIFICATIONS = "modifications"
    ASSESSMENT_PARTICIPATION = "assessment_participation"
    TRANSITION_SERVICES = "transition_services"
    BEHAVIOR_INTERVENTION = "behavior_intervention"
    ESY_SERVICES = "esy_services"
    OTHER = "other"


class QualityMetrics(BaseModel):
    """Quality assessment metrics for content chunks"""
    
    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True,
        use_enum_values=True
    )
    
    extraction_confidence: float = Field(
        ..., 
        ge=0.0, 
        le=1.0,
        description="Confidence in text extraction (OCR/parsing)"
    )
    
    information_density: float = Field(
        ..., 
        ge=0.0, 
        le=1.0,
        description="Density of useful educational information"
    )
    
    readability_score: float = Field(
        ..., 
        ge=0.0, 
        le=1.0,
        description="Content readability and clarity"
    )
    
    completeness_score: float = Field(
        ..., 
        ge=0.0, 
        le=1.0,
        description="Completeness of extracted information"
    )
    
    validation_status: str = Field(
        ...,
        pattern=r'^(validated|unvalidated|flagged|error)$',
        description="Manual or automated validation status"
    )
    
    overall_quality: float = Field(
        ..., 
        ge=0.0, 
        le=1.0,
        description="Overall quality score (weighted combination)"
    )


class TemporalMetadata(BaseModel):
    """Temporal information for tracking document chronology"""
    
    model_config = ConfigDict(extra='forbid', validate_assignment=True)
    
    document_date: Optional[datetime] = Field(
        None,
        description="Date the document was created/authored"
    )
    
    assessment_date: Optional[datetime] = Field(
        None,
        description="Date assessment was administered"
    )
    
    processing_date: datetime = Field(
        ...,
        description="Date document was processed into RAG system"
    )
    
    last_modified: Optional[datetime] = Field(
        None,
        description="Last modification date of source document"
    )
    
    school_year: Optional[str] = Field(
        None,
        pattern=r'^\d{4}-\d{4}$',
        description="Academic year (e.g., '2024-2025')"
    )
    
    temporal_sequence: Optional[int] = Field(
        None,
        ge=1,
        description="Sequence number in chronological order for student"
    )


class SemanticMetadata(BaseModel):
    """Semantic content classification and tags"""
    
    model_config = ConfigDict(extra='forbid', validate_assignment=True)
    
    primary_topic: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Primary educational topic or focus"
    )
    
    secondary_topics: List[str] = Field(
        default_factory=list,
        max_items=10,
        description="Secondary topics covered"
    )
    
    educational_domain: List[str] = Field(
        default_factory=list,
        description="Educational domains (reading, math, behavior, etc.)"
    )
    
    disability_relevance: List[str] = Field(
        default_factory=list,
        description="Relevant disability categories"
    )
    
    grade_level_relevance: List[str] = Field(
        default_factory=list,
        description="Relevant grade levels"
    )
    
    content_type: str = Field(
        ...,
        pattern=r'^(narrative|data|scores|recommendations|goals|accommodations)$',
        description="Type of content (narrative, data, etc.)"
    )
    
    entities_extracted: Dict[str, List[str]] = Field(
        default_factory=dict,
        description="Named entities by category"
    )


class IEPSectionRelevance(BaseModel):
    """Relevance scores for each IEP section"""
    
    model_config = ConfigDict(extra='forbid', validate_assignment=True)
    
    student_info: float = Field(default=0.0, ge=0.0, le=1.0)
    present_levels: float = Field(default=0.0, ge=0.0, le=1.0)
    annual_goals: float = Field(default=0.0, ge=0.0, le=1.0)
    short_term_objectives: float = Field(default=0.0, ge=0.0, le=1.0)
    special_education_services: float = Field(default=0.0, ge=0.0, le=1.0)
    related_services: float = Field(default=0.0, ge=0.0, le=1.0)
    accommodations: float = Field(default=0.0, ge=0.0, le=1.0)
    modifications: float = Field(default=0.0, ge=0.0, le=1.0)
    assessment_participation: float = Field(default=0.0, ge=0.0, le=1.0)
    transition_services: float = Field(default=0.0, ge=0.0, le=1.0)
    behavior_intervention: float = Field(default=0.0, ge=0.0, le=1.0)
    esy_services: float = Field(default=0.0, ge=0.0, le=1.0)
    
    @property
    def max_relevance_section(self) -> str:
        """Get the section with highest relevance score"""
        scores = {
            'student_info': self.student_info,
            'present_levels': self.present_levels,
            'annual_goals': self.annual_goals,
            'short_term_objectives': self.short_term_objectives,
            'special_education_services': self.special_education_services,
            'related_services': self.related_services,
            'accommodations': self.accommodations,
            'modifications': self.modifications,
            'assessment_participation': self.assessment_participation,
            'transition_services': self.transition_services,
            'behavior_intervention': self.behavior_intervention,
            'esy_services': self.esy_services
        }
        return max(scores, key=scores.get)


class RelationshipMetadata(BaseModel):
    """Relationships between chunks and documents"""
    
    model_config = ConfigDict(extra='forbid', validate_assignment=True)
    
    # Sequential relationships
    previous_chunk_id: Optional[str] = Field(
        None,
        description="ID of previous chunk in sequence"
    )
    
    next_chunk_id: Optional[str] = Field(
        None,
        description="ID of next chunk in sequence"
    )
    
    parent_section_id: Optional[str] = Field(
        None,
        description="ID of parent section or document"
    )
    
    # Semantic relationships
    related_chunk_ids: List[str] = Field(
        default_factory=list,
        description="IDs of semantically related chunks"
    )
    
    cross_references: List[str] = Field(
        default_factory=list,
        description="Cross-referenced document or chunk IDs"
    )
    
    # Student context
    student_id: Optional[str] = Field(
        None,
        description="Student ID for student-specific content"
    )
    
    same_student_docs: List[str] = Field(
        default_factory=list,
        description="Other document IDs for same student"
    )
    
    # Assessment relationships
    baseline_assessment_id: Optional[str] = Field(
        None,
        description="ID of baseline assessment for progress tracking"
    )
    
    follow_up_assessment_ids: List[str] = Field(
        default_factory=list,
        description="IDs of follow-up assessments"
    )


class DocumentLevelMetadata(BaseModel):
    """Comprehensive metadata for entire documents"""
    
    model_config = ConfigDict(extra='forbid', validate_assignment=True)
    
    # Identity fields
    document_id: str = Field(..., min_length=1, description="Unique document identifier")
    document_hash: str = Field(..., min_length=1, description="Content hash for deduplication")
    source_path: str = Field(..., min_length=1, description="Original file path")
    filename: str = Field(..., min_length=1, description="Original filename")
    
    # Classification fields
    document_type: DocumentType = Field(..., description="Primary document type")
    document_subtype: Optional[str] = Field(None, description="Document subtype if applicable")
    assessment_type: Optional[AssessmentType] = Field(None, description="Assessment type if applicable")
    language: str = Field(default="en", description="Document language")
    
    # File metadata
    file_size_bytes: int = Field(..., ge=0, description="File size in bytes")
    page_count: Optional[int] = Field(None, ge=1, description="Number of pages")
    word_count: Optional[int] = Field(None, ge=0, description="Estimated word count")
    
    # Temporal information
    temporal_metadata: TemporalMetadata = Field(..., description="Temporal information")
    
    # Quality assessment
    quality_metrics: QualityMetrics = Field(..., description="Quality assessment metrics")
    
    # Processing metadata
    total_chunks: int = Field(..., ge=1, description="Total number of chunks created")
    processing_version: str = Field(default="1.0", description="Processing pipeline version")
    extraction_method: str = Field(..., description="Method used for text extraction")
    
    # Educational context
    student_identifiers: List[str] = Field(
        default_factory=list,
        description="Student IDs mentioned in document"
    )
    
    assessor_information: Optional[Dict[str, str]] = Field(
        default_factory=dict,
        description="Information about assessor/author"
    )
    
    school_context: Optional[Dict[str, str]] = Field(
        default_factory=dict,
        description="School district, school name, etc."
    )


class ChunkLevelMetadata(BaseModel):
    """Enhanced metadata for individual content chunks"""
    
    model_config = ConfigDict(extra='forbid', validate_assignment=True)
    
    # Identity and position
    chunk_id: str = Field(..., min_length=1, description="Unique chunk identifier")
    document_id: str = Field(..., min_length=1, description="Parent document ID")
    chunk_index: int = Field(..., ge=0, description="Position in document")
    
    # Content information
    content_length: int = Field(..., ge=0, description="Length of chunk content")
    start_position: Optional[int] = Field(None, description="Start position in original document")
    end_position: Optional[int] = Field(None, description="End position in original document")
    
    # Context preservation
    preceding_context: Optional[str] = Field(
        None,
        max_length=500,
        description="Preview of preceding content"
    )
    
    following_context: Optional[str] = Field(
        None,
        max_length=500,
        description="Preview of following content"
    )
    
    # Section classification
    section_type: Optional[IEPSection] = Field(
        None,
        description="IEP section this chunk belongs to"
    )
    
    section_hierarchy: List[str] = Field(
        default_factory=list,
        description="Hierarchical section path (e.g., ['Goals', 'Reading', 'Comprehension'])"
    )
    
    # Semantic information
    semantic_metadata: SemanticMetadata = Field(..., description="Semantic classification")
    
    # IEP section relevance
    iep_section_relevance: IEPSectionRelevance = Field(
        ...,
        description="Relevance scores for each IEP section"
    )
    
    # Quality and relationships
    quality_metrics: QualityMetrics = Field(..., description="Chunk-specific quality metrics")
    relationships: RelationshipMetadata = Field(..., description="Relationship information")
    
    # Extracted data
    extracted_scores: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Assessment scores extracted from this chunk"
    )
    
    extracted_recommendations: List[str] = Field(
        default_factory=list,
        description="Educational recommendations extracted"
    )
    
    extracted_goals: List[str] = Field(
        default_factory=list,
        description="Educational goals extracted"
    )
    
    # Processing metadata
    embedding_model: str = Field(..., description="Model used for embeddings")
    embedding_version: str = Field(..., description="Version of embedding model")
    processing_timestamp: datetime = Field(..., description="When this chunk was processed")
    
    # Update tracking
    last_updated: datetime = Field(..., description="Last update timestamp")
    update_reason: Optional[str] = Field(None, description="Reason for last update")


class SearchContext(BaseModel):
    """Context information for enhanced search and retrieval"""
    
    model_config = ConfigDict(extra='forbid', validate_assignment=True)
    
    # Query context
    target_iep_section: Optional[IEPSection] = Field(
        None,
        description="Specific IEP section being generated"
    )
    
    student_context: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Student-specific context for personalization"
    )
    
    # Filtering criteria
    document_types: List[DocumentType] = Field(
        default_factory=list,
        description="Allowed document types"
    )
    
    assessment_types: List[AssessmentType] = Field(
        default_factory=list,
        description="Relevant assessment types"
    )
    
    date_range: Optional[Dict[str, datetime]] = Field(
        None,
        description="Date range for temporal filtering"
    )
    
    quality_threshold: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Minimum quality score for results"
    )
    
    # Search preferences
    max_results: int = Field(default=10, ge=1, le=100, description="Maximum results to return")
    include_low_relevance: bool = Field(default=False, description="Include low relevance results")
    boost_recent: bool = Field(default=True, description="Boost recent documents")


class EnhancedSearchResult(BaseModel):
    """Enhanced search result with metadata and explanation"""
    
    model_config = ConfigDict(extra='forbid', validate_assignment=True)
    
    # Core result
    chunk_id: str = Field(..., description="Matched chunk ID")
    content: str = Field(..., description="Chunk content")
    
    # Scoring information
    similarity_score: float = Field(..., ge=0.0, le=1.0, description="Vector similarity score")
    relevance_score: float = Field(..., ge=0.0, le=1.0, description="Computed relevance score")
    quality_score: float = Field(..., ge=0.0, le=1.0, description="Content quality score")
    final_score: float = Field(..., ge=0.0, le=1.0, description="Final weighted score")
    
    # Metadata
    chunk_metadata: ChunkLevelMetadata = Field(..., description="Complete chunk metadata")
    
    # Match explanation
    match_highlights: List[str] = Field(
        default_factory=list,
        description="Highlighted matching terms"
    )
    
    relevance_explanation: str = Field(
        ...,
        description="Why this chunk is relevant"
    )
    
    source_attribution: Dict[str, str] = Field(
        default_factory=dict,
        description="Source document attribution"
    )


class MetadataValidationReport(BaseModel):
    """Validation report for metadata quality"""
    
    model_config = ConfigDict(extra='forbid', validate_assignment=True)
    
    validation_timestamp: datetime = Field(..., description="When validation was performed")
    is_valid: bool = Field(..., description="Overall validation status")
    
    # Validation results by category
    schema_validation: bool = Field(..., description="Pydantic schema validation passed")
    consistency_validation: bool = Field(..., description="Cross-field consistency checks")
    quality_validation: bool = Field(..., description="Quality thresholds met")
    relationship_validation: bool = Field(..., description="Relationships are valid")
    
    # Issues found
    validation_errors: List[str] = Field(
        default_factory=list,
        description="Validation errors found"
    )
    
    validation_warnings: List[str] = Field(
        default_factory=list,
        description="Validation warnings"
    )
    
    # Recommendations
    improvement_suggestions: List[str] = Field(
        default_factory=list,
        description="Suggestions for improvement"
    )
    
    # Summary statistics
    total_fields_validated: int = Field(..., ge=0, description="Total fields checked")
    fields_passed: int = Field(..., ge=0, description="Fields that passed validation")
    fields_failed: int = Field(..., ge=0, description="Fields that failed validation")
    
    @property
    def validation_score(self) -> float:
        """Calculate overall validation score"""
        if self.total_fields_validated == 0:
            return 0.0
        return self.fields_passed / self.total_fields_validated


# Export all schemas for easy import
__all__ = [
    'DocumentType',
    'AssessmentType', 
    'IEPSection',
    'QualityMetrics',
    'TemporalMetadata',
    'SemanticMetadata',
    'IEPSectionRelevance',
    'RelationshipMetadata',
    'DocumentLevelMetadata',
    'ChunkLevelMetadata',
    'SearchContext',
    'EnhancedSearchResult',
    'MetadataValidationReport'
]