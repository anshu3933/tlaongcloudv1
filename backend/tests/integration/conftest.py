"""Shared test configuration and fixtures for integration tests."""

import os
import pytest
import asyncio
from typing import AsyncGenerator
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

# Set test environment
os.environ["ENVIRONMENT"] = "test"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test_integration.db"
os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-integration-tests"
os.environ["GCP_PROJECT_ID"] = "test-project"
os.environ["SMTP_ENABLED"] = "false"

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def integration_test_engine():
    """Create a test database engine for integration tests."""
    test_db_url = "sqlite+aiosqlite:///./test_integration.db"
    engine = create_async_engine(test_db_url, echo=False)
    yield engine
    await engine.dispose()
    
    # Clean up test database file
    try:
        os.remove("./test_integration.db")
    except FileNotFoundError:
        pass

@pytest.fixture
async def integration_db_session(integration_test_engine):
    """Create a database session for integration tests."""
    async_session = async_sessionmaker(
        integration_test_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session
        await session.rollback()

@pytest.fixture
def anyio_backend():
    """Use asyncio as the anyio backend for pytest-asyncio."""
    return "asyncio"