"""Service layer for async job management with transactional safety"""

import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from uuid import uuid4, UUID
from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..models.job_models import IEPGenerationJob
from ..models.special_education_models import Student, IEP, IEPTemplate
from ..repositories.student_repository import StudentRepository
from ..repositories.iep_repository import IEPRepository
from ..repositories.template_repository import TemplateRepository
from ..utils.json_helpers import ensure_json_serializable
from pydantic import BaseModel, Field
from typing import Union

logger = logging.getLogger(__name__)


class JobRequest(BaseModel):
    """Base job request model"""
    job_type: str = Field(..., min_length=1)
    priority: int = Field(default=5, ge=1, le=10)
    parameters: Dict[str, Any] = Field(default_factory=dict)


class IEPGenerationRequest(JobRequest):
    """IEP generation job request"""
    job_type: str = Field(default="iep_generation", pattern="iep_generation")
    student_id: str = Field(..., min_length=1)
    template_id: Optional[str] = None
    academic_year: str = Field(..., pattern=r"^\d{4}-\d{4}$")
    include_previous_ieps: bool = Field(default=True)
    include_assessments: bool = Field(default=True)


class SectionGenerationRequest(JobRequest):
    """Section generation job request"""
    job_type: str = Field(default="section_generation", pattern="section_generation")
    iep_id: str = Field(..., min_length=1)
    section_type: str = Field(..., min_length=1)
    context_data: Dict[str, Any] = Field(default_factory=dict)


class JobStatus(BaseModel):
    """Job status response model"""
    job_id: str
    status: str
    progress_percentage: int
    status_message: Optional[str]
    created_at: datetime
    completed_at: Optional[datetime]
    failed_at: Optional[datetime]
    result: Optional[Dict[str, Any]]
    error_details: Optional[Dict[str, Any]]


class AsyncJobService:
    """Service for managing async IEP generation jobs"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.student_repo = StudentRepository(session)
        self.iep_repo = IEPRepository(session)
        self.template_repo = TemplateRepository(session)
    
    async def submit_iep_generation_job(
        self, 
        request: IEPGenerationRequest,
        created_by_auth_id: str
    ) -> str:
        """Submit an IEP generation job with data validation"""
        try:
            # Validate student exists
            student = await self.student_repo.get_student_by_id(UUID(request.student_id))
            if not student:
                raise ValueError(f"Student {request.student_id} not found")
            
            # Validate template if provided
            template = None
            if request.template_id:
                template = await self.template_repo.get_template_by_id(UUID(request.template_id))
                if not template:
                    raise ValueError(f"Template {request.template_id} not found")
            
            # Gather student data
            student_data = await self._prepare_student_data(student)
            
            # Gather template data
            template_data = await self._prepare_template_data(template, student)
            
            # Gather context data if requested
            previous_ieps = None
            previous_assessments = None
            
            if request.include_previous_ieps:
                previous_ieps = await self._get_previous_ieps(student.id)
            
            if request.include_assessments:
                previous_assessments = await self._get_assessment_data(student.id)
            
            # Create job parameters
            job_params = {
                'student_data': student_data,
                'template_data': template_data,
                'previous_ieps': previous_ieps,
                'previous_assessments': previous_assessments,
                'academic_year': request.academic_year,
                'created_by_auth_id': created_by_auth_id
            }
            
            # Create job record
            job = IEPGenerationJob(
                id=str(uuid4()),
                student_id=request.student_id,
                academic_year=request.academic_year,
                template_id=request.template_id,
                status='PENDING',
                priority=request.priority,
                input_data=json.dumps(job_params),
                created_by=created_by_auth_id
            )
            
            self.session.add(job)
            await self.session.commit()
            
            logger.info(f"Submitted IEP generation job {job.id} for student {request.student_id}")
            return job.id
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error submitting IEP generation job: {e}", exc_info=True)
            raise
    
    async def submit_section_generation_job(
        self,
        request: SectionGenerationRequest,
        created_by_auth_id: str
    ) -> str:
        """Submit a section generation job"""
        try:
            # Validate IEP exists
            iep = await self.iep_repo.get_by_id(UUID(request.iep_id))
            if not iep:
                raise ValueError(f"IEP {request.iep_id} not found")
            
            # Get student data
            student = await self.student_repo.get_student_by_id(iep.student_id)
            if not student:
                raise ValueError(f"Student for IEP {request.iep_id} not found")
            
            # Prepare job parameters
            job_params = {
                'iep_id': request.iep_id,
                'section_type': request.section_type,
                'student_data': await self._prepare_student_data(student),
                'context_data': request.context_data,
                'created_by_auth_id': created_by_auth_id
            }
            
            # Create job record (section generation uses same job model)
            job = IEPGenerationJob(
                id=str(uuid4()),
                student_id=str(student.id),
                academic_year='section_generation',  # Placeholder for section generation
                template_id=None,
                status='PENDING',
                priority=request.priority,
                input_data=json.dumps(job_params),
                created_by=created_by_auth_id
            )
            
            self.session.add(job)
            await self.session.commit()
            
            logger.info(f"Submitted section generation job {job.id} for IEP {request.iep_id}")
            return job.id
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error submitting section generation job: {e}", exc_info=True)
            raise
    
    async def get_job_status(self, job_id: str) -> Optional[JobStatus]:
        """Get job status by ID"""
        try:
            result = await self.session.execute(
                select(IEPGenerationJob).where(IEPGenerationJob.id == job_id)
            )
            job = result.scalar_one_or_none()
            
            if not job:
                return None
            
            return JobStatus(
                job_id=job.id,
                status=job.status,
                progress_percentage=job.progress_percentage or 0,
                status_message=job.status_message,
                created_at=job.created_at,
                completed_at=job.completed_at,
                failed_at=job.failed_at,
                result=job.result,
                error_details=job.error_details
            )
            
        except Exception as e:
            logger.error(f"Error getting job status: {e}", exc_info=True)
            raise
    
    async def list_user_jobs(
        self,
        created_by_auth_id: str,
        status_filter: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[JobStatus]:
        """List jobs for a user with optional filtering"""
        try:
            query = select(IEPGenerationJob).where(
                IEPGenerationJob.created_by == created_by_auth_id
            )
            
            if status_filter:
                query = query.where(IEPGenerationJob.status == status_filter)
            
            query = query.order_by(IEPGenerationJob.created_at.desc())
            query = query.limit(limit).offset(offset)
            
            result = await self.session.execute(query)
            jobs = result.scalars().all()
            
            return [
                JobStatus(
                    job_id=job.id,
                    status=job.status,
                    progress_percentage=job.progress_percentage or 0,
                    status_message=job.status_message,
                    created_at=job.created_at,
                    completed_at=job.completed_at,
                    failed_at=job.failed_at,
                    result=job.result,
                    error_details=job.error_details
                )
                for job in jobs
            ]
            
        except Exception as e:
            logger.error(f"Error listing user jobs: {e}", exc_info=True)
            raise
    
    async def cancel_job(self, job_id: str, user_auth_id: str) -> bool:
        """Cancel a pending job if user owns it"""
        try:
            result = await self.session.execute(
                update(IEPGenerationJob)
                .where(
                    (IEPGenerationJob.id == job_id) &
                    (IEPGenerationJob.created_by_auth_id == user_auth_id) &
                    (IEPGenerationJob.status.in_(['pending', 'processing']))
                )
                .values(
                    status='cancelled',
                    status_message='Cancelled by user',
                    updated_at=datetime.utcnow()
                )
            )
            
            success = result.rowcount > 0
            if success:
                await self.session.commit()
                logger.info(f"Cancelled job {job_id} by user {user_auth_id}")
            else:
                logger.warning(f"Could not cancel job {job_id} - not found or not owned by {user_auth_id}")
            
            return success
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error cancelling job: {e}", exc_info=True)
            raise
    
    async def get_queue_stats(self) -> Dict[str, Any]:
        """Get queue statistics"""
        try:
            # Count jobs by status
            result = await self.session.execute(
                select(
                    IEPGenerationJob.status,
                    func.count(IEPGenerationJob.id).label('count')
                )
                .group_by(IEPGenerationJob.status)
            )
            
            status_counts = {row.status: row.count for row in result}
            
            # Get oldest pending job
            oldest_pending = await self.session.execute(
                select(IEPGenerationJob.created_at)
                .where(IEPGenerationJob.status == 'pending')
                .order_by(IEPGenerationJob.created_at.asc())
                .limit(1)
            )
            
            oldest_pending_time = oldest_pending.scalar_one_or_none()
            
            # Calculate queue wait time
            queue_wait_minutes = None
            if oldest_pending_time:
                queue_wait_minutes = int(
                    (datetime.utcnow() - oldest_pending_time).total_seconds() / 60
                )
            
            return {
                'queue_stats': status_counts,
                'total_jobs': sum(status_counts.values()),
                'pending_jobs': status_counts.get('pending', 0),
                'processing_jobs': status_counts.get('processing', 0),
                'completed_jobs': status_counts.get('completed', 0),
                'failed_jobs': status_counts.get('failed', 0),
                'oldest_pending_wait_minutes': queue_wait_minutes
            }
            
        except Exception as e:
            logger.error(f"Error getting queue stats: {e}", exc_info=True)
            raise
    
    async def cleanup_old_jobs(self, days_old: int = 30) -> int:
        """Clean up old completed/failed jobs"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_old)
            
            result = await self.session.execute(
                select(func.count(IEPGenerationJob.id))
                .where(
                    (IEPGenerationJob.status.in_(['completed', 'failed', 'cancelled'])) &
                    (IEPGenerationJob.updated_at < cutoff_date)
                )
            )
            
            count_to_delete = result.scalar()
            
            if count_to_delete > 0:
                # Delete old jobs
                await self.session.execute(
                    update(IEPGenerationJob)
                    .where(
                        (IEPGenerationJob.status.in_(['completed', 'failed', 'cancelled'])) &
                        (IEPGenerationJob.updated_at < cutoff_date)
                    )
                    .values(
                        # For audit purposes, mark as archived instead of deleting
                        status='archived',
                        result=None,  # Clear large result data
                        updated_at=datetime.utcnow()
                    )
                )
                
                await self.session.commit()
                logger.info(f"Archived {count_to_delete} old jobs (older than {days_old} days)")
            
            return count_to_delete
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error cleaning up old jobs: {e}", exc_info=True)
            raise
    
    # Helper methods
    
    async def _prepare_student_data(self, student: Student) -> Dict[str, Any]:
        """Prepare student data for job processing"""
        try:
            return ensure_json_serializable({
                'student_id': str(student.id),
                'first_name': student.first_name,
                'last_name': student.last_name,
                'date_of_birth': student.date_of_birth.isoformat() if student.date_of_birth else None,
                'grade_level': student.grade_level,
                'disability_codes': student.disability_codes or [],
                'school_district': student.school_district,
                'school_name': student.school_name,
                'enrollment_date': student.enrollment_date.isoformat() if student.enrollment_date else None,
                'student_profile': student.student_profile
            })
        except Exception as e:
            logger.error(f"Error preparing student data: {e}")
            raise
    
    async def _prepare_template_data(self, template: Optional[IEPTemplate], student: Student) -> Dict[str, Any]:
        """Prepare template data for job processing"""
        if not template:
            # Return default template structure
            return {
                'template_id': None,
                'template_name': 'Default IEP Template',
                'sections': ['student_info', 'present_levels', 'goals', 'services'],
                'grade_level': student.grade_level,
                'disability_categories': student.disability_codes or ['SLD']
            }
        
        try:
            return ensure_json_serializable({
                'template_id': str(template.id),
                'template_name': template.name,
                'description': template.description,
                'sections': template.sections or [],
                'grade_level': template.grade_level,
                'disability_categories': template.disability_categories or [],
                'content': template.content or {}
            })
        except Exception as e:
            logger.error(f"Error preparing template data: {e}")
            raise
    
    async def _get_previous_ieps(self, student_id: UUID) -> Optional[List[Dict[str, Any]]]:
        """Get previous IEPs for context"""
        try:
            # Get last 3 IEPs for context
            result = await self.session.execute(
                select(IEP)
                .where(IEP.student_id == student_id)
                .where(IEP.status == 'active')
                .order_by(IEP.effective_date.desc())
                .limit(3)
            )
            
            ieps = result.scalars().all()
            
            if not ieps:
                return None
            
            return [
                ensure_json_serializable({
                    'iep_id': str(iep.id),
                    'academic_year': iep.academic_year,
                    'effective_date': iep.effective_date.isoformat() if iep.effective_date else None,
                    'content': iep.content or {}
                })
                for iep in ieps
            ]
            
        except Exception as e:
            logger.error(f"Error getting previous IEPs: {e}")
            return None
    
    async def _get_assessment_data(self, student_id: UUID) -> Optional[List[Dict[str, Any]]]:
        """Get assessment data for context"""
        try:
            # This would typically query a separate assessments table
            # For now, return placeholder data
            return [
                {
                    'assessment_type': 'Academic Assessment',
                    'date': datetime.utcnow().isoformat(),
                    'summary': 'Student demonstrates strengths in visual learning'
                }
            ]
            
        except Exception as e:
            logger.error(f"Error getting assessment data: {e}")
            return None