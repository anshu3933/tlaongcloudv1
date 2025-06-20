"""Global error handling middleware."""

import logging
import traceback
from datetime import datetime, timezone
from typing import Dict
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.exc import SQLAlchemyError
from pydantic import ValidationError

from ..schemas import ErrorResponse, ErrorDetail

logger = logging.getLogger(__name__)

class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """Middleware for handling exceptions and returning consistent error responses."""
    
    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
            
        except HTTPException as exc:
            # FastAPI HTTPExceptions are already properly formatted
            return await self.create_error_response(
                request=request,
                status_code=exc.status_code,
                detail=exc.detail,
                error_type="http_exception"
            )
            
        except ValidationError as exc:
            # Pydantic validation errors
            errors = []
            for error in exc.errors():
                field = ".".join(str(loc) for loc in error["loc"])
                errors.append(ErrorDetail(
                    type="validation_error",
                    message=error["msg"],
                    field=field
                ))
            
            return await self.create_error_response(
                request=request,
                status_code=422,
                detail="Validation failed",
                errors=errors,
                error_type="validation_error"
            )
            
        except SQLAlchemyError as exc:
            # Database errors
            logger.error(f"Database error on {request.method} {request.url}: {exc}")
            
            return await self.create_error_response(
                request=request,
                status_code=500,
                detail="Database error occurred",
                error_type="database_error"
            )
            
        except Exception as exc:
            # Unexpected errors
            logger.error(
                f"Unexpected error on {request.method} {request.url}: {exc}\n"
                f"Traceback: {traceback.format_exc()}"
            )
            
            return await self.create_error_response(
                request=request,
                status_code=500,
                detail="Internal server error",
                error_type="internal_error"
            )
    
    async def create_error_response(
        self,
        request: Request,
        status_code: int,
        detail: str,
        error_type: str,
        errors: list = None
    ) -> JSONResponse:
        """Create a standardized error response."""
        
        # Log error details
        logger.warning(
            f"Error response: {status_code} - {detail} "
            f"for {request.method} {request.url} "
            f"from {request.client.host if request.client else 'unknown'}"
        )
        
        error_response = ErrorResponse(
            detail=detail,
            errors=errors,
            timestamp=datetime.now(timezone.utc)
        )
        
        # Add additional context for debugging in development
        response_data = error_response.dict()
        if logger.isEnabledFor(logging.DEBUG):
            response_data["debug"] = {
                "method": request.method,
                "url": str(request.url),
                "error_type": error_type
            }
        
        return JSONResponse(
            status_code=status_code,
            content=response_data
        )

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware for adding security headers to responses."""
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        
        # Remove server header for security
        if "server" in response.headers:
            del response.headers["server"]
        
        return response

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging HTTP requests and responses."""
    
    def __init__(self, app, log_body: bool = False):
        super().__init__(app)
        self.log_body = log_body
    
    async def dispatch(self, request: Request, call_next):
        start_time = datetime.now(timezone.utc)
        
        # Log request
        client_ip = self.get_client_ip(request)
        logger.info(
            f"Request started: {request.method} {request.url} "
            f"from {client_ip}"
        )
        
        # Process request
        response = await call_next(request)
        
        # Calculate duration
        duration = (datetime.now(timezone.utc) - start_time).total_seconds()
        
        # Log response
        logger.info(
            f"Request completed: {request.method} {request.url} "
            f"status={response.status_code} duration={duration:.3f}s"
        )
        
        # Add timing header
        response.headers["X-Process-Time"] = str(duration)
        
        return response
    
    def get_client_ip(self, request: Request) -> str:
        """Extract client IP address."""
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else "unknown"

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple in-memory rate limiting middleware."""
    
    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.request_counts: Dict[str, list] = {}
    
    async def dispatch(self, request: Request, call_next):
        client_ip = self.get_client_ip(request)
        current_time = datetime.now(timezone.utc)
        
        # Skip rate limiting for health checks
        if request.url.path in ["/health", "/", "/docs", "/openapi.json"]:
            return await call_next(request)
        
        # Initialize or get request history for this IP
        if client_ip not in self.request_counts:
            self.request_counts[client_ip] = []
        
        request_history = self.request_counts[client_ip]
        
        # Remove requests older than 1 minute
        cutoff_time = current_time.timestamp() - 60
        self.request_counts[client_ip] = [
            timestamp for timestamp in request_history
            if timestamp > cutoff_time
        ]
        
        # Check rate limit
        if len(self.request_counts[client_ip]) >= self.requests_per_minute:
            logger.warning(f"Rate limit exceeded for IP: {client_ip}")
            
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Rate limit exceeded. Please try again later.",
                    "retry_after": 60
                },
                headers={"Retry-After": "60"}
            )
        
        # Add current request
        self.request_counts[client_ip].append(current_time.timestamp())
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        remaining = max(0, self.requests_per_minute - len(self.request_counts[client_ip]))
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int(current_time.timestamp()) + 60)
        
        return response
    
    def get_client_ip(self, request: Request) -> str:
        """Extract client IP address."""
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else "unknown"