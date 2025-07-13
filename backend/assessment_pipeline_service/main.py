"""
Assessment Pipeline Service - Main FastAPI Application
"""
import sys
import os
import logging
import traceback
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app with lifecycle management
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle management"""
    
    # Startup
    logger.info("Assessment Pipeline Service starting up...")
    
    try:
        # Initialize database (connect to special education service database)
        from special_education_service.src.database import check_database_connection, create_tables
        
        # Check database connection
        db_connected = await check_database_connection()
        if not db_connected:
            logger.error("Failed to connect to database")
            raise Exception("Database connection failed")
        
        logger.info("Database connection established")
        
        # Assessment pipeline models are now integrated into the special education service
        logger.info("Assessment pipeline service ready - using shared database")
        
    except Exception as e:
        logger.error(f"Failed to initialize service: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Assessment Pipeline Service shutting down...")

# Create FastAPI app
app = FastAPI(
    title="Assessment Pipeline Service",
    description="Psychoeducational assessment document processing and quantification service",
    version="2.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler with proper logging"""
    
    logger.error(f"Unhandled exception on {request.method} {request.url}: {exc}")
    logger.error(f"Traceback: {traceback.format_exc()}")
    
    # Don't expose internal errors in production
    if isinstance(exc, HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail}
        )
    
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "timestamp": datetime.utcnow().isoformat(),
            "path": str(request.url)
        }
    )

# Health check endpoint (no auth required)
@app.get("/health", response_model=dict)
async def health_check():
    """Service health check - publicly accessible"""
    
    try:
        # Check database connection
        from special_education_service.src.database import check_database_connection
        db_healthy = await check_database_connection()
        
        # Check auth service connection
        from assessment_pipeline_service.src.service_clients import auth_client
        auth_health = await auth_client.health_check()
        auth_healthy = auth_health.get("healthy", False)
        
        overall_healthy = db_healthy and auth_healthy
        
        return {
            "status": "healthy" if overall_healthy else "unhealthy",
            "service": "assessment_pipeline_service",
            "version": "2.0.0",
            "timestamp": datetime.utcnow().isoformat(),
            "database": "connected" if db_healthy else "disconnected",
            "auth_service": "connected" if auth_healthy else "disconnected",
            "components": {
                "document_ai": "available",
                "data_mapper": "active",
                "quantification_engine": "active",
                "assessment_intake": "active",
                "jwt_authentication": "connected" if auth_healthy else "disconnected"
            },
            "dependencies": {
                "special_education_service": "connected" if db_healthy else "disconnected",
                "auth_service": auth_health
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "service": "assessment_pipeline_service",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        )

# Include routers
# NOTE: assessment_routes.py disabled due to direct database access conflicts
# Using processing_routes.py which follows service-oriented architecture
# try:
#     from assessment_pipeline_service.api.assessment_routes import router as assessment_router
#     app.include_router(assessment_router)
#     logger.info("Assessment routes loaded successfully")
# except ImportError as e:
#     logger.error(f"Failed to load assessment routes: {e}")

try:
    from assessment_pipeline_service.api.pipeline_routes import router as pipeline_router
    app.include_router(pipeline_router)
    logger.info("Pipeline routes loaded successfully")
except ImportError as e:
    logger.warning(f"Pipeline routes not available: {e}")

try:
    from assessment_pipeline_service.api.processing_routes import router as processing_router
    app.include_router(processing_router)
    logger.info("Processing routes loaded successfully")
except ImportError as e:
    logger.warning(f"Processing routes not available: {e}")

# Root endpoint (no auth required)
@app.get("/", response_model=dict)
async def root():
    """Service information - publicly accessible"""
    return {
        "service": "Assessment Pipeline Service",
        "version": "2.0.0",
        "description": "Psychoeducational assessment document processing and quantification",
        "endpoints": {
            "health": "/health",
            "docs": "/docs",
            "assessment_operations": "/assessment-pipeline/*",
            "pipeline_orchestration": "/pipeline/*"
        },
        "features": [
            "Google Document AI integration",
            "Automated score extraction (76-98% confidence)",
            "Psychoeducational assessment processing",
            "RAG-ready data quantification",
            "Multi-stage pipeline orchestration",
            "Real-time processing status"
        ],
        "timestamp": datetime.utcnow().isoformat()
    }

# Development server entry point
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8006,  # Different port from special education service (8005)
        reload=True,
        log_level="info"
    )