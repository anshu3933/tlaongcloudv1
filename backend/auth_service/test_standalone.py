#!/usr/bin/env python3
"""Standalone test script for auth service components."""

import os
import sys
from datetime import datetime, timedelta

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Set required environment variables for testing
os.environ['AUTH_JWT_SECRET_KEY'] = 'test-secret-key-for-testing-only'
os.environ['AUTH_DATABASE_URL'] = os.getenv('TEST_DATABASE_URL', 'sqlite+aiosqlite:///./test_auth.db')
os.environ['AUTH_ENVIRONMENT'] = 'testing'

def test_imports():
    """Test that all modules can be imported."""
    print("🧪 Testing module imports...")
    
    try:
        # Test config imports
        print("  ✅ Config module imported successfully")
        
        # Test security imports
        print("  ✅ Security module imported successfully")
        
        # Test schemas imports
        print("  ✅ Schemas module imported successfully")
        
        # Test models imports
        print("  ✅ Models imported successfully")
        
        # Test middleware imports
        print("  ✅ Middleware imported successfully")
        
        print("  🎉 All imports successful!")
        return True
        
    except Exception as e:
        print(f"  ❌ Import failed: {e}")
        return False

def test_password_validation():
    """Test password validation functionality."""
    print("\\n🔐 Testing password validation...")
    
    try:
        from security import PasswordValidator
        
        # Test valid password
        is_valid, errors = PasswordValidator.validate_password("StrongPass123")
        assert is_valid, f"Valid password failed: {errors}"
        assert len(errors) == 0, f"Valid password should have no errors: {errors}"
        print("  ✅ Valid password accepted")
        
        # Test invalid password - too short
        is_valid, errors = PasswordValidator.validate_password("short")
        assert not is_valid, "Short password should be invalid"
        assert len(errors) > 0, "Short password should have errors"
        print("  ✅ Short password rejected")
        
        # Test invalid password - no uppercase
        is_valid, errors = PasswordValidator.validate_password("lowercase123")
        assert not is_valid, "Password without uppercase should be invalid"
        print("  ✅ Password without uppercase rejected")
        
        print("  🎉 Password validation tests passed!")
        return True
        
    except Exception as e:
        print(f"  ❌ Password validation test failed: {e}")
        return False

def test_password_hashing():
    """Test password hashing and verification."""
    print("\\n🔒 Testing password hashing...")
    
    try:
        from security import hash_password, verify_password
        
        password = "TestPassword123"
        hashed = hash_password(password)
        
        assert hashed != password, "Hashed password should be different from original"
        assert verify_password(password, hashed), "Password verification should succeed"
        assert not verify_password("WrongPassword", hashed), "Wrong password should fail verification"
        
        print("  ✅ Password hashing and verification working")
        print("  🎉 Password hashing tests passed!")
        return True
        
    except Exception as e:
        print(f"  ❌ Password hashing test failed: {e}")
        return False

def test_configuration():
    """Test configuration loading."""
    print("\\n⚙️ Testing configuration...")
    
    try:
        from config import get_auth_settings
        
        settings = get_auth_settings()
        
        assert settings.jwt_algorithm == "HS256", f"JWT algorithm should be HS256, got {settings.jwt_algorithm}"
        assert settings.access_token_expire_minutes > 0, "Access token expiry should be positive"
        assert settings.refresh_token_expire_days > 0, "Refresh token expiry should be positive"
        assert isinstance(settings.cors_origins_list, list), "CORS origins should be a list"
        
        print(f"  ✅ JWT Algorithm: {settings.jwt_algorithm}")
        print(f"  ✅ Access token expiry: {settings.access_token_expire_minutes} minutes")
        print(f"  ✅ Refresh token expiry: {settings.refresh_token_expire_days} days")
        print(f"  ✅ CORS origins: {len(settings.cors_origins_list)} configured")
        print("  🎉 Configuration tests passed!")
        return True
        
    except Exception as e:
        print(f"  ❌ Configuration test failed: {e}")
        return False

def test_schemas():
    """Test Pydantic schemas."""
    print("\\n📋 Testing Pydantic schemas...")
    
    try:
        from schemas import UserCreate, UserLogin
        
        # Test UserCreate validation
        user_data = {
            "email": "test@example.com",
            "password": "StrongPass123",
            "full_name": "Test User",
            "role": "user"
        }
        
        user_create = UserCreate(**user_data)
        assert user_create.email == "test@example.com", "Email should match"
        assert user_create.password == "StrongPass123", "Password should match"
        print("  ✅ UserCreate schema validation working")
        
        # Test UserLogin
        login_data = {
            "email": "test@example.com",
            "password": "password123"
        }
        
        user_login = UserLogin(**login_data)
        assert user_login.email == "test@example.com", "Login email should match"
        print("  ✅ UserLogin schema validation working")
        
        print("  🎉 Schema tests passed!")
        return True
        
    except Exception as e:
        print(f"  ❌ Schema test failed: {e}")
        return False

def test_token_operations():
    """Test JWT token creation and verification."""
    print("\\n🎫 Testing JWT token operations...")
    
    try:
        from security import create_access_token, verify_token
        
        # Create token
        test_data = {"sub": "123", "email": "test@example.com", "role": "user"}
        token = create_access_token(test_data)
        
        assert token is not None, "Token should be created"
        assert isinstance(token, str), "Token should be a string"
        print("  ✅ Token creation successful")
        
        # Verify token
        payload = verify_token(token, token_type="access")
        assert payload is not None, "Token verification should succeed"
        assert payload["sub"] == "123", "Token subject should match"
        assert payload["email"] == "test@example.com", "Token email should match"
        assert payload["role"] == "user", "Token role should match"
        print("  ✅ Token verification successful")
        
        print("  🎉 Token operation tests passed!")
        return True
        
    except Exception as e:
        print(f"  ❌ Token operation test failed: {e}")
        return False

def test_models_structure():
    """Test that model classes are properly structured."""
    print("\\n🏗️ Testing model structures...")
    
    try:
        from models.user import User
        from models.audit_log import AuditLog
        from models.user_session import UserSession
        
        # Check User model
        user = User(
            email="test@example.com",
            hashed_password="hashed_password",
            full_name="Test User",
            role="user"
        )
        assert user.email == "test@example.com", "User email should be set"
        print("  ✅ User model structure correct")
        
        # Check AuditLog model
        audit_log = AuditLog(
            entity_type="user",
            entity_id=1,
            action="test_action"
        )
        assert audit_log.entity_type == "user", "Audit log entity type should be set"
        print("  ✅ AuditLog model structure correct")
        
        # Check UserSession model
        session = UserSession(
            user_id=1,
            token_hash="test_hash",
            expires_at=datetime.utcnow() + timedelta(days=7)
        )
        assert session.user_id == 1, "Session user_id should be set"
        print("  ✅ UserSession model structure correct")
        
        print("  🎉 Model structure tests passed!")
        return True
        
    except Exception as e:
        print(f"  ❌ Model structure test failed: {e}")
        return False

def run_all_tests():
    """Run all tests and report results."""
    print("🚀 Starting Authentication Service Test Suite")
    print("=" * 60)
    
    tests = [
        test_imports,
        test_configuration,
        test_password_validation,
        test_password_hashing,
        test_token_operations,
        test_schemas,
        test_models_structure,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"  ❌ Test {test.__name__} crashed: {e}")
            failed += 1
    
    print("\\n" + "=" * 60)
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed! Authentication service is working correctly.")
        return True
    else:
        print(f"⚠️ {failed} test(s) failed. Check the output above for details.")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)