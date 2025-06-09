import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from ..src.main import app
from ..src.models.user import Base as UserBase
from ..src.models.audit_log import Base as AuditBase

# Test database setup
TEST_DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/test_db"
engine = create_async_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

@pytest.fixture(scope="function")
async def test_db():
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(UserBase.metadata.create_all)
        await conn.run_sync(AuditBase.metadata.create_all)
    
    yield
    
    # Drop tables
    async with engine.begin() as conn:
        await conn.run_sync(UserBase.metadata.drop_all)
        await conn.run_sync(AuditBase.metadata.drop_all)

@pytest.fixture(scope="function")
def client(test_db):
    return TestClient(app)

def test_register_user(client):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@example.com",
            "password": "testpassword",
            "full_name": "Test User",
            "role": "admin"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "user" in data
    assert data["user"]["email"] == "test@example.com"
    assert data["user"]["role"] == "admin"
    assert "message" in data

def test_login_user(client):
    # First register a user
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@example.com",
            "password": "testpassword",
            "full_name": "Test User",
            "role": "admin"
        }
    )
    
    # Then try to login
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "test@example.com",
            "password": "testpassword"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "token_type" in data
    assert "user" in data
    assert data["user"]["email"] == "test@example.com"

def test_verify_token(client):
    # First register and login
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@example.com",
            "password": "testpassword",
            "full_name": "Test User",
            "role": "admin"
        }
    )
    
    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "test@example.com",
            "password": "testpassword"
        }
    )
    token = login_response.json()["access_token"]
    
    # Then verify the token
    response = client.post(
        "/verify-token",
        json={"token": token}
    )
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert "email" in data
    assert "role" in data
    assert data["email"] == "test@example.com"

def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "auth-service" 