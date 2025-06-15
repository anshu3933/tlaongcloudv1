"""Template management API endpoints"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from uuid import UUID
import logging
import math

from ..database import get_db
from ..repositories.template_repository import TemplateRepository
from ..services.user_adapter import UserAdapter
from ..schemas.template_schemas import (
    IEPTemplateCreate, IEPTemplateUpdate, IEPTemplateResponse, IEPTemplateSearch,
    DisabilityTypeCreate, DisabilityTypeResponse
)
from ..schemas.common_schemas import PaginatedResponse, SuccessResponse
from common.src.config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/templates", tags=["Templates"])
settings = get_settings()

# Initialize user adapter
user_adapter = UserAdapter(
    auth_service_url=getattr(settings, 'auth_service_url', 'http://localhost:8080'),
    cache_ttl_seconds=300
)

async def get_template_repository(db: AsyncSession = Depends(get_db)) -> TemplateRepository:
    """Dependency to get Template repository"""
    return TemplateRepository(db)

async def enrich_template_response(template_data: dict) -> IEPTemplateResponse:
    """Enrich template data with user information"""
    enriched_data = template_data.copy()
    
    # Resolve creator user
    if template_data.get("created_by_auth_id"):
        user = await user_adapter.resolve_user(template_data["created_by_auth_id"])
        enriched_data["created_by_user"] = user
    
    return IEPTemplateResponse(**enriched_data)

@router.post("", response_model=IEPTemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_template(
    template_data: IEPTemplateCreate,
    current_user_id: int = Query(..., description="Current user's auth ID"),
    template_repo: TemplateRepository = Depends(get_template_repository)
):
    """Create a new IEP template"""
    try:
        # Verify disability type exists if provided
        if template_data.disability_type_id:
            disability = await template_repo.get_disability_type(template_data.disability_type_id)
            if not disability:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Disability type {template_data.disability_type_id} not found"
                )
        
        # Prepare template data
        template_dict = template_data.model_dump()
        template_dict["created_by_auth_id"] = current_user_id
        
        # Create template
        created_template = await template_repo.create_template(template_dict)
        
        # Enrich and return response
        return await enrich_template_response(created_template)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating template: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create template"
        )

@router.get("/{template_id}", response_model=IEPTemplateResponse)
async def get_template(
    template_id: UUID,
    template_repo: TemplateRepository = Depends(get_template_repository)
):
    """Get template by ID"""
    template = await template_repo.get_template(template_id)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template {template_id} not found"
        )
    
    return await enrich_template_response(template)

@router.put("/{template_id}", response_model=IEPTemplateResponse)
async def update_template(
    template_id: UUID,
    template_updates: IEPTemplateUpdate,
    template_repo: TemplateRepository = Depends(get_template_repository)
):
    """Update an existing template"""
    # Check if template exists
    existing_template = await template_repo.get_template(template_id)
    if not existing_template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template {template_id} not found"
        )
    
    # Verify disability type exists if being updated
    if template_updates.disability_type_id:
        disability = await template_repo.get_disability_type(template_updates.disability_type_id)
        if not disability:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Disability type {template_updates.disability_type_id} not found"
            )
    
    # Update template
    updates_dict = template_updates.model_dump(exclude_unset=True)
    updated_template = await template_repo.update_template(template_id, updates_dict)
    
    if not updated_template:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update template"
        )
    
    return await enrich_template_response(updated_template)

@router.delete("/{template_id}", response_model=SuccessResponse)
async def delete_template(
    template_id: UUID,
    template_repo: TemplateRepository = Depends(get_template_repository)
):
    """Soft delete a template"""
    success = await template_repo.delete_template(template_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template {template_id} not found"
        )
    
    return SuccessResponse(
        message=f"Template {template_id} deactivated successfully"
    )

@router.get("", response_model=PaginatedResponse[IEPTemplateResponse])
async def list_templates(
    disability_type_id: Optional[UUID] = Query(None, description="Filter by disability type"),
    grade_level: Optional[str] = Query(None, description="Filter by grade level"),
    is_active: bool = Query(True, description="Filter by active status"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
    template_repo: TemplateRepository = Depends(get_template_repository)
):
    """List templates with filtering and pagination"""
    try:
        # Calculate offset
        offset = (page - 1) * size
        
        # Get templates
        templates = await template_repo.list_templates(
            disability_type_id=disability_type_id,
            grade_level=grade_level,
            is_active=is_active,
            limit=size,
            offset=offset
        )
        
        # For pagination, get total count (simplified approach)
        all_templates = await template_repo.list_templates(
            disability_type_id=disability_type_id,
            grade_level=grade_level,
            is_active=is_active,
            limit=1000,
            offset=0
        )
        total = len(all_templates)
        
        # Enrich responses
        enriched_templates = []
        for template in templates:
            enriched_template = await enrich_template_response(template)
            enriched_templates.append(enriched_template)
        
        # Calculate pagination info
        pages = math.ceil(total / size) if total > 0 else 1
        has_next = page < pages
        has_prev = page > 1
        
        return PaginatedResponse[IEPTemplateResponse](
            items=enriched_templates,
            total=total,
            page=page,
            size=size,
            pages=pages,
            has_next=has_next,
            has_prev=has_prev
        )
        
    except Exception as e:
        logger.error(f"Error listing templates: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve templates"
        )

@router.get("/disability/{disability_type_id}/grade/{grade_level}", response_model=List[IEPTemplateResponse])
async def get_templates_for_disability_and_grade(
    disability_type_id: UUID,
    grade_level: str,
    template_repo: TemplateRepository = Depends(get_template_repository)
):
    """Get templates for specific disability type and grade level"""
    try:
        # Verify disability type exists
        disability = await template_repo.get_disability_type(disability_type_id)
        if not disability:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Disability type {disability_type_id} not found"
            )
        
        templates = await template_repo.get_templates_by_disability_and_grade(
            disability_type_id, grade_level
        )
        
        # Enrich responses
        enriched_templates = []
        for template in templates:
            enriched_template = await enrich_template_response(template)
            enriched_templates.append(enriched_template)
        
        return enriched_templates
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting templates for disability/grade: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve templates"
        )

# Disability Type endpoints
@router.post("/disability-types", response_model=DisabilityTypeResponse, status_code=status.HTTP_201_CREATED)
async def create_disability_type(
    disability_data: DisabilityTypeCreate,
    template_repo: TemplateRepository = Depends(get_template_repository)
):
    """Create a new disability type"""
    try:
        # Check if code already exists
        existing = await template_repo.get_disability_type_by_code(disability_data.code)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Disability type with code {disability_data.code} already exists"
            )
        
        # Create disability type
        disability_dict = disability_data.model_dump()
        created_disability = await template_repo.create_disability_type(disability_dict)
        
        return DisabilityTypeResponse(**created_disability)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating disability type: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create disability type"
        )

@router.get("/disability-types", response_model=List[DisabilityTypeResponse])
async def list_disability_types(
    is_active: bool = Query(True, description="Filter by active status"),
    template_repo: TemplateRepository = Depends(get_template_repository)
):
    """List all disability types"""
    try:
        disabilities = await template_repo.list_disability_types(is_active=is_active)
        return [DisabilityTypeResponse(**disability) for disability in disabilities]
        
    except Exception as e:
        logger.error(f"Error listing disability types: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve disability types"
        )

@router.get("/disability-types/{disability_id}", response_model=DisabilityTypeResponse)
async def get_disability_type(
    disability_id: UUID,
    template_repo: TemplateRepository = Depends(get_template_repository)
):
    """Get disability type by ID"""
    disability = await template_repo.get_disability_type(disability_id)
    if not disability:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Disability type {disability_id} not found"
        )
    
    return DisabilityTypeResponse(**disability)

@router.get("/disability-types/by-code/{code}", response_model=DisabilityTypeResponse)
async def get_disability_type_by_code(
    code: str,
    template_repo: TemplateRepository = Depends(get_template_repository)
):
    """Get disability type by code"""
    disability = await template_repo.get_disability_type_by_code(code)
    if not disability:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Disability type with code {code} not found"
        )
    
    return DisabilityTypeResponse(**disability)