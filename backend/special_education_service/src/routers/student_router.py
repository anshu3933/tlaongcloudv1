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

@router.get("/{student_id}/profile")
async def get_student_profile_bff(
    student_id: UUID,
    student_repo: StudentRepository = Depends(get_student_repository)
):
    """
    Complete student profile BFF endpoint with goals, IEP data, activities, and progress metrics
    """
    try:
        # Get basic student data
        student = await student_repo.get_student(student_id, include_ieps=True)
        if not student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Student {student_id} not found"
            )
        
        # Mock data for Phase 2 implementation
        # In a real implementation, this would come from actual repositories
        
        # Generate personalized goals based on student's disability and grade
        disability_type = student.get("primary_disability_type", "Specific Learning Disability")
        grade_level = student["grade_level"]
        student_name = f"{student['first_name']} {student['last_name']}"
        
        goals = []
        
        # Academic goals based on disability type
        if "Learning" in disability_type or "SLD" in disability_type:
            goals.append({
                "id": f"goal-academic-{student['id'][:8]}",
                "title": f"Reading Comprehension - Grade {grade_level}",
                "description": f"{student['first_name']} will read {grade_level} level passages and answer comprehension questions with 80% accuracy",
                "category": "academic",
                "target_date": "2024-08-30",
                "progress_percentage": 72,
                "status": "active",
                "milestones": [
                    {
                        "id": "milestone-1",
                        "title": "Baseline reading assessment",
                        "description": "Establish current reading level",
                        "target_date": "2024-02-15",
                        "completed": True,
                        "completed_date": "2024-02-10"
                    },
                    {
                        "id": "milestone-2",
                        "title": "Mid-year progress review",
                        "description": "Reassess reading comprehension skills",
                        "target_date": "2024-04-15",
                        "completed": True,
                        "completed_date": "2024-04-12"
                    }
                ],
                "last_updated": "2024-04-15T10:30:00Z"
            })
            
            goals.append({
                "id": f"goal-math-{student['id'][:8]}",
                "title": f"Math Problem Solving - Grade {grade_level}",
                "description": f"{student['first_name']} will solve multi-step word problems appropriate for {grade_level} with 75% accuracy",
                "category": "academic",
                "target_date": "2024-08-30",
                "progress_percentage": 68,
                "status": "active",
                "milestones": [
                    {
                        "id": "milestone-3",
                        "title": "Single-step problems mastery",
                        "description": "Complete single-step word problems",
                        "target_date": "2024-03-01",
                        "completed": True,
                        "completed_date": "2024-02-28"
                    }
                ],
                "last_updated": "2024-04-10T14:20:00Z"
            })
        
        # Social/Behavioral goals
        goals.append({
            "id": f"goal-social-{student['id'][:8]}",
            "title": "Social Interaction Skills",
            "description": f"{student['first_name']} will initiate appropriate conversations with peers during structured activities",
            "category": "social",
            "target_date": "2024-06-30",
            "progress_percentage": 85,
            "status": "active",
            "milestones": [
                {
                    "id": "milestone-4",
                    "title": "Peer interaction practice",
                    "description": "Practice conversations with teacher support",
                    "target_date": "2024-03-15",
                    "completed": True,
                    "completed_date": "2024-03-10"
                }
            ],
            "last_updated": "2024-04-20T09:15:00Z"
        })
        
        # Communication goals if applicable
        if "Speech" in disability_type or "Communication" in disability_type:
            goals.append({
                "id": f"goal-comm-{student['id'][:8]}",
                "title": "Expressive Communication",
                "description": f"{student['first_name']} will use complete sentences to express needs and wants in 8/10 opportunities",
                "category": "communication",
                "target_date": "2024-07-15",
                "progress_percentage": 78,
                "status": "active",
                "milestones": [
                    {
                        "id": "milestone-5",
                        "title": "Sentence structure practice",
                        "description": "Use subject-verb-object structure",
                        "target_date": "2024-03-30",
                        "completed": True,
                        "completed_date": "2024-03-25"
                    }
                ],
                "last_updated": "2024-04-18T11:45:00Z"
            })
        
        # Mock IEP data
        iep_data = {
            "id": "iep-1",
            "status": "active",
            "start_date": "2023-09-01",
            "end_date": "2024-08-31",
            "review_date": "2024-03-01",
            "compliance_status": "compliant",
            "milestones": [
                {
                    "id": "iep-milestone-1",
                    "title": "Annual Review",
                    "target_date": "2024-03-01",
                    "status": "completed"
                },
                {
                    "id": "iep-milestone-2",
                    "title": "Spring Progress Review",
                    "target_date": "2024-05-15",
                    "status": "pending"
                }
            ],
            "documents": [
                {
                    "id": "doc-1",
                    "name": "IEP Document 2023-2024",
                    "type": "IEP",
                    "upload_date": "2023-09-01",
                    "file_url": "/documents/iep-2023-2024.pdf"
                },
                {
                    "id": "doc-2",
                    "name": "Behavioral Assessment",
                    "type": "Assessment",
                    "upload_date": "2024-02-15",
                    "file_url": "/documents/behavior-assessment-2024.pdf"
                }
            ],
            "meetings": [
                {
                    "id": "meeting-1",
                    "type": "annual",
                    "scheduled_date": "2024-03-01",
                    "status": "completed",
                    "attendees": ["Teacher", "Parent", "Case Manager", "School Psychologist"]
                },
                {
                    "id": "meeting-2",
                    "type": "quarterly",
                    "scheduled_date": "2024-05-15",
                    "status": "scheduled",
                    "attendees": ["Teacher", "Parent", "Case Manager"]
                }
            ]
        }
        
        # Generate personalized activities for the student
        activities = [
            {
                "id": f"activity-1-{student['id'][:8]}",
                "type": "goal_update",
                "description": f"Updated {student['first_name']}'s reading comprehension goal progress to 72%",
                "timestamp": "2024-04-20T10:30:00Z",
                "user_name": "Ms. Rodriguez",
                "metadata": {
                    "goal_id": f"goal-academic-{student['id'][:8]}",
                    "previous_progress": 68,
                    "new_progress": 72,
                    "student_name": student_name
                }
            },
            {
                "id": f"activity-2-{student['id'][:8]}",
                "type": "assessment",
                "description": f"Completed quarterly progress assessment for {student['first_name']}",
                "timestamp": "2024-04-18T14:20:00Z",
                "user_name": "Mr. Thompson",
                "metadata": {
                    "assessment_type": "quarterly_progress",
                    "score": 82,
                    "grade_level": grade_level,
                    "student_name": student_name
                }
            },
            {
                "id": f"activity-3-{student['id'][:8]}",
                "type": "iep_update",
                "description": f"Updated IEP accommodations for {student['first_name']}",
                "timestamp": "2024-04-15T09:00:00Z", 
                "user_name": "Case Manager Wilson",
                "metadata": {
                    "update_type": "accommodations",
                    "disability_type": disability_type,
                    "student_name": student_name
                }
            },
            {
                "id": f"activity-4-{student['id'][:8]}",
                "type": "meeting",
                "description": f"Parent conference completed for {student['first_name']}",
                "timestamp": "2024-04-10T15:30:00Z",
                "user_name": "Ms. Rodriguez",
                "metadata": {
                    "meeting_type": "parent_conference",
                    "attendees_count": 3,
                    "student_name": student_name
                }
            }
        ]
        
        # Calculate progress metrics
        progress_metrics = {
            "overall_percentage": student.get("progress_percentage", 70),
            "academic_progress": 75,
            "behavioral_progress": 65,
            "social_progress": 60,
            "goals_completed": len([g for g in goals if g["status"] == "completed"]),
            "goals_total": len(goals),
            "trend": "improving"
        }
        
        # Format student data using real student information
        student_data = {
            "id": str(student["id"]),
            "first_name": student["first_name"],
            "last_name": student["last_name"],
            "grade": student["grade_level"],
            "primary_disability": student.get("primary_disability_type", "Specific Learning Disability"),
            "current_iep_status": iep_data["status"] if iep_data else None,
            "progress_percentage": progress_metrics["overall_percentage"],
            "alert_status": "warning" if progress_metrics["overall_percentage"] < 60 else "success",
            "alert_message": "Below target progress" if progress_metrics["overall_percentage"] < 60 else "On track",
            "last_activity": activities[0]["timestamp"] if activities else None
        }
        
        profile_data = {
            "student": student_data,
            "goals": goals,
            "iep": iep_data,
            "activities": activities,
            "progressMetrics": progress_metrics,
            "lastUpdated": "2024-04-15T15:30:00Z"
        }
        
        logger.info(
            f"Student profile fetched for {student_id}",
            extra={
                "student_id": str(student_id),
                "goals_count": len(goals),
                "activities_count": len(activities),
                "has_iep": bool(iep_data)
            }
        )
        
        return profile_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching student profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch student profile"
        )