# Integration Test Suite

This test suite validates the concurrent IEP creation functionality and version conflict resolution that was implemented to fix the database integrity constraint violations.

## Test Categories

### 1. Concurrent IEP Creation Tests (`test_concurrent_iep_creation.py`)
Tests the core functionality that resolves version conflicts during concurrent IEP creation:

- **Sequential Creation**: Basic IEP versioning works correctly
- **Same Student Concurrency**: Multiple concurrent requests for same student resolve correctly
- **Different Students**: Concurrent requests for different students work independently  
- **Different Academic Years**: Version isolation between academic years
- **High Concurrency Stress Test**: 20+ concurrent requests with retry mechanism validation

### 2. Version Integrity Tests (`test_version_integrity.py`)
Tests the database constraints and version management:

- **Version Uniqueness**: Ensures versions are properly assigned and unique
- **Parent-Child Relationships**: Validates IEP version chains remain intact
- **Atomic Version Assignment**: Tests the get_next_version_number mechanism
- **Concurrent Version Assignment**: Ensures no duplicate version numbers
- **Isolation Testing**: Versions isolated between students and academic years
- **Latest Version Retrieval**: Correct latest version identification

### 3. Load Performance Tests (`test_load_performance.py`)
Tests system behavior under stress and performance characteristics:

- **Concurrent Student Creation**: Performance of bulk student operations
- **Mixed Workload**: Combined student creation, IEP creation, and queries
- **Retry Mechanism Performance**: Impact of retry logic under contention
- **Database Connection Pool**: Behavior under database pressure

## Key Features Tested

### ✅ Retry Mechanism
- Exponential backoff with jitter
- Conflict detection and automatic retry
- Maximum retry limits
- Success rate validation under high concurrency

### ✅ Version Conflict Resolution  
- Atomic version number assignment using PostgreSQL advisory locks
- SQLite fallback for development environments
- Request-scoped database sessions
- Proper parent-child relationship maintenance

### ✅ Database Integrity
- Unique constraint enforcement
- Foreign key relationship validation
- Transaction isolation
- Connection pool management

## Running the Tests

### Quick Test Commands
```bash
# Run all integration tests
./dev-tools.sh test-integration

# Run just concurrent creation tests
./dev-tools.sh test-concurrent

# Run performance tests (slower)
./dev-tools.sh test-performance

# Run all tests including performance
./dev-tools.sh test-all
```

### Direct pytest Commands
```bash
# Basic integration tests (fast)
pytest tests/test_concurrent_iep_creation.py -v

# Version integrity tests
pytest tests/test_version_integrity.py -v

# Performance tests (slow)
pytest tests/test_load_performance.py -v -m performance

# All tests with coverage
pytest tests/ --cov=src --cov-report=html
```

### Test Markers
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.concurrent` - Concurrency-focused tests  
- `@pytest.mark.performance` - Performance/load tests
- `@pytest.mark.slow` - Tests that take longer to run

## Test Environment

The tests use:
- **In-memory SQLite** for fast test execution
- **Mock dependencies** for vector store and AI generation
- **Async/await patterns** throughout
- **Isolated test sessions** with automatic rollback

## Expected Results

### Success Criteria
- **95%+ success rate** for concurrent operations
- **Sequential version numbers** with no duplicates
- **Proper parent-child relationships** in version chains
- **Isolated versioning** between students and academic years
- **Reasonable performance** under load

### Performance Expectations
- Student creation: <500ms average
- IEP creation with retry: <2.0s average under high contention
- Mixed workload: >90% success rate
- High concurrency (20+ tasks): >85% success rate

## Troubleshooting

### Common Issues
1. **Import Errors**: Ensure all dependencies are installed (`pip install -r requirements.txt`)
2. **Database Connection**: Tests use in-memory SQLite, no external DB needed
3. **Timeout Failures**: Performance tests may timeout on slower systems

### Debug Mode
```bash
# Run with detailed logging
pytest tests/ -v -s --log-cli-level=DEBUG

# Run single test with output
pytest tests/test_concurrent_iep_creation.py::TestConcurrentIEPCreation::test_concurrent_iep_creation_same_student -v -s
```

## Implementation Context

These tests validate the solution to the original problem:

**Original Issue**: Database integrity constraint violations during concurrent IEP creation
- Multiple requests created IEPs with duplicate version numbers
- Unique constraint violations on (student_id, academic_year, version)

**Solution Implemented**:
1. **Atomic Version Assignment**: `get_next_version_number()` with advisory locks
2. **Retry Mechanism**: Exponential backoff for temporary conflicts  
3. **Request-Scoped Sessions**: Proper async session lifecycle management
4. **Conflict Detection**: Convert database exceptions to retryable errors

**Result**: These tests demonstrate that concurrent IEP creation now works reliably with proper version sequencing and conflict resolution.