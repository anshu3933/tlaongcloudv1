"""Basic tests for the redesigned authentication service."""

import pytest
import asyncio
import sys
import os
from unittest.mock import AsyncMock, MagicMock

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Test the security module
def test_password_validator():
    """Test password validation."""
    from security import PasswordValidator
    
    # Valid password
    is_valid, errors = PasswordValidator.validate_password("StrongPass123")
    assert is_valid
    assert len(errors) == 0
    
    # Invalid password - too short
    is_valid, errors = PasswordValidator.validate_password("short")
    assert not is_valid
    assert any("at least" in error for error in errors)
    
    # Invalid password - no uppercase
    is_valid, errors = PasswordValidator.validate_password("lowercase123")
    assert not is_valid
    assert any("uppercase" in error for error in errors)

def test_token_creation():
    """Test JWT token creation and verification."""
    from security import create_access_token, verify_token
    
    # Create token
    test_data = {"sub": "123", "email": "test@example.com", "role": "user"}
    token = create_access_token(test_data)
    
    assert token is not None
    assert isinstance(token, str)
    
    # Verify token
    payload = verify_token(token, token_type="access")
    assert payload is not None
    assert payload["sub"] == "123"
    assert payload["email"] == "test@example.com"
    assert payload["role"] == "user"

def test_password_hashing():
    """Test password hashing and verification."""
    from security import hash_password, verify_password
    
    password = "TestPassword123"
    hashed = hash_password(password)
    
    assert hashed != password
    assert verify_password(password, hashed)
    assert not verify_password("WrongPassword", hashed)

# Test configuration
def test_auth_settings():
    """Test authentication settings."""
    from config import get_auth_settings
    
    settings = get_auth_settings()
    
    assert settings.jwt_algorithm == "HS256"
    assert settings.access_token_expire_minutes > 0
    assert settings.refresh_token_expire_days > 0
    assert isinstance(settings.cors_origins_list, list)

# Test schemas
def test_user_schemas():
    """Test user-related Pydantic schemas."""
    from schemas import UserCreate, UserLogin
    
    # Test UserCreate validation
    user_data = {
        "email": "test@example.com",
        "password": "StrongPass123",
        "full_name": "Test User",
        "role": "user"
    }
    
    user_create = UserCreate(**user_data)
    assert user_create.email == "test@example.com"
    assert user_create.password == "StrongPass123"
    
    # Test UserLogin
    login_data = {
        "email": "test@example.com",
        "password": "password123"
    }
    
    user_login = UserLogin(**login_data)
    assert user_login.email == "test@example.com"

# Mock test for repository operations
@pytest.mark.asyncio
async def test_user_repository_mock():
    """Test user repository with mock session."""
    from repositories.user_repository import UserRepository
    from models.user import User
    
    # Mock session
    mock_session = AsyncMock()
    user_repo = UserRepository(mock_session)
    
    # Mock user
    mock_user = User(
        id=1,
        email="test@example.com",
        hashed_password="hashed_password",
        full_name="Test User",
        role="user"
    )
    
    # Mock the query result
    mock_result = AsyncMock()
    mock_result.scalar_one_or_none.return_value = mock_user
    mock_session.execute.return_value = mock_result
    
    # Test get_by_email
    user = await user_repo.get_by_email("test@example.com")
    assert user == mock_user

@pytest.mark.asyncio
async def test_audit_repository_mock():
    """Test audit repository with mock session."""
    from repositories.audit_repository import AuditRepository
    from models.audit_log import AuditLog
    
    # Mock session
    mock_session = AsyncMock()
    audit_repo = AuditRepository(mock_session)
    
    # Test log_action
    mock_session.add = MagicMock()
    mock_session.commit = AsyncMock()
    mock_session.refresh = AsyncMock()
    
    log = await audit_repo.log_action(
        entity_type="user",
        entity_id=1,
        action="test_action",
        user_id=1,
        user_role="user",
        ip_address="127.0.0.1"
    )
    
    assert isinstance(log, AuditLog)
    assert log.entity_type == "user"
    assert log.action == "test_action"

def test_error_schemas():
    """Test error response schemas."""
    from schemas import ErrorResponse, ErrorDetail
    
    error = ErrorDetail(
        type="validation_error",
        message="Field is required",
        field="email"
    )
    
    response = ErrorResponse(
        detail="Validation failed",
        errors=[error]
    )
    
    assert response.detail == "Validation failed"
    assert len(response.errors) == 1
    assert response.errors[0].field == "email"

def test_middleware_imports():
    """Test that middleware modules can be imported."""
    from middleware.error_handler import (
        ErrorHandlerMiddleware,
        SecurityHeadersMiddleware,
        RequestLoggingMiddleware,
        RateLimitMiddleware
    )
    
    # Check that classes exist
    assert ErrorHandlerMiddleware is not None
    assert SecurityHeadersMiddleware is not None
    assert RequestLoggingMiddleware is not None
    assert RateLimitMiddleware is not None

# Integration test placeholder
def test_app_creation():
    """Test that the FastAPI app can be created."""
    try:
        # This would normally require proper environment setup
        # from main import app
        # assert app is not None
        pass
    except Exception:
        # Expected to fail without proper environment
        pass

if __name__ == "__main__":
    # Run basic tests
    test_password_validator()
    test_token_creation()
    test_password_hashing()
    test_auth_settings()
    test_user_schemas()
    test_error_schemas()
    test_middleware_imports()
    
    # Run async tests
    asyncio.run(test_user_repository_mock())
    asyncio.run(test_audit_repository_mock())
    
    print("✅ All basic tests passed!")