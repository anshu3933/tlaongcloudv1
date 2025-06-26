# TLA Educational Platform - API Documentation

**Last Updated**: 2025-06-26  
**Status**: ✅ All Endpoints Operational  
**Base URL**: Multiple services (see service URLs below)

## 🌐 SERVICE ENDPOINTS

| Service | Port | Base URL | Status | Documentation |
|---------|------|----------|--------|---------------|
| **ADK Host** | 8002 | `http://localhost:8002` | ✅ | `/docs` |
| **Auth Service** | 8003 | `http://localhost:8003` | ✅ | `/docs` |
| **Special Ed Service** | 8005 | `http://localhost:8005` | ✅ | `/docs` |
| **MCP Server** | 8001 | `http://localhost:8001` | ✅ | Custom endpoints |
| **Workflow Service** | 8004 | `http://localhost:8004` | ✅ | `/docs` |

## 🎓 STUDENT MANAGEMENT API

### Students Endpoints

#### List All Students
```http
GET /api/v1/students
Host: localhost:8005
```

**Response:**
```json
{
  "items": [
    {
      "id": "e90f1152-38c9-4186-b266-e4a10825c61b",
      "student_id": "TEST123",
      "first_name": "Test",
      "last_name": "Student",
      "middle_name": null,
      "date_of_birth": "2015-01-01",
      "grade_level": "5",
      "disability_codes": ["SLD"],
      "school_district": "Default District", 
      "school_name": "Default School",
      "enrollment_date": "2025-06-26",
      "full_name": "Test Student",
      "case_manager_auth_id": null,
      "primary_teacher_auth_id": null,
      "parent_guardian_auth_ids": [],
      "active_iep_id": null,
      "is_active": true,
      "created_at": "2025-06-26T15:58:01.095268Z",
      "updated_at": null
    }
  ],
  "total": 6,
  "page": 1,
  "size": 20,
  "pages": 1,
  "has_next": false,
  "has_prev": false,
  "metadata": {
    "timestamp": "2025-06-26T16:03:35.024497Z",
    "request_id": null,
    "version": "1.0.0"
  }
}
```

#### Create Student
```http
POST /api/v1/students
Host: localhost:8005
Content-Type: application/json
```

**Request Body:**
```json
{
  "student_id": "STU001",
  "first_name": "John",
  "last_name": "Doe",
  "middle_name": "James",
  "date_of_birth": "2015-03-15",
  "grade_level": "3",
  "disability_codes": ["SLD"],
  "school_district": "Sample District",
  "school_name": "Sample Elementary",
  "enrollment_date": "2025-06-26"
}
```

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440001",
  "student_id": "STU001",
  "first_name": "John",
  "last_name": "Doe",
  "middle_name": "James",
  "date_of_birth": "2015-03-15",
  "grade_level": "3",
  "disability_codes": ["SLD"],
  "school_district": "Sample District",
  "school_name": "Sample Elementary",
  "enrollment_date": "2025-06-26",
  "full_name": "John James Doe",
  "case_manager_auth_id": null,
  "primary_teacher_auth_id": null,
  "parent_guardian_auth_ids": [],
  "active_iep_id": null,
  "is_active": true,
  "created_at": "2025-06-26T16:30:00.000000Z",
  "updated_at": null
}
```

#### Get Student by ID
```http
GET /api/v1/students/{student_id}
Host: localhost:8005
```

**Response:** Same as individual student object above.

#### Update Student
```http
PUT /api/v1/students/{student_id}
Host: localhost:8005
Content-Type: application/json
```

**Request Body:** Same as create, all fields optional except required validation.

#### Search Students
```http
GET /api/v1/students/search?q=john&grade=3&disability=SLD
Host: localhost:8005
```

**Query Parameters:**
- `q`: Search term (searches name, student_id)
- `grade`: Filter by grade level
- `disability`: Filter by disability code
- `active`: Filter by active status (default: true)

## 📋 IEP MANAGEMENT API

### IEP Endpoints

#### Get Student's IEPs
```http
GET /api/v1/ieps/student/{student_id}
Host: localhost:8005
```

**Response:**
```json
[
  {
    "id": "iep-550e8400-e29b-41d4-a716-446655440001",
    "student_id": "550e8400-e29b-41d4-a716-446655440001",
    "status": "active",
    "start_date": "2025-06-26",
    "end_date": "2026-06-26", 
    "academic_year": "2025-2026",
    "goals": [
      {
        "id": "goal-1",
        "domain": "academic",
        "title": "Reading Comprehension",
        "goal_text": "Student will improve reading comprehension skills",
        "target_criteria": "80% accuracy on grade-level passages",
        "measurement_method": "Weekly assessments"
      }
    ],
    "created_at": "2025-06-26T16:30:00.000000Z",
    "updated_at": null
  }
]
```

#### Create IEP
```http
POST /api/v1/ieps?current_user_id=teacher-123
Host: localhost:8005
Content-Type: application/json
```

**Request Body:**
```json
{
  "student_id": "550e8400-e29b-41d4-a716-446655440001",
  "status": "active",
  "start_date": "2025-06-26",
  "end_date": "2026-06-26",
  "academic_year": "2025-2026",
  "goals": [
    {
      "domain": "academic",
      "title": "Reading Comprehension", 
      "goal_text": "Student will improve reading comprehension skills",
      "target_criteria": "80% accuracy on grade-level passages",
      "measurement_method": "Weekly assessments"
    }
  ]
}
```

#### Get IEP by ID
```http
GET /api/v1/ieps/{iep_id}
Host: localhost:8005
```

#### Update IEP
```http
PUT /api/v1/ieps/{iep_id}?current_user_id=teacher-123
Host: localhost:8005
Content-Type: application/json
```

## 🏠 DASHBOARD API

### Dashboard Endpoints

#### Teacher Dashboard (Mock Data)
```http
GET /api/v1/dashboard/teacher/{user_id}
Host: localhost:8005
```

**Response:**
```json
{
  "stats": {
    "total_students": 12,
    "active_ieps": 10,
    "goals_achieved": 23,
    "tasks_due": 5,
    "pending_approvals": 0,
    "compliance_rate": 94.5,
    "overdue_items": 2
  },
  "students": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440001",
      "first_name": "Emma",
      "last_name": "Johnson",
      "grade": "3rd",
      "primary_disability": "Specific Learning Disability",
      "current_iep_status": "Active",
      "progress_percentage": 75,
      "alert_status": "success",
      "alert_message": "Goal achieved this week!",
      "last_activity": "2025-06-26T14:00:00.000Z"
    }
  ],
  "recent_activities": [
    {
      "id": "act-1",
      "type": "iep_updated",
      "description": "Updated reading goals for student",
      "student_id": "550e8400-e29b-41d4-a716-446655440001",
      "student_name": "Emma Johnson",
      "timestamp": "2025-06-26T14:00:00.000Z",
      "user_id": "teacher-123",
      "user_name": "Current Teacher"
    }
  ],
  "pending_tasks": [
    {
      "id": "task-1",
      "type": "iep_review",
      "title": "Annual IEP Review",
      "description": "Annual review meeting scheduled",
      "due_date": "2025-06-27T14:00:00.000Z",
      "priority": "high",
      "student_id": "550e8400-e29b-41d4-a716-446655440001",
      "student_name": "Emma Johnson",
      "status": "pending"
    }
  ],
  "notifications": [
    {
      "id": "notif-1",
      "type": "reminder",
      "title": "IEP Meeting Reminder", 
      "message": "Meeting scheduled for tomorrow at 2 PM",
      "timestamp": "2025-06-26T15:30:00.000Z",
      "read": false,
      "action_url": "/students/550e8400-e29b-41d4-a716-446655440001/iep"
    }
  ],
  "last_updated": "2025-06-26T16:00:00.000Z"
}
```

**Note**: Dashboard endpoints currently return mock data. The frontend combines this with real student data from the `/students` endpoint for accurate counts.

## 🤖 AI & DOCUMENT API

### Query Endpoints (ADK Host)

#### AI Chat Query
```http
POST /api/v1/query
Host: localhost:8002
Content-Type: application/json
```

**Request Body:**
```json
{
  "query": "What assessment reports are available for students with reading difficulties?",
  "options": {
    "include_sources": true,
    "max_documents": 5
  }
}
```

**Response:**
```json
{
  "response": "Based on the available assessment reports, there are several documents that focus on reading difficulties...",
  "sources": [
    {
      "document_name": "AR1.pdf",
      "relevance_score": 0.92,
      "chunk_text": "Reading assessment results show..."
    }
  ],
  "query_id": "query-550e8400-e29b-41d4-a716-446655440001",
  "timestamp": "2025-06-26T16:00:00.000Z"
}
```

### Document Endpoints (MCP Server)

#### List Documents
```http
GET /documents/list
Host: localhost:8001
```

**Response:**
```json
{
  "documents": [
    {
      "id": "doc-1",
      "name": "AR1.pdf",
      "type": "assessment_report",
      "size": 245760,
      "processed_at": "2025-06-26T10:00:00.000Z"
    }
  ],
  "count": 18,
  "processed_chunks": 30
}
```

#### Process Documents
```http
POST /documents/process
Host: localhost:8001
```

**Response:**
```json
{
  "status": "success",
  "documents_processed": 18,
  "chunks_created": 30
}
```

#### Upload Document
```http
POST /documents/upload
Host: localhost:8002
Content-Type: multipart/form-data
```

**Form Data:**
- `file`: Document file (PDF, DOCX, TXT)
- `metadata`: JSON string with document metadata

## 🔐 AUTHENTICATION API

### Auth Endpoints (Auth Service)

#### Login
```http
POST /api/v1/auth/login
Host: localhost:8003
Content-Type: application/json
```

**Request Body:**
```json
{
  "email": "teacher@school.edu",
  "password": "secure_password"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "user": {
      "id": "user-550e8400-e29b-41d4-a716-446655440001",
      "email": "teacher@school.edu",
      "name": "Jane Smith",
      "role": "teacher",
      "permissions": ["read_students", "create_students", "update_ieps"]
    },
    "tokens": {
      "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
      "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
      "token_type": "bearer",
      "expires_in": 1800
    }
  }
}
```

#### Get Current User
```http
GET /api/v1/auth/me
Host: localhost:8003
Authorization: Bearer {access_token}
```

#### Refresh Token
```http
POST /api/v1/auth/refresh
Host: localhost:8003
Content-Type: application/json
```

**Request Body:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

#### Logout
```http
POST /api/v1/auth/logout
Host: localhost:8003
Authorization: Bearer {access_token}
```

## 🏥 HEALTH CHECK ENDPOINTS

### Service Health Checks

All services provide health check endpoints:

```http
GET /health
```

**ADK Host Response:**
```json
{
  "status": "healthy",
  "service": "adk-host", 
  "version": "1.0.0",
  "environment": "development",
  "dependencies": {
    "mcp_server": {
      "status": "healthy",
      "status_code": 200
    },
    "gemini": {
      "status": "available",
      "model": "gemini-2.5-flash"
    }
  }
}
```

**Special Ed Service Response:**
```json
{
  "status": "healthy",
  "service": "special-education",
  "version": "1.0.0", 
  "database": "connected",
  "environment": "development"
}
```

## 📊 ERROR RESPONSES

### Standard Error Format

All APIs use consistent error response format:

```json
{
  "detail": "Student not found",
  "type": "not_found",
  "status_code": 404,
  "timestamp": "2025-06-26T16:00:00.000Z",
  "request_id": "req-550e8400-e29b-41d4-a716-446655440001"
}
```

### Common HTTP Status Codes

| Code | Meaning | Usage |
|------|---------|-------|
| 200 | OK | Successful GET/PUT requests |
| 201 | Created | Successful POST requests |
| 400 | Bad Request | Invalid request data |
| 401 | Unauthorized | Missing/invalid authentication |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource doesn't exist |
| 422 | Unprocessable Entity | Validation errors |
| 500 | Internal Server Error | Server-side errors |

### Validation Error Format

```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "first_name"],
      "msg": "Field required",
      "input": null
    },
    {
      "type": "string_too_short", 
      "loc": ["body", "student_id"],
      "msg": "String should have at least 1 character",
      "input": ""
    }
  ]
}
```

## 🔧 PAGINATION

### List Endpoints Pagination

Most list endpoints support pagination:

```http
GET /api/v1/students?page=2&size=10&sort=created_at&order=desc
```

**Parameters:**
- `page`: Page number (default: 1)
- `size`: Items per page (default: 20, max: 100)
- `sort`: Sort field (default: created_at)
- `order`: Sort order (asc/desc, default: desc)

**Response Structure:**
```json
{
  "items": [...],
  "total": 150,
  "page": 2,
  "size": 10,
  "pages": 15,
  "has_next": true,
  "has_prev": true
}
```

## 🔒 AUTHENTICATION & AUTHORIZATION

### JWT Token Structure

```json
{
  "sub": "user-550e8400-e29b-41d4-a716-446655440001",
  "email": "teacher@school.edu",
  "role": "teacher",
  "permissions": ["read_students", "create_students"],
  "exp": 1672531200,
  "iat": 1672529400
}
```

### Required Headers

For protected endpoints:

```http
Authorization: Bearer {access_token}
Content-Type: application/json
X-Request-ID: {optional_request_id}
```

### Role-Based Permissions

| Role | Permissions |
|------|-------------|
| **Teacher** | read_students, create_students, update_students, read_ieps, create_ieps, update_ieps |
| **Coordinator** | All teacher permissions + approve_ieps, manage_assignments |
| **Admin** | All permissions + manage_users, system_config |

## 🚀 RATE LIMITING

### Current Limits

| Endpoint Type | Limit | Window |
|---------------|-------|---------|
| Authentication | 5 attempts | 15 minutes |
| General API | 100 requests | 1 minute |
| Document Upload | 10 uploads | 1 hour |
| AI Queries | 30 queries | 1 minute |

### Rate Limit Headers

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1672529460
```

## 🔍 TESTING EXAMPLES

### Complete Student Workflow

```bash
# 1. Create a student
curl -X POST http://localhost:8005/api/v1/students \
  -H "Content-Type: application/json" \
  -d '{
    "student_id": "TEST001",
    "first_name": "Alice", 
    "last_name": "Johnson",
    "date_of_birth": "2014-09-15",
    "grade_level": "4",
    "disability_codes": ["SLD"],
    "school_district": "Test District",
    "school_name": "Test Elementary", 
    "enrollment_date": "2025-06-26"
  }'

# 2. Get the student (use ID from response)
curl http://localhost:8005/api/v1/students/{student_id}

# 3. Create an IEP  
curl -X POST "http://localhost:8005/api/v1/ieps?current_user_id=teacher-123" \
  -H "Content-Type: application/json" \
  -d '{
    "student_id": "{student_id}",
    "status": "active",
    "start_date": "2025-06-26",
    "end_date": "2026-06-26", 
    "academic_year": "2025-2026",
    "goals": [
      {
        "domain": "academic",
        "title": "Reading Fluency",
        "goal_text": "Student will improve reading fluency",
        "target_criteria": "90 words per minute",
        "measurement_method": "Weekly timed readings"
      }
    ]
  }'

# 4. Query AI about the student
curl -X POST http://localhost:8002/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What reading interventions are recommended for 4th grade students with specific learning disabilities?"
  }'
```

---

**API Status**: ✅ All Endpoints Operational  
**Documentation**: ✅ Complete with Examples  
**Authentication**: ✅ JWT-based Security  
**Real Data**: ✅ Student Management Fully Functional