"""
Service-to-Service Communication Patterns for Assessment Pipeline
Implements communication protocols, error handling, and coordination patterns
"""
import logging
import asyncio
import json
from typing import Dict, List, Any, Optional, Tuple, Callable
from uuid import UUID, uuid4
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, asdict
import httpx

from assessment_pipeline_service.src.service_clients import (
    special_education_client, auth_client, ServiceError, ServiceUnavailableError, ServiceTimeoutError
)

logger = logging.getLogger(__name__)

class CommunicationStatus(Enum):
    """Status of service communication operations"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CIRCUIT_OPEN = "circuit_open"

class ServiceType(Enum):
    """Types of services in the architecture"""
    SPECIAL_EDUCATION = "special_education_service"
    AUTH_SERVICE = "auth_service"
    ADK_HOST = "adk_host"
    ASSESSMENT_PIPELINE = "assessment_pipeline_service"

@dataclass
class ServiceRequest:
    """Structured service request with tracking"""
    id: str
    source_service: ServiceType
    target_service: ServiceType
    operation: str
    payload: Dict[str, Any]
    correlation_id: str
    timestamp: datetime
    timeout_seconds: int = 60
    retry_count: int = 0
    max_retries: int = 3
    
@dataclass
class ServiceResponse:
    """Structured service response with metadata"""
    request_id: str
    status: CommunicationStatus
    data: Optional[Dict[str, Any]]
    error_message: Optional[str]
    execution_time_ms: float
    timestamp: datetime
    metadata: Dict[str, Any]

@dataclass
class CommunicationMetrics:
    """Metrics for service communication monitoring"""
    total_requests: int
    successful_requests: int
    failed_requests: int
    average_response_time_ms: float
    circuit_breaker_trips: int
    timeout_errors: int
    last_updated: datetime

class ServiceCommunicationManager:
    """Central manager for all service-to-service communication"""
    
    def __init__(self):
        self.active_requests: Dict[str, ServiceRequest] = {}
        self.communication_history: List[ServiceResponse] = []
        self.metrics: Dict[ServiceType, CommunicationMetrics] = {}
        self.request_callbacks: Dict[str, Callable] = {}
        
        # Initialize metrics for all services
        for service_type in ServiceType:
            self.metrics[service_type] = CommunicationMetrics(
                total_requests=0,
                successful_requests=0,
                failed_requests=0,
                average_response_time_ms=0.0,
                circuit_breaker_trips=0,
                timeout_errors=0,
                last_updated=datetime.utcnow()
            )
    
    async def send_request(
        self,
        target_service: ServiceType,
        operation: str,
        payload: Dict[str, Any],
        correlation_id: Optional[str] = None,
        timeout_seconds: int = 60,
        retry_enabled: bool = True
    ) -> ServiceResponse:
        """
        Send a request to another service with comprehensive error handling
        
        Args:
            target_service: Target service type
            operation: Operation to perform
            payload: Request payload
            correlation_id: Optional correlation ID for tracking
            timeout_seconds: Request timeout
            retry_enabled: Whether to retry on failure
            
        Returns:
            ServiceResponse with result or error information
        """
        request_id = str(uuid4())
        correlation_id = correlation_id or str(uuid4())
        start_time = datetime.utcnow()
        
        # Create request object
        request = ServiceRequest(
            id=request_id,
            source_service=ServiceType.ASSESSMENT_PIPELINE,
            target_service=target_service,
            operation=operation,
            payload=payload,
            correlation_id=correlation_id,
            timestamp=start_time,
            timeout_seconds=timeout_seconds,
            max_retries=3 if retry_enabled else 0
        )
        
        self.active_requests[request_id] = request
        
        logger.info(
            f"Sending request {request_id} to {target_service.value} "
            f"operation: {operation}, correlation: {correlation_id}"
        )
        
        try:
            # Execute the request with retry logic
            response_data, execution_time = await self._execute_request_with_retries(request)
            
            # Create successful response
            response = ServiceResponse(
                request_id=request_id,
                status=CommunicationStatus.SUCCESS,
                data=response_data,
                error_message=None,
                execution_time_ms=execution_time,
                timestamp=datetime.utcnow(),
                metadata={
                    "correlation_id": correlation_id,
                    "retry_count": request.retry_count,
                    "target_service": target_service.value,
                    "operation": operation
                }
            )
            
            # Update metrics
            await self._update_metrics(target_service, True, execution_time)
            
            logger.info(
                f"Request {request_id} completed successfully in {execution_time:.2f}ms"
            )
            
            return response
            
        except Exception as e:
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            # Determine error type
            if isinstance(e, ServiceTimeoutError):
                status = CommunicationStatus.TIMEOUT
                await self._update_metrics(target_service, False, execution_time, timeout=True)
            elif isinstance(e, ServiceUnavailableError):
                status = CommunicationStatus.CIRCUIT_OPEN
                await self._update_metrics(target_service, False, execution_time, circuit_break=True)
            else:
                status = CommunicationStatus.FAILED
                await self._update_metrics(target_service, False, execution_time)
            
            # Create error response
            response = ServiceResponse(
                request_id=request_id,
                status=status,
                data=None,
                error_message=str(e),
                execution_time_ms=execution_time,
                timestamp=datetime.utcnow(),
                metadata={
                    "correlation_id": correlation_id,
                    "retry_count": request.retry_count,
                    "target_service": target_service.value,
                    "operation": operation,
                    "error_type": type(e).__name__
                }
            )
            
            logger.error(
                f"Request {request_id} failed after {request.retry_count} retries: {e}"
            )
            
            return response
            
        finally:
            # Clean up
            if request_id in self.active_requests:
                del self.active_requests[request_id]
            
            # Store in history (keep last 1000 requests)
            self.communication_history.append(response)
            if len(self.communication_history) > 1000:
                self.communication_history = self.communication_history[-1000:]
    
    async def _execute_request_with_retries(
        self, 
        request: ServiceRequest
    ) -> Tuple[Dict[str, Any], float]:
        """Execute request with retry logic"""
        
        for attempt in range(request.max_retries + 1):
            request.retry_count = attempt
            start_time = datetime.utcnow()
            
            try:
                if request.target_service == ServiceType.SPECIAL_EDUCATION:
                    response_data = await self._call_special_education_service(
                        request.operation, request.payload
                    )
                elif request.target_service == ServiceType.AUTH_SERVICE:
                    response_data = await self._call_auth_service(
                        request.operation, request.payload
                    )
                else:
                    raise ServiceError(f"Unsupported target service: {request.target_service}")
                
                execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
                return response_data, execution_time
                
            except (ServiceTimeoutError, ServiceUnavailableError):
                # Don't retry circuit breaker or timeout errors
                raise
            except Exception as e:
                if attempt == request.max_retries:
                    raise
                
                # Exponential backoff
                wait_time = min(2 ** attempt, 16)  # Max 16 seconds
                logger.warning(
                    f"Request {request.id} attempt {attempt + 1} failed: {e}. "
                    f"Retrying in {wait_time}s..."
                )
                await asyncio.sleep(wait_time)
    
    async def _call_special_education_service(
        self, 
        operation: str, 
        payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Call special education service operations"""
        
        # Map operations to client methods
        if operation == "create_assessment_document":
            return await special_education_client.create_assessment_document(payload)
        elif operation == "update_assessment_document":
            document_id = payload.pop("document_id")
            return await special_education_client.update_assessment_document(document_id, payload)
        elif operation == "create_psychoed_scores":
            return await special_education_client.create_psychoed_scores(payload.get("scores", []))
        elif operation == "create_extracted_data":
            return await special_education_client.create_extracted_data(payload)
        elif operation == "create_quantified_data":
            return await special_education_client.create_quantified_data(payload)
        elif operation == "get_student_assessment_data":
            student_id = payload.get("student_id")
            return await special_education_client.get_student_assessment_data(student_id)
        elif operation == "health_check":
            return await special_education_client.health_check()
        else:
            raise ServiceError(f"Unknown special education service operation: {operation}")
    
    async def _call_auth_service(
        self, 
        operation: str, 
        payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Call auth service operations"""
        
        if operation == "validate_token":
            token = payload.get("token")
            result = await auth_client.validate_token(token)
            return result if result else {"valid": False}
        elif operation == "get_user_info":
            user_id = payload.get("user_id")
            result = await auth_client.get_user_info(user_id)
            return result if result else {"error": "User not found"}
        elif operation == "health_check":
            return await auth_client.health_check()
        else:
            raise ServiceError(f"Unknown auth service operation: {operation}")
    
    async def _update_metrics(
        self,
        service_type: ServiceType,
        success: bool,
        execution_time_ms: float,
        timeout: bool = False,
        circuit_break: bool = False
    ):
        """Update communication metrics"""
        
        metrics = self.metrics[service_type]
        metrics.total_requests += 1
        
        if success:
            metrics.successful_requests += 1
        else:
            metrics.failed_requests += 1
            
        if timeout:
            metrics.timeout_errors += 1
            
        if circuit_break:
            metrics.circuit_breaker_trips += 1
        
        # Update average response time
        if metrics.total_requests > 1:
            metrics.average_response_time_ms = (
                (metrics.average_response_time_ms * (metrics.total_requests - 1) + execution_time_ms) /
                metrics.total_requests
            )
        else:
            metrics.average_response_time_ms = execution_time_ms
        
        metrics.last_updated = datetime.utcnow()
    
    async def batch_request(
        self,
        requests: List[Tuple[ServiceType, str, Dict[str, Any]]],
        correlation_id: Optional[str] = None
    ) -> List[ServiceResponse]:
        """Execute multiple requests concurrently"""
        
        correlation_id = correlation_id or str(uuid4())
        logger.info(f"Executing batch request with {len(requests)} operations, correlation: {correlation_id}")
        
        # Create tasks for concurrent execution
        tasks = []
        for target_service, operation, payload in requests:
            task = self.send_request(
                target_service, operation, payload, 
                correlation_id=f"{correlation_id}-{len(tasks)}"
            )
            tasks.append(task)
        
        # Execute all requests concurrently
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Convert exceptions to error responses
        processed_responses = []
        for i, response in enumerate(responses):
            if isinstance(response, Exception):
                error_response = ServiceResponse(
                    request_id=f"batch-{correlation_id}-{i}",
                    status=CommunicationStatus.FAILED,
                    data=None,
                    error_message=str(response),
                    execution_time_ms=0.0,
                    timestamp=datetime.utcnow(),
                    metadata={"correlation_id": correlation_id, "batch_index": i}
                )
                processed_responses.append(error_response)
            else:
                processed_responses.append(response)
        
        logger.info(
            f"Batch request {correlation_id} completed: "
            f"{sum(1 for r in processed_responses if r.status == CommunicationStatus.SUCCESS)}/{len(requests)} successful"
        )
        
        return processed_responses
    
    def get_service_metrics(self, service_type: ServiceType) -> Dict[str, Any]:
        """Get communication metrics for a specific service"""
        metrics = self.metrics[service_type]
        return {
            "service": service_type.value,
            "total_requests": metrics.total_requests,
            "successful_requests": metrics.successful_requests,
            "failed_requests": metrics.failed_requests,
            "success_rate": (
                metrics.successful_requests / metrics.total_requests 
                if metrics.total_requests > 0 else 0.0
            ),
            "average_response_time_ms": metrics.average_response_time_ms,
            "circuit_breaker_trips": metrics.circuit_breaker_trips,
            "timeout_errors": metrics.timeout_errors,
            "last_updated": metrics.last_updated.isoformat()
        }
    
    def get_all_metrics(self) -> Dict[str, Any]:
        """Get metrics for all services"""
        return {
            "communication_metrics": {
                service_type.value: self.get_service_metrics(service_type)
                for service_type in ServiceType
            },
            "active_requests": len(self.active_requests),
            "history_size": len(self.communication_history),
            "overall_stats": {
                "total_requests": sum(m.total_requests for m in self.metrics.values()),
                "total_successful": sum(m.successful_requests for m in self.metrics.values()),
                "total_failed": sum(m.failed_requests for m in self.metrics.values())
            }
        }
    
    def get_recent_communication_history(
        self, 
        limit: int = 50,
        service_type: Optional[ServiceType] = None
    ) -> List[Dict[str, Any]]:
        """Get recent communication history"""
        
        history = self.communication_history[-limit:] if not service_type else [
            response for response in self.communication_history[-limit*2:]
            if response.metadata.get("target_service") == service_type.value
        ][-limit:]
        
        return [
            {
                "request_id": response.request_id,
                "status": response.status.value,
                "target_service": response.metadata.get("target_service"),
                "operation": response.metadata.get("operation"),
                "execution_time_ms": response.execution_time_ms,
                "timestamp": response.timestamp.isoformat(),
                "error_message": response.error_message,
                "correlation_id": response.metadata.get("correlation_id")
            }
            for response in history
        ]

# Global service communication manager
service_comm_manager = ServiceCommunicationManager()

# Convenience functions for common operations
async def create_assessment_document(document_data: Dict[str, Any], correlation_id: Optional[str] = None) -> ServiceResponse:
    """Create assessment document via special education service"""
    return await service_comm_manager.send_request(
        ServiceType.SPECIAL_EDUCATION,
        "create_assessment_document",
        document_data,
        correlation_id
    )

async def validate_user_token(token: str, correlation_id: Optional[str] = None) -> ServiceResponse:
    """Validate user token via auth service"""
    return await service_comm_manager.send_request(
        ServiceType.AUTH_SERVICE,
        "validate_token",
        {"token": token},
        correlation_id
    )

async def get_service_health_status() -> Dict[str, Any]:
    """Get health status of all dependent services"""
    
    health_requests = [
        (ServiceType.SPECIAL_EDUCATION, "health_check", {}),
        (ServiceType.AUTH_SERVICE, "health_check", {})
    ]
    
    responses = await service_comm_manager.batch_request(health_requests, "health-check")
    
    health_status = {}
    for i, (service_type, _, _) in enumerate(health_requests):
        response = responses[i]
        health_status[service_type.value] = {
            "healthy": response.status == CommunicationStatus.SUCCESS,
            "response_time_ms": response.execution_time_ms,
            "status": response.status.value,
            "error": response.error_message,
            "data": response.data
        }
    
    return health_status