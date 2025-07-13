"""
Assessment Pipeline Service - Main Application
Processing-only microservice for psychoeducational assessment processing
"""
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
from datetime import datetime

# Import routes
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.processing_routes import router as processing_router
from src.service_communication import service_comm_manager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    # Startup
    logger.info("🚀 Starting Assessment Pipeline Service v2.0.0")
    logger.info("📊 Architecture: Processing-only microservice")
    logger.info("🔗 Service communication: Enabled")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down Assessment Pipeline Service")

# Create FastAPI application
app = FastAPI(
    title="Assessment Pipeline Service",
    description="Processing-only microservice for psychoeducational assessment document processing and data quantification",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(processing_router)

@app.get("/", tags=["service"])
async def root():
    """Service information endpoint"""
    return {
        "service": "Assessment Pipeline Service",
        "version": "2.0.0",
        "description": "Processing-only microservice for psychoeducational assessment processing",
        "architecture": "processing-only microservice",
        "endpoints": {
            "health": "/health",
            "processing": "/assessment-pipeline/processing",
            "docs": "/docs",
            "redoc": "/redoc"
        },
        "features": [
            "Document upload and processing",
            "Score extraction with 76-98% confidence",
            "Data quantification for RAG integration",
            "Background processing with status tracking",
            "Service-oriented architecture (no direct database access)",
            "Circuit breaker patterns for fault tolerance",
            "Correlation ID tracking for debugging"
        ],
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/health", tags=["monitoring"])
async def health_check():
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "service": "assessment_pipeline_service",
        "version": "2.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }

# For development/testing
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8006,
        reload=True,
        log_level="info"
    )