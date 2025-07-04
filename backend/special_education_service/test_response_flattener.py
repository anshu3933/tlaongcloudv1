#!/usr/bin/env python3
"""
Comprehensive test suite for the Response Flattener
Tests all known problematic patterns and validates fixes
"""

import sys
import os
import json
import time
import unittest
from uuid import uuid4
from datetime import datetime, date

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.response_flattener import SimpleIEPFlattener, get_flattener_statistics, reset_flattener_statistics

class TestResponseFlattener(unittest.TestCase):
    """Test suite for response flattener functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.flattener = SimpleIEPFlattener(enable_detailed_logging=True)
        reset_flattener_statistics()
    
    def test_triple_nested_services(self):
        """Test flattening of triple-nested services structure"""
        input_data = {
            "id": str(uuid4()),
            "student_id": str(uuid4()),
            "content": {
                "student_name": "Test Student",
                "services": {
                    "services": {
                        "special_education": [
                            {
                                "name": "Reading Support",
                                "frequency": "3x per week",
                                "duration": "30 minutes"
                            },
                            {
                                "name": "Math Support", 
                                "frequency": "2x per week",
                                "duration": "45 minutes"
                            }
                        ],
                        "speech_therapy": [
                            {
                                "name": "Articulation",
                                "frequency": "1x per week",
                                "duration": "20 minutes"
                            }
                        ]
                    }
                }
            }
        }
        
        result = self.flattener.flatten(input_data)
        
        # Check that services is now a string
        self.assertIsInstance(result["content"]["services"], str)
        
        # Check that it contains the service information
        services_str = result["content"]["services"]
        self.assertIn("Reading Support", services_str)
        self.assertIn("3x per week", services_str)
        self.assertIn("Math Support", services_str)
        self.assertIn("Articulation", services_str)
        
        # Ensure no [object Object] would appear
        self.assertNotIn("[object Object]", json.dumps(result))
        
        print("✅ Triple-nested services test passed")
    
    def test_double_nested_present_levels(self):
        """Test flattening of double-nested present_levels structure"""
        input_data = {
            "id": str(uuid4()),
            "student_id": str(uuid4()),
            "content": {
                "student_name": "Test Student",
                "present_levels": {
                    "present_levels": "Student demonstrates grade-level performance in mathematics but shows significant challenges in reading comprehension. Current reading level is approximately 2 grades below grade level."
                }
            }
        }
        
        result = self.flattener.flatten(input_data)
        
        # Check that present_levels is extracted correctly
        self.assertIsInstance(result["content"]["present_levels"], str)
        self.assertEqual(
            result["content"]["present_levels"],
            "Student demonstrates grade-level performance in mathematics but shows significant challenges in reading comprehension. Current reading level is approximately 2 grades below grade level."
        )
        
        # Ensure no [object Object] would appear
        self.assertNotIn("[object Object]", json.dumps(result))
        
        print("✅ Double-nested present_levels test passed")
    
    def test_complex_assessment_summary(self):
        """Test flattening of complex assessment_summary objects"""
        input_data = {
            "id": str(uuid4()),
            "student_id": str(uuid4()),
            "content": {
                "student_name": "Test Student",
                "assessment_summary": {
                    "reading_level": "Grade 3",
                    "math_level": "Grade 5", 
                    "strengths": ["Visual learning", "Problem solving", "Verbal communication"],
                    "areas_for_growth": ["Reading fluency", "Written expression"],
                    "learning_profile": {
                        "learning_style": "Visual-kinesthetic",
                        "attention_span": "15-20 minutes",
                        "processing_speed": "Below average"
                    },
                    "behavioral_observations": "Student is engaged and motivated when working on hands-on activities"
                }
            }
        }
        
        result = self.flattener.flatten(input_data)
        
        # Check that assessment_summary is now a formatted JSON string
        self.assertIsInstance(result["content"]["assessment_summary"], str)
        
        # Parse the JSON to ensure it's valid
        parsed_assessment = json.loads(result["content"]["assessment_summary"])
        self.assertEqual(parsed_assessment["reading_level"], "Grade 3")
        self.assertIn("Visual learning", parsed_assessment["strengths"])
        
        # Ensure no [object Object] would appear
        self.assertNotIn("[object Object]", json.dumps(result))
        
        print("✅ Complex assessment_summary test passed")
    
    def test_array_of_complex_goals(self):
        """Test flattening of arrays containing complex goal objects"""
        input_data = {
            "id": str(uuid4()),
            "student_id": str(uuid4()),
            "content": {
                "student_name": "Test Student",
                "goals": [
                    {
                        "domain": "Reading",
                        "goal_text": "Student will improve reading comprehension",
                        "baseline": "Currently reading at 2nd grade level",
                        "target_criteria": "80% accuracy on grade-level passages",
                        "measurement_method": "Weekly assessments",
                        "target_date": "2025-06-01"
                    },
                    {
                        "domain": "Math",
                        "goal_text": "Student will solve multi-step word problems",
                        "baseline": "Currently solves 30% of problems correctly",
                        "target_criteria": "75% accuracy on grade-level problems",
                        "measurement_method": "Bi-weekly assessments",
                        "target_date": "2025-06-01"
                    }
                ]
            }
        }
        
        result = self.flattener.flatten(input_data)
        
        # Check that goals is now a formatted JSON string
        self.assertIsInstance(result["content"]["goals"], str)
        
        # Parse the JSON to ensure it's valid and contains goal data
        parsed_goals = json.loads(result["content"]["goals"])
        self.assertEqual(len(parsed_goals), 2)
        self.assertEqual(parsed_goals[0]["domain"], "Reading")
        self.assertEqual(parsed_goals[1]["domain"], "Math")
        
        # Ensure no [object Object] would appear
        self.assertNotIn("[object Object]", json.dumps(result))
        
        print("✅ Array of complex goals test passed")
    
    def test_no_content_section(self):
        """Test handling of IEP data without content section"""
        input_data = {
            "id": str(uuid4()),
            "student_id": str(uuid4()),
            "status": "draft",
            "academic_year": "2025-2026"
        }
        
        result = self.flattener.flatten(input_data)
        
        # Should return original data unchanged
        self.assertEqual(result, input_data)
        
        print("✅ No content section test passed")
    
    def test_simple_string_values_unchanged(self):
        """Test that simple string values are not modified"""
        input_data = {
            "id": str(uuid4()),
            "student_id": str(uuid4()),
            "content": {
                "student_name": "Test Student",
                "grade_level": "5",
                "case_manager_name": "Ms. Johnson",
                "simple_present_levels": "Student shows good progress in math",
                "simple_goals": "Improve reading comprehension"
            }
        }
        
        result = self.flattener.flatten(input_data)
        
        # All simple values should remain unchanged
        self.assertEqual(result["content"]["student_name"], "Test Student")
        self.assertEqual(result["content"]["grade_level"], "5")
        self.assertEqual(result["content"]["case_manager_name"], "Ms. Johnson")
        self.assertEqual(result["content"]["simple_present_levels"], "Student shows good progress in math")
        self.assertEqual(result["content"]["simple_goals"], "Improve reading comprehension")
        
        print("✅ Simple string values test passed")
    
    def test_performance_measurement(self):
        """Test performance impact of flattening"""
        # Create a large, complex IEP data structure
        large_input = {
            "id": str(uuid4()),
            "student_id": str(uuid4()),
            "content": {
                "student_name": "Performance Test Student",
                "services": {
                    "services": {
                        f"service_category_{i}": [
                            {
                                "name": f"Service {j}",
                                "frequency": f"{j}x per week",
                                "duration": f"{j*10} minutes"
                            } for j in range(1, 6)
                        ] for i in range(1, 11)
                    }
                },
                "assessment_summary": {
                    f"assessment_area_{i}": f"Assessment data for area {i}" for i in range(1, 21)
                }
            }
        }
        
        # Measure performance
        start_time = time.time()
        result = self.flattener.flatten(large_input)
        end_time = time.time()
        
        duration_ms = (end_time - start_time) * 1000
        
        # Performance should be under 50ms for large structures
        self.assertLess(duration_ms, 50, f"Flattening took {duration_ms:.2f}ms, expected < 50ms")
        
        # Result should still be valid
        self.assertIsInstance(result["content"]["services"], str)
        self.assertIsInstance(result["content"]["assessment_summary"], str)
        
        print(f"✅ Performance test passed: {duration_ms:.2f}ms")
    
    def test_error_handling_invalid_input(self):
        """Test error handling for invalid input types"""
        # Test with non-dict input
        result = self.flattener.flatten("not a dict")
        self.assertEqual(result, "not a dict")
        
        # Test with None input
        result = self.flattener.flatten(None)
        self.assertEqual(result, None)
        
        # Test with list input
        result = self.flattener.flatten([1, 2, 3])
        self.assertEqual(result, [1, 2, 3])
        
        print("✅ Error handling test passed")
    
    def test_statistics_tracking(self):
        """Test that statistics are properly tracked"""
        # Use the static method which uses the global flattener instance
        test_data = {
            "id": str(uuid4()),
            "student_id": str(uuid4()),
            "content": {
                "services": {
                    "services": {"special_ed": [{"name": "test"}]}
                }
            }
        }
        
        # Reset statistics first
        reset_flattener_statistics()
        
        # Flatten multiple times using the static method
        for _ in range(5):
            SimpleIEPFlattener.flatten_for_frontend(test_data)
        
        # Check statistics
        stats = get_flattener_statistics()
        self.assertEqual(stats['total_operations'], 5)
        self.assertGreater(stats['total_structures_flattened'], 0)
        self.assertGreater(stats['total_time_ms'], 0)
        self.assertEqual(stats['error_count'], 0)
        
        print(f"✅ Statistics tracking test passed: {stats}")
    
    def test_transformation_metadata(self):
        """Test that transformation metadata is added when detailed logging is enabled"""
        input_data = {
            "id": str(uuid4()),
            "student_id": str(uuid4()),
            "content": {
                "services": {
                    "services": {"special_ed": [{"name": "Reading Support"}]}
                }
            }
        }
        
        result = self.flattener.flatten(input_data)
        
        # Check that metadata was added
        self.assertIn('_transformation_metadata', result)
        metadata = result['_transformation_metadata']
        
        self.assertIn('flattened_at', metadata)
        self.assertIn('transformation_summary', metadata)
        self.assertIn('problems_detected', metadata)
        self.assertEqual(metadata['flattener_version'], '1.0.0')
        
        print("✅ Transformation metadata test passed")
    
    def test_real_world_maya_case(self):
        """Test with the actual Maya Rodriguez case that caused issues"""
        maya_data = {
            "id": str(uuid4()),
            "student_id": str(uuid4()),
            "content": {
                "student_name": "Maya Rodriguez",
                "grade_level": "7th",
                "case_manager_name": "Ms. Sarah Wilson",
                "assessment_summary": {
                    "current_achievement": "Maya is currently performing below grade level in reading comprehension and written expression. She demonstrates strengths in verbal communication and problem-solving when content is presented orally.",
                    "strengths": ["Strong verbal communication skills", "Problem-solving abilities", "Positive attitude toward learning"],
                    "areas_for_growth": ["Reading comprehension", "Written expression", "Organization skills"],
                    "learning_profile": "Maya learns best through auditory instruction and benefits from visual supports. She requires frequent breaks and prefers hands-on activities.",
                    "interests": "Art, music, and working with animals"
                },
                "present_levels": {
                    "present_levels": "Based on recent assessments and classroom observations, Maya demonstrates the following present levels of academic achievement and functional performance..."
                },
                "services": {
                    "services": {
                        "special_education": [
                            {
                                "name": "Resource Room Support",
                                "frequency": "5 times per week",
                                "duration": "45 minutes per session"
                            }
                        ],
                        "related_services": [
                            {
                                "name": "Speech-Language Therapy",
                                "frequency": "2 times per week", 
                                "duration": "30 minutes per session"
                            }
                        ]
                    }
                }
            }
        }
        
        result = self.flattener.flatten(maya_data)
        
        # Verify all problematic structures are flattened
        self.assertIsInstance(result["content"]["assessment_summary"], str)
        self.assertIsInstance(result["content"]["present_levels"], str)
        self.assertIsInstance(result["content"]["services"], str)
        
        # Verify content is preserved
        assessment_json = json.loads(result["content"]["assessment_summary"])
        self.assertIn("Maya is currently performing", assessment_json["current_achievement"])
        
        # Verify no [object Object] would appear
        result_str = json.dumps(result)
        self.assertNotIn("[object Object]", result_str)
        self.assertNotIn("object Object", result_str)
        
        print("✅ Real-world Maya case test passed")

def run_comprehensive_tests():
    """Run all flattener tests with detailed output"""
    print("🧪 Starting Response Flattener Test Suite")
    print("=" * 60)
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestResponseFlattener)
    
    # Run tests with verbose output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "=" * 60)
    print("📊 Test Summary")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.failures:
        print("\n❌ Failures:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback}")
    
    if result.errors:
        print("\n💥 Errors:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback}")
    
    # Print final statistics
    final_stats = get_flattener_statistics()
    print(f"\n📈 Final Flattener Statistics:")
    print(f"  Total operations: {final_stats['total_operations']}")
    print(f"  Structures flattened: {final_stats['total_structures_flattened']}")
    print(f"  Average time per operation: {final_stats['average_time_per_operation_ms']:.2f}ms")
    print(f"  Error rate: {final_stats['error_rate']:.2%}")
    
    success = len(result.failures) == 0 and len(result.errors) == 0
    print(f"\n{'🎉 All tests passed!' if success else '❌ Some tests failed!'}")
    
    return success

if __name__ == "__main__":
    run_comprehensive_tests()