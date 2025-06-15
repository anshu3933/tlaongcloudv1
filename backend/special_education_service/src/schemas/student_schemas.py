"""Pydantic schemas for Student operations"""
from pydantic import BaseModel, Field, ConfigDict, validator
from typing import Optional, List
from datetime import date, datetime
from uuid import UUID

from .common_schemas import UserInfo

class StudentBase(BaseModel):
    """Base student fields"""
    student_id: str = Field(..., min_length=1, max_length=50, description="School student ID")
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    middle_name: Optional[str] = Field(None, max_length=100)
    date_of_birth: date
    grade_level: str = Field(..., max_length=20)
    disability_codes: List[str] = Field(default_factory=list, description="List of disability type codes")
    school_district: Optional[str] = Field(None, max_length=200)
    school_name: Optional[str] = Field(None, max_length=200)
    enrollment_date: Optional[date] = None

class StudentCreate(StudentBase):
    """Schema for creating a new student"""
    case_manager_auth_id: Optional[int] = Field(None, description="Auth service ID of case manager")
    primary_teacher_auth_id: Optional[int] = Field(None, description="Auth service ID of primary teacher")
    parent_guardian_auth_ids: List[int] = Field(default_factory=list, description="Auth service IDs of parents/guardians")
    
    @validator('disability_codes')
    def validate_disability_codes(cls, v):
        """Validate disability codes are not empty strings"""
        return [code.strip().upper() for code in v if code.strip()]

class StudentUpdate(BaseModel):
    """Schema for updating a student"""
    student_id: Optional[str] = Field(None, min_length=1, max_length=50)
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    middle_name: Optional[str] = Field(None, max_length=100)
    date_of_birth: Optional[date] = None
    grade_level: Optional[str] = Field(None, max_length=20)
    disability_codes: Optional[List[str]] = None
    case_manager_auth_id: Optional[int] = None
    primary_teacher_auth_id: Optional[int] = None
    parent_guardian_auth_ids: Optional[List[int]] = None
    school_district: Optional[str] = Field(None, max_length=200)
    school_name: Optional[str] = Field(None, max_length=200)
    enrollment_date: Optional[date] = None
    is_active: Optional[bool] = None

class ActiveIEPInfo(BaseModel):
    """Active IEP information"""
    id: UUID
    academic_year: str
    status: str
    effective_date: Optional[date] = None
    review_date: Optional[date] = None

class StudentResponse(StudentBase):
    """Schema for student responses"""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    full_name: str
    case_manager_auth_id: Optional[int] = None
    primary_teacher_auth_id: Optional[int] = None
    parent_guardian_auth_ids: List[int] = Field(default_factory=list)
    active_iep_id: Optional[UUID] = None
    is_active: bool = True
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # Enriched fields (populated by user adapter)
    case_manager_user: Optional[UserInfo] = None
    primary_teacher_user: Optional[UserInfo] = None
    parent_guardian_users: List[UserInfo] = Field(default_factory=list)
    active_iep: Optional[ActiveIEPInfo] = None

class StudentSearch(BaseModel):
    """Schema for student search parameters"""
    search_term: Optional[str] = Field(None, min_length=1, description="Search by name or student ID")
    grade_level: Optional[str] = None
    disability_code: Optional[str] = None
    case_manager_auth_id: Optional[int] = None
    is_active: Optional[bool] = True
    page: int = Field(1, ge=1)
    size: int = Field(20, ge=1, le=100)

class StudentCaseloadSummary(BaseModel):
    """Caseload summary for a case manager"""
    total_students: int
    active_ieps: int
    students_by_grade: dict[str, int]
    case_manager_auth_id: int
    case_manager_user: Optional[UserInfo] = None