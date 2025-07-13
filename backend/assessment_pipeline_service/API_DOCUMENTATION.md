# Assessment Pipeline Service - API Documentation

## Service Overview

The Assessment Pipeline Service is a **processing-only microservice** designed for psychoeducational assessment document processing and data quantification. It operates without direct database access, using service-to-service communication for all data persistence.

### Service Architecture
- **Type**: Processing-only microservice
- **Port**: 8006 (development)
- **Dependencies**: 
  - Special Education Service (:8005) - Data persistence
  - Auth Service (:8003) - JWT authentication
- **Database Access**: None (service-to-service communication only)

---

## Authentication & Authorization

All endpoints require JWT authentication with role-based access control:

### Required Roles
- **Teacher or above**: Most processing operations
- **Coordinator or above**: Administrative metrics and management
- **Admin**: System administration

### Authentication Headers
```http
Authorization: Bearer <jwt_token>
```

---

## API Endpoints

### 1. Document Upload & Processing

#### `POST /assessment-pipeline/processing/upload`
Upload a single assessment document for processing.

**Authentication**: Teacher+ required

**Request Body**:
```json
{
  "student_id": "uuid",
  "document_type": "wisc_v|wiat_iv|wj_iv|basc_3|conners_3|ktea_3|das_ii|brief_2",
  "file_name": "assessment_report.pdf",
  "file_path": "/path/to/document.pdf",
  "assessment_date": "2025-01-15T10:30:00Z",
  "assessor_name": "Dr. Jane Smith",
  "assessor_title": "School Psychologist",
  "referral_reason": "Cognitive assessment for academic concerns"
}
```

**Response**:
```json
{
  "document_id": "uuid",
  "status": "uploaded",
  "message": "Document uploaded successfully. Processing will begin shortly.",
  "service_response_time_ms": 45.2
}
```

**Error Responses**:
- `400`: Invalid request data
- `401`: Authentication required
- `403`: Insufficient permissions
- `500`: Service error

---

#### `POST /assessment-pipeline/processing/upload-batch`
Upload multiple assessment documents for batch processing.

**Authentication**: Teacher+ required

**Request Body**:
```json
{
  "documents": [
    {
      "student_id": "uuid",
      "document_type": "wisc_v",
      "file_name": "cognitive_assessment.pdf",
      "file_path": "/path/to/cognitive_assessment.pdf",
      "assessment_date": "2025-01-15T10:30:00Z",
      "assessor_name": "Dr. Jane Smith",
      "assessor_title": "School Psychologist",
      "referral_reason": "Cognitive assessment"
    },
    {
      "student_id": "uuid",
      "document_type": "wiat_iv",
      "file_name": "academic_assessment.pdf",
      "file_path": "/path/to/academic_assessment.pdf",
      "assessment_date": "2025-01-16T14:00:00Z",
      "assessor_name": "Dr. Jane Smith",
      "assessor_title": "School Psychologist",
      "referral_reason": "Academic assessment"
    }
  ]
}
```

**Response**:
```json
{
  "document_ids": ["uuid1", "uuid2"],
  "status": "completed",
  "successful_uploads": 2,
  "failed_uploads": 0,
  "message": "Successfully uploaded 2 of 2 documents.",
  "failures": []
}
```

---

### 2. Data Extraction & Processing

#### `POST /assessment-pipeline/processing/extract/{document_id}`
Extract scores and data from an uploaded assessment document.

**Authentication**: Teacher+ required

**Path Parameters**:
- `document_id`: UUID of the uploaded document

**Response**:
```json
{
  "document_id": "uuid",
  "extraction_status": "success",
  "confidence_score": 0.92,
  "extracted_scores": [
    {
      "test_name": "WISC-V",
      "subtest_name": "Verbal Comprehension",
      "standard_score": 115,
      "percentile_rank": 84,
      "confidence_interval": [108, 122],
      "classification": "High Average"
    }
  ],
  "processing_notes": "High confidence extraction completed",
  "service_response_time_ms": 1250.5
}
```

---

#### `POST /assessment-pipeline/processing/quantify/{document_id}`
Quantify assessment metrics for RAG integration.

**Authentication**: Teacher+ required

**Path Parameters**:
- `document_id`: UUID of the document with extracted data

**Response**:
```json
{
  "document_id": "uuid",
  "quantification_status": "success",
  "metrics": {
    "cognitive_composite": 110,
    "academic_composite": 95,
    "behavioral_composite": 85
  },
  "grade_level_analysis": {
    "current_grade": "5th",
    "functioning_level": "4th grade equivalent",
    "strengths": ["Visual processing", "Working memory"],
    "needs": ["Reading fluency", "Math computation"]
  },
  "service_response_time_ms": 850.3
}
```

---

### 3. Status & Monitoring

#### `GET /assessment-pipeline/processing/status/{document_id}`
Get processing status for a document.

**Authentication**: Any authenticated user

**Path Parameters**:
- `document_id`: UUID of the document

**Response**:
```json
{
  "document_id": "uuid",
  "processing_status": "completed",
  "confidence_score": 0.89,
  "processing_notes": "Document processed successfully",
  "created_at": "2025-01-15T10:30:00Z",
  "updated_at": "2025-01-15T10:35:00Z",
  "service_response_time_ms": 25.1
}
```

**Processing Status Values**:
- `pending`: Upload completed, processing queued
- `in_progress`: Currently being processed
- `completed`: Processing finished successfully
- `failed`: Processing failed
- `manual_entry`: Manually entered data

---

#### `GET /assessment-pipeline/processing/health`
Service health check with dependency status.

**Authentication**: None required

**Response**:
```json
{
  "status": "healthy",
  "service": "assessment_pipeline_processing",
  "version": "2.0.0",
  "timestamp": "2025-01-15T15:30:00Z",
  "dependencies": {
    "special_education_service": "connected",
    "auth_service": "connected",
    "assessment_processor": "active"
  },
  "capabilities": [
    "Document upload and processing",
    "Score extraction with 76-98% confidence",
    "Data quantification for RAG integration",
    "Background processing with status tracking",
    "Service-oriented architecture (no direct database access)"
  ]
}
```

---

#### `GET /assessment-pipeline/processing/metrics`
Get processing metrics and communication statistics.

**Authentication**: Coordinator+ required

**Response**:
```json
{
  "service": "assessment_pipeline_processing",
  "timestamp": "2025-01-15T15:30:00Z",
  "communication_metrics": {
    "communication_metrics": {
      "special_education_service": {
        "total_requests": 45,
        "successful_requests": 42,
        "failed_requests": 3,
        "success_rate": 0.93,
        "average_response_time_ms": 234.5
      },
      "auth_service": {
        "total_requests": 15,
        "successful_requests": 15,
        "failed_requests": 0,
        "success_rate": 1.0,
        "average_response_time_ms": 45.2
      }
    },
    "active_requests": 2,
    "history_size": 100
  },
  "recent_activity": [
    {
      "request_id": "uuid",
      "status": "success",
      "target_service": "special_education_service",
      "operation": "create_assessment_document",
      "execution_time_ms": 125.5,
      "timestamp": "2025-01-15T15:29:45Z"
    }
  ]
}
```

---

### 4. Legacy Routes (Pipeline Orchestration)

#### `POST /assessment-pipeline/orchestrator/execute-complete`
Execute complete assessment pipeline from documents to IEP.

**Authentication**: Teacher+ required

**Request Body**:
```json
{
  "student_id": "uuid",
  "assessment_documents": [
    {
      "file_name": "cognitive_assessment.pdf",
      "file_path": "/path/to/document.pdf",
      "assessment_type": "wisc_v"
    }
  ],
  "template_id": "uuid",
  "academic_year": "2025-2026",
  "generate_iep": true
}
```

**Response**:
```json
{
  "status": "success",
  "message": "Complete assessment pipeline executed successfully",
  "pipeline_result": {
    "extraction_results": {...},
    "quantification_results": {...},
    "iep_generation_results": {...}
  }
}
```

---

## Error Handling

### Standard Error Response Format
```json
{
  "detail": "Error description",
  "status_code": 400,
  "timestamp": "2025-01-15T15:30:00Z",
  "correlation_id": "uuid"
}
```

### Common Error Codes
- **400 Bad Request**: Invalid request data or parameters
- **401 Unauthorized**: Missing or invalid JWT token
- **403 Forbidden**: Insufficient permissions for operation
- **404 Not Found**: Requested resource not found
- **422 Unprocessable Entity**: Validation errors in request data
- **500 Internal Server Error**: Service processing error
- **503 Service Unavailable**: Dependent service unavailable

---

## Service Communication

### Circuit Breaker Pattern
The service implements circuit breaker patterns for fault tolerance:
- **Failure Threshold**: 5 consecutive failures
- **Recovery Timeout**: 60 seconds
- **States**: CLOSED, OPEN, HALF_OPEN

### Retry Logic
- **Max Retries**: 3 attempts
- **Backoff Strategy**: Exponential backoff (1s, 2s, 4s)
- **Retry Conditions**: Network errors, 5xx responses
- **No Retry**: 4xx client errors

### Request Correlation
All requests include correlation IDs for tracking:
- Format: `operation-{timestamp}-{uuid}`
- Used for: Debugging, performance monitoring, audit trails

---

## Performance & Monitoring

### Key Metrics
- **Request Success Rate**: >95% target
- **Average Response Time**: <500ms for simple operations
- **Document Processing Time**: 30-120 seconds depending on complexity
- **Service Availability**: >99.9% target

### Health Check Endpoints
- **Service Health**: `GET /health`
- **Processing Health**: `GET /assessment-pipeline/processing/health`
- **Metrics**: `GET /assessment-pipeline/processing/metrics`

---

## Integration Guide

### For Frontend Applications
1. **Authentication**: Include JWT token in Authorization header
2. **Upload Documents**: Use `/processing/upload` or `/processing/upload-batch`
3. **Monitor Progress**: Poll `/processing/status/{document_id}`
4. **Handle Errors**: Implement retry logic for 5xx errors

### For Other Services
1. **Service Discovery**: Service runs on port 8006
2. **Health Checks**: Use `/health` endpoint for service discovery
3. **Circuit Breaker**: Implement client-side circuit breaker for resilience
4. **Correlation IDs**: Include correlation headers for request tracking

### Example Integration Code
```python
import httpx
import asyncio

async def upload_assessment(token: str, assessment_data: dict):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8006/assessment-pipeline/processing/upload",
            json=assessment_data,
            headers={"Authorization": f"Bearer {token}"},
            timeout=60.0
        )
        return response.json()
```

---

## Change Log

### Version 2.0.0 (Current)
- **New**: Processing-only architecture
- **New**: Service-to-service communication
- **New**: Circuit breaker patterns
- **New**: Comprehensive error handling
- **New**: JWT authentication integration
- **Improved**: Performance monitoring
- **Removed**: Direct database access

### Migration Notes
- Legacy endpoints remain available during transition
- New processing endpoints recommended for all new integrations
- Backward compatibility maintained for existing clients