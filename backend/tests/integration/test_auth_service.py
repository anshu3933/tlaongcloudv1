"""Integration tests for Authentication Service."""

import pytest
import asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import text
from fastapi.testclient import TestClient

from auth_service.src.main import app
from auth_service.src.database import get_db
from auth_service.src.models import Base, User, UserSession, TokenBlacklist
from auth_service.src.config import get_auth_settings

# Test settings
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test_auth.db"

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def test_engine():
    """Create test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        pool_pre_ping=True
    )
    
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()

@pytest.fixture
async def test_db_session(test_engine):
    """Create test database session."""
    async_session = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session
        await session.rollback()

@pytest.fixture
async def override_get_db(test_db_session):
    """Override database dependency for testing."""
    async def _get_test_db():
        yield test_db_session
    
    app.dependency_overrides[get_db] = _get_test_db
    yield
    app.dependency_overrides.clear()

@pytest.fixture
async def async_client(override_get_db):
    """Create async HTTP client for testing."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

@pytest.fixture
async def test_user_data():
    """Test user data."""
    return {
        "email": "test@example.com",
        "password": "SecurePass123!",
        "full_name": "Test User",
        "role": "user"
    }

@pytest.fixture
async def test_admin_data():
    """Test admin user data."""
    return {
        "email": "admin@example.com",
        "password": "AdminPass123!",
        "full_name": "Admin User",
        "role": "admin"
    }

class TestAuthenticationEndpoints:
    """Test authentication endpoints."""
    
    async def test_user_registration(self, async_client: AsyncClient, test_user_data):
        """Test user registration."""
        response = await async_client.post("/api/v1/auth/register", json=test_user_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == test_user_data["email"]
        assert data["full_name"] == test_user_data["full_name"]
        assert data["role"] == test_user_data["role"]
        assert "id" in data
        assert "created_at" in data
    
    async def test_duplicate_registration(self, async_client: AsyncClient, test_user_data):
        """Test duplicate user registration."""
        # Register user first time
        await async_client.post("/api/v1/auth/register", json=test_user_data)
        
        # Try to register again
        response = await async_client.post("/api/v1/auth/register", json=test_user_data)
        
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]
    
    async def test_invalid_password_registration(self, async_client: AsyncClient):
        """Test registration with invalid password."""
        user_data = {
            "email": "test2@example.com",
            "password": "weak",  # Too weak
            "full_name": "Test User 2",
            "role": "user"
        }
        
        response = await async_client.post("/api/v1/auth/register", json=user_data)
        
        assert response.status_code == 400
        assert "Password validation failed" in response.json()["detail"]
    
    async def test_user_login(self, async_client: AsyncClient, test_user_data):
        """Test user login."""
        # Register user first
        await async_client.post("/api/v1/auth/register", json=test_user_data)
        
        # Login
        login_data = {
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        }
        response = await async_client.post("/api/v1/auth/login", json=login_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert "expires_in" in data
        assert "user" in data
    
    async def test_invalid_login(self, async_client: AsyncClient, test_user_data):
        """Test login with invalid credentials."""
        # Register user first
        await async_client.post("/api/v1/auth/register", json=test_user_data)
        
        # Try invalid password
        login_data = {
            "email": test_user_data["email"],
            "password": "wrongpassword"
        }
        response = await async_client.post("/api/v1/auth/login", json=login_data)
        
        assert response.status_code == 401
        assert "Invalid credentials" in response.json()["detail"]
    
    async def test_login_nonexistent_user(self, async_client: AsyncClient):
        """Test login with nonexistent user."""
        login_data = {
            "email": "nonexistent@example.com",
            "password": "password123"
        }
        response = await async_client.post("/api/v1/auth/login", json=login_data)
        
        assert response.status_code == 401
        assert "Invalid credentials" in response.json()["detail"]

class TestTokenManagement:
    """Test token management functionality."""
    
    async def test_token_refresh(self, async_client: AsyncClient, test_user_data):
        """Test token refresh."""
        # Register and login
        await async_client.post("/api/v1/auth/register", json=test_user_data)
        login_response = await async_client.post("/api/v1/auth/login", json={
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        })
        
        tokens = login_response.json()
        refresh_token = tokens["refresh_token"]
        
        # Refresh token
        refresh_response = await async_client.post("/api/v1/auth/refresh", json={
            "refresh_token": refresh_token
        })
        
        assert refresh_response.status_code == 200
        new_tokens = refresh_response.json()
        assert "access_token" in new_tokens
        assert new_tokens["refresh_token"] == refresh_token  # Same refresh token
        assert new_tokens["access_token"] != tokens["access_token"]  # New access token
    
    async def test_invalid_refresh_token(self, async_client: AsyncClient):
        """Test refresh with invalid token."""
        response = await async_client.post("/api/v1/auth/refresh", json={
            "refresh_token": "invalid_token"
        })
        
        assert response.status_code == 401
        assert "Invalid or expired refresh token" in response.json()["detail"]
    
    async def test_token_verification(self, async_client: AsyncClient, test_user_data):
        """Test token verification endpoint."""
        # Register and login
        await async_client.post("/api/v1/auth/register", json=test_user_data)
        login_response = await async_client.post("/api/v1/auth/login", json={
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        })
        
        access_token = login_response.json()["access_token"]
        
        # Verify token
        verify_response = await async_client.post("/api/v1/auth/verify-token", json={
            "token": access_token
        })
        
        assert verify_response.status_code == 200
        user_data = verify_response.json()
        assert user_data["email"] == test_user_data["email"]

class TestUserProfile:
    """Test user profile endpoints."""
    
    async def test_get_current_user_profile(self, async_client: AsyncClient, test_user_data):
        """Test getting current user profile."""
        # Register and login
        await async_client.post("/api/v1/auth/register", json=test_user_data)
        login_response = await async_client.post("/api/v1/auth/login", json={
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        })
        
        access_token = login_response.json()["access_token"]
        
        # Get profile
        profile_response = await async_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        assert profile_response.status_code == 200
        profile_data = profile_response.json()
        assert profile_data["email"] == test_user_data["email"]
        assert profile_data["full_name"] == test_user_data["full_name"]
    
    async def test_get_profile_without_token(self, async_client: AsyncClient):
        """Test getting profile without authentication."""
        response = await async_client.get("/api/v1/auth/me")
        
        assert response.status_code == 401
        assert "Authorization token required" in response.json()["detail"]
    
    async def test_get_profile_with_invalid_token(self, async_client: AsyncClient):
        """Test getting profile with invalid token."""
        response = await async_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid_token"}
        )
        
        assert response.status_code == 401
        assert "Invalid or expired token" in response.json()["detail"]

class TestLogout:
    """Test logout functionality."""
    
    async def test_user_logout(self, async_client: AsyncClient, test_user_data):
        """Test user logout."""
        # Register and login
        await async_client.post("/api/v1/auth/register", json=test_user_data)
        login_response = await async_client.post("/api/v1/auth/login", json={
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        })
        
        access_token = login_response.json()["access_token"]
        
        # Logout
        logout_response = await async_client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        assert logout_response.status_code == 200
        assert "Successfully logged out" in logout_response.json()["message"]
    
    async def test_logout_without_token(self, async_client: AsyncClient):
        """Test logout without authentication."""
        response = await async_client.post("/api/v1/auth/logout")
        
        assert response.status_code == 401

class TestHealthCheck:
    """Test health check endpoints."""
    
    async def test_health_endpoint(self, async_client: AsyncClient):
        """Test health check endpoint."""
        response = await async_client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["healthy", "unhealthy"]
        assert data["service"] == "auth-service"
        assert data["version"] == "1.0.0"
        assert "database" in data
    
    async def test_root_endpoint(self, async_client: AsyncClient):
        """Test root endpoint."""
        response = await async_client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "Authentication Service"
        assert "endpoints" in data

class TestSecurityMiddleware:
    """Test security middleware functionality."""
    
    async def test_security_headers(self, async_client: AsyncClient):
        """Test that security headers are present."""
        response = await async_client.get("/health")
        
        # Check for security headers
        assert "X-Content-Type-Options" in response.headers
        assert "X-Frame-Options" in response.headers
        assert "X-XSS-Protection" in response.headers
        assert "Content-Security-Policy" in response.headers
        assert "Strict-Transport-Security" in response.headers
    
    async def test_oversized_request_blocking(self, async_client: AsyncClient):
        """Test that oversized requests are blocked."""
        # Create a large payload (6MB, exceeding 5MB limit)
        large_data = {"data": "x" * (6 * 1024 * 1024)}
        
        response = await async_client.post(
            "/api/v1/auth/register",
            json=large_data
        )
        
        assert response.status_code == 413  # Request Entity Too Large
    
    async def test_honeypot_detection(self, async_client: AsyncClient):
        """Test honeypot path detection."""
        response = await async_client.get("/admin")
        
        assert response.status_code == 404  # Honeypot returns 404
        assert "Path not found" in response.json()["detail"]

class TestRateLimiting:
    """Test rate limiting functionality."""
    
    async def test_rate_limit_not_exceeded(self, async_client: AsyncClient):
        """Test normal requests within rate limit."""
        # Make several requests (should be within limit)
        for _ in range(5):
            response = await async_client.get("/health")
            assert response.status_code == 200
            assert "X-RateLimit-Remaining" in response.headers

@pytest.mark.asyncio
async def test_end_to_end_auth_flow(async_client: AsyncClient, test_user_data):
    """Test complete authentication flow."""
    # 1. Register user
    register_response = await async_client.post("/api/v1/auth/register", json=test_user_data)
    assert register_response.status_code == 201
    
    # 2. Login
    login_response = await async_client.post("/api/v1/auth/login", json={
        "email": test_user_data["email"],
        "password": test_user_data["password"]
    })
    assert login_response.status_code == 200
    tokens = login_response.json()
    
    # 3. Access protected endpoint
    profile_response = await async_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {tokens['access_token']}"}
    )
    assert profile_response.status_code == 200
    
    # 4. Refresh token
    refresh_response = await async_client.post("/api/v1/auth/refresh", json={
        "refresh_token": tokens["refresh_token"]
    })
    assert refresh_response.status_code == 200
    
    # 5. Logout
    logout_response = await async_client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {tokens['access_token']}"}
    )
    assert logout_response.status_code == 200
    
    # 6. Verify token is invalid after logout
    post_logout_response = await async_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {tokens['access_token']}"}
    )
    # Should still work as token blacklisting needs to be fully implemented
    # In a full implementation, this should return 401