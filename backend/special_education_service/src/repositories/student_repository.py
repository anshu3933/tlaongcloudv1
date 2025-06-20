"""Repository layer for Student operations"""
from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_, or_, func
from sqlalchemy.orm import selectinload
from datetime import datetime, date

from ..models.special_education_models import Student, IEP

class StudentRepository:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create_student(self, student_data: dict) -> dict:
        """Create new student record"""
        student = Student(
            student_id=student_data["student_id"],
            first_name=student_data["first_name"],
            last_name=student_data["last_name"],
            middle_name=student_data.get("middle_name"),
            date_of_birth=student_data["date_of_birth"],
            grade_level=student_data["grade_level"],
            disability_codes=student_data.get("disability_codes", []),
            case_manager_auth_id=student_data.get("case_manager_auth_id"),
            primary_teacher_auth_id=student_data.get("primary_teacher_auth_id"),
            parent_guardian_auth_ids=student_data.get("parent_guardian_auth_ids", []),
            school_district=student_data.get("school_district"),
            school_name=student_data.get("school_name"),
            enrollment_date=student_data.get("enrollment_date")
        )
        
        self.session.add(student)
        await self.session.commit()
        await self.session.refresh(student)
        
        return await self._student_to_dict(student)
    
    async def get_student(self, student_id: UUID, include_ieps: bool = False) -> Optional[dict]:
        """Get student by ID with optional IEPs"""
        query = select(Student).where(Student.id == student_id)
        
        if include_ieps:
            query = query.options(selectinload(Student.ieps))
        
        result = await self.session.execute(query)
        student = result.scalar_one_or_none()
        
        if not student:
            return None
        
        return await self._student_to_dict(student)
    
    async def get_student_by_student_id(self, student_id: str) -> Optional[dict]:
        """Get student by their school student ID"""
        result = await self.session.execute(
            select(Student).where(Student.student_id == student_id)
        )
        student = result.scalar_one_or_none()
        
        if not student:
            return None
        
        return await self._student_to_dict(student)
    
    async def update_student(self, student_id: UUID, updates: dict) -> Optional[dict]:
        """Update student record"""
        student = await self.session.get(Student, student_id)
        if not student:
            return None
        
        # Update fields
        for field, value in updates.items():
            if hasattr(student, field) and field not in ["id", "created_at"]:
                setattr(student, field, value)
        
        await self.session.commit()
        await self.session.refresh(student)
        
        return await self._student_to_dict(student)
    
    async def delete_student(self, student_id: UUID) -> bool:
        """Soft delete student (mark as inactive)"""
        result = await self.session.execute(
            update(Student)
            .where(Student.id == student_id)
            .values(is_active=False)
        )
        await self.session.commit()
        return result.rowcount > 0
    
    async def list_students(
        self, 
        grade_level: Optional[str] = None,
        disability_code: Optional[str] = None,
        case_manager_auth_id: Optional[int] = None,
        is_active: bool = True,
        limit: int = 100,
        offset: int = 0
    ) -> List[dict]:
        """List students with filtering"""
        query = select(Student).where(Student.is_active == is_active)
        
        if grade_level:
            query = query.where(Student.grade_level == grade_level)
        
        if disability_code:
            query = query.where(Student.disability_codes.contains([disability_code]))
        
        if case_manager_auth_id:
            query = query.where(Student.case_manager_auth_id == case_manager_auth_id)
        
        query = query.order_by(Student.last_name, Student.first_name)
        query = query.offset(offset).limit(limit)
        
        result = await self.session.execute(query)
        students = result.scalars().all()
        
        return [await self._student_to_dict(student) for student in students]
    
    async def search_students(self, search_term: str, limit: int = 50) -> List[dict]:
        """Search students by name or student ID"""
        search_pattern = f"%{search_term}%"
        
        query = select(Student).where(
            and_(
                Student.is_active == True,
                or_(
                    Student.first_name.ilike(search_pattern),
                    Student.last_name.ilike(search_pattern),
                    Student.student_id.ilike(search_pattern),
                    func.concat(Student.first_name, ' ', Student.last_name).ilike(search_pattern)
                )
            )
        ).order_by(Student.last_name, Student.first_name).limit(limit)
        
        result = await self.session.execute(query)
        students = result.scalars().all()
        
        return [await self._student_to_dict(student) for student in students]
    
    async def get_students_by_teacher(self, teacher_auth_id: int) -> List[dict]:
        """Get all students assigned to a teacher"""
        query = select(Student).where(
            and_(
                Student.is_active == True,
                or_(
                    Student.case_manager_auth_id == teacher_auth_id,
                    Student.primary_teacher_auth_id == teacher_auth_id
                )
            )
        ).order_by(Student.last_name, Student.first_name)
        
        result = await self.session.execute(query)
        students = result.scalars().all()
        
        return [await self._student_to_dict(student) for student in students]
    
    async def get_student_with_active_iep(self, student_id: UUID) -> Optional[dict]:
        """Get student with their active IEP"""
        query = select(Student).where(Student.id == student_id)
        query = query.options(selectinload(Student.active_iep))
        
        result = await self.session.execute(query)
        student = result.scalar_one_or_none()
        
        if not student:
            return None
        
        student_dict = await self._student_to_dict(student)
        
        if student.active_iep:
            student_dict["active_iep"] = {
                "id": str(student.active_iep.id),
                "academic_year": student.active_iep.academic_year,
                "status": student.active_iep.status,
                "effective_date": student.active_iep.effective_date.isoformat() if student.active_iep.effective_date else None,
                "review_date": student.active_iep.review_date.isoformat() if student.active_iep.review_date else None
            }
        
        return student_dict
    
    async def update_active_iep(self, student_id: UUID, iep_id: UUID) -> bool:
        """Set the active IEP for a student"""
        result = await self.session.execute(
            update(Student)
            .where(Student.id == student_id)
            .values(active_iep_id=iep_id)
        )
        await self.session.commit()
        return result.rowcount > 0
    
    async def get_student_caseload_summary(self, case_manager_auth_id: int) -> dict:
        """Get caseload summary for a case manager"""
        # Get total students
        total_students_query = select(func.count(Student.id)).where(
            and_(
                Student.case_manager_auth_id == case_manager_auth_id,
                Student.is_active == True
            )
        )
        total_result = await self.session.execute(total_students_query)
        total_students = total_result.scalar()
        
        # Get students by grade level
        grade_query = select(
            Student.grade_level,
            func.count(Student.id).label('count')
        ).where(
            and_(
                Student.case_manager_auth_id == case_manager_auth_id,
                Student.is_active == True
            )
        ).group_by(Student.grade_level)
        
        grade_result = await self.session.execute(grade_query)
        grades = {row.grade_level: row.count for row in grade_result}
        
        # Get active IEPs count
        active_ieps_query = select(func.count(IEP.id)).join(Student).where(
            and_(
                Student.case_manager_auth_id == case_manager_auth_id,
                Student.is_active == True,
                IEP.status == "active"
            )
        )
        active_ieps_result = await self.session.execute(active_ieps_query)
        active_ieps = active_ieps_result.scalar()
        
        return {
            "total_students": total_students,
            "active_ieps": active_ieps,
            "students_by_grade": grades,
            "case_manager_auth_id": case_manager_auth_id
        }
    
    async def get_students_needing_iep_review(self, days_ahead: int = 30) -> List[dict]:
        """Get students whose IEPs need review soon"""
        cutoff_date = date.today() + datetime.timedelta(days=days_ahead)
        
        query = select(Student).join(IEP, Student.active_iep_id == IEP.id).where(
            and_(
                Student.is_active == True,
                IEP.review_date <= cutoff_date,
                IEP.status == "active"
            )
        ).options(selectinload(Student.active_iep))
        
        result = await self.session.execute(query)
        students = result.scalars().all()
        
        return [await self._student_to_dict(student) for student in students]
    
    async def _student_to_dict(self, student: Student) -> dict:
        """Convert Student model to dictionary"""
        return {
            "id": str(student.id),
            "student_id": student.student_id,
            "first_name": student.first_name,
            "last_name": student.last_name,
            "middle_name": student.middle_name,
            "full_name": f"{student.first_name} {student.last_name}",
            "date_of_birth": student.date_of_birth.isoformat() if student.date_of_birth else None,
            "grade_level": student.grade_level,
            "disability_codes": student.disability_codes or [],
            "case_manager_auth_id": student.case_manager_auth_id,
            "primary_teacher_auth_id": student.primary_teacher_auth_id,
            "parent_guardian_auth_ids": student.parent_guardian_auth_ids or [],
            "school_district": student.school_district,
            "school_name": student.school_name,
            "enrollment_date": student.enrollment_date.isoformat() if student.enrollment_date else None,
            "active_iep_id": str(student.active_iep_id) if student.active_iep_id else None,
            "is_active": student.is_active,
            "created_at": student.created_at.isoformat() if student.created_at else None,
            "updated_at": student.updated_at.isoformat() if student.updated_at else None
        }