"""Pydantic schemas for IEP operations"""
from pydantic import BaseModel, Field, ConfigDict, validator
from typing import Optional, List, Dict, Any
from datetime import date, datetime
from uuid import UUID
from enum import Enum

from .common_schemas import UserInfo
from .student_schemas import StudentResponse

class IEPStatusEnum(str, Enum):
    DRAFT = "draft"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    ACTIVE = "active"
    EXPIRED = "expired"
    RETURNED = "returned"

class GoalStatusEnum(str, Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    MASTERED = "mastered"
    DISCONTINUED = "discontinued"

class IEPGoalBase(BaseModel):
    """Base IEP goal fields"""
    domain: str = Field(..., max_length=100, description="Goal domain (Academic, Behavioral, etc.)")
    goal_text: str = Field(..., min_length=10, description="Complete goal statement")
    baseline: Optional[str] = Field(None, description="Current performance baseline")
    target_criteria: str = Field(..., description="Measurable target criteria")
    measurement_method: str = Field(..., description="How progress will be measured")
    measurement_frequency: Optional[str] = Field(None, description="How often progress is measured")
    target_date: Optional[date] = None
    start_date: Optional[date] = None

class IEPGoalCreate(IEPGoalBase):
    """Schema for creating IEP goals"""
    pass

class IEPGoalUpdate(BaseModel):
    """Schema for updating IEP goals"""
    domain: Optional[str] = Field(None, max_length=100)
    goal_text: Optional[str] = Field(None, min_length=10)
    baseline: Optional[str] = None
    target_criteria: Optional[str] = None
    measurement_method: Optional[str] = None
    measurement_frequency: Optional[str] = None
    target_date: Optional[date] = None
    start_date: Optional[date] = None
    progress_status: Optional[GoalStatusEnum] = None

class ProgressNote(BaseModel):
    """Progress note structure"""
    date: str
    note: str
    status: str

class IEPGoalResponse(IEPGoalBase):
    """Schema for IEP goal responses"""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    iep_id: UUID
    progress_status: GoalStatusEnum
    progress_notes: List[ProgressNote] = Field(default_factory=list)
    created_at: datetime
    updated_at: Optional[datetime] = None

class IEPBase(BaseModel):
    """Base IEP fields"""
    academic_year: str = Field(..., pattern=r"^\d{4}-\d{4}$", description="Academic year (e.g., '2023-2024')")
    content: Dict[str, Any] = Field(default_factory=dict, description="IEP content structure")
    meeting_date: Optional[date] = None
    effective_date: Optional[date] = None
    review_date: Optional[date] = None

class IEPCreate(IEPBase):
    """Schema for creating a new IEP"""
    student_id: UUID
    template_id: Optional[UUID] = None
    goals: List[IEPGoalCreate] = Field(default_factory=list, description="Initial goals")
    
    @validator('goals')
    def validate_goals_not_empty_if_provided(cls, v):
        """Ensure goals list is valid if provided"""
        return [goal for goal in v if goal.goal_text.strip()]

class IEPCreateWithRAG(IEPBase):
    """Schema for creating a new IEP with RAG generation (requires template)"""
    student_id: UUID
    template_id: UUID  # Required for RAG generation
    goals: List[IEPGoalCreate] = Field(default_factory=list, description="Initial goals")
    
    @validator('goals')
    def validate_goals_not_empty_if_provided(cls, v):
        """Ensure goals list is valid if provided"""
        return [goal for goal in v if goal.goal_text.strip()]

class IEPUpdate(BaseModel):
    """Schema for updating an IEP"""
    academic_year: Optional[str] = Field(None, pattern=r"^\d{4}-\d{4}$")
    content: Optional[Dict[str, Any]] = None
    meeting_date: Optional[date] = None
    effective_date: Optional[date] = None
    review_date: Optional[date] = None
    status: Optional[IEPStatusEnum] = None

class IEPResponse(IEPBase):
    """Schema for IEP responses"""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    student_id: UUID
    template_id: Optional[UUID] = None
    status: IEPStatusEnum
    version: int
    parent_version_id: Optional[UUID] = None
    created_by_auth_id: int
    created_at: datetime
    approved_at: Optional[datetime] = None
    approved_by_auth_id: Optional[int] = None
    goals: List[IEPGoalResponse] = Field(default_factory=list)
    
    # Enriched fields
    student: Optional[StudentResponse] = None
    created_by_user: Optional[UserInfo] = None
    approved_by_user: Optional[UserInfo] = None

class IEPSubmitForApproval(BaseModel):
    """Schema for submitting IEP for approval"""
    comments: Optional[str] = Field(None, max_length=1000, description="Optional submission comments")

class IEPGenerateSection(BaseModel):
    """Schema for generating IEP sections"""
    section_name: str = Field(..., description="Name of section to generate")
    additional_context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional context for generation")

class IEPVersionHistory(BaseModel):
    """IEP version history entry"""
    id: UUID
    version: int
    status: IEPStatusEnum
    created_by_auth_id: int
    created_at: datetime
    created_by_user: Optional[UserInfo] = None

class IEPSearch(BaseModel):
    """Schema for IEP search parameters"""
    student_id: Optional[UUID] = None
    academic_year: Optional[str] = None
    status: Optional[IEPStatusEnum] = None
    created_by_auth_id: Optional[int] = None
    page: int = Field(1, ge=1)
    size: int = Field(20, ge=1, le=100)

class GoalProgressUpdate(BaseModel):
    """Schema for updating goal progress"""
    progress_status: GoalStatusEnum
    progress_note: Optional[str] = Field(None, max_length=500, description="Progress note")