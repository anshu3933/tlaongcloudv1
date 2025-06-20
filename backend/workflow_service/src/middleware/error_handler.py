"""Global error handling middleware for Workflow Service."""

import logging
import traceback
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from pydantic import BaseModel, Field
from typing import List

logger = logging.getLogger(__name__)

class ErrorDetail(BaseModel):
    """Schema for error details."""
    type: str
    message: str
    field: Optional[str] = None

class ErrorResponse(BaseModel):
    """Schema for error responses."""
    detail: str
    errors: Optional[List[ErrorDetail]] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    request_id: Optional[str] = None

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
            errors=errors
        )
        
        return JSONResponse(
            status_code=status_code,
            content=error_response.dict()
        )