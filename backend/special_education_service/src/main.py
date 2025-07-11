"""Special Education Service - Main Application"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import logging

from .database import create_tables, init_database, check_database_connection
from .routers import (
    iep_router, student_router, template_router, dashboard_router, 
    observability_router, monitoring_router, async_jobs_router, assessment_router
)
# from .middleware.error_handler import ErrorHandlerMiddleware, add_request_id_middleware
# from .middleware.session_middleware import RequestScopedSessionMiddleware
# from .monitoring.middleware import MonitoringMiddleware
# from .monitoring.health_monitor import health_monitor
from common.src.config import get_settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()

# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     """Application lifespan manager"""
#     logger.info("Starting Special Education Service...")
#     
#     # Check database connection
#     if not await check_database_connection():
#         logger.error("Failed to connect to database")
#         raise RuntimeError("Database connection failed")
#     
#     # Create tables
#     await create_tables()
#     
#     # Initialize with default data
#     await init_database()
#     
#     # Start health monitoring
#     await health_monitor.start()
#     logger.info("Health monitoring started")
#     
#     logger.info("Special Education Service started successfully")
#     yield
#     
#     logger.info("Shutting down Special Education Service...")
#     
#     # Stop health monitoring
#     await health_monitor.stop()
#     logger.info("Health monitoring stopped")

app = FastAPI(
    title="Special Education Service",
    version="1.0.0",
    description="Service for managing IEPs, assessments, and special education workflows"
    # lifespan=lifespan
)

# Add middleware (order matters - session middleware should be early)
# app.add_middleware(MonitoringMiddleware)  # Monitor all requests
# app.add_middleware(RequestScopedSessionMiddleware)
# app.middleware("http")(add_request_id_middleware)
# app.add_middleware(ErrorHandlerMiddleware)

# Configure CORS
cors_origins = settings.cors_origins if hasattr(settings, 'cors_origins') else ["*"]
if isinstance(cors_origins, str):
    cors_origins = [origin.strip() for origin in cors_origins.split(",")]
logger.info(f"CORS origins configured: {cors_origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(iep_router)
app.include_router(student_router)  
app.include_router(template_router)
app.include_router(dashboard_router)  
app.include_router(observability_router)  # Fixed response_model issues
app.include_router(monitoring_router)  # Fixed response_model issues
app.include_router(async_jobs_router)   # Fixed response_model issues
app.include_router(assessment_router)

# Include advanced features
# from .routers import advanced_iep_router  # Temporarily disabled for debugging
# app.include_router(advanced_iep_router.router)  # Temporarily disabled for debugging

from typing import Dict, Any

@app.get("/health", response_model=Dict[str, Any])
async def health_check():
    """Health check endpoint with database connectivity test"""
    try:
        db_connected = await check_database_connection()
        
        return {
            "status": "healthy" if db_connected else "degraded",
            "service": "special-education",
            "version": "1.0.0",
            "database": "connected" if db_connected else "disconnected",
            "environment": settings.environment
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unhealthy")

@app.get("/", response_model=Dict[str, Any])
async def root():
    """Root endpoint with service information"""
    return {
        "service": "Special Education Service",
        "version": "1.0.0",
        "description": "Service for managing IEPs, assessments, and special education workflows",
        "endpoints": {
            "health": "/health",
            "docs": "/docs",
            "openapi": "/openapi.json"
        },
        "features": [
            "IEP Management",
            "Student Records",
            "Assessment Tracking", 
            "RAG-powered Content Generation",
            "Workflow Integration"
        ]
    }

# Entry point for running directly
if __name__ == "__main__":
    import uvicorn
    
    logger.info(f"Starting Special Education Service on port {settings.special_education_port if hasattr(settings, 'special_education_port') else 8005}")
    logger.info(f"Environment: {settings.environment}")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=getattr(settings, 'special_education_port', 8005),
        reload=settings.is_development,
        log_level=getattr(settings, 'log_level', 'info').lower()
    )
