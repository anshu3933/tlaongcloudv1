"""
Service Communication Patterns Testing Suite
Tests inter-service communication, error handling, and coordination
"""
import asyncio
import logging
import json
from typing import Dict, Any, List
from datetime import datetime, timedelta

from assessment_pipeline_service.src.service_communication import (
    service_comm_manager, ServiceType, CommunicationStatus,
    create_assessment_document, validate_user_token, get_service_health_status
)

# Configure logging for testing
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class CommunicationTestSuite:
    """Test suite for service communication patterns"""
    
    def __init__(self):
        self.test_results: Dict[str, Dict[str, Any]] = {}
        
    async def test_service_health_checks(self) -> bool:
        """Test health checks for all dependent services"""
        logger.info("🔍 Testing service health checks...")
        
        try:
            health_status = await get_service_health_status()
            
            logger.info("Service health status:")
            for service, status in health_status.items():
                health_indicator = "✅" if status["healthy"] else "❌"
                response_time = status["response_time_ms"]
                logger.info(f"  {health_indicator} {service}: {status['status']} ({response_time:.1f}ms)")
                
                if status["error"]:
                    logger.warning(f"    Error: {status['error']}")
            
            # Check if at least one service is healthy
            healthy_services = sum(1 for status in health_status.values() if status["healthy"])
            success = healthy_services > 0
            
            self.test_results["service_health_checks"] = {
                "success": success,
                "healthy_services": healthy_services,
                "total_services": len(health_status),
                "details": health_status
            }
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Service health check failed: {e}")
            self.test_results["service_health_checks"] = {
                "success": False,
                "error": str(e)
            }
            return False
    
    async def test_authentication_service_communication(self) -> bool:
        """Test communication with auth service"""
        logger.info("🔐 Testing authentication service communication...")
        
        try:
            # Test with mock token (will fail validation but test communication)
            response = await validate_user_token("mock.jwt.token")
            
            # We expect this to fail validation but succeed in communication
            communication_success = (
                response.status in [CommunicationStatus.SUCCESS, CommunicationStatus.FAILED] and
                response.error_message is None or "401" in str(response.error_message)
            )
            
            logger.info(f"Auth service response status: {response.status.value}")
            logger.info(f"Execution time: {response.execution_time_ms:.1f}ms")
            
            if response.error_message:
                logger.info(f"Expected error (invalid token): {response.error_message}")
            
            self.test_results["auth_service_communication"] = {
                "success": communication_success,
                "response_status": response.status.value,
                "execution_time_ms": response.execution_time_ms,
                "error_message": response.error_message
            }
            
            return communication_success
            
        except Exception as e:
            logger.error(f"❌ Auth service communication test failed: {e}")
            self.test_results["auth_service_communication"] = {
                "success": False,
                "error": str(e)
            }
            return False
    
    async def test_special_education_service_communication(self) -> bool:
        """Test communication with special education service"""
        logger.info("📚 Testing special education service communication...")
        
        try:
            # Test document creation (may fail due to validation but tests communication)
            mock_document_data = {
                "student_id": "test-student-123",
                "file_name": "test_assessment.pdf",
                "file_path": "/tmp/test_assessment.pdf",
                "assessment_type": "WISC-V",
                "assessor_name": "Test Assessor",
                "upload_date": datetime.utcnow().isoformat()
            }
            
            response = await create_assessment_document(mock_document_data)
            
            # Communication is successful if we get a response (even if validation fails)
            communication_success = response.status in [
                CommunicationStatus.SUCCESS, 
                CommunicationStatus.FAILED
            ]
            
            logger.info(f"Special education service response status: {response.status.value}")
            logger.info(f"Execution time: {response.execution_time_ms:.1f}ms")
            
            if response.error_message:
                logger.info(f"Response error: {response.error_message}")
            
            self.test_results["special_education_service_communication"] = {
                "success": communication_success,
                "response_status": response.status.value,
                "execution_time_ms": response.execution_time_ms,
                "error_message": response.error_message
            }
            
            return communication_success
            
        except Exception as e:
            logger.error(f"❌ Special education service communication test failed: {e}")
            self.test_results["special_education_service_communication"] = {
                "success": False,
                "error": str(e)
            }
            return False
    
    async def test_batch_communication(self) -> bool:
        """Test batch communication patterns"""
        logger.info("📦 Testing batch communication patterns...")
        
        try:
            # Create a batch of requests
            batch_requests = [
                (ServiceType.AUTH_SERVICE, "health_check", {}),
                (ServiceType.SPECIAL_EDUCATION, "health_check", {}),
                (ServiceType.AUTH_SERVICE, "validate_token", {"token": "test.token"})
            ]
            
            responses = await service_comm_manager.batch_request(batch_requests)
            
            logger.info(f"Batch request completed with {len(responses)} responses")
            
            success_count = sum(
                1 for response in responses 
                if response.status in [CommunicationStatus.SUCCESS, CommunicationStatus.FAILED]
            )
            
            communication_success = success_count == len(responses)
            
            for i, response in enumerate(responses):
                logger.info(
                    f"  Request {i+1}: {response.status.value} "
                    f"({response.execution_time_ms:.1f}ms)"
                )
            
            self.test_results["batch_communication"] = {
                "success": communication_success,
                "total_requests": len(responses),
                "successful_communications": success_count,
                "average_response_time": sum(r.execution_time_ms for r in responses) / len(responses)
            }
            
            return communication_success
            
        except Exception as e:
            logger.error(f"❌ Batch communication test failed: {e}")
            self.test_results["batch_communication"] = {
                "success": False,
                "error": str(e)
            }
            return False
    
    async def test_error_handling_patterns(self) -> bool:
        """Test error handling and retry mechanisms"""
        logger.info("⚠️  Testing error handling patterns...")
        
        try:
            # Test with invalid service operation
            response = await service_comm_manager.send_request(
                ServiceType.SPECIAL_EDUCATION,
                "invalid_operation",
                {},
                timeout_seconds=5
            )
            
            # Should handle error gracefully
            error_handled = response.status == CommunicationStatus.FAILED
            
            logger.info(f"Error handling test result: {response.status.value}")
            if response.error_message:
                logger.info(f"Error message: {response.error_message}")
            
            self.test_results["error_handling"] = {
                "success": error_handled,
                "response_status": response.status.value,
                "error_message": response.error_message,
                "execution_time_ms": response.execution_time_ms
            }
            
            return error_handled
            
        except Exception as e:
            logger.error(f"❌ Error handling test failed: {e}")
            self.test_results["error_handling"] = {
                "success": False,
                "error": str(e)
            }
            return False
    
    async def test_metrics_collection(self) -> bool:
        """Test communication metrics collection"""
        logger.info("📊 Testing metrics collection...")
        
        try:
            # Get all metrics
            metrics = service_comm_manager.get_all_metrics()
            
            logger.info("Communication metrics:")
            logger.info(f"  Active requests: {metrics['active_requests']}")
            logger.info(f"  History size: {metrics['history_size']}")
            logger.info(f"  Total requests: {metrics['overall_stats']['total_requests']}")
            logger.info(f"  Total successful: {metrics['overall_stats']['total_successful']}")
            logger.info(f"  Total failed: {metrics['overall_stats']['total_failed']}")
            
            # Check service-specific metrics
            for service_name, service_metrics in metrics["communication_metrics"].items():
                success_rate = service_metrics["success_rate"] * 100
                avg_time = service_metrics["average_response_time_ms"]
                logger.info(f"  {service_name}: {success_rate:.1f}% success, {avg_time:.1f}ms avg")
            
            metrics_available = (
                isinstance(metrics, dict) and
                "communication_metrics" in metrics and
                "overall_stats" in metrics
            )
            
            self.test_results["metrics_collection"] = {
                "success": metrics_available,
                "metrics": metrics
            }
            
            return metrics_available
            
        except Exception as e:
            logger.error(f"❌ Metrics collection test failed: {e}")
            self.test_results["metrics_collection"] = {
                "success": False,
                "error": str(e)
            }
            return False
    
    async def test_communication_history(self) -> bool:
        """Test communication history tracking"""
        logger.info("📜 Testing communication history tracking...")
        
        try:
            # Get recent communication history
            history = service_comm_manager.get_recent_communication_history(limit=10)
            
            logger.info(f"Communication history contains {len(history)} recent entries")
            
            if history:
                logger.info("Recent communications:")
                for entry in history[-3:]:  # Show last 3
                    timestamp = entry["timestamp"]
                    status = entry["status"]
                    service = entry["target_service"]
                    operation = entry["operation"]
                    time_ms = entry["execution_time_ms"]
                    logger.info(f"  {timestamp}: {service}/{operation} -> {status} ({time_ms:.1f}ms)")
            
            history_working = isinstance(history, list)
            
            self.test_results["communication_history"] = {
                "success": history_working,
                "history_entries": len(history),
                "sample_entries": history[-3:] if history else []
            }
            
            return history_working
            
        except Exception as e:
            logger.error(f"❌ Communication history test failed: {e}")
            self.test_results["communication_history"] = {
                "success": False,
                "error": str(e)
            }
            return False
    
    async def run_complete_test_suite(self) -> Dict[str, Any]:
        """Run complete service communication test suite"""
        logger.info("🧪 Starting service communication test suite...")
        start_time = datetime.utcnow()
        
        test_functions = [
            ("Service Health Checks", self.test_service_health_checks),
            ("Auth Service Communication", self.test_authentication_service_communication),
            ("Special Education Service Communication", self.test_special_education_service_communication),
            ("Batch Communication", self.test_batch_communication),
            ("Error Handling", self.test_error_handling_patterns),
            ("Metrics Collection", self.test_metrics_collection),
            ("Communication History", self.test_communication_history)
        ]
        
        results = {}
        
        for test_name, test_function in test_functions:
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
        logger.info("🏁 Service Communication Test Suite Complete!")
        logger.info("=" * 60)
        
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            logger.info(f"{test_name}: {status}")
        
        logger.info("=" * 60)
        logger.info(f"Results: {passed}/{total} tests passed")
        logger.info(f"Duration: {duration:.2f} seconds")
        
        if passed == total:
            logger.info("🎉 All service communication tests passed!")
        else:
            logger.warning(f"⚠️  {total - passed} tests failed - review service integration")
        
        # Final metrics summary
        logger.info("\n📊 Final Communication Metrics:")
        try:
            final_metrics = service_comm_manager.get_all_metrics()
            logger.info(f"Total requests: {final_metrics['overall_stats']['total_requests']}")
            logger.info(f"Success rate: {final_metrics['overall_stats']['total_successful']}/{final_metrics['overall_stats']['total_requests']}")
        except Exception as e:
            logger.warning(f"Could not retrieve final metrics: {e}")
        
        return {
            "test_results": results,
            "summary": {
                "passed": passed,
                "total": total,
                "success_rate": passed / total,
                "duration_seconds": duration
            },
            "detailed_results": self.test_results
        }

async def main():
    """Run service communication tests"""
    test_suite = CommunicationTestSuite()
    results = await test_suite.run_complete_test_suite()
    
    # Save results to file for analysis
    with open("/tmp/communication_test_results.json", "w") as f:
        json.dump(results, f, indent=2, default=str)
    
    logger.info("\n📁 Detailed results saved to /tmp/communication_test_results.json")
    
    return results

if __name__ == "__main__":
    asyncio.run(main())