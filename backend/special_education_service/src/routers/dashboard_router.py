"""
Dashboard BFF (Backend for Frontend) API endpoints
Optimized endpoints that return aggregated data for dashboard views
"""

from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, Any
from uuid import UUID
import logging
from datetime import datetime, timedelta
import asyncio

from ..database import get_db
from ..repositories.student_repository import StudentRepository
from ..repositories.iep_repository import IEPRepository
from ..services.user_adapter import UserAdapter
from ..schemas.student_schemas import StudentResponse
from ..schemas.iep_schemas import IEPResponse
from ..schemas.common_schemas import SuccessResponse
from common.src.config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/dashboard", tags=["Dashboard BFF"])
settings = get_settings()

# Initialize user adapter
user_adapter = UserAdapter(
    auth_service_url=getattr(settings, 'auth_service_url', 'http://localhost:8080'),
    cache_ttl_seconds=300
)

async def get_repositories(db: AsyncSession = Depends(get_db)):
    """Dependency to get repositories"""
    return {
        'student': StudentRepository(db),
        'iep': IEPRepository(db)
    }

# Response schemas for BFF endpoints
from pydantic import BaseModel
from typing import List, Optional

class DashboardStats(BaseModel):
    total_students: int
    active_ieps: int
    goals_achieved: int
    tasks_due: int
    pending_approvals: int = 0
    compliance_rate: float = 0.0
    overdue_items: int = 0

class StudentCardData(BaseModel):
    id: UUID
    first_name: str
    last_name: str
    grade: str
    primary_disability: str
    current_iep_status: Optional[str] = None
    progress_percentage: float = 0.0
    alert_status: Optional[str] = None  # 'urgent', 'warning', 'success', None
    alert_message: Optional[str] = None
    last_activity: Optional[datetime] = None

class RecentActivity(BaseModel):
    id: UUID
    type: str  # 'iep_updated', 'goal_achieved', 'progress_recorded', etc.
    description: str
    student_id: UUID
    student_name: str
    timestamp: datetime
    user_id: Optional[str] = None
    user_name: Optional[str] = None

class TaskItem(BaseModel):
    id: UUID
    type: str  # 'iep_review', 'goal_assessment', 'meeting_scheduled'
    title: str
    description: str
    due_date: datetime
    priority: str  # 'high', 'medium', 'low'
    student_id: UUID
    student_name: str
    status: str = 'pending'

class NotificationItem(BaseModel):
    id: UUID
    type: str
    title: str
    message: str
    timestamp: datetime
    read: bool = False
    action_url: Optional[str] = None

class TeacherDashboardResponse(BaseModel):
    stats: DashboardStats
    students: List[StudentCardData]
    recent_activities: List[RecentActivity]
    pending_tasks: List[TaskItem]
    notifications: List[NotificationItem]
    last_updated: datetime

class CoordinatorDashboardResponse(BaseModel):
    stats: DashboardStats
    pending_approvals: List[Dict[str, Any]]
    team_overview: List[Dict[str, Any]]
    compliance_metrics: Dict[str, Any]
    system_alerts: List[Dict[str, Any]]
    last_updated: datetime

class AdminDashboardResponse(BaseModel):
    stats: DashboardStats
    system_metrics: Dict[str, Any]
    user_activity: List[Dict[str, Any]]
    security_alerts: List[Dict[str, Any]]
    last_updated: datetime

@router.get("/teacher/{user_id}", response_model=TeacherDashboardResponse)
async def get_teacher_dashboard(
    user_id: str,
    repositories = Depends(get_repositories),
    x_request_id: Optional[str] = Header(None),
    x_client_session_id: Optional[str] = Header(None)
):
    """
    BFF endpoint for teacher dashboard - returns all data needed in a single call
    Optimized for teacher workflow and student management
    """
    logger.info(f"Fetching teacher dashboard for user {user_id}", extra={
        "request_id": x_request_id,
        "user_id": user_id,
        "endpoint": "teacher_dashboard"
    })
    
    try:
        # Get repositories
        student_repo = repositories['student']
        iep_repo = repositories['iep']
        
        # Fetch teacher's students (for now, get all students - will filter by teacher later)
        students_data = await student_repo.list_students()
        
        # Parallel data fetching for better performance
        async def fetch_dashboard_data():
            # Get all students assigned to this teacher
            # TODO: Add teacher assignment logic when user relationships are implemented
            students = students_data[:25]  # Limit for demo
            
            # Get IEP data for students
            student_ids = [student['id'] for student in students]
            ieps_data = await asyncio.gather(*[
                iep_repo.get_student_ieps(student_id) for student_id in student_ids
            ], return_exceptions=True)
            
            return students, ieps_data
        
        students, ieps_data = await fetch_dashboard_data()
        
        # Process student cards
        student_cards = []
        active_ieps_count = 0
        goals_achieved = 0
        
        for i, student in enumerate(students):
            try:
                student_ieps = ieps_data[i] if not isinstance(ieps_data[i], Exception) else []
                current_iep = student_ieps[0] if student_ieps else None
                
                # Calculate progress and status
                progress_percentage = 75.0 if current_iep else 0.0  # Mock calculation
                alert_status = None
                alert_message = None
                
                if current_iep:
                    active_ieps_count += 1
                    # Mock some goal achievements
                    if i % 3 == 0:
                        goals_achieved += 1
                        alert_status = "success"
                        alert_message = "Goal achieved this week!"
                    elif hasattr(current_iep, 'status') and current_iep.status == 'under_review':
                        alert_status = "warning"
                        alert_message = "IEP review due"
                
                disability_codes = student.get('disability_codes', [])
                primary_disability = disability_codes[0] if disability_codes else "Not specified"
                
                student_cards.append(StudentCardData(
                    id=student['id'],
                    first_name=student['first_name'],
                    last_name=student['last_name'],
                    grade=student.get('grade_level') or "N/A",
                    primary_disability=primary_disability,
                    current_iep_status=current_iep.status if current_iep and hasattr(current_iep, 'status') else "No IEP",
                    progress_percentage=progress_percentage,
                    alert_status=alert_status,
                    alert_message=alert_message,
                    last_activity=current_iep.updated_at if current_iep and hasattr(current_iep, 'updated_at') else student.get('updated_at')
                ))
            except Exception as e:
                logger.warning(f"Error processing student {i}: {e}", exc_info=True)
                continue
        
        # Calculate dashboard stats
        stats = DashboardStats(
            total_students=len(students),
            active_ieps=active_ieps_count,
            goals_achieved=goals_achieved,
            tasks_due=5,  # Mock data
            pending_approvals=0,  # Teachers don't typically approve
            compliance_rate=94.5,  # Mock data
            overdue_items=2  # Mock data
        )
        
        # Generate mock recent activities
        recent_activities = [
            RecentActivity(
                id=UUID("12345678-1234-5678-9012-123456789001"),
                type="iep_updated",
                description="Updated reading goals for student",
                student_id=student_cards[0].id if student_cards else UUID("12345678-1234-5678-9012-123456789999"),
                student_name=f"{student_cards[0].first_name} {student_cards[0].last_name}" if student_cards else "Sample Student",
                timestamp=datetime.now() - timedelta(hours=2),
                user_id=user_id,
                user_name="Current Teacher"
            ),
            RecentActivity(
                id=UUID("12345678-1234-5678-9012-123456789002"),
                type="goal_achieved",
                description="Math fluency milestone reached",
                student_id=student_cards[1].id if len(student_cards) > 1 else UUID("12345678-1234-5678-9012-123456789998"),
                student_name=f"{student_cards[1].first_name} {student_cards[1].last_name}" if len(student_cards) > 1 else "Another Student",
                timestamp=datetime.now() - timedelta(hours=5),
                user_id=user_id,
                user_name="Current Teacher"
            )
        ]
        
        # Generate mock pending tasks
        pending_tasks = [
            TaskItem(
                id=UUID("12345678-1234-5678-9012-123456789003"),
                type="iep_review",
                title="Annual IEP Review",
                description="Annual review meeting scheduled",
                due_date=datetime.now() + timedelta(days=1),
                priority="high",
                student_id=student_cards[0].id if student_cards else UUID("12345678-1234-5678-9012-123456789999"),
                student_name=f"{student_cards[0].first_name} {student_cards[0].last_name}" if student_cards else "Sample Student",
                status="pending"
            ),
            TaskItem(
                id=UUID("12345678-1234-5678-9012-123456789004"),
                type="goal_assessment",
                title="Quarterly Progress Assessment",
                description="Assess reading comprehension progress",
                due_date=datetime.now() + timedelta(days=3),
                priority="medium",
                student_id=student_cards[1].id if len(student_cards) > 1 else UUID("12345678-1234-5678-9012-123456789998"),
                student_name=f"{student_cards[1].first_name} {student_cards[1].last_name}" if len(student_cards) > 1 else "Another Student",
                status="pending"
            )
        ]
        
        # Generate mock notifications
        notifications = [
            NotificationItem(
                id=UUID("12345678-1234-5678-9012-123456789005"),
                type="reminder",
                title="IEP Meeting Reminder",
                message="Meeting scheduled for tomorrow at 2 PM",
                timestamp=datetime.now() - timedelta(minutes=30),
                read=False,
                action_url=f"/students/{student_cards[0].id}/iep" if student_cards else None
            )
        ]
        
        response = TeacherDashboardResponse(
            stats=stats,
            students=student_cards,
            recent_activities=recent_activities,
            pending_tasks=pending_tasks,
            notifications=notifications,
            last_updated=datetime.now()
        )
        
        logger.info(f"Successfully fetched teacher dashboard for user {user_id}", extra={
            "request_id": x_request_id,
            "student_count": len(student_cards),
            "active_ieps": active_ieps_count
        })
        
        return response
        
    except Exception as e:
        logger.error(f"Error fetching teacher dashboard for user {user_id}: {e}", extra={
            "request_id": x_request_id,
            "error": str(e)
        })
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch dashboard data: {str(e)}"
        )

@router.get("/coordinator/{user_id}", response_model=CoordinatorDashboardResponse)
async def get_coordinator_dashboard(
    user_id: str,
    repositories = Depends(get_repositories),
    x_request_id: Optional[str] = Header(None)
):
    """
    BFF endpoint for coordinator dashboard - returns team oversight data
    """
    logger.info(f"Fetching coordinator dashboard for user {user_id}", extra={
        "request_id": x_request_id,
        "user_id": user_id,
        "endpoint": "coordinator_dashboard"
    })
    
    try:
        # Mock data for coordinator dashboard
        stats = DashboardStats(
            total_students=156,
            active_ieps=134,
            goals_achieved=89,
            tasks_due=23,
            pending_approvals=8,
            compliance_rate=94.2,
            overdue_items=3
        )
        
        # Mock pending approvals
        pending_approvals = [
            {
                "id": "12345678-1234-5678-9012-123456789006",
                "type": "iep_approval",
                "student_name": "Arjun Patel",
                "submitted_by": "Ms. Sharma",
                "submitted_date": datetime.now() - timedelta(days=2),
                "priority": "urgent",
                "status": "pending"
            },
            {
                "id": "12345678-1234-5678-9012-123456789007",
                "type": "goal_modification",
                "student_name": "Kavya Reddy",
                "submitted_by": "Mr. Patel",
                "submitted_date": datetime.now() - timedelta(days=1),
                "priority": "high",
                "status": "pending"
            }
        ]
        
        # Mock team overview
        team_overview = [
            {
                "teacher_name": "Ms. Sharma",
                "student_count": 8,
                "pending_items": 2,
                "compliance_score": 96.5,
                "status": "on_track"
            },
            {
                "teacher_name": "Mr. Patel",
                "student_count": 6,
                "pending_items": 1,
                "compliance_score": 92.0,
                "status": "attention_needed"
            }
        ]
        
        # Mock compliance metrics
        compliance_metrics = {
            "iep_renewals": 94.0,
            "goal_reviews": 87.0,
            "documentation": 91.0,
            "meeting_compliance": 89.5
        }
        
        # Mock system alerts
        system_alerts = [
            {
                "type": "overdue_ieps",
                "message": "3 IEPs past renewal deadline",
                "severity": "high",
                "count": 3
            },
            {
                "type": "missing_signatures",
                "message": "2 parent consent forms pending",
                "severity": "medium",
                "count": 2
            }
        ]
        
        response = CoordinatorDashboardResponse(
            stats=stats,
            pending_approvals=pending_approvals,
            team_overview=team_overview,
            compliance_metrics=compliance_metrics,
            system_alerts=system_alerts,
            last_updated=datetime.now()
        )
        
        logger.info(f"Successfully fetched coordinator dashboard for user {user_id}")
        return response
        
    except Exception as e:
        logger.error(f"Error fetching coordinator dashboard: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch coordinator dashboard: {str(e)}"
        )

@router.get("/admin/{user_id}", response_model=AdminDashboardResponse)
async def get_admin_dashboard(
    user_id: str,
    repositories = Depends(get_repositories),
    x_request_id: Optional[str] = Header(None)
):
    """
    BFF endpoint for admin dashboard - returns system-wide metrics
    """
    logger.info(f"Fetching admin dashboard for user {user_id}")
    
    try:
        # Mock data for admin dashboard
        stats = DashboardStats(
            total_students=1245,
            active_ieps=1089,
            goals_achieved=2341,
            tasks_due=67,
            pending_approvals=23,
            compliance_rate=93.8,
            overdue_items=15
        )
        
        # Mock system metrics
        system_metrics = {
            "total_users": 156,
            "system_health": 99.8,
            "data_storage_gb": 2400,
            "storage_usage_percent": 68,
            "security_alerts": 2,
            "api_response_time_ms": 245,
            "uptime_percent": 99.9
        }
        
        # Mock user activity
        user_activity = [
            {
                "user_name": "Dr. Priya Mehta",
                "role": "coordinator",
                "action": "User added",
                "timestamp": datetime.now() - timedelta(hours=2),
                "status": "active"
            },
            {
                "user_name": "Rajesh Kumar",
                "role": "teacher",
                "action": "Role updated to Senior Teacher",
                "timestamp": datetime.now() - timedelta(days=2),
                "status": "updated"
            }
        ]
        
        # Mock security alerts
        security_alerts = [
            {
                "type": "login_attempt",
                "message": "Multiple failed login attempts",
                "severity": "medium",
                "timestamp": datetime.now() - timedelta(hours=6),
                "user_id": "unknown"
            }
        ]
        
        response = AdminDashboardResponse(
            stats=stats,
            system_metrics=system_metrics,
            user_activity=user_activity,
            security_alerts=security_alerts,
            last_updated=datetime.now()
        )
        
        logger.info(f"Successfully fetched admin dashboard for user {user_id}")
        return response
        
    except Exception as e:
        logger.error(f"Error fetching admin dashboard: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch admin dashboard: {str(e)}"
        )

# Health check endpoint with observability
@router.get("/health", response_model=Dict[str, Any])
async def dashboard_health_check():
    """Health check for dashboard BFF endpoints"""
    return {
        "status": "healthy",
        "service": "dashboard_bff",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }