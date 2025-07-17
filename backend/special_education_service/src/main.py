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
from .middleware.session_middleware import RequestScopedSessionMiddleware
# from .monitoring.middleware import MonitoringMiddleware
# from .monitoring.health_monitor import health_monitor
from .config import get_settings

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
app.add_middleware(RequestScopedSessionMiddleware)
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
logger.info("🔧 Starting advanced IEP router registration...")
try:
    logger.info("🔧 Importing advanced IEP router...")
    from .routers import advanced_iep_router
    logger.info("🔧 Advanced IEP router imported successfully")
    
    logger.info("🔧 Registering advanced IEP router...")
    app.include_router(advanced_iep_router.router)
    logger.info(f"✅ Advanced IEP router loaded successfully with {len(advanced_iep_router.router.routes)} routes")
    logger.info(f"✅ Advanced router prefix: {advanced_iep_router.router.prefix}")
    
    # Log specific routes for debugging
    for route in advanced_iep_router.router.routes:
        if hasattr(route, 'path') and hasattr(route, 'methods'):
            logger.info(f"   Route: {list(route.methods)} {route.path}")
            
except ImportError as e:
    logger.error(f"❌ Failed to import advanced IEP router: {e}")
    import traceback
    logger.error(f"Import traceback: {traceback.format_exc()}")
except Exception as e:
    logger.error(f"❌ Error registering advanced IEP router: {e}")
    import traceback
    logger.error(f"Registration traceback: {traceback.format_exc()}")

from typing import Dict, Any

@app.on_event("startup")
async def startup_event():
    """Initialize resources and validate schema on startup"""
    try:
        logger.info("🚀 Starting Special Education Service with schema validation")
        
        # Test database connection
        if not await check_database_connection():
            logger.error("Failed to connect to database")
            raise RuntimeError("Database connection failed")
        
        # Validate database schema
        from .utils.schema_validation import validate_startup_schema
        from .database import engine
        
        try:
            schema_results = await validate_startup_schema(engine)
            if schema_results['status'] == 'valid':
                logger.info("✅ Database schema validation passed")
            else:
                logger.warning(f"⚠️ Database schema validation warnings: {schema_results.get('warnings', [])}")
        except Exception as schema_error:
            logger.error(f"❌ Database schema validation failed: {schema_error}")
            # Don't fail startup for schema issues - graceful degradation will handle it
            logger.warning("⚠️ Starting with schema issues - some features may be degraded")
        
        logger.info("✅ Startup completed successfully")
    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
        raise

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
            "environment": settings.ENVIRONMENT
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

@app.get("/debug/routes", response_model=Dict[str, Any])
async def debug_routes():
    """Debug endpoint to list all registered routes"""
    routes = []
    for route in app.routes:
        if hasattr(route, 'path') and hasattr(route, 'methods'):
            routes.append({
                "path": route.path,
                "methods": list(route.methods),
                "name": getattr(route, 'name', 'unknown')
            })
    return {
        "total_routes": len(routes),
        "routes": routes,
        "advanced_routes": [r for r in routes if "advanced" in r["path"]]
    }

@app.get("/debug/circuit-breaker", response_model=Dict[str, Any])
async def debug_circuit_breaker():
    """Debug endpoint to check circuit breaker status"""
    from .utils.schema_validation import get_circuit_breaker
    
    circuit_breaker = get_circuit_breaker()
    status = circuit_breaker.get_status()
    
    return {
        "circuit_breaker": status,
        "health": "healthy" if status["state"] == "CLOSED" else "degraded",
        "recommendation": {
            "CLOSED": "Assessment operations are working normally",
            "OPEN": "Assessment operations are disabled due to repeated schema errors. Please run database migrations: alembic upgrade head",
            "HALF_OPEN": "Assessment operations are being tested after failure recovery"
        }.get(status["state"], "Unknown state")
    }

# Entry point for running directly
if __name__ == "__main__":
    import uvicorn
    
    logger.info(f"Starting Special Education Service on port {settings.special_education_port if hasattr(settings, 'special_education_port') else 8005}")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=getattr(settings, 'special_education_port', 8005),
        reload=settings.is_development,
        log_level=getattr(settings, 'log_level', 'info').lower()
    )
