"""Repository layer for IEP operations"""
from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_, desc, func, text
from sqlalchemy.orm import selectinload, joinedload
from datetime import datetime
import logging

from ..models.special_education_models import (
    IEP, IEPGoal, IEPTemplate, IEPStatus, GoalStatus
)

class IEPRepository:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.logger = logging.getLogger(__name__)
    
    async def get_next_version_number(self, student_id: UUID, academic_year: str) -> int:
        """Get the next available version number atomically
        
        Uses PostgreSQL advisory locks for production, SELECT FOR UPDATE for SQLite.
        """
        # Check if we're using PostgreSQL (advisory locks) or SQLite (row locks)
        db_url = str(self.session.bind.url)
        is_postgresql = not db_url.startswith('sqlite')
        
        if is_postgresql:
            return await self._get_next_version_postgresql(student_id, academic_year)
        else:
            return await self._get_next_version_sqlite(student_id, academic_year)
    
    async def _get_next_version_postgresql(self, student_id: UUID, academic_year: str) -> int:
        """PostgreSQL implementation using advisory locks"""
        # Create a unique lock key from student_id and academic_year hash
        lock_key = abs(hash(f"{student_id}:{academic_year}")) % (2**31)
        
        try:
            # Acquire advisory lock to prevent concurrent version conflicts
            await self.session.execute(text("SELECT pg_advisory_lock(:lock_key)"), {"lock_key": lock_key})
            
            self.logger.info(f"Advisory lock acquired for student {student_id}, academic year {academic_year}")
            
            # Now safely get the maximum version
            query = select(func.max(IEP.version)).where(
                and_(
                    IEP.student_id == student_id,
                    IEP.academic_year == academic_year
                )
            )
            
            result = await self.session.execute(query)
            max_version = result.scalar()
            next_version = (max_version or 0) + 1
            
            self.logger.info(f"Next version number: {next_version} for student {student_id}")
            return next_version
            
        finally:
            # Always release the advisory lock
            await self.session.execute(text("SELECT pg_advisory_unlock(:lock_key)"), {"lock_key": lock_key})
            self.logger.info(f"Advisory lock released for student {student_id}, academic year {academic_year}")
    
    async def _get_next_version_sqlite(self, student_id: UUID, academic_year: str) -> int:
        """SQLite implementation using SELECT FOR UPDATE (row-level locking)"""
        self.logger.info(f"Using SQLite row-level locking for student {student_id}, academic year {academic_year}")
        
        # Use SELECT FOR UPDATE to lock the rows and prevent race conditions
        query = select(func.max(IEP.version)).where(
            and_(
                IEP.student_id == student_id,
                IEP.academic_year == academic_year
            )
        ).with_for_update()
        
        result = await self.session.execute(query)
        max_version = result.scalar()
        next_version = (max_version or 0) + 1
        
        self.logger.info(f"Next version number: {next_version} for student {student_id}")
        return next_version
    
    async def get_latest_iep_version(self, student_id: UUID, academic_year: str) -> Optional[dict]:
        """Get the latest IEP version for a student in an academic year"""
        query = select(IEP).where(
            and_(
                IEP.student_id == student_id,
                IEP.academic_year == academic_year
            )
        ).order_by(desc(IEP.version)).limit(1)
        
        result = await self.session.execute(query)
        iep = result.scalar_one_or_none()
        
        if not iep:
            return None
            
        return self._iep_to_dict(iep, include_goals=False)
    
    async def create_iep(self, iep_data: dict) -> dict:
        """Create new IEP with validation"""
        # Create IEP instance
        iep = IEP(
            student_id=iep_data["student_id"],
            template_id=iep_data.get("template_id"),
            academic_year=iep_data["academic_year"],
            status=iep_data.get("status", IEPStatus.DRAFT.value),
            content=iep_data.get("content", {}),
            meeting_date=iep_data.get("meeting_date"),
            effective_date=iep_data.get("effective_date"),
            review_date=iep_data.get("review_date"),
            version=iep_data["version"],  # Version must be provided, no default
            parent_version_id=iep_data.get("parent_version_id"),
            created_by_auth_id=iep_data["created_by"]
        )
        
        self.session.add(iep)
        await self.session.flush()  # Get the ID
        
        # Create goals if provided
        if "goals" in iep_data:
            for goal_data in iep_data["goals"]:
                goal = IEPGoal(
                    iep_id=iep.id,
                    domain=goal_data["domain"],
                    goal_text=goal_data["goal_text"],
                    baseline=goal_data.get("baseline"),
                    target_criteria=goal_data["target_criteria"],
                    measurement_method=goal_data["measurement_method"],
                    measurement_frequency=goal_data.get("measurement_frequency"),
                    target_date=goal_data.get("target_date"),
                    start_date=goal_data.get("start_date"),
                    progress_status=goal_data.get("progress_status", GoalStatus.NOT_STARTED.value)
                )
                self.session.add(goal)
        
        await self.session.flush()  # Flush to get the ID without committing yet
        
        # Refresh the IEP object to get all data
        await self.session.refresh(iep)
        
        # Get the result as dict before committing (within same transaction)
        result = self._iep_to_dict(iep, include_goals=True)
        
        # Now commit the transaction
        await self.session.commit()
        
        return result
    
    async def get_iep(self, iep_id: UUID, include_goals: bool = True) -> Optional[dict]:
        """Get IEP by ID with optional goals"""
        query = select(IEP).where(IEP.id == iep_id)
        
        if include_goals:
            query = query.options(selectinload(IEP.goals))
        
        result = await self.session.execute(query)
        iep = result.scalar_one_or_none()
        
        if not iep:
            return None
        
        return self._iep_to_dict(iep)
    
    async def update_iep(self, iep_id: UUID, updates: dict) -> Optional[dict]:
        """Update IEP with validation"""
        # Get existing IEP
        iep = await self.session.get(IEP, iep_id)
        if not iep:
            return None
        
        # Update fields
        for field, value in updates.items():
            if hasattr(iep, field) and field not in ["id", "created_at"]:
                setattr(iep, field, value)
        
        await self.session.commit()
        await self.session.refresh(iep)
        
        return self._iep_to_dict(iep)
    
    async def delete_iep(self, iep_id: UUID) -> bool:
        """Soft delete IEP (mark as inactive)"""
        result = await self.session.execute(
            update(IEP)
            .where(IEP.id == iep_id)
            .values(status="deleted")
        )
        await self.session.commit()
        return result.rowcount > 0
    
    async def get_student_ieps(
        self, 
        student_id: UUID, 
        academic_year: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50
    ) -> List[dict]:
        """Get IEPs for a student with filtering"""
        query = select(IEP).where(IEP.student_id == student_id)
        
        if academic_year:
            query = query.where(IEP.academic_year == academic_year)
        
        if status:
            query = query.where(IEP.status == status)
        
        query = query.order_by(desc(IEP.created_at)).limit(limit)
        query = query.options(selectinload(IEP.goals))
        
        result = await self.session.execute(query)
        ieps = result.scalars().all()
        
        return [self._iep_to_dict(iep) for iep in ieps]
    
    async def get_iep_version_history(
        self, 
        student_id: UUID, 
        academic_year: str
    ) -> List[dict]:
        """Get all versions of IEP for student in academic year"""
        query = select(IEP).where(
            and_(
                IEP.student_id == student_id,
                IEP.academic_year == academic_year
            )
        ).order_by(IEP.version)
        
        result = await self.session.execute(query)
        ieps = result.scalars().all()
        
        return [self._iep_to_dict(iep, include_goals=False) for iep in ieps]
    
    async def update_iep_status(self, iep_id: UUID, new_status: str) -> bool:
        """Update IEP status"""
        result = await self.session.execute(
            update(IEP)
            .where(IEP.id == iep_id)
            .values(status=new_status)
        )
        await self.session.commit()
        return result.rowcount > 0
    
    async def create_iep_version(
        self, 
        original_iep_id: UUID, 
        updates: dict,
        created_by_auth_id: int
    ) -> dict:
        """Create new version of existing IEP"""
        # Get original IEP
        original = await self.session.get(IEP, original_iep_id)
        if not original:
            raise ValueError(f"Original IEP {original_iep_id} not found")
        
        # Create new version
        new_version_data = {
            "student_id": original.student_id,
            "template_id": original.template_id,
            "academic_year": original.academic_year,
            "content": {**original.content, **updates.get("content", {})},
            "version": original.version + 1,
            "parent_version_id": original_iep_id,
            "created_by": created_by_auth_id,
            "status": IEPStatus.DRAFT.value
        }
        
        # Merge any additional updates
        new_version_data.update({k: v for k, v in updates.items() if k != "content"})
        
        return await self.create_iep(new_version_data)
    
    async def get_template(self, template_id: UUID) -> Optional[dict]:
        """Get IEP template by ID"""
        result = await self.session.execute(
            select(IEPTemplate).where(IEPTemplate.id == template_id)
        )
        template = result.scalar_one_or_none()
        
        if not template:
            return None
        
        return {
            "id": str(template.id),
            "name": template.name,
            "disability_type_id": str(template.disability_type_id) if template.disability_type_id else None,
            "grade_level": template.grade_level,
            "sections": template.sections,
            "default_goals": template.default_goals,
            "version": template.version,
            "is_active": template.is_active,
            "created_by_auth_id": template.created_by_auth_id,
            "created_at": template.created_at.isoformat() if template.created_at else None,
            "updated_at": template.updated_at.isoformat() if template.updated_at else None
        }
    
    async def create_iep_goal(self, goal_data: dict) -> dict:
        """Create individual IEP goal"""
        goal = IEPGoal(
            iep_id=goal_data["iep_id"],
            domain=goal_data["domain"],
            goal_text=goal_data["goal_text"],
            baseline=goal_data.get("baseline"),
            target_criteria=goal_data["target_criteria"],
            measurement_method=goal_data["measurement_method"],
            measurement_frequency=goal_data.get("measurement_frequency"),
            target_date=goal_data.get("target_date"),
            start_date=goal_data.get("start_date"),
            progress_status=goal_data.get("progress_status", GoalStatus.NOT_STARTED.value)
        )
        
        self.session.add(goal)
        await self.session.commit()
        await self.session.refresh(goal)
        
        return self._goal_to_dict(goal)
    
    async def get_iep_goals(self, iep_id: UUID) -> List[dict]:
        """Get all goals for an IEP"""
        result = await self.session.execute(
            select(IEPGoal).where(IEPGoal.iep_id == iep_id)
        )
        goals = result.scalars().all()
        
        return [self._goal_to_dict(goal) for goal in goals]
    
    async def update_goal_progress(
        self, 
        goal_id: UUID, 
        progress_status: str,
        progress_note: Optional[str] = None
    ) -> bool:
        """Update goal progress status and add note"""
        goal = await self.session.get(IEPGoal, goal_id)
        if not goal:
            return False
        
        goal.progress_status = progress_status
        
        if progress_note:
            # Add progress note with timestamp
            progress_notes = goal.progress_notes or []
            progress_notes.append({
                "date": datetime.utcnow().isoformat(),
                "note": progress_note,
                "status": progress_status
            })
            goal.progress_notes = progress_notes
        
        await self.session.commit()
        return True
    
    async def get_ieps_for_approval(
        self, 
        status: str = "under_review",
        limit: int = 50
    ) -> List[dict]:
        """Get IEPs pending approval"""
        query = select(IEP).where(IEP.status == status)
        query = query.options(
            joinedload(IEP.student),
            selectinload(IEP.goals)
        )
        query = query.order_by(IEP.created_at).limit(limit)
        
        result = await self.session.execute(query)
        ieps = result.scalars().all()
        
        return [self._iep_to_dict(iep) for iep in ieps]
    
    def _iep_to_dict(self, iep: IEP, include_goals: bool = True) -> dict:
        """Convert IEP model to dictionary"""
        data = {
            "id": str(iep.id),
            "student_id": str(iep.student_id),
            "template_id": str(iep.template_id) if iep.template_id else None,
            "academic_year": iep.academic_year,
            "status": iep.status,
            "content": iep.content,
            "meeting_date": iep.meeting_date.isoformat() if iep.meeting_date else None,
            "effective_date": iep.effective_date.isoformat() if iep.effective_date else None,
            "review_date": iep.review_date.isoformat() if iep.review_date else None,
            "version": iep.version,
            "parent_version_id": str(iep.parent_version_id) if iep.parent_version_id else None,
            "created_by_auth_id": iep.created_by_auth_id,
            "created_at": iep.created_at.isoformat() if iep.created_at else None,
            "approved_at": iep.approved_at.isoformat() if iep.approved_at else None,
            "approved_by_auth_id": iep.approved_by_auth_id
        }
        
        if include_goals and hasattr(iep, 'goals') and iep.goals:
            data["goals"] = [self._goal_to_dict(goal) for goal in iep.goals]
        
        return data
    
    def _goal_to_dict(self, goal: IEPGoal) -> dict:
        """Convert IEPGoal model to dictionary"""
        return {
            "id": str(goal.id),
            "iep_id": str(goal.iep_id),
            "domain": goal.domain,
            "goal_text": goal.goal_text,
            "baseline": goal.baseline,
            "target_criteria": goal.target_criteria,
            "measurement_method": goal.measurement_method,
            "measurement_frequency": goal.measurement_frequency,
            "target_date": goal.target_date.isoformat() if goal.target_date else None,
            "start_date": goal.start_date.isoformat() if goal.start_date else None,
            "progress_status": goal.progress_status,
            "progress_notes": goal.progress_notes or [],
            "created_at": goal.created_at.isoformat() if goal.created_at else None,
            "updated_at": goal.updated_at.isoformat() if goal.updated_at else None
        }