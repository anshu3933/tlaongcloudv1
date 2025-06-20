"""Student management API endpoints"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from uuid import UUID
import logging
import math

from ..database import get_db
from ..repositories.student_repository import StudentRepository
from ..services.user_adapter import UserAdapter
from ..schemas.student_schemas import (
    StudentCreate, StudentUpdate, StudentResponse, StudentCaseloadSummary
)
from ..schemas.common_schemas import PaginatedResponse, SuccessResponse
from common.src.config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/students", tags=["Students"])
settings = get_settings()

# Initialize user adapter
user_adapter = UserAdapter(
    auth_service_url=getattr(settings, 'auth_service_url', 'http://localhost:8080'),
    cache_ttl_seconds=300
)

async def get_student_repository(db: AsyncSession = Depends(get_db)) -> StudentRepository:
    """Dependency to get Student repository"""
    return StudentRepository(db)

async def enrich_student_response(student_data: dict) -> StudentResponse:
    """Enrich student data with user information"""
    # Collect auth IDs for user resolution
    auth_ids = []
    if student_data.get("case_manager_auth_id"):
        auth_ids.append(student_data["case_manager_auth_id"])
    if student_data.get("primary_teacher_auth_id"):
        auth_ids.append(student_data["primary_teacher_auth_id"])
    if student_data.get("parent_guardian_auth_ids"):
        auth_ids.extend(student_data["parent_guardian_auth_ids"])
    
    # Resolve users
    users = {}
    if auth_ids:
        users = await user_adapter.resolve_users(auth_ids)
    
    # Enrich response
    enriched_data = student_data.copy()
    if student_data.get("case_manager_auth_id"):
        enriched_data["case_manager_user"] = users.get(student_data["case_manager_auth_id"])
    if student_data.get("primary_teacher_auth_id"):
        enriched_data["primary_teacher_user"] = users.get(student_data["primary_teacher_auth_id"])
    if student_data.get("parent_guardian_auth_ids"):
        enriched_data["parent_guardian_users"] = [
            users.get(auth_id) for auth_id in student_data["parent_guardian_auth_ids"]
            if users.get(auth_id) is not None
        ]
    
    return StudentResponse(**enriched_data)

@router.post("", response_model=StudentResponse, status_code=status.HTTP_201_CREATED)
async def create_student(
    student_data: StudentCreate,
    student_repo: StudentRepository = Depends(get_student_repository)
):
    """Create a new student record"""
    try:
        # Check if student ID already exists
        existing_student = await student_repo.get_student_by_student_id(student_data.student_id)
        if existing_student:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Student with ID {student_data.student_id} already exists"
            )
        
        # Create student
        student_dict = student_data.model_dump()
        created_student = await student_repo.create_student(student_dict)
        
        # Enrich and return response
        return await enrich_student_response(created_student)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating student: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create student"
        )

@router.get("/{student_id}", response_model=StudentResponse)
async def get_student(
    student_id: UUID,
    include_ieps: bool = Query(False, description="Include student's IEPs"),
    student_repo: StudentRepository = Depends(get_student_repository)
):
    """Get student by ID"""
    student = await student_repo.get_student(student_id, include_ieps=include_ieps)
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student {student_id} not found"
        )
    
    return await enrich_student_response(student)

@router.get("/by-student-id/{student_id}", response_model=StudentResponse)
async def get_student_by_school_id(
    student_id: str,
    student_repo: StudentRepository = Depends(get_student_repository)
):
    """Get student by their school student ID"""
    student = await student_repo.get_student_by_student_id(student_id)
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student with school ID {student_id} not found"
        )
    
    return await enrich_student_response(student)

@router.put("/{student_id}", response_model=StudentResponse)
async def update_student(
    student_id: UUID,
    student_updates: StudentUpdate,
    student_repo: StudentRepository = Depends(get_student_repository)
):
    """Update an existing student"""
    # Check if student exists
    existing_student = await student_repo.get_student(student_id)
    if not existing_student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student {student_id} not found"
        )
    
    # If updating student_id, check for conflicts
    if student_updates.student_id and student_updates.student_id != existing_student["student_id"]:
        conflicting_student = await student_repo.get_student_by_student_id(student_updates.student_id)
        if conflicting_student and conflicting_student["id"] != str(student_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Student with ID {student_updates.student_id} already exists"
            )
    
    # Update student
    updates_dict = student_updates.model_dump(exclude_unset=True)
    updated_student = await student_repo.update_student(student_id, updates_dict)
    
    if not updated_student:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update student"
        )
    
    return await enrich_student_response(updated_student)

@router.delete("/{student_id}", response_model=SuccessResponse)
async def delete_student(
    student_id: UUID,
    student_repo: StudentRepository = Depends(get_student_repository)
):
    """Soft delete a student (mark as inactive)"""
    success = await student_repo.delete_student(student_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student {student_id} not found"
        )
    
    return SuccessResponse(
        message=f"Student {student_id} deactivated successfully"
    )

@router.get("", response_model=PaginatedResponse[StudentResponse])
async def list_students(
    grade_level: Optional[str] = Query(None, description="Filter by grade level"),
    disability_code: Optional[str] = Query(None, description="Filter by disability code"),
    case_manager_auth_id: Optional[int] = Query(None, description="Filter by case manager"),
    is_active: bool = Query(True, description="Filter by active status"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
    student_repo: StudentRepository = Depends(get_student_repository)
):
    """List students with filtering and pagination"""
    try:
        # Calculate offset
        offset = (page - 1) * size
        
        # Get students
        students = await student_repo.list_students(
            grade_level=grade_level,
            disability_code=disability_code,
            case_manager_auth_id=case_manager_auth_id,
            is_active=is_active,
            limit=size,
            offset=offset
        )
        
        # For pagination, we need total count (simplified approach)
        total_students = await student_repo.list_students(
            grade_level=grade_level,
            disability_code=disability_code,
            case_manager_auth_id=case_manager_auth_id,
            is_active=is_active,
            limit=1000,  # Large number to get total
            offset=0
        )
        total = len(total_students)
        
        # Enrich responses
        enriched_students = []
        for student in students:
            enriched_student = await enrich_student_response(student)
            enriched_students.append(enriched_student)
        
        # Calculate pagination info
        pages = math.ceil(total / size) if total > 0 else 1
        has_next = page < pages
        has_prev = page > 1
        
        return PaginatedResponse[StudentResponse](
            items=enriched_students,
            total=total,
            page=page,
            size=size,
            pages=pages,
            has_next=has_next,
            has_prev=has_prev
        )
        
    except Exception as e:
        logger.error(f"Error listing students: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve students"
        )

@router.get("/search", response_model=List[StudentResponse])
async def search_students(
    q: str = Query(..., min_length=1, description="Search term (name or student ID)"),
    limit: int = Query(50, ge=1, le=100, description="Maximum results"),
    student_repo: StudentRepository = Depends(get_student_repository)
):
    """Search students by name or student ID"""
    try:
        students = await student_repo.search_students(q, limit=limit)
        
        # Enrich responses
        enriched_students = []
        for student in students:
            enriched_student = await enrich_student_response(student)
            enriched_students.append(enriched_student)
        
        return enriched_students
        
    except Exception as e:
        logger.error(f"Error searching students: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Search failed"
        )

@router.get("/teacher/{teacher_auth_id}/caseload", response_model=List[StudentResponse])
async def get_teacher_caseload(
    teacher_auth_id: int,
    student_repo: StudentRepository = Depends(get_student_repository)
):
    """Get all students assigned to a teacher"""
    try:
        students = await student_repo.get_students_by_teacher(teacher_auth_id)
        
        # Enrich responses
        enriched_students = []
        for student in students:
            enriched_student = await enrich_student_response(student)
            enriched_students.append(enriched_student)
        
        return enriched_students
        
    except Exception as e:
        logger.error(f"Error getting teacher caseload: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve teacher caseload"
        )

@router.get("/teacher/{teacher_auth_id}/caseload-summary", response_model=StudentCaseloadSummary)
async def get_caseload_summary(
    teacher_auth_id: int,
    student_repo: StudentRepository = Depends(get_student_repository)
):
    """Get caseload summary for a case manager"""
    try:
        summary = await student_repo.get_student_caseload_summary(teacher_auth_id)
        
        # Enrich with user info
        teacher_user = await user_adapter.resolve_user(teacher_auth_id)
        summary["case_manager_user"] = teacher_user
        
        return StudentCaseloadSummary(**summary)
        
    except Exception as e:
        logger.error(f"Error getting caseload summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve caseload summary"
        )

@router.get("/{student_id}/active-iep", response_model=StudentResponse)
async def get_student_with_active_iep(
    student_id: UUID,
    student_repo: StudentRepository = Depends(get_student_repository)
):
    """Get student with their active IEP information"""
    student = await student_repo.get_student_with_active_iep(student_id)
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student {student_id} not found"
        )
    
    return await enrich_student_response(student)

@router.put("/{student_id}/active-iep/{iep_id}", response_model=SuccessResponse)
async def set_active_iep(
    student_id: UUID,
    iep_id: UUID,
    student_repo: StudentRepository = Depends(get_student_repository)
):
    """Set the active IEP for a student"""
    # Verify student exists
    student = await student_repo.get_student(student_id)
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student {student_id} not found"
        )
    
    # Update active IEP
    success = await student_repo.update_active_iep(student_id, iep_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update active IEP"
        )
    
    return SuccessResponse(
        message="Active IEP updated successfully",
        data={
            "student_id": str(student_id),
            "active_iep_id": str(iep_id)
        }
    )

@router.get("/review-needed", response_model=List[StudentResponse])
async def get_students_needing_review(
    days_ahead: int = Query(30, ge=1, le=365, description="Days ahead to check for reviews"),
    student_repo: StudentRepository = Depends(get_student_repository)
):
    """Get students whose IEPs need review soon"""
    try:
        students = await student_repo.get_students_needing_iep_review(days_ahead)
        
        # Enrich responses
        enriched_students = []
        for student in students:
            enriched_student = await enrich_student_response(student)
            enriched_students.append(enriched_student)
        
        return enriched_students
        
    except Exception as e:
        logger.error(f"Error getting students needing review: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve students needing review"
        )