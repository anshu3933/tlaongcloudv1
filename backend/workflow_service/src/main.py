from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timezone
import logging

from .middleware.error_handler import ErrorHandlerMiddleware

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Workflow Service",
    version="1.0.0",
    description="Service for managing workflows and process automation"
)

# Add error handling middleware
app.add_middleware(ErrorHandlerMiddleware)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    """Enhanced health check endpoint with system status."""
    try:
        return {
            "status": "healthy",
            "service": "workflow-service",
            "version": "1.0.0",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "components": {
                "api": "operational",
                "cors": "enabled"
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unhealthy")

@app.get("/")
async def root():
    """Root endpoint with service information."""
    return {
        "service": "Workflow Service",
        "version": "1.0.0",
        "description": "Service for managing workflows and process automation",
        "endpoints": {
            "health": "/health",
            "docs": "/docs"
        }
    }
