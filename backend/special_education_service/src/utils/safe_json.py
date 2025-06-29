"""Safe JSON response utilities with guaranteed serialization safety"""

import orjson
from typing import Any, Optional, Dict
from fastapi import Response
from fastapi.responses import JSONResponse
from datetime import datetime, date
from uuid import UUID
import logging

logger = logging.getLogger(__name__)


class SafeJSONResponse(JSONResponse):
    """JSON response with guaranteed serialization safety"""
    
    def render(self, content: Any) -> bytes:
        """Safely render content as JSON with validation"""
        if content is None:
            return b"null"
        
        try:
            # Custom serialization for common problematic types
            def default_serializer(obj):
                if isinstance(obj, (datetime, date)):
                    return obj.isoformat()
                elif isinstance(obj, UUID):
                    return str(obj)
                elif hasattr(obj, '__dict__'):
                    return obj.__dict__
                elif hasattr(obj, 'model_dump'):  # Pydantic models
                    return obj.model_dump()
                else:
                    return str(obj)
            
            # Serialize with orjson for speed and safety
            # Using appropriate options for consistent output
            encoded = orjson.dumps(
                content,
                default=default_serializer,
                option=orjson.OPT_NON_STR_KEYS | orjson.OPT_SERIALIZE_NUMPY | orjson.OPT_OMIT_MICROSECONDS
            )
            
            # Validate round-trip
            try:
                orjson.loads(encoded)
            except Exception as e:
                logger.error(f"JSON round-trip validation failed: {e}")
                # Fallback to error response
                error_content = {
                    "error": "Serialization validation failed",
                    "timestamp": datetime.utcnow().isoformat()
                }
                encoded = orjson.dumps(error_content, option=orjson.OPT_OMIT_MICROSECONDS)
            
            return encoded
            
        except Exception as e:
            logger.error(f"JSON serialization failed: {e}", extra={"content_type": type(content).__name__})
            
            # Safe fallback error response
            error_response = {
                "error": "Internal serialization error",
                "message": "Failed to generate valid JSON response",
                "timestamp": datetime.utcnow().isoformat()
            }
            return orjson.dumps(error_response, option=orjson.OPT_OMIT_MICROSECONDS)


def safe_json_response(
    content: Any,
    status_code: int = 200,
    headers: Optional[Dict[str, str]] = None,
    **kwargs
) -> SafeJSONResponse:
    """Helper to create SafeJSONResponse with proper headers"""
    return SafeJSONResponse(
        content=content,
        status_code=status_code,
        headers=headers,
        **kwargs
    )