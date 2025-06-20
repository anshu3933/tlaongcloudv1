"""Present Levels Repository for managing present level assessments"""

from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc
from sqlalchemy.orm import selectinload

from ..models.special_education_models import PresentLevel
import logging

logger = logging.getLogger(__name__)

class PLRepository:
    """Repository for Present Level operations"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_student_present_levels(
        self, 
        student_id: UUID, 
        limit: Optional[int] = None,
        include_templates: bool = True
    ) -> List[Dict[str, Any]]:
        """Get present levels for a student"""
        try:
            query = select(PresentLevel).where(
                PresentLevel.student_id == student_id
            ).order_by(desc(PresentLevel.assessment_date))
            
            if include_templates:
                query = query.options(selectinload(PresentLevel.template))
            
            if limit:
                query = query.limit(limit)
            
            result = await self.session.execute(query)
            present_levels = result.scalars().all()
            
            return [
                {
                    "id": str(pl.id),
                    "student_id": str(pl.student_id),
                    "template_id": str(pl.template_id) if pl.template_id else None,
                    "assessment_type": pl.assessment_type,
                    "assessment_date": pl.assessment_date.isoformat(),
                    "assessor_name": pl.assessor_name,
                    "assessor_auth_id": pl.assessor_auth_id,
                    "content": pl.content,
                    "strengths": pl.strengths,
                    "needs": pl.needs,
                    "recommendations": pl.recommendations,
                    "version": pl.version,
                    "created_at": pl.created_at.isoformat(),
                    "template": {
                        "id": str(pl.template.id),
                        "name": pl.template.name,
                        "category": pl.template.category
                    } if pl.template else None
                }
                for pl in present_levels
            ]
        except Exception as e:
            logger.error(f"Error fetching present levels for student {student_id}: {e}")
            return []
    
    async def get_present_level(self, pl_id: UUID) -> Optional[Dict[str, Any]]:
        """Get a specific present level by ID"""
        try:
            query = select(PresentLevel).where(
                PresentLevel.id == pl_id
            ).options(
                selectinload(PresentLevel.template),
                selectinload(PresentLevel.student)
            )
            
            result = await self.session.execute(query)
            pl = result.scalar_one_or_none()
            
            if not pl:
                return None
            
            return {
                "id": str(pl.id),
                "student_id": str(pl.student_id),
                "template_id": str(pl.template_id) if pl.template_id else None,
                "assessment_type": pl.assessment_type,
                "assessment_date": pl.assessment_date.isoformat(),
                "assessor_name": pl.assessor_name,
                "assessor_auth_id": pl.assessor_auth_id,
                "content": pl.content,
                "strengths": pl.strengths,
                "needs": pl.needs,
                "recommendations": pl.recommendations,
                "version": pl.version,
                "created_at": pl.created_at.isoformat(),
                "student": {
                    "id": str(pl.student.id),
                    "first_name": pl.student.first_name,
                    "last_name": pl.student.last_name
                } if pl.student else None,
                "template": {
                    "id": str(pl.template.id),
                    "name": pl.template.name,
                    "category": pl.template.category
                } if pl.template else None
            }
        except Exception as e:
            logger.error(f"Error fetching present level {pl_id}: {e}")
            return None
    
    async def create_present_level(self, pl_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a new present level assessment"""
        try:
            present_level = PresentLevel(
                student_id=UUID(pl_data["student_id"]),
                template_id=UUID(pl_data["template_id"]) if pl_data.get("template_id") else None,
                assessment_type=pl_data["assessment_type"],
                assessment_date=datetime.fromisoformat(pl_data["assessment_date"]).date(),
                assessor_name=pl_data["assessor_name"],
                assessor_auth_id=pl_data["assessor_auth_id"],
                content=pl_data.get("content", {}),
                strengths=pl_data.get("strengths", []),
                needs=pl_data.get("needs", []),
                recommendations=pl_data.get("recommendations", []),
                version=pl_data.get("version", 1)
            )
            
            self.session.add(present_level)
            await self.session.commit()
            await self.session.refresh(present_level)
            
            return await self.get_present_level(present_level.id)
        except Exception as e:
            logger.error(f"Error creating present level: {e}")
            await self.session.rollback()
            return None
    
    async def update_present_level(
        self, 
        pl_id: UUID, 
        updates: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Update an existing present level"""
        try:
            query = select(PresentLevel).where(PresentLevel.id == pl_id)
            result = await self.session.execute(query)
            present_level = result.scalar_one_or_none()
            
            if not present_level:
                logger.warning(f"Present level {pl_id} not found for update")
                return None
            
            # Update fields
            for field, value in updates.items():
                if hasattr(present_level, field):
                    if field == "assessment_date" and isinstance(value, str):
                        value = datetime.fromisoformat(value).date()
                    setattr(present_level, field, value)
            
            await self.session.commit()
            await self.session.refresh(present_level)
            
            return await self.get_present_level(present_level.id)
        except Exception as e:
            logger.error(f"Error updating present level {pl_id}: {e}")
            await self.session.rollback()
            return None
    
    async def delete_present_level(self, pl_id: UUID) -> bool:
        """Delete a present level assessment"""
        try:
            query = select(PresentLevel).where(PresentLevel.id == pl_id)
            result = await self.session.execute(query)
            present_level = result.scalar_one_or_none()
            
            if not present_level:
                logger.warning(f"Present level {pl_id} not found for deletion")
                return False
            
            await self.session.delete(present_level)
            await self.session.commit()
            
            logger.info(f"Present level {pl_id} deleted successfully")
            return True
        except Exception as e:
            logger.error(f"Error deleting present level {pl_id}: {e}")
            await self.session.rollback()
            return False
    
    async def get_present_levels_by_type(
        self, 
        student_id: UUID, 
        assessment_type: str,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get present levels by assessment type for a student"""
        try:
            query = select(PresentLevel).where(
                and_(
                    PresentLevel.student_id == student_id,
                    PresentLevel.assessment_type == assessment_type
                )
            ).order_by(desc(PresentLevel.assessment_date))
            
            if limit:
                query = query.limit(limit)
            
            result = await self.session.execute(query)
            present_levels = result.scalars().all()
            
            return [
                {
                    "id": str(pl.id),
                    "assessment_date": pl.assessment_date.isoformat(),
                    "assessor_name": pl.assessor_name,
                    "content": pl.content,
                    "strengths": pl.strengths,
                    "needs": pl.needs,
                    "recommendations": pl.recommendations,
                    "version": pl.version
                }
                for pl in present_levels
            ]
        except Exception as e:
            logger.error(f"Error fetching present levels by type {assessment_type}: {e}")
            return []
    
    async def get_latest_present_level_by_type(
        self, 
        student_id: UUID, 
        assessment_type: str
    ) -> Optional[Dict[str, Any]]:
        """Get the most recent present level assessment by type"""
        results = await self.get_present_levels_by_type(student_id, assessment_type, limit=1)
        return results[0] if results else None