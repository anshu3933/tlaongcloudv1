"""Repository layer for Template operations"""
from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_
from sqlalchemy.orm import selectinload

from ..models.special_education_models import (
    IEPTemplate, DisabilityType
)

class TemplateRepository:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create_template(self, template_data: dict) -> dict:
        """Create new IEP template"""
        template = IEPTemplate(
            name=template_data["name"],
            disability_type_id=template_data.get("disability_type_id"),
            grade_level=template_data.get("grade_level"),
            sections=template_data["sections"],
            default_goals=template_data.get("default_goals", []),
            version=template_data.get("version", 1),
            created_by_auth_id=template_data["created_by_auth_id"]
        )
        
        self.session.add(template)
        await self.session.commit()
        await self.session.refresh(template)
        
        # Create response dict manually to avoid any potential field access issues
        response_data = {
            "id": str(template.id),
            "name": template_data["name"],
            "disability_type_id": str(template_data.get("disability_type_id")) if template_data.get("disability_type_id") else None,
            "grade_level": template_data.get("grade_level"),
            "sections": template_data["sections"],
            "default_goals": template_data.get("default_goals", []),
            "version": template_data.get("version", 1),
            "is_active": True,
            "created_by_auth_id": template_data["created_by_auth_id"],
            "created_at": template.created_at.isoformat() if hasattr(template, 'created_at') and template.created_at else None,
            "updated_at": None,
            "disability_type": None
        }
        
        return response_data
    
    async def get_template(self, template_id: UUID) -> Optional[dict]:
        """Get template by ID with eager loading"""
        query = select(IEPTemplate).where(IEPTemplate.id == template_id)
        query = query.options(selectinload(IEPTemplate.disability_type))
        
        result = await self.session.execute(query)
        template = result.scalar_one_or_none()
        
        if not template:
            return None
        
        return await self._template_to_dict_safe(template)
    
    async def update_template(self, template_id: UUID, updates: dict) -> Optional[dict]:
        """Update template"""
        template = await self.session.get(IEPTemplate, template_id)
        if not template:
            return None
        
        # Update fields
        for field, value in updates.items():
            if hasattr(template, field) and field not in ["id", "created_at"]:
                setattr(template, field, value)
        
        await self.session.commit()
        await self.session.refresh(template)
        
        return await self._template_to_dict(template)
    
    async def delete_template(self, template_id: UUID) -> bool:
        """Soft delete template"""
        result = await self.session.execute(
            update(IEPTemplate)
            .where(IEPTemplate.id == template_id)
            .values(is_active=False)
        )
        await self.session.commit()
        return result.rowcount > 0
    
    async def list_templates(
        self,
        disability_type_id: Optional[UUID] = None,
        grade_level: Optional[str] = None,
        is_active: bool = True,
        limit: int = 100,
        offset: int = 0
    ) -> List[dict]:
        """List templates with filtering"""
        query = select(IEPTemplate).where(IEPTemplate.is_active == is_active)
        
        if disability_type_id:
            query = query.where(IEPTemplate.disability_type_id == disability_type_id)
        
        if grade_level:
            query = query.where(IEPTemplate.grade_level == grade_level)
        
        query = query.options(selectinload(IEPTemplate.disability_type))
        query = query.order_by(IEPTemplate.name)
        query = query.offset(offset).limit(limit)
        
        result = await self.session.execute(query)
        templates = result.scalars().all()
        
        return [await self._template_to_dict_safe(template) for template in templates]
    
    async def get_templates_by_disability_and_grade(
        self,
        disability_type_id: UUID,
        grade_level: str
    ) -> List[dict]:
        """Get templates for specific disability type and grade"""
        query = select(IEPTemplate).where(
            and_(
                IEPTemplate.disability_type_id == disability_type_id,
                IEPTemplate.grade_level == grade_level,
                IEPTemplate.is_active == True
            )
        ).options(selectinload(IEPTemplate.disability_type))
        
        result = await self.session.execute(query)
        templates = result.scalars().all()
        
        return [await self._template_to_dict_safe(template) for template in templates]
    
    async def create_disability_type(self, disability_data: dict) -> dict:
        """Create new disability type"""
        disability = DisabilityType(
            code=disability_data["code"],
            name=disability_data["name"],
            description=disability_data.get("description"),
            federal_category=disability_data.get("federal_category"),
            state_category=disability_data.get("state_category"),
            accommodation_defaults=disability_data.get("accommodation_defaults", {})
        )
        
        self.session.add(disability)
        await self.session.commit()
        await self.session.refresh(disability)
        
        return await self._disability_to_dict(disability)
    
    async def get_disability_type(self, disability_id: UUID) -> Optional[dict]:
        """Get disability type by ID"""
        disability = await self.session.get(DisabilityType, disability_id)
        if not disability:
            return None
        
        return await self._disability_to_dict(disability)
    
    async def get_disability_type_by_code(self, code: str) -> Optional[dict]:
        """Get disability type by code"""
        result = await self.session.execute(
            select(DisabilityType).where(DisabilityType.code == code.upper())
        )
        disability = result.scalar_one_or_none()
        
        if not disability:
            return None
        
        return await self._disability_to_dict(disability)
    
    async def list_disability_types(self, is_active: bool = True) -> List[dict]:
        """List all disability types"""
        query = select(DisabilityType).where(DisabilityType.is_active == is_active)
        query = query.order_by(DisabilityType.name)
        
        result = await self.session.execute(query)
        disabilities = result.scalars().all()
        
        return [await self._disability_to_dict(disability) for disability in disabilities]
    
    async def _template_to_dict(self, template: IEPTemplate) -> dict:
        """Convert IEPTemplate model to dictionary"""
        data = {
            "id": str(template.id),
            "name": template.name,
            "disability_type_id": str(template.disability_type_id) if template.disability_type_id else None,
            "grade_level": template.grade_level,
            "sections": template.sections,
            "default_goals": template.default_goals or [],
            "version": template.version,
            "is_active": template.is_active,
            "created_by_auth_id": template.created_by_auth_id,
            "created_at": template.created_at.isoformat() if template.created_at else None,
            "updated_at": template.updated_at.isoformat() if template.updated_at else None
        }
        
        # Add disability type info if loaded
        if hasattr(template, 'disability_type') and template.disability_type:
            data["disability_type"] = {
                "id": str(template.disability_type.id),
                "code": template.disability_type.code,
                "name": template.disability_type.name,
                "description": template.disability_type.description,
                "federal_category": template.disability_type.federal_category
            }
        
        return data
    
    def _template_to_dict_safe(self, template: IEPTemplate) -> dict:
        """Convert IEPTemplate to dictionary safely - no relationship access"""
        return {
            "id": str(template.id),
            "name": template.name,
            "disability_type_id": str(template.disability_type_id) if template.disability_type_id else None,
            "grade_level": template.grade_level,
            "sections": template.sections,
            "default_goals": template.default_goals or [],
            "version": template.version,
            "is_active": template.is_active,
            "created_by_auth_id": template.created_by_auth_id,
            "created_at": template.created_at.isoformat() if template.created_at else None,
            "updated_at": template.updated_at.isoformat() if template.updated_at else None,
            "disability_type": None  # Will be populated separately if needed
        }
    
    async def _disability_to_dict(self, disability: DisabilityType) -> dict:
        """Convert DisabilityType model to dictionary"""
        return {
            "id": str(disability.id),
            "code": disability.code,
            "name": disability.name,
            "description": disability.description,
            "federal_category": disability.federal_category,
            "state_category": disability.state_category,
            "accommodation_defaults": disability.accommodation_defaults or {},
            "is_active": disability.is_active,
            "created_at": disability.created_at.isoformat() if disability.created_at else None
        }