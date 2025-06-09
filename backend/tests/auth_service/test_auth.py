"""Tests for auth service endpoints"""
import pytest
from httpx import AsyncClient
from uuid import uuid4

pytestmark = pytest.mark.asyncio

async def test_health_check(auth_client):
    """Test health check endpoint"""
    response = auth_client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

async def test_register_user(auth_client):
    """Test user registration"""
    user_data = {
        "email": f"test_{uuid4()}@example.com",
        "password": "secure_password123",
        "full_name": "Test User",
        "role": "teacher"
    }
    
    response = auth_client.post("/api/v1/auth/register", json=user_data)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == user_data["email"]
    assert data["full_name"] == user_data["full_name"]
    assert data["role"] == user_data["role"]
    assert "id" in data
    assert "password" not in data

async def test_login_user(auth_client):
    """Test user login"""
    # First register a user
    user_data = {
        "email": f"test_{uuid4()}@example.com",
        "password": "secure_password123",
        "full_name": "Test User",
        "role": "teacher"
    }
    auth_client.post("/api/v1/auth/register", json=user_data)
    
    # Then try to login
    login_data = {
        "email": user_data["email"],
        "password": user_data["password"]
    }
    response = auth_client.post("/api/v1/auth/login", json=login_data)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

async def test_verify_token(auth_client):
    """Test token verification"""
    # First register and login
    user_data = {
        "email": f"test_{uuid4()}@example.com",
        "password": "secure_password123",
        "full_name": "Test User",
        "role": "teacher"
    }
    auth_client.post("/api/v1/auth/register", json=user_data)
    
    login_data = {
        "email": user_data["email"],
        "password": user_data["password"]
    }
    login_response = auth_client.post("/api/v1/auth/login", json=login_data)
    token = login_response.json()["access_token"]
    
    # Verify token
    response = auth_client.post(
        "/verify-token",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == user_data["email"]
    assert data["role"] == user_data["role"]

async def test_invalid_token(auth_client):
    """Test invalid token handling"""
    response = auth_client.post(
        "/verify-token",
        headers={"Authorization": "Bearer invalid_token"}
    )
    assert response.status_code == 401

async def test_register_duplicate_email(auth_client):
    """Test duplicate email registration"""
    user_data = {
        "email": f"test_{uuid4()}@example.com",
        "password": "secure_password123",
        "full_name": "Test User",
        "role": "teacher"
    }
    
    # Register first time
    auth_client.post("/api/v1/auth/register", json=user_data)
    
    # Try to register again with same email
    response = auth_client.post("/api/v1/auth/register", json=user_data)
    assert response.status_code == 400
    assert "email already registered" in response.json()["detail"].lower() 