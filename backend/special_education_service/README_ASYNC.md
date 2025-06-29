# Async IEP Generation System

## Overview

This is a **production-ready async IEP generation system** that implements all phases of the simplified plan for real Gemini API integration with SQLite concurrency safety.

## System Architecture

```
┌─────────────┐    ┌──────────────┐    ┌───────────────┐    ┌─────────────┐
│   Frontend  │    │  FastAPI     │    │  SQLite Job   │    │   Gemini    │
│             │───▶│  API Layer   │───▶│    Queue      │───▶│     API     │
│             │    │              │    │               │    │             │
└─────────────┘    └──────────────┘    └───────────────┘    └─────────────┘
                           │                    │
                           ▼                    ▼
                   ┌──────────────┐    ┌───────────────┐
                   │  Safe JSON   │    │ SQLite Worker │
                   │  Response    │    │   Process     │
                   └──────────────┘    └───────────────┘
```

## Features

### ✅ Phase 1: Database Schema & Configuration
- SQLite WAL mode for better concurrency
- Job queue table with proper indexing
- Migration system with Alembic

### ✅ Phase 2: Safe JSON Response System  
- orjson for guaranteed serialization
- Round-trip validation
- Defensive datetime handling

### ✅ Phase 3: Enhanced Gemini Integration
- Circuit breaker pattern for API resilience
- Response compression for large outputs
- Structured prompt building
- Pydantic v2 validation schemas

### ✅ Phase 4: SQLite-Safe Background Worker
- Single-writer concurrency model
- Job claiming with timeouts
- Retry logic with exponential backoff
- Graceful shutdown handling

### ✅ Phase 5: Service Layer with Transactional Safety
- Clean separation of concerns
- Comprehensive error handling
- Request validation with Pydantic
- Session management with rollback safety

### ✅ Phase 6: API Layer with Safe JSON
- RESTful endpoints for job management
- Polling support for real-time updates
- Admin endpoints for queue monitoring
- Background task support

### ✅ Phase 7: Testing & Deployment
- Comprehensive test suite
- Startup scripts for workers
- Configuration management
- Health monitoring

## Quick Start

### 1. Install Dependencies

```bash
# Install additional async requirements
pip install -r requirements_async.txt
```

### 2. Set Environment Variables

```bash
export GEMINI_API_KEY="your_gemini_api_key"
export DATABASE_URL="sqlite+aiosqlite:///./special_ed.db"
export ENVIRONMENT="development"
```

### 3. Run Tests

```bash
# Test the complete system
python test_async_system.py

# Or use the worker script in test mode
python start_async_worker.py --test
```

### 4. Start the Worker

```bash
# Start async worker process
python start_async_worker.py --workers 1 --poll-interval 5
```

### 5. Use the API

```bash
# Submit IEP generation job
curl -X POST "http://localhost:8005/api/v1/jobs/iep-generation" \
  -H "Content-Type: application/json" \
  -d '{
    "student_id": "your-student-id",
    "template_id": "your-template-id",
    "academic_year": "2025-2026",
    "include_previous_ieps": true,
    "include_assessments": true,
    "priority": 8
  }'

# Check job status
curl "http://localhost:8005/api/v1/jobs/{job_id}"

# Poll for completion
curl "http://localhost:8005/api/v1/jobs/{job_id}/poll?timeout_seconds=60"
```

## API Endpoints

### Job Management
- `POST /api/v1/jobs/iep-generation` - Submit IEP generation job
- `POST /api/v1/jobs/section-generation` - Submit section generation job  
- `GET /api/v1/jobs/{job_id}` - Get job status
- `GET /api/v1/jobs` - List user jobs
- `PATCH /api/v1/jobs/{job_id}/cancel` - Cancel job
- `GET /api/v1/jobs/{job_id}/poll` - Poll for completion

### Admin Endpoints
- `GET /api/v1/jobs/admin/queue-stats` - Queue statistics
- `POST /api/v1/jobs/admin/cleanup` - Clean up old jobs
- `GET /api/v1/jobs/health` - Job system health check

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `GEMINI_API_KEY` | Required | Google Gemini API key |
| `DATABASE_URL` | SQLite | Database connection string |
| `NUM_WORKERS` | 1 | Number of worker processes |
| `POLL_INTERVAL` | 5 | Worker poll interval (seconds) |
| `ENVIRONMENT` | development | Environment setting |

### Worker Configuration

```python
# Single worker for SQLite safety
worker = SQLiteAsyncWorker(
    worker_id="worker-1",
    poll_interval=5,
    max_retries=3,
    claim_timeout=300  # 5 minutes
)
```

## Job Types

### IEP Generation Job
- **Type**: `iep_generation`
- **Input**: Student data, template, context
- **Output**: Complete IEP with all sections
- **Duration**: 30-120 seconds

### Section Generation Job  
- **Type**: `section_generation`
- **Input**: IEP ID, section type, context
- **Output**: Specific IEP section content
- **Duration**: 10-30 seconds

## Monitoring

### Job Status States
- `pending` - Waiting in queue
- `processing` - Being processed by worker
- `completed` - Successfully completed
- `failed` - Failed after retries
- `cancelled` - Cancelled by user
- `archived` - Old job archived for cleanup

### Health Monitoring
```bash
# Check job system health
curl "http://localhost:8005/api/v1/jobs/health"

# Check queue statistics
curl "http://localhost:8005/api/v1/jobs/admin/queue-stats"
```

## Error Handling

### Retry Logic
- Automatic retry for transient failures
- Exponential backoff with jitter
- Maximum 3 retry attempts
- Circuit breaker for API protection

### Error Types
- **Validation Errors**: Invalid input data
- **API Errors**: Gemini API failures
- **Database Errors**: SQLite concurrency issues
- **Timeout Errors**: Long-running job timeouts

## Performance

### SQLite Optimizations
- WAL mode for concurrent reads
- Proper indexing for job queue
- Single writer to avoid contention
- Batch operations where possible

### Gemini API Optimizations
- Response compression for large outputs
- Circuit breaker to prevent cascading failures
- Request deduplication
- Structured prompts for consistent output

## Deployment

### Production Considerations
1. **Database**: Consider PostgreSQL for high load
2. **Workers**: Scale workers based on job volume
3. **Monitoring**: Implement comprehensive logging
4. **Security**: API authentication and rate limiting
5. **Backup**: Regular database backups

### Docker Deployment
```dockerfile
FROM python:3.11
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt -r requirements_async.txt
CMD ["python", "start_async_worker.py"]
```

## Troubleshooting

### Common Issues

1. **SQLite Lock Errors**
   - Ensure only one worker process
   - Check WAL mode is enabled
   - Verify proper session cleanup

2. **Gemini API Errors**
   - Check API key validity
   - Monitor rate limits
   - Review prompt structure

3. **Job Stuck in Processing**
   - Check worker process is running
   - Review claim timeout settings
   - Check database connectivity

### Debug Commands
```bash
# Check database status
python -c "from src.database import check_database_connection; import asyncio; print(asyncio.run(check_database_connection()))"

# Test Gemini connection
python -c "from src.utils.gemini_client import GeminiClient; import asyncio; client = GeminiClient(); print('Gemini client initialized')"

# Check job queue
sqlite3 special_ed.db "SELECT status, COUNT(*) FROM iep_generation_jobs GROUP BY status;"
```

## Contributing

This system follows production-ready patterns:
- Comprehensive error handling
- Proper logging and monitoring
- Clean separation of concerns
- Extensive testing coverage
- Configuration management

For modifications, ensure all tests pass and follow the established patterns for database transactions, error handling, and async safety.