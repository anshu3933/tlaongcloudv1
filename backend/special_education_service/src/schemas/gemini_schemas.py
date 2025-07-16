"""Strict response validation schemas for Gemini with Pydantic v2"""

from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict
from typing import List, Dict, Optional, Any
from datetime import datetime
import re


class StrictGeminiModel(BaseModel):
    """Base model with strict validation for Gemini responses"""
    
    model_config = ConfigDict(
        extra='forbid',  # Reject any extra fields
        str_strip_whitespace=True,
        validate_assignment=True,
        use_enum_values=True,
        str_max_length=50000  # INCREASED from 10000 to allow comprehensive IEP content
    )


class StudentInfoSchema(StrictGeminiModel):
    name: str = Field(..., min_length=1, max_length=100)
    dob: str = Field(..., pattern=r'^(\d{4}-\d{2}-\d{2}|To be provided)$')
    grade: str = Field(..., min_length=1, max_length=20, alias="class")
    date_of_iep: str = Field(..., pattern=r'^\d{4}-\d{2}-\d{2}$')


class OralLanguageSchema(StrictGeminiModel):
    receptive: str = Field(..., min_length=10, max_length=5000)  # INCREASED for comprehensive content
    expressive: str = Field(..., min_length=10, max_length=5000)  # INCREASED for comprehensive content
    recommendations: str = Field(..., min_length=10, max_length=8000)  # INCREASED for comprehensive content


class ReadingSchema(StrictGeminiModel):
    familiar: str = Field(..., min_length=10, max_length=5000)  # INCREASED for comprehensive content
    unfamiliar: str = Field(..., min_length=10, max_length=5000)  # INCREASED for comprehensive content
    comprehension: str = Field(..., min_length=10, max_length=5000)  # INCREASED for comprehensive content


class SpellingSchema(StrictGeminiModel):
    goals: str = Field(..., min_length=10, max_length=5000)  # INCREASED for comprehensive content


class WritingSchema(StrictGeminiModel):
    recommendations: str = Field(..., min_length=10, max_length=8000)  # INCREASED for comprehensive content


class ConceptSchema(StrictGeminiModel):
    recommendations: str = Field(..., min_length=10, max_length=8000)  # INCREASED for comprehensive content


class MathSchema(StrictGeminiModel):
    goals: str = Field(..., min_length=10, max_length=5000)  # INCREASED for comprehensive content
    recommendations: str = Field(..., min_length=10, max_length=8000)  # INCREASED for comprehensive content


class ServiceSchema(StrictGeminiModel):
    special_education: str = Field(..., min_length=10, max_length=5000)  # INCREASED for comprehensive content
    related_services: List[str] = Field(default_factory=list, max_length=20)  # INCREASED for more services
    accommodations: List[str] = Field(..., min_length=1, max_length=50)  # INCREASED for more accommodations
    frequency: str = Field(..., min_length=10, max_length=2000)  # INCREASED for detailed frequency descriptions
    
    @field_validator('accommodations', 'related_services')
    @classmethod
    def validate_service_items(cls, v: List[str]) -> List[str]:
        """Validate each service item"""
        for item in v:
            if not isinstance(item, str) or len(item) < 5 or len(item) > 2000:  # INCREASED from 200 to 2000
                raise ValueError(f'Service item must be 5-2000 characters: {item[:50]}...')
        return v


class GenerationMetadataSchema(StrictGeminiModel):
    generated_at: str
    schema_version: str = "1.0"
    model: str = "gemini-2.5-flash"


class GeminiIEPResponse(StrictGeminiModel):
    """Complete IEP response schema with strict validation"""
    
    student_info: StudentInfoSchema
    long_term_goal: str = Field(..., min_length=20, max_length=8000)  # INCREASED for comprehensive content
    short_term_goals: str = Field(..., min_length=20, max_length=10000)  # INCREASED for comprehensive content
    
    # Academic sections
    oral_language: OralLanguageSchema
    reading: ReadingSchema
    spelling: SpellingSchema
    writing: WritingSchema
    concept: ConceptSchema
    math: MathSchema
    
    # Support services
    services: ServiceSchema
    
    # Metadata
    generation_metadata: GenerationMetadataSchema
    
    @field_validator('long_term_goal', 'short_term_goals')
    @classmethod
    def validate_goals_content(cls, v: str) -> str:
        """Ensure goals contain actionable language"""
        action_verbs = ['will', 'shall', 'demonstrate', 'achieve', 'complete', 'improve', 'develop']
        if not any(verb in v.lower() for verb in action_verbs):
            raise ValueError(f'Goal must contain actionable language: {v[:50]}...')
        return v