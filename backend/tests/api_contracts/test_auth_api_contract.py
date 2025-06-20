"""API contract tests for Authentication Service."""

import pytest
from httpx import AsyncClient
from typing import Dict, Any
import jsonschema

# JSON Schema definitions for API responses
AUTH_USER_SCHEMA = {
    "type": "object",
    "properties": {
        "id": {"type": "integer"},
        "email": {"type": "string", "format": "email"},
        "full_name": {"type": ["string", "null"]},
        "role": {"type": "string", "enum": ["user", "teacher", "co_coordinator", "coordinator", "admin", "superuser"]},
        "is_active": {"type": "boolean"},
        "is_superuser": {"type": "boolean"},
        "created_at": {"type": "string", "format": "date-time"},
        "updated_at": {"type": ["string", "null"], "format": "date-time"},
        "last_login": {"type": ["string", "null"], "format": "date-time"}
    },
    "required": ["id", "email", "role", "is_active", "is_superuser", "created_at"],
    "additionalProperties": False
}

TOKEN_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "access_token": {"type": "string"},
        "refresh_token": {"type": "string"},
        "token_type": {"type": "string", "enum": ["bearer"]},
        "expires_in": {"type": "integer"},
        "user": AUTH_USER_SCHEMA
    },
    "required": ["access_token", "refresh_token", "token_type", "expires_in", "user"],
    "additionalProperties": False
}

ERROR_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "detail": {"type": "string"},
        "errors": {
            "type": ["array", "null"],
            "items": {
                "type": "object",
                "properties": {
                    "type": {"type": "string"},
                    "message": {"type": "string"},
                    "field": {"type": ["string", "null"]}
                },
                "required": ["type", "message"]
            }
        },
        "timestamp": {"type": "string", "format": "date-time"}
    },
    "required": ["detail", "timestamp"],
    "additionalProperties": False
}

HEALTH_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "status": {"type": "string", "enum": ["healthy", "unhealthy", "degraded"]},
        "service": {"type": "string"},
        "version": {"type": "string"},
        "database": {"type": ["string", "null"]},
        "timestamp": {"type": "string", "format": "date-time"}
    },
    "required": ["status", "service", "version"],
    "additionalProperties": True  # Allow additional fields
}

def validate_schema(data: Dict[Any, Any], schema: Dict[str, Any]) -> None:
    """Validate data against JSON schema."""
    try:
        jsonschema.validate(instance=data, schema=schema)
    except jsonschema.ValidationError as e:
        pytest.fail(f"Schema validation failed: {e.message}")

class TestAuthAPIContract:
    """Test Authentication Service API contracts."""
    
    @pytest.mark.asyncio
    async def test_registration_endpoint_contract(self, async_client: AsyncClient):
        """Test user registration endpoint API contract."""
        user_data = {
            "email": "contract_test@example.com",
            "password": "SecurePass123!",
            "full_name": "Contract Test User",
            "role": "user"
        }
        
        response = await async_client.post("/api/v1/auth/register", json=user_data)
        
        # Test successful response contract
        if response.status_code == 201:
            validate_schema(response.json(), AUTH_USER_SCHEMA)
        # Test error response contract
        elif response.status_code >= 400:
            validate_schema(response.json(), ERROR_RESPONSE_SCHEMA)
        else:
            pytest.fail(f"Unexpected status code: {response.status_code}")
    
    @pytest.mark.asyncio
    async def test_login_endpoint_contract(self, async_client: AsyncClient):
        """Test login endpoint API contract."""
        # First register a user
        user_data = {
            "email": "login_contract@example.com",
            "password": "SecurePass123!",
            "full_name": "Login Contract Test",
            "role": "user"
        }
        await async_client.post("/api/v1/auth/register", json=user_data)
        
        # Test login
        login_data = {
            "email": user_data["email"],
            "password": user_data["password"]
        }
        response = await async_client.post("/api/v1/auth/login", json=login_data)
        
        # Test successful response contract
        if response.status_code == 200:
            validate_schema(response.json(), TOKEN_RESPONSE_SCHEMA)
        # Test error response contract
        elif response.status_code >= 400:
            validate_schema(response.json(), ERROR_RESPONSE_SCHEMA)
        else:
            pytest.fail(f"Unexpected status code: {response.status_code}")
    
    @pytest.mark.asyncio
    async def test_token_refresh_endpoint_contract(self, async_client: AsyncClient):
        """Test token refresh endpoint API contract."""
        # Register and login to get refresh token
        user_data = {
            "email": "refresh_contract@example.com",
            "password": "SecurePass123!",
            "full_name": "Refresh Contract Test",
            "role": "user"
        }
        await async_client.post("/api/v1/auth/register", json=user_data)
        
        login_response = await async_client.post("/api/v1/auth/login", json={
            "email": user_data["email"],
            "password": user_data["password"]
        })
        
        refresh_token = login_response.json()["refresh_token"]
        
        # Test refresh
        response = await async_client.post("/api/v1/auth/refresh", json={
            "refresh_token": refresh_token
        })
        
        # Test successful response contract
        if response.status_code == 200:
            validate_schema(response.json(), TOKEN_RESPONSE_SCHEMA)
        # Test error response contract
        elif response.status_code >= 400:
            validate_schema(response.json(), ERROR_RESPONSE_SCHEMA)
        else:
            pytest.fail(f"Unexpected status code: {response.status_code}")
    
    @pytest.mark.asyncio
    async def test_user_profile_endpoint_contract(self, async_client: AsyncClient):
        """Test user profile endpoint API contract."""
        # Register and login to get access token
        user_data = {
            "email": "profile_contract@example.com",
            "password": "SecurePass123!",
            "full_name": "Profile Contract Test",
            "role": "user"
        }
        await async_client.post("/api/v1/auth/register", json=user_data)
        
        login_response = await async_client.post("/api/v1/auth/login", json={
            "email": user_data["email"],
            "password": user_data["password"]
        })
        
        access_token = login_response.json()["access_token"]
        
        # Test profile endpoint
        response = await async_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        # Test successful response contract
        if response.status_code == 200:
            validate_schema(response.json(), AUTH_USER_SCHEMA)
        # Test error response contract
        elif response.status_code >= 400:
            validate_schema(response.json(), ERROR_RESPONSE_SCHEMA)
        else:
            pytest.fail(f"Unexpected status code: {response.status_code}")
    
    @pytest.mark.asyncio
    async def test_health_endpoint_contract(self, async_client: AsyncClient):
        """Test health endpoint API contract."""
        response = await async_client.get("/health")
        
        # Health endpoint should always return 200 or 503
        assert response.status_code in [200, 503]
        validate_schema(response.json(), HEALTH_RESPONSE_SCHEMA)
    
    @pytest.mark.asyncio
    async def test_error_response_consistency(self, async_client: AsyncClient):
        """Test that all error responses follow the same schema."""
        # Test various error scenarios
        error_scenarios = [
            # Invalid registration data
            {
                "method": "POST",
                "url": "/api/v1/auth/register",
                "json": {"email": "invalid-email", "password": "weak"}
            },
            # Invalid login credentials
            {
                "method": "POST",
                "url": "/api/v1/auth/login",
                "json": {"email": "nonexistent@example.com", "password": "wrong"}
            },
            # Invalid token
            {
                "method": "GET",
                "url": "/api/v1/auth/me",
                "headers": {"Authorization": "Bearer invalid_token"}
            },
            # Missing token
            {
                "method": "GET",
                "url": "/api/v1/auth/me"
            }
        ]
        
        for scenario in error_scenarios:
            if scenario["method"] == "POST":
                response = await async_client.post(
                    scenario["url"],
                    json=scenario.get("json"),
                    headers=scenario.get("headers", {})
                )
            else:
                response = await async_client.get(
                    scenario["url"],
                    headers=scenario.get("headers", {})
                )
            
            # All error responses should be 4xx or 5xx
            assert response.status_code >= 400
            
            # All error responses should follow the error schema
            validate_schema(response.json(), ERROR_RESPONSE_SCHEMA)

class TestResponseHeaders:
    """Test API response headers consistency."""
    
    @pytest.mark.asyncio
    async def test_security_headers_present(self, async_client: AsyncClient):
        """Test that security headers are present in responses."""
        response = await async_client.get("/health")
        
        # Check for important security headers
        security_headers = [
            "X-Content-Type-Options",
            "X-Frame-Options", 
            "X-XSS-Protection",
            "Content-Security-Policy"
        ]
        
        for header in security_headers:
            assert header in response.headers, f"Missing security header: {header}"
    
    @pytest.mark.asyncio
    async def test_cors_headers_configured(self, async_client: AsyncClient):
        """Test CORS headers configuration."""
        # Test preflight request
        response = await async_client.options("/api/v1/auth/register")
        
        # Should include CORS headers
        if response.status_code == 200:
            assert "Access-Control-Allow-Origin" in response.headers
            assert "Access-Control-Allow-Methods" in response.headers
    
    @pytest.mark.asyncio
    async def test_content_type_consistency(self, async_client: AsyncClient):
        """Test that API endpoints return consistent content types."""
        endpoints = [
            "/health",
            "/",
        ]
        
        for endpoint in endpoints:
            response = await async_client.get(endpoint)
            
            if response.status_code == 200:
                assert response.headers.get("content-type", "").startswith("application/json")

class TestAPIVersioning:
    """Test API versioning consistency."""
    
    @pytest.mark.asyncio
    async def test_versioned_endpoints_accessible(self, async_client: AsyncClient):
        """Test that versioned API endpoints are accessible."""
        # Test v1 endpoints
        v1_endpoints = [
            "/api/v1/auth/register",
            "/api/v1/auth/login",
            "/api/v1/auth/refresh"
        ]
        
        for endpoint in v1_endpoints:
            # Make a request (even if it fails, endpoint should exist)
            response = await async_client.post(endpoint, json={})
            
            # Should not be 404 (not found)
            assert response.status_code != 404, f"Endpoint not found: {endpoint}"
    
    @pytest.mark.asyncio
    async def test_api_documentation_accessible(self, async_client: AsyncClient):
        """Test that API documentation is accessible."""
        # Test OpenAPI documentation
        docs_endpoints = ["/docs", "/openapi.json"]
        
        for endpoint in docs_endpoints:
            response = await async_client.get(endpoint)
            
            # Should be accessible (200) or explicitly disabled (404)
            assert response.status_code in [200, 404], f"Unexpected response for {endpoint}"

class TestRateLimitingContract:
    """Test rate limiting behavior consistency."""
    
    @pytest.mark.asyncio
    async def test_rate_limit_headers_present(self, async_client: AsyncClient):
        """Test that rate limiting headers are included."""
        response = await async_client.get("/health")
        
        # Should include rate limiting headers
        rate_limit_headers = [
            "X-RateLimit-Limit",
            "X-RateLimit-Remaining",
            "X-RateLimit-Reset"
        ]
        
        # At least some rate limiting headers should be present
        present_headers = [h for h in rate_limit_headers if h in response.headers]
        assert len(present_headers) > 0, "No rate limiting headers found"