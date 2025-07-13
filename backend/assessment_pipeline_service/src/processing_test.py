"""
Processing Routes Test Suite
Tests the new service-oriented processing endpoints
"""
import asyncio
import logging
import json
from typing import Dict, Any
from datetime import datetime

# Configure logging for testing
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ProcessingRouteTest:
    """Test suite for new processing routes"""
    
    def __init__(self):
        self.test_results: Dict[str, Any] = {}
        
    async def test_service_imports(self) -> bool:
        """Test that all processing route imports work"""
        logger.info("🔍 Testing service imports...")
        
        try:
            # Test service communication imports
            from assessment_pipeline_service.src.service_communication import (
                service_comm_manager, ServiceType, CommunicationStatus
            )
            
            # Test auth middleware imports
            from assessment_pipeline_service.src.auth_middleware import (
                get_current_user, require_teacher_or_above
            )
            
            # Test data mapper imports
            from assessment_pipeline_service.src.data_mapper import DataMapper
            
            # Test schema imports
            from assessment_pipeline_service.schemas.assessment_schemas import (
                AssessmentUploadDTO, ExtractedDataDTO
            )
            
            logger.info("✅ All imports successful")
            self.test_results["imports"] = {"success": True}
            return True
            
        except Exception as e:
            logger.error(f"❌ Import failed: {e}")
            self.test_results["imports"] = {"success": False, "error": str(e)}
            return False
    
    async def test_data_mapper_methods(self) -> bool:
        """Test new DataMapper methods"""
        logger.info("📊 Testing DataMapper methods...")
        
        try:
            from assessment_pipeline_service.src.data_mapper import DataMapper
            
            # Test extraction_result_to_dict
            mock_extraction_result = {
                "confidence_score": 0.85,
                "extracted_text": "Test extraction",
                "scores": [{"test": "WISC-V", "score": 100}],
                "notes": "Test notes"
            }
            
            extraction_dict = DataMapper.extraction_result_to_dict(
                mock_extraction_result, "test-doc-123"
            )
            
            assert extraction_dict["document_id"] == "test-doc-123"
            assert extraction_dict["extraction_confidence"] == 0.85
            assert "metadata" in extraction_dict
            
            # Test quantified_result_to_dict
            mock_quantified_result = {
                "confidence_score": 0.90,
                "cognitive_profile": {"memory": 85},
                "grade_analysis": {"current_grade": "5th"}
            }
            
            quantified_dict = DataMapper.quantified_result_to_dict(
                mock_quantified_result, "test-doc-123"
            )
            
            assert quantified_dict["document_id"] == "test-doc-123"
            assert quantified_dict["quantification_confidence"] == 0.90
            assert "rag_ready_metrics" in quantified_dict
            
            logger.info("✅ DataMapper methods working correctly")
            self.test_results["data_mapper"] = {"success": True}
            return True
            
        except Exception as e:
            logger.error(f"❌ DataMapper test failed: {e}")
            self.test_results["data_mapper"] = {"success": False, "error": str(e)}
            return False
    
    async def test_processing_route_structure(self) -> bool:
        """Test processing route module structure"""
        logger.info("🛠️ Testing processing route structure...")
        
        try:
            # Import the processing routes module
            import assessment_pipeline_service.api.processing_routes as processing_routes
            
            # Check that router exists
            assert hasattr(processing_routes, 'router')
            router = processing_routes.router
            
            # Check router configuration
            assert router.prefix == "/assessment-pipeline/processing"
            assert "assessment-processing" in router.tags
            
            # Check that key functions exist
            assert hasattr(processing_routes, 'upload_assessment_document')
            assert hasattr(processing_routes, 'upload_multiple_documents')
            assert hasattr(processing_routes, 'extract_assessment_data')
            assert hasattr(processing_routes, 'quantify_assessment_metrics')
            assert hasattr(processing_routes, 'get_processing_status')
            assert hasattr(processing_routes, 'processing_health_check')
            
            logger.info("✅ Processing route structure is correct")
            self.test_results["route_structure"] = {"success": True}
            return True
            
        except Exception as e:
            logger.error(f"❌ Processing route structure test failed: {e}")
            self.test_results["route_structure"] = {"success": False, "error": str(e)}
            return False
    
    async def test_assessment_dto_creation(self) -> bool:
        """Test AssessmentUploadDTO creation"""
        logger.info("📝 Testing AssessmentUploadDTO creation...")
        
        try:
            from assessment_pipeline_service.schemas.assessment_schemas import AssessmentUploadDTO
            from uuid import uuid4
            from datetime import datetime
            
            # Create test DTO (using proper enum value)
            test_dto = AssessmentUploadDTO(
                student_id=uuid4(),
                document_type="wisc_v",  # Use enum value instead of display name
                file_name="test_assessment.pdf",
                file_path="/tmp/test_assessment.pdf",
                assessment_date=datetime.now(),
                assessor_name="Dr. Test",
                assessor_title="School Psychologist",
                referral_reason="Cognitive assessment"
            )
            
            # Test conversion to dict
            from assessment_pipeline_service.src.data_mapper import DataMapper
            dto_dict = DataMapper.upload_dto_to_dict(test_dto)
            
            assert "student_id" in dto_dict
            assert dto_dict["document_type"] == "wisc_v"
            assert dto_dict["file_name"] == "test_assessment.pdf"
            assert dto_dict["processing_status"] == "pending"
            
            logger.info("✅ AssessmentUploadDTO creation and conversion working")
            self.test_results["dto_creation"] = {"success": True}
            return True
            
        except Exception as e:
            logger.error(f"❌ DTO creation test failed: {e}")
            self.test_results["dto_creation"] = {"success": False, "error": str(e)}
            return False
    
    async def test_service_communication_integration(self) -> bool:
        """Test service communication manager integration"""
        logger.info("🔗 Testing service communication integration...")
        
        try:
            from assessment_pipeline_service.src.service_communication import (
                service_comm_manager, ServiceType
            )
            
            # Test getting metrics (should work without external dependencies)
            metrics = service_comm_manager.get_all_metrics()
            
            assert isinstance(metrics, dict)
            assert "communication_metrics" in metrics
            assert "overall_stats" in metrics
            
            # Test getting service metrics for special education service
            special_ed_metrics = service_comm_manager.get_service_metrics(
                ServiceType.SPECIAL_EDUCATION
            )
            
            assert isinstance(special_ed_metrics, dict)
            assert "service" in special_ed_metrics
            assert special_ed_metrics["service"] == "special_education_service"
            
            logger.info("✅ Service communication integration working")
            self.test_results["service_communication"] = {"success": True}
            return True
            
        except Exception as e:
            logger.error(f"❌ Service communication test failed: {e}")
            self.test_results["service_communication"] = {"success": False, "error": str(e)}
            return False
    
    async def test_authentication_middleware_integration(self) -> bool:
        """Test authentication middleware integration"""
        logger.info("🔐 Testing authentication middleware integration...")
        
        try:
            from assessment_pipeline_service.src.auth_middleware import (
                UserRole, auth_middleware, require_teacher_or_above
            )
            
            # Test UserRole enum
            assert UserRole.TEACHER.value == "teacher"
            assert UserRole.COORDINATOR.value == "coordinator"
            assert UserRole.ADMIN.value == "admin"
            
            # Test middleware existence
            assert auth_middleware is not None
            assert hasattr(auth_middleware, 'get_current_user')
            assert hasattr(auth_middleware, 'require_role')
            
            # Test dependency functions
            assert callable(require_teacher_or_above)
            
            logger.info("✅ Authentication middleware integration working")
            self.test_results["auth_middleware"] = {"success": True}
            return True
            
        except Exception as e:
            logger.error(f"❌ Authentication middleware test failed: {e}")
            self.test_results["auth_middleware"] = {"success": False, "error": str(e)}
            return False
    
    async def run_complete_test_suite(self) -> Dict[str, Any]:
        """Run complete processing routes test suite"""
        logger.info("🧪 Starting processing routes test suite...")
        start_time = datetime.utcnow()
        
        test_functions = [
            ("Service Imports", self.test_service_imports),
            ("DataMapper Methods", self.test_data_mapper_methods),
            ("Processing Route Structure", self.test_processing_route_structure),
            ("DTO Creation", self.test_assessment_dto_creation),
            ("Service Communication", self.test_service_communication_integration),
            ("Authentication Middleware", self.test_authentication_middleware_integration)
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
        logger.info("🏁 Processing Routes Test Suite Complete!")
        logger.info("=" * 60)
        
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            logger.info(f"{test_name}: {status}")
        
        logger.info("=" * 60)
        logger.info(f"Results: {passed}/{total} tests passed")
        logger.info(f"Duration: {duration:.2f} seconds")
        
        if passed == total:
            logger.info("🎉 All processing route tests passed!")
            logger.info("✅ Processing-only architecture is ready for deployment!")
        else:
            logger.warning(f"⚠️  {total - passed} tests failed - review implementation")
        
        return {
            "test_results": results,
            "summary": {
                "passed": passed,
                "total": total,
                "success_rate": passed / total,
                "duration_seconds": duration
            },
            "detailed_results": self.test_results,
            "deployment_ready": passed == total
        }

async def main():
    """Run processing routes tests"""
    test_suite = ProcessingRouteTest()
    results = await test_suite.run_complete_test_suite()
    
    # Save results to file for analysis
    with open("/tmp/processing_routes_test_results.json", "w") as f:
        json.dump(results, f, indent=2, default=str)
    
    logger.info("\n📁 Detailed results saved to /tmp/processing_routes_test_results.json")
    
    return results

if __name__ == "__main__":
    asyncio.run(main())