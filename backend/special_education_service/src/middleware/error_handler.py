"""Global error handling middleware"""
import logging
import traceback
import time
from typing import Callable
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from pydantic import ValidationError
import uuid

from ..schemas.common_schemas import ErrorResponse, ErrorDetail

logger = logging.getLogger(__name__)

class ErrorHandlerMiddleware:
    """Global error handling middleware"""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        # Generate request ID for tracking
        request_id = str(uuid.uuid4())
        
        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                headers.append([b"x-request-id", request_id.encode()])
                message["headers"] = headers
            await send(message)
        
        try:
            # Add request ID to scope for access in handlers
            scope["request_id"] = request_id
            await self.app(scope, receive, send_wrapper)
            
        except Exception as e:
            # Handle uncaught exceptions
            response = await self._handle_exception(e, request_id)
            await self._send_error_response(response, send_wrapper)

    async def _handle_exception(self, exc: Exception, request_id: str) -> JSONResponse:
        """Handle different types of exceptions"""
        
        if isinstance(exc, HTTPException):
            # FastAPI HTTP exceptions - already handled
            return JSONResponse(
                status_code=exc.status_code,
                content=ErrorResponse(
                    message=exc.detail,
                    metadata={"request_id": request_id}
                ).model_dump()
            )
        
        elif isinstance(exc, ValidationError):
            # Pydantic validation errors
            details = []
            for error in exc.errors():
                details.append(ErrorDetail(
                    field=".".join(str(loc) for loc in error["loc"]),
                    message=error["msg"],
                    code=error["type"]
                ))
            
            logger.warning(f"Validation error (request {request_id}): {exc}")
            
            return JSONResponse(
                status_code=422,
                content=ErrorResponse(
                    message="Validation failed",
                    details=details,
                    metadata={"request_id": request_id}
                ).model_dump()
            )
        
        elif isinstance(exc, IntegrityError):
            # Database integrity constraints
            logger.error(f"Database integrity error (request {request_id}): {exc}")
            
            # Try to extract meaningful error message
            error_msg = "Database constraint violation"
            if "UNIQUE constraint failed" in str(exc):
                error_msg = "Record with this value already exists"
            elif "FOREIGN KEY constraint failed" in str(exc):
                error_msg = "Referenced record not found"
            elif "NOT NULL constraint failed" in str(exc):
                error_msg = "Required field is missing"
            
            return JSONResponse(
                status_code=400,
                content=ErrorResponse(
                    message=error_msg,
                    details=[ErrorDetail(message=str(exc.orig), code="integrity_error")],
                    metadata={"request_id": request_id}
                ).model_dump()
            )
        
        elif isinstance(exc, SQLAlchemyError):
            # Other database errors
            logger.error(f"Database error (request {request_id}): {exc}")
            
            return JSONResponse(
                status_code=500,
                content=ErrorResponse(
                    message="Database operation failed",
                    details=[ErrorDetail(message="Internal database error", code="database_error")],
                    metadata={"request_id": request_id}
                ).model_dump()
            )
        
        else:
            # Unexpected server errors
            logger.error(f"Unexpected error (request {request_id}): {exc}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            
            return JSONResponse(
                status_code=500,
                content=ErrorResponse(
                    message="Internal server error",
                    details=[ErrorDetail(message="An unexpected error occurred", code="internal_error")],
                    metadata={"request_id": request_id}
                ).model_dump()
            )
    
    async def _send_error_response(self, response: JSONResponse, send: Callable):
        """Send error response through ASGI"""
        await send({
            "type": "http.response.start",
            "status": response.status_code,
            "headers": [
                [b"content-type", b"application/json"],
                [b"x-request-id", response.headers.get("x-request-id", "unknown").encode()],
            ],
        })
        
        await send({
            "type": "http.response.body",
            "body": response.body,
        })

async def add_request_id_middleware(request: Request, call_next):
    """Add request ID to all requests"""
    request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
    
    # Add to request state for access in route handlers
    request.state.request_id = request_id
    
    start_time = time.time()
    
    response = await call_next(request)
    
    # Add request ID to response headers
    response.headers["x-request-id"] = request_id
    
    # Log request duration
    duration = time.time() - start_time
    logger.info(f"Request {request_id} completed in {duration:.3f}s - {request.method} {request.url.path} - {response.status_code}")
    
    return response