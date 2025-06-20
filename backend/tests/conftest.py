"""Test configuration and fixtures"""
import asyncio
import pytest
import os
from typing import AsyncGenerator, Generator
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from httpx import AsyncClient

# Set test environment before importing settings
os.environ.setdefault('ENVIRONMENT', 'testing')
os.environ.setdefault('DATABASE_URL', 'sqlite+aiosqlite:///./test_special_education.db')
os.environ.setdefault('TEST_DATABASE_URL', 'sqlite+aiosqlite:///./test_special_education.db')
os.environ.setdefault('JWT_SECRET_KEY', 'test-jwt-secret-key-for-testing-only-32-chars')
os.environ.setdefault('GCP_PROJECT_ID', 'test-project')
os.environ.setdefault('GCS_BUCKET_NAME', 'test-bucket')
os.environ.setdefault('GEMINI_MODEL', 'gemini-1.5-pro')

from common.src.config import get_settings
from auth_service.src.models import Base
from auth_service.src.main import app as auth_app
from workflow_service.src.main import app as workflow_app
from special_education_service.src.main import app as special_ed_app
from mcp_server.src.main import app as mcp_app
from adk_host.src.main import app as adk_app

# Get test settings from environment
test_settings = get_settings()

# Database setup
engine = create_async_engine(test_settings.database_url)
TestingSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create a fresh database session for each test."""
    async with TestingSessionLocal() as session:
        yield session
        await session.rollback()

@pytest.fixture(scope="session")
def test_client() -> Generator:
    """Create a test client for the auth service."""
    with TestClient(auth_app) as client:
        yield client

@pytest.fixture(scope="session")
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """Create an async test client."""
    async with AsyncClient(app=auth_app, base_url="http://test") as client:
        yield client

@pytest.fixture(scope="session")
def auth_client() -> Generator:
    """Create a test client for the auth service."""
    with TestClient(auth_app) as client:
        yield client

@pytest.fixture(scope="session")
def workflow_client() -> Generator:
    """Create a test client for the workflow service."""
    with TestClient(workflow_app) as client:
        yield client

@pytest.fixture(scope="session")
def special_ed_client() -> Generator:
    """Create a test client for the special education service."""
    with TestClient(special_ed_app) as client:
        yield client

@pytest.fixture(scope="session")
def mcp_client() -> Generator:
    """Create a test client for the MCP server."""
    with TestClient(mcp_app) as client:
        yield client

@pytest.fixture(scope="session")
def adk_client() -> Generator:
    """Create a test client for the ADK host."""
    with TestClient(adk_app) as client:
        yield client

@pytest.fixture(autouse=True)
async def setup_test_db():
    """Set up test database before each test."""
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield
    
    # Drop tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all) 