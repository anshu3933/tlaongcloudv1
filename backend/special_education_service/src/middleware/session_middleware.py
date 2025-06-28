"""Request-scoped database session middleware for atomic operations"""
import uuid
import time
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import async_session_factory

logger = logging.getLogger(__name__)

class RequestScopedSessionMiddleware(BaseHTTPMiddleware):
    """Middleware to provide single database session per HTTP request"""
    
    async def dispatch(self, request: Request, call_next):
        # Generate correlation ID for request tracking
        correlation_id = str(uuid.uuid4())
        request.state.correlation_id = correlation_id
        
        # Start timing
        start_time = time.time()
        
        # Create request-scoped database session
        async with async_session_factory() as session:
            # Store session in request state
            request.state.db_session = session
            request.state.session_created_at = start_time
            
            logger.info(f"[{correlation_id}] Database session created for {request.method} {request.url.path}")
            
            try:
                # Process the request
                response = await call_next(request)
                
                # If we made it here without exceptions, commit the transaction
                await session.commit()
                
                duration = time.time() - start_time
                logger.info(f"[{correlation_id}] Request completed successfully in {duration:.3f}s")
                
                return response
                
            except Exception as e:
                # Rollback on any error
                await session.rollback()
                
                duration = time.time() - start_time
                logger.error(f"[{correlation_id}] Request failed after {duration:.3f}s: {str(e)}")
                
                # Re-raise the exception
                raise
            
            finally:
                # Session is automatically closed by the context manager
                duration = time.time() - start_time
                logger.debug(f"[{correlation_id}] Database session closed after {duration:.3f}s")


# Dependency to get the request-scoped session
async def get_request_session(request: Request) -> AsyncSession:
    """Get the request-scoped database session"""
    session = getattr(request.state, 'db_session', None)
    if session is None:
        raise RuntimeError("No database session found in request state. "
                         "Ensure RequestScopedSessionMiddleware is installed.")
    return session


def get_correlation_id(request: Request) -> str:
    """Get the correlation ID for the current request"""
    return getattr(request.state, 'correlation_id', 'unknown')


@asynccontextmanager
async def get_advisory_lock_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Get a separate session specifically for advisory locks.
    This ensures advisory locks don't interfere with the main transaction.
    """
    async with async_session_factory() as session:
        try:
            yield session
        except Exception as e:
            logger.error(f"Advisory lock session error: {e}")
            await session.rollback()
            raise
        finally:
            await session.close()