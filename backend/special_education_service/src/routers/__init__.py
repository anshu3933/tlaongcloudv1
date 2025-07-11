"""API routers for Special Education Service"""

from .student_router import router as student_router
from .iep_router import router as iep_router  
from .template_router import router as template_router
from .dashboard_router import router as dashboard_router
from .observability_router import router as observability_router
from .monitoring_router import router as monitoring_router
from .async_jobs import router as async_jobs_router
from .assessment_router import router as assessment_router

__all__ = [
    'student_router', 
    'iep_router', 
    'template_router', 
    'dashboard_router',
    'observability_router',
    'monitoring_router',
    'async_jobs_router',
    'assessment_router'
]