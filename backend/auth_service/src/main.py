"""FastAPI main application for Authentication Service."""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import get_auth_settings
from .database import create_tables, close_db
from .middleware.error_handler import (
    ErrorHandlerMiddleware, SecurityHeadersMiddleware,
    RequestLoggingMiddleware, RateLimitMiddleware
)
from .routers import auth, users
from .schemas import HealthResponse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Get settings
settings = get_auth_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info("Starting Authentication Service...")
    
    try:
        # Create database tables
        await create_tables()
        logger.info("Database tables created successfully")
        
        logger.info("Authentication Service started successfully")
        yield
        
    except Exception as e:
        logger.error(f"Failed to start Authentication Service: {e}")
        raise
    
    finally:
        # Shutdown
        logger.info("Shutting down Authentication Service...")
        await close_db()
        logger.info("Authentication Service shutdown complete")

# Create FastAPI application
app = FastAPI(
    title="Authentication Service",
    description="Comprehensive authentication and user management service for RAG MCP Backend",
    version="1.0.0",
    docs_url="/docs" if not settings.is_production else None,
    redoc_url="/redoc" if not settings.is_production else None,
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Add custom middleware (order matters - last added is executed first)
app.add_middleware(ErrorHandlerMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(
    RateLimitMiddleware,
    requests_per_minute=settings.rate_limit_requests
)

# Include routers
app.include_router(auth.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")

# System endpoints
@app.get("/", tags=["system"])
async def root():
    """Root endpoint with API information."""
    return {
        "service": "Authentication Service",
        "version": "1.0.0",
        "description": "Comprehensive authentication and user management service",
        "documentation": "/docs" if not settings.is_production else "Documentation disabled in production",
        "endpoints": {
            "authentication": "/api/v1/auth",
            "user_management": "/api/v1/users",
            "health_check": "/health"
        }
    }

@app.get("/health", response_model=HealthResponse, tags=["system"])
async def health_check():
    """Health check endpoint for load balancers and monitoring."""
    try:
        # Basic health check - could be extended to check database connectivity
        return HealthResponse(
            status="healthy",
            service="auth-service",
            version="1.0.0",
            database="connected"  # Could verify actual DB connection
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthResponse(
            status="unhealthy",
            service="auth-service",
            version="1.0.0",
            database="error"
        )

# Legacy endpoint for backward compatibility
@app.post("/verify-token", tags=["legacy"])
async def verify_token_legacy(token_data: dict):
    """Legacy token verification endpoint for backward compatibility."""
    from .routers.auth import verify_user_token
    return await verify_user_token(token_data)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8003,
        reload=True if not settings.is_production else False,
        log_level=settings.log_level.lower()
    )