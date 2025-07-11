"""
Service clients for inter-service communication with enhanced error handling
"""
import httpx
import logging
import asyncio
from typing import Dict, List, Optional, Any, Union
from uuid import UUID
import os
from datetime import datetime, timedelta
from enum import Enum
import json

logger = logging.getLogger(__name__)

class ServiceError(Exception):
    """Base exception for service communication errors"""
    pass

class ServiceUnavailableError(ServiceError):
    """Service is temporarily unavailable"""
    pass

class ServiceTimeoutError(ServiceError):
    """Service request timed out"""
    pass

class ServiceValidationError(ServiceError):
    """Service returned validation error"""
    pass

class CircuitBreakerState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

class CircuitBreaker:
    """Circuit breaker pattern for service reliability"""
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitBreakerState.CLOSED
    
    async def call(self, func, *args, **kwargs):
        if self.state == CircuitBreakerState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitBreakerState.HALF_OPEN
            else:
                raise ServiceUnavailableError("Circuit breaker is OPEN")
        
        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise
    
    def _should_attempt_reset(self):
        return (
            self.last_failure_time and 
            datetime.now() - self.last_failure_time > timedelta(seconds=self.recovery_timeout)
        )
    
    def _on_success(self):
        self.failure_count = 0
        self.state = CircuitBreakerState.CLOSED
    
    def _on_failure(self):
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitBreakerState.OPEN

class SpecialEducationServiceClient:
    """Enhanced client for communicating with the Special Education Service"""
    
    def __init__(self, base_url: str = None, max_retries: int = 3, retry_delay: float = 1.0):
        self.base_url = base_url or os.getenv("SPECIAL_EDUCATION_SERVICE_URL", "http://localhost:8005")
        self.timeout = httpx.Timeout(timeout=60.0, connect=10.0, read=50.0)
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.circuit_breaker = CircuitBreaker(failure_threshold=5, recovery_timeout=60)
    
    async def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make HTTP request with retry logic and error handling"""
        url = f"{self.base_url}{endpoint}"
        
        for attempt in range(self.max_retries + 1):
            try:
                return await self.circuit_breaker.call(self._execute_request, method, url, **kwargs)
            except (httpx.TimeoutException, httpx.ConnectError) as e:
                if attempt == self.max_retries:
                    logger.error(f"Request failed after {self.max_retries + 1} attempts: {url}")
                    raise ServiceTimeoutError(f"Service timeout after {self.max_retries + 1} attempts: {e}")
                
                wait_time = self.retry_delay * (2 ** attempt)  # Exponential backoff
                logger.warning(f"Request attempt {attempt + 1} failed, retrying in {wait_time}s: {e}")
                await asyncio.sleep(wait_time)
            except httpx.HTTPStatusError as e:
                if e.response.status_code >= 500:
                    # Server errors - retry
                    if attempt == self.max_retries:
                        logger.error(f"Server error after {self.max_retries + 1} attempts: {e}")
                        raise ServiceUnavailableError(f"Service unavailable: {e}")
                    
                    wait_time = self.retry_delay * (2 ** attempt)
                    logger.warning(f"Server error attempt {attempt + 1}, retrying in {wait_time}s: {e}")
                    await asyncio.sleep(wait_time)
                elif e.response.status_code >= 400:
                    # Client errors - don't retry
                    error_detail = self._extract_error_detail(e.response)
                    logger.error(f"Client error {e.response.status_code}: {error_detail}")
                    raise ServiceValidationError(f"Validation error: {error_detail}")
                else:
                    raise
            except ServiceUnavailableError:
                # Circuit breaker is open
                raise
            except Exception as e:
                if attempt == self.max_retries:
                    logger.error(f"Unexpected error after {self.max_retries + 1} attempts: {e}")
                    raise ServiceError(f"Unexpected service error: {e}")
                
                wait_time = self.retry_delay * (2 ** attempt)
                logger.warning(f"Unexpected error attempt {attempt + 1}, retrying in {wait_time}s: {e}")
                await asyncio.sleep(wait_time)
    
    async def _execute_request(self, method: str, url: str, **kwargs) -> Dict[str, Any]:
        """Execute a single HTTP request"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
    
    def _extract_error_detail(self, response: httpx.Response) -> str:
        """Extract error details from response"""
        try:
            error_data = response.json()
            if isinstance(error_data, dict):
                return error_data.get('detail', error_data.get('message', str(error_data)))
            return str(error_data)
        except Exception:
            return response.text or f"HTTP {response.status_code}"
        
    async def create_assessment_document(self, document_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create an assessment document record with enhanced error handling"""
        try:
            return await self._make_request(
                "POST", 
                "/api/v1/assessments/documents", 
                json=document_data
            )
        except Exception as e:
            logger.error(f"Failed to create assessment document: {e}")
            logger.error(f"Document data: {json.dumps(document_data, default=str)}")
            raise
    
    async def update_assessment_document(self, document_id: UUID, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update an assessment document record with enhanced error handling"""
        try:
            return await self._make_request(
                "PUT", 
                f"/api/v1/assessments/documents/{document_id}", 
                json=updates
            )
        except Exception as e:
            logger.error(f"Failed to update assessment document {document_id}: {e}")
            logger.error(f"Update data: {json.dumps(updates, default=str)}")
            raise
    
    async def create_psychoed_scores(self, scores_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Create multiple psychoeducational scores with enhanced error handling"""
        try:
            return await self._make_request(
                "POST", 
                "/api/v1/assessments/scores/batch", 
                json={"scores": scores_data}
            )
        except Exception as e:
            logger.error(f"Failed to create psychoed scores: {e}")
            logger.error(f"Scores count: {len(scores_data)}")
            raise
    
    async def create_extracted_data(self, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create extracted assessment data record with enhanced error handling"""
        try:
            return await self._make_request(
                "POST", 
                "/api/v1/assessments/extracted-data", 
                json=extracted_data
            )
        except Exception as e:
            logger.error(f"Failed to create extracted data: {e}")
            logger.error(f"Data keys: {list(extracted_data.keys())}")
            raise
    
    async def create_quantified_data(self, quantified_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create quantified assessment data record with enhanced error handling"""
        try:
            return await self._make_request(
                "POST", 
                "/api/v1/assessments/quantified-data", 
                json=quantified_data
            )
        except Exception as e:
            logger.error(f"Failed to create quantified data: {e}")
            logger.error(f"Data keys: {list(quantified_data.keys())}")
            raise
    
    async def get_student_assessment_data(self, student_id: UUID) -> Dict[str, Any]:
        """Get all assessment data for a student with enhanced error handling"""
        try:
            return await self._make_request(
                "GET", 
                f"/api/v1/assessments/student/{student_id}"
            )
        except Exception as e:
            logger.error(f"Failed to get student assessment data for {student_id}: {e}")
            raise
    
    async def health_check(self) -> Dict[str, Any]:
        """Check if the special education service is healthy with detailed status"""
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(timeout=5.0)) as client:
                response = await client.get(f"{self.base_url}/health")
                if response.status_code == 200:
                    health_data = response.json()
                    return {
                        "healthy": True,
                        "status": health_data.get("status", "unknown"),
                        "response_time_ms": response.elapsed.total_seconds() * 1000,
                        "circuit_breaker_state": self.circuit_breaker.state.value,
                        "details": health_data
                    }
                else:
                    return {
                        "healthy": False,
                        "status": f"HTTP {response.status_code}",
                        "circuit_breaker_state": self.circuit_breaker.state.value,
                        "error": response.text
                    }
        except Exception as e:
            logger.error(f"Health check failed for special education service: {e}")
            return {
                "healthy": False,
                "error": str(e),
                "circuit_breaker_state": self.circuit_breaker.state.value
            }
    
    def get_circuit_breaker_status(self) -> Dict[str, Any]:
        """Get current circuit breaker status"""
        return {
            "state": self.circuit_breaker.state.value,
            "failure_count": self.circuit_breaker.failure_count,
            "failure_threshold": self.circuit_breaker.failure_threshold,
            "last_failure": self.circuit_breaker.last_failure_time.isoformat() if self.circuit_breaker.last_failure_time else None
        }

class AuthServiceClient:
    """Enhanced client for communicating with the Auth Service"""
    
    def __init__(self, base_url: str = None, max_retries: int = 2):
        self.base_url = base_url or os.getenv("AUTH_SERVICE_URL", "http://localhost:8003")
        self.timeout = httpx.Timeout(timeout=10.0, connect=5.0)
        self.max_retries = max_retries
        self.circuit_breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=30)
    
    async def validate_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Validate a JWT token and return user info with enhanced error handling"""
        try:
            return await self.circuit_breaker.call(self._validate_token_impl, token)
        except ServiceUnavailableError:
            logger.error("Auth service unavailable (circuit breaker open)")
            return None
        except Exception as e:
            logger.error(f"Token validation failed: {e}")
            return None
    
    async def _validate_token_impl(self, token: str) -> Optional[Dict[str, Any]]:
        """Internal token validation implementation"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/auth/verify-token",
                json={"token": token}
            )
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 401:
                logger.warning("Invalid token provided")
                return None
            else:
                response.raise_for_status()
                return None
    
    async def get_user_info(self, user_id: UUID) -> Optional[Dict[str, Any]]:
        """Get user information by ID with enhanced error handling"""
        try:
            return await self.circuit_breaker.call(self._get_user_info_impl, user_id)
        except ServiceUnavailableError:
            logger.error(f"Auth service unavailable for user {user_id} (circuit breaker open)")
            return None
        except Exception as e:
            logger.error(f"Failed to get user info for {user_id}: {e}")
            return None
    
    async def _get_user_info_impl(self, user_id: UUID) -> Optional[Dict[str, Any]]:
        """Internal user info implementation"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(f"{self.base_url}/users/{user_id}")
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                logger.warning(f"User {user_id} not found")
                return None
            else:
                response.raise_for_status()
                return None
    
    async def health_check(self) -> Dict[str, Any]:
        """Check if the auth service is healthy with detailed status"""
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(timeout=5.0)) as client:
                response = await client.get(f"{self.base_url}/health")
                if response.status_code == 200:
                    health_data = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
                    return {
                        "healthy": True,
                        "status": health_data.get("status", "healthy"),
                        "response_time_ms": response.elapsed.total_seconds() * 1000,
                        "circuit_breaker_state": self.circuit_breaker.state.value,
                        "details": health_data
                    }
                else:
                    return {
                        "healthy": False,
                        "status": f"HTTP {response.status_code}",
                        "circuit_breaker_state": self.circuit_breaker.state.value,
                        "error": response.text
                    }
        except Exception as e:
            logger.error(f"Health check failed for auth service: {e}")
            return {
                "healthy": False,
                "error": str(e),
                "circuit_breaker_state": self.circuit_breaker.state.value
            }
    
    def get_circuit_breaker_status(self) -> Dict[str, Any]:
        """Get current circuit breaker status"""
        return {
            "state": self.circuit_breaker.state.value,
            "failure_count": self.circuit_breaker.failure_count,
            "failure_threshold": self.circuit_breaker.failure_threshold,
            "last_failure": self.circuit_breaker.last_failure_time.isoformat() if self.circuit_breaker.last_failure_time else None
        }

# Global service clients (initialized at startup)
special_education_client = SpecialEducationServiceClient()
auth_client = AuthServiceClient()