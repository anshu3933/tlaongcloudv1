"""Pydantic schemas for Template operations"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID

from .common_schemas import UserInfo

class IEPTemplateBase(BaseModel):
    """Base IEP template fields"""
    name: str = Field(..., min_length=1, max_length=200, description="Template name")
    grade_level: Optional[str] = Field(None, max_length=20, description="Target grade level")
    sections: Dict[str, Any] = Field(..., description="Template structure and sections")
    default_goals: List[Dict[str, Any]] = Field(default_factory=list, description="Pre-defined goal templates")

class IEPTemplateCreate(IEPTemplateBase):
    """Schema for creating IEP templates"""
    disability_type_id: Optional[UUID] = Field(None, description="Associated disability type")

class IEPTemplateUpdate(BaseModel):
    """Schema for updating IEP templates"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    disability_type_id: Optional[UUID] = None
    grade_level: Optional[str] = Field(None, max_length=20)
    sections: Optional[Dict[str, Any]] = None
    default_goals: Optional[List[Dict[str, Any]]] = None
    is_active: Optional[bool] = None

class DisabilityTypeInfo(BaseModel):
    """Disability type information"""
    id: UUID
    code: str
    name: str
    description: Optional[str] = None
    federal_category: Optional[str] = None

class IEPTemplateResponse(IEPTemplateBase):
    """Schema for IEP template responses"""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    disability_type_id: Optional[UUID] = None
    version: int
    is_active: bool
    created_by_auth_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # Enriched fields
    disability_type: Optional[DisabilityTypeInfo] = None
    created_by_user: Optional[UserInfo] = None

class IEPTemplateSearch(BaseModel):
    """Schema for template search parameters"""
    disability_type_id: Optional[UUID] = None
    grade_level: Optional[str] = None
    is_active: Optional[bool] = True
    page: int = Field(1, ge=1)
    size: int = Field(20, ge=1, le=100)

class DisabilityTypeCreate(BaseModel):
    """Schema for creating disability types"""
    code: str = Field(..., min_length=1, max_length=20, description="Disability code")
    name: str = Field(..., min_length=1, max_length=100, description="Disability name")
    description: Optional[str] = None
    federal_category: Optional[str] = Field(None, max_length=100)
    state_category: Optional[str] = Field(None, max_length=100)
    accommodation_defaults: Optional[Dict[str, Any]] = Field(default_factory=dict)

class DisabilityTypeResponse(BaseModel):
    """Schema for disability type responses"""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    code: str
    name: str
    description: Optional[str] = None
    federal_category: Optional[str] = None
    state_category: Optional[str] = None
    accommodation_defaults: Optional[Dict[str, Any]] = None
    is_active: bool
    created_at: datetime