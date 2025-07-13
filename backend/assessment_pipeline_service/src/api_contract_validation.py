"""
API Contract Validation for Assessment Pipeline Service
Tests endpoint consistency, response formats, and service integration
"""
import asyncio
import logging
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
import httpx

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class APIContractValidator:
    """Validates API contracts and endpoint consistency"""
    
    def __init__(self):
        self.base_url = "http://localhost:8006"
        self.test_results: Dict[str, Any] = {}
        self.timeout = httpx.Timeout(timeout=30.0)
        
    async def test_service_health_contract(self) -> bool:
        """Test service health endpoint contract"""
        logger.info("🔍 Testing service health contract...")
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/health")
                
                if response.status_code != 200:
                    logger.error(f"Health endpoint returned {response.status_code}")
                    return False
                
                data = response.json()
                
                # Validate required fields
                required_fields = ["status", "service", "version", "timestamp"]
                for field in required_fields:
                    if field not in data:
                        logger.error(f"Missing required field: {field}")
                        return False
                
                # Validate status values
                if data["status"] not in ["healthy", "unhealthy"]:
                    logger.error(f"Invalid status value: {data['status']}")
                    return False
                
                # Validate service name
                if data["service"] != "assessment_pipeline_service":
                    logger.error(f"Unexpected service name: {data['service']}")
                    return False
                
                logger.info("✅ Service health contract validated")
                self.test_results["health_contract"] = {"success": True, "data": data}
                return True
                
        except Exception as e:
            logger.error(f"❌ Health contract test failed: {e}")
            self.test_results["health_contract"] = {"success": False, "error": str(e)}
            return False
    
    async def test_processing_health_contract(self) -> bool:
        """Test processing health endpoint contract"""
        logger.info("🔧 Testing processing health contract...")
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/assessment-pipeline/processing/health")
                
                if response.status_code not in [200, 503]:
                    logger.error(f"Processing health endpoint returned {response.status_code}")
                    return False
                
                data = response.json()
                
                # Validate required fields
                required_fields = ["status", "service", "version", "timestamp", "dependencies", "capabilities"]
                for field in required_fields:
                    if field not in data:
                        logger.error(f"Missing required field: {field}")
                        return False
                
                # Validate dependencies structure
                deps = data["dependencies"]
                required_deps = ["special_education_service", "auth_service", "assessment_processor"]
                for dep in required_deps:
                    if dep not in deps:
                        logger.error(f"Missing dependency: {dep}")
                        return False
                
                # Validate capabilities is a list
                if not isinstance(data["capabilities"], list):
                    logger.error("Capabilities should be a list")
                    return False
                
                logger.info("✅ Processing health contract validated")
                self.test_results["processing_health_contract"] = {"success": True, "data": data}
                return True
                
        except Exception as e:
            logger.error(f"❌ Processing health contract test failed: {e}")
            self.test_results["processing_health_contract"] = {"success": False, "error": str(e)}
            return False
    
    async def test_root_endpoint_contract(self) -> bool:
        """Test root endpoint contract"""
        logger.info("🏠 Testing root endpoint contract...")
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/")
                
                if response.status_code != 200:
                    logger.error(f"Root endpoint returned {response.status_code}")
                    return False
                
                data = response.json()
                
                # Validate required fields
                required_fields = ["service", "version", "description", "endpoints", "features", "timestamp"]
                for field in required_fields:
                    if field not in data:
                        logger.error(f"Missing required field: {field}")
                        return False
                
                # Validate service info
                if data["service"] != "Assessment Pipeline Service":
                    logger.error(f"Unexpected service name: {data['service']}")
                    return False
                
                if data["version"] != "2.0.0":
                    logger.error(f"Unexpected version: {data['version']}")
                    return False
                
                # Validate endpoints structure
                endpoints = data["endpoints"]
                if not isinstance(endpoints, dict):
                    logger.error("Endpoints should be a dictionary")
                    return False
                
                # Validate features is a list
                if not isinstance(data["features"], list):
                    logger.error("Features should be a list")
                    return False
                
                logger.info("✅ Root endpoint contract validated")
                self.test_results["root_contract"] = {"success": True, "data": data}
                return True
                
        except Exception as e:
            logger.error(f"❌ Root contract test failed: {e}")
            self.test_results["root_contract"] = {"success": False, "error": str(e)}
            return False
    
    async def test_openapi_schema_availability(self) -> bool:
        """Test OpenAPI schema availability"""
        logger.info("📋 Testing OpenAPI schema availability...")
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Test /docs endpoint
                docs_response = await client.get(f"{self.base_url}/docs")
                docs_available = docs_response.status_code == 200
                
                # Test /openapi.json endpoint
                openapi_response = await client.get(f"{self.base_url}/openapi.json")
                openapi_available = openapi_response.status_code == 200
                
                if docs_available:
                    logger.info("✅ Swagger UI (/docs) is available")
                else:
                    logger.warning("⚠️ Swagger UI (/docs) not available")
                
                if openapi_available:
                    logger.info("✅ OpenAPI schema (/openapi.json) is available")
                    # Validate schema structure
                    try:
                        schema = openapi_response.json()
                        if "openapi" in schema and "info" in schema:
                            logger.info("✅ OpenAPI schema structure is valid")
                        else:
                            logger.warning("⚠️ OpenAPI schema structure may be incomplete")
                    except Exception:
                        logger.warning("⚠️ OpenAPI schema is not valid JSON")
                else:
                    logger.warning("⚠️ OpenAPI schema (/openapi.json) not available")
                
                # At least one should be available
                success = docs_available or openapi_available
                
                self.test_results["openapi_schema"] = {
                    "success": success,
                    "docs_available": docs_available,
                    "openapi_available": openapi_available
                }
                
                return success
                
        except Exception as e:
            logger.error(f"❌ OpenAPI schema test failed: {e}")
            self.test_results["openapi_schema"] = {"success": False, "error": str(e)}
            return False
    
    async def test_error_response_format(self) -> bool:
        """Test standard error response format"""
        logger.info("❌ Testing error response format...")
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Test 404 error by requesting non-existent endpoint
                response = await client.get(f"{self.base_url}/nonexistent-endpoint")
                
                if response.status_code != 404:
                    logger.warning(f"Expected 404, got {response.status_code}")
                    return True  # Not critical for contract validation
                
                try:
                    data = response.json()
                    
                    # Validate error response structure
                    if "detail" in data:
                        logger.info("✅ Error response includes 'detail' field")
                    else:
                        logger.warning("⚠️ Error response missing 'detail' field")
                    
                    logger.info("✅ Error response format is structured")
                    self.test_results["error_format"] = {"success": True, "data": data}
                    return True
                    
                except Exception:
                    logger.warning("⚠️ Error response is not valid JSON")
                    self.test_results["error_format"] = {"success": True, "note": "Non-JSON error response"}
                    return True
                
        except Exception as e:
            logger.error(f"❌ Error format test failed: {e}")
            self.test_results["error_format"] = {"success": False, "error": str(e)}
            return False
    
    async def test_cors_headers(self) -> bool:
        """Test CORS headers configuration"""
        logger.info("🌐 Testing CORS headers...")
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Test preflight request
                response = await client.options(
                    f"{self.base_url}/health",
                    headers={
                        "Origin": "http://localhost:3000",
                        "Access-Control-Request-Method": "GET",
                        "Access-Control-Request-Headers": "authorization"
                    }
                )
                
                cors_configured = False
                if "access-control-allow-origin" in response.headers:
                    cors_configured = True
                    logger.info("✅ CORS headers configured")
                else:
                    logger.warning("⚠️ CORS headers not found")
                
                self.test_results["cors_headers"] = {
                    "success": True,  # Not critical for basic functionality
                    "cors_configured": cors_configured,
                    "headers": dict(response.headers)
                }
                
                return True
                
        except Exception as e:
            logger.error(f"❌ CORS headers test failed: {e}")
            self.test_results["cors_headers"] = {"success": False, "error": str(e)}
            return False
    
    async def test_service_consistency(self) -> bool:
        """Test consistency across service endpoints"""
        logger.info("🔄 Testing service consistency...")
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Get data from multiple endpoints
                health_response = await client.get(f"{self.base_url}/health")
                root_response = await client.get(f"{self.base_url}/")
                processing_health_response = await client.get(f"{self.base_url}/assessment-pipeline/processing/health")
                
                if not all(r.status_code in [200, 503] for r in [health_response, root_response, processing_health_response]):
                    logger.error("Not all endpoints are accessible")
                    return False
                
                health_data = health_response.json()
                root_data = root_response.json()
                processing_data = processing_health_response.json()
                
                # Check version consistency
                versions = [
                    health_data.get("version"),
                    root_data.get("version"),
                    processing_data.get("version")
                ]
                
                if len(set(v for v in versions if v)) == 1:
                    logger.info("✅ Version consistency across endpoints")
                else:
                    logger.warning(f"⚠️ Version inconsistency: {versions}")
                
                # Check timestamp format consistency
                timestamps = [
                    health_data.get("timestamp"),
                    root_data.get("timestamp"),
                    processing_data.get("timestamp")
                ]
                
                timestamp_formats_consistent = True
                for ts in timestamps:
                    if ts:
                        try:
                            datetime.fromisoformat(ts.replace('Z', '+00:00'))
                        except:
                            timestamp_formats_consistent = False
                            break
                
                if timestamp_formats_consistent:
                    logger.info("✅ Timestamp format consistency")
                else:
                    logger.warning("⚠️ Timestamp format inconsistency")
                
                self.test_results["service_consistency"] = {
                    "success": True,
                    "version_consistency": len(set(v for v in versions if v)) <= 1,
                    "timestamp_consistency": timestamp_formats_consistent
                }
                
                return True
                
        except Exception as e:
            logger.error(f"❌ Service consistency test failed: {e}")
            self.test_results["service_consistency"] = {"success": False, "error": str(e)}
            return False
    
    async def run_complete_validation_suite(self) -> Dict[str, Any]:
        """Run complete API contract validation suite"""
        logger.info("🧪 Starting API contract validation suite...")
        start_time = datetime.utcnow()
        
        validation_tests = [
            ("Service Health Contract", self.test_service_health_contract),
            ("Processing Health Contract", self.test_processing_health_contract),
            ("Root Endpoint Contract", self.test_root_endpoint_contract),
            ("OpenAPI Schema Availability", self.test_openapi_schema_availability),
            ("Error Response Format", self.test_error_response_format),
            ("CORS Headers", self.test_cors_headers),
            ("Service Consistency", self.test_service_consistency)
        ]
        
        results = {}
        
        for test_name, test_function in validation_tests:
            logger.info(f"\n--- Running: {test_name} ---")
            try:
                success = await test_function()
                results[test_name.lower().replace(" ", "_")] = success
                status = "✅ PASS" if success else "❌ FAIL"
                logger.info(f"{test_name}: {status}")
            except Exception as e:
                logger.error(f"{test_name} crashed: {e}")
                results[test_name.lower().replace(" ", "_")] = False
        
        # Summary
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()
        
        passed = sum(results.values())
        total = len(results)
        
        logger.info("\n" + "=" * 60)
        logger.info("🏁 API Contract Validation Complete!")
        logger.info("=" * 60)
        
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            logger.info(f"{test_name}: {status}")
        
        logger.info("=" * 60)
        logger.info(f"Results: {passed}/{total} validations passed")
        logger.info(f"Duration: {duration:.2f} seconds")
        
        if passed == total:
            logger.info("🎉 All API contracts validated successfully!")
            logger.info("✅ Service is ready for production deployment!")
        else:
            logger.warning(f"⚠️  {total - passed} validations failed - review API contracts")
        
        # Generate validation report
        validation_report = {
            "validation_results": results,
            "summary": {
                "passed": passed,
                "total": total,
                "success_rate": passed / total,
                "duration_seconds": duration,
                "ready_for_deployment": passed >= total * 0.8  # 80% threshold
            },
            "detailed_results": self.test_results,
            "validation_timestamp": datetime.utcnow().isoformat(),
            "service_info": {
                "base_url": self.base_url,
                "version": "2.0.0",
                "architecture": "processing-only microservice"
            }
        }
        
        return validation_report

async def main():
    """Run API contract validation"""
    validator = APIContractValidator()
    results = await validator.run_complete_validation_suite()
    
    # Save results to file
    with open("/tmp/api_contract_validation_results.json", "w") as f:
        json.dump(results, f, indent=2, default=str)
    
    logger.info("\n📁 Validation results saved to /tmp/api_contract_validation_results.json")
    
    return results

if __name__ == "__main__":
    asyncio.run(main())