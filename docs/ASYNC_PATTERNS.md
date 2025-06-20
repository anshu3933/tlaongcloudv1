# Async/Await Patterns and Best Practices

## Overview

This document outlines the async/await patterns implemented in the Special Education RAG System and best practices for maintaining proper async code.

## When to Use Async

### ✅ Always Async
- **Database operations** (SQLAlchemy async sessions)
- **HTTP requests** (API calls, external services)
- **File I/O operations** (reading/writing files)
- **Network operations** (Redis, external APIs)

### ⚠️ Use with Thread Pool
- **CPU-intensive operations** (password hashing, data processing)
- **Synchronous third-party APIs** (Google Genai, ML models)
- **Blocking operations** (compression, encryption)

### ❌ Don't Make Async
- **Simple data transformations** (JSON parsing, string operations)
- **Configuration loading** (environment variables)
- **Pure calculations** (math operations)

## Implementation Patterns

### 1. Database Operations
```python
# ✅ Good - Proper async database usage
async def get_user(self, user_id: int) -> Optional[User]:
    result = await self.session.execute(
        select(User).where(User.id == user_id)
    )
    return result.scalar_one_or_none()
```

### 2. HTTP Requests
```python
# ✅ Good - Async HTTP client
async def call_external_api(self, endpoint: str) -> Dict:
    async with self.http_client.get(endpoint) as response:
        return await response.json()
```

### 3. CPU-Intensive Operations
```python
# ✅ Good - Use thread pool for blocking operations
async def hash_password_async(password: str) -> str:
    """Hash password in thread pool to avoid blocking event loop"""
    return await asyncio.to_thread(pwd_context.hash, password)

async def generate_ai_content(prompt: str) -> str:
    """Run AI generation in thread pool"""
    return await asyncio.to_thread(ai_model.generate, prompt)
```

### 4. File Operations
```python
# ✅ Good - Async file operations
async def read_config_file(self, path: str) -> Dict:
    async with aiofiles.open(path, 'r') as f:
        content = await f.read()
        return json.loads(content)
```

## Current Implementation

### IEP Generator (Fixed ✅)
- **Google Gemini API calls** now use `asyncio.to_thread()` to prevent event loop blocking
- **Vector store operations** properly async
- **Content generation** non-blocking

### Authentication Service (Enhanced ✅)
- **Password hashing** available in both sync and async variants
- **Database operations** fully async
- **JWT operations** synchronous (fast enough)

### Database Layer (Correct ✅)
- **All repositories** use async SQLAlchemy
- **Connection management** with async context managers
- **Transaction handling** properly async

## Performance Considerations

### Thread Pool Sizing
```python
# Configure thread pool for CPU-intensive operations
import asyncio
import concurrent.futures

# Set appropriate thread pool size
executor = concurrent.futures.ThreadPoolExecutor(max_workers=4)
asyncio.get_event_loop().set_default_executor(executor)
```

### Connection Pooling
```python
# Database connection pooling (already configured)
engine = create_async_engine(
    database_url,
    pool_size=20,
    max_overflow=30,
    pool_recycle=300
)
```

## Testing Async Code

### Test Fixtures
```python
@pytest.fixture
async def async_client():
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

@pytest.mark.asyncio
async def test_async_endpoint(async_client):
    response = await async_client.get("/api/endpoint")
    assert response.status_code == 200
```

## Common Pitfalls to Avoid

### ❌ Blocking the Event Loop
```python
# BAD - Blocks event loop
async def bad_password_hash(password: str):
    return pwd_context.hash(password)  # CPU-intensive, blocks event loop

# GOOD - Non-blocking
async def good_password_hash(password: str):
    return await asyncio.to_thread(pwd_context.hash, password)
```

### ❌ Unnecessary Async
```python
# BAD - No I/O operations, shouldn't be async
async def calculate_age(birth_date: date) -> int:
    return (date.today() - birth_date).days // 365

# GOOD - Simple calculation, keep synchronous
def calculate_age(birth_date: date) -> int:
    return (date.today() - birth_date).days // 365
```

### ❌ Mixing Sync/Async
```python
# BAD - Mixing sync/async patterns
def mixed_function():
    result = asyncio.run(async_operation())  # Don't do this in async context
    return process(result)

# GOOD - Keep patterns consistent
async def async_function():
    result = await async_operation()
    return process(result)
```

## Monitoring and Debugging

### Event Loop Monitoring
```python
import asyncio
import time

async def monitor_task_duration():
    """Monitor for slow tasks that might block the event loop"""
    start_time = time.time()
    await some_operation()
    duration = time.time() - start_time
    
    if duration > 0.1:  # Log if operation takes more than 100ms
        logger.warning(f"Slow async operation detected: {duration:.2f}s")
```

### Async Stack Traces
```python
# Enable detailed async stack traces for debugging
import asyncio
asyncio.get_event_loop().set_debug(True)
```

## Migration Guidelines

When updating existing code to proper async patterns:

1. **Identify blocking operations** (CPU-intensive, sync APIs)
2. **Wrap with asyncio.to_thread()** for blocking operations
3. **Update calling code** to use await
4. **Test thoroughly** to ensure no regressions
5. **Monitor performance** to verify improvements

## References

- [FastAPI Async Best Practices](https://fastapi.tiangolo.com/async/)
- [SQLAlchemy Async Documentation](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
- [Python asyncio Documentation](https://docs.python.org/3/library/asyncio.html)