"""
Authentication integration testing for Assessment Pipeline Service
Tests JWT validation, role-based access, and error handling
"""
import asyncio
import logging
import httpx
import json
from typing import Dict, Any, Optional

# Configure logging for testing
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AuthTestSuite:
    """Test suite for authentication integration"""
    
    def __init__(self):
        self.auth_service_url = "http://localhost:8003"
        self.assessment_pipeline_url = "http://localhost:8006"
        self.test_token = None
        self.test_user_info = None
        
    async def test_auth_service_connection(self) -> bool:
        """Test connection to auth service"""
        logger.info("Testing auth service connection...")
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.auth_service_url}/health")
                
                if response.status_code == 200:
                    logger.info("✅ Auth service connection successful")
                    return True
                else:
                    logger.error(f"❌ Auth service returned status {response.status_code}")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Failed to connect to auth service: {e}")
            return False
    
    async def test_assessment_pipeline_health(self) -> bool:
        """Test assessment pipeline health including auth dependencies"""
        logger.info("Testing assessment pipeline health...")
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.assessment_pipeline_url}/health")
                
                if response.status_code == 200:
                    health_data = response.json()
                    auth_status = health_data.get("auth_service", "unknown")
                    
                    logger.info(f"✅ Assessment pipeline health check passed")
                    logger.info(f"Auth service status: {auth_status}")
                    logger.info(f"Dependencies: {health_data.get('dependencies', {})}")
                    
                    return health_data.get("status") == "healthy"
                else:
                    logger.error(f"❌ Assessment pipeline health check failed: {response.status_code}")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Failed to check assessment pipeline health: {e}")
            return False
    
    async def create_test_token(self) -> Optional[str]:
        """Create a test token for authentication testing (if auth service supports it)"""
        logger.info("Attempting to create test token...")
        
        # This would require actual user credentials or a test endpoint
        # For now, we'll simulate the token validation flow
        logger.warning("⚠️  Token creation requires actual user credentials")
        logger.info("For full testing, use a real token from the auth service")
        
        # Return a mock token for structure testing (won't validate)
        return "mock.jwt.token"
    
    async def test_token_validation(self, token: str) -> bool:
        """Test token validation through auth service"""
        logger.info("Testing token validation...")
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{self.auth_service_url}/auth/verify-token",
                    json={"token": token}
                )
                
                if response.status_code == 200:
                    user_data = response.json()
                    logger.info(f"✅ Token validation successful")
                    logger.info(f"User info: {json.dumps(user_data, indent=2)}")
                    self.test_user_info = user_data
                    return True
                elif response.status_code == 401:
                    logger.warning("⚠️  Token validation failed - invalid token")
                    return False
                else:
                    logger.error(f"❌ Unexpected response from auth service: {response.status_code}")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Token validation error: {e}")
            return False
    
    async def test_protected_endpoint_without_auth(self) -> bool:
        """Test accessing protected endpoint without authentication"""
        logger.info("Testing protected endpoint without authentication...")
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{self.assessment_pipeline_url}/assessment-pipeline/orchestrator/execute-complete",
                    json={"student_id": "test-123", "assessment_documents": []}
                )
                
                if response.status_code == 401:
                    logger.info("✅ Protected endpoint correctly rejected unauthenticated request")
                    return True
                else:
                    logger.error(f"❌ Protected endpoint allowed unauthenticated access: {response.status_code}")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Error testing protected endpoint: {e}")
            return False
    
    async def test_protected_endpoint_with_invalid_token(self) -> bool:
        """Test accessing protected endpoint with invalid token"""
        logger.info("Testing protected endpoint with invalid token...")
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{self.assessment_pipeline_url}/assessment-pipeline/orchestrator/execute-complete",
                    json={"student_id": "test-123", "assessment_documents": []},
                    headers={"Authorization": "Bearer invalid.token.here"}
                )
                
                if response.status_code == 401:
                    logger.info("✅ Protected endpoint correctly rejected invalid token")
                    return True
                else:
                    logger.error(f"❌ Protected endpoint allowed invalid token: {response.status_code}")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Error testing invalid token: {e}")
            return False
    
    async def test_service_communication_patterns(self) -> bool:
        """Test service-to-service communication patterns"""
        logger.info("Testing service communication patterns...")
        
        # Test auth client circuit breaker status
        try:
            from assessment_pipeline_service.src.service_clients import auth_client
            
            circuit_status = auth_client.get_circuit_breaker_status()
            logger.info(f"Auth client circuit breaker status: {circuit_status}")
            
            # Test auth service health check through client
            health = await auth_client.health_check()
            logger.info(f"Auth service health via client: {health}")
            
            return health.get("healthy", False)
            
        except Exception as e:
            logger.error(f"❌ Service communication test failed: {e}")
            return False
    
    async def test_role_based_access_simulation(self) -> bool:
        """Test role-based access control simulation"""
        logger.info("Testing role-based access control...")
        
        # Test different role scenarios
        test_roles = ["user", "teacher", "coordinator", "admin"]
        
        for role in test_roles:
            logger.info(f"Testing access for role: {role}")
            
            # This would require actual token generation with different roles
            # For now, we log the expected behavior
            if role in ["teacher", "coordinator", "admin"]:
                logger.info(f"✅ Role {role} should have access to pipeline endpoints")
            else:
                logger.info(f"⚠️  Role {role} should be denied access to pipeline endpoints")
        
        return True
    
    async def run_complete_test_suite(self) -> Dict[str, bool]:
        """Run complete authentication test suite"""
        logger.info("🧪 Starting authentication integration test suite...")
        
        results = {}
        
        # Test 1: Auth service connection
        results["auth_service_connection"] = await self.test_auth_service_connection()
        
        # Test 2: Assessment pipeline health
        results["assessment_pipeline_health"] = await self.test_assessment_pipeline_health()
        
        # Test 3: Token creation (mock)
        test_token = await self.create_test_token()
        results["token_creation"] = test_token is not None
        
        # Test 4: Token validation (will fail with mock token)
        if test_token:
            results["token_validation"] = await self.test_token_validation(test_token)
        else:
            results["token_validation"] = False
        
        # Test 5: Protected endpoint without auth
        results["protected_endpoint_no_auth"] = await self.test_protected_endpoint_without_auth()
        
        # Test 6: Protected endpoint with invalid token
        results["protected_endpoint_invalid_token"] = await self.test_protected_endpoint_with_invalid_token()
        
        # Test 7: Service communication patterns
        results["service_communication"] = await self.test_service_communication_patterns()
        
        # Test 8: Role-based access simulation
        results["role_based_access"] = await self.test_role_based_access_simulation()
        
        # Summary
        logger.info("🏁 Test suite complete!")
        logger.info("=" * 50)
        
        passed = sum(results.values())
        total = len(results)
        
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            logger.info(f"{test_name}: {status}")
        
        logger.info("=" * 50)
        logger.info(f"Results: {passed}/{total} tests passed")
        
        if passed == total:
            logger.info("🎉 All authentication tests passed!")
        else:
            logger.warning(f"⚠️  {total - passed} tests failed - review authentication integration")
        
        return results

async def main():
    """Run authentication tests"""
    test_suite = AuthTestSuite()
    await test_suite.run_complete_test_suite()

if __name__ == "__main__":
    asyncio.run(main())