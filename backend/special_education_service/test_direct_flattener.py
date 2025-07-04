#!/usr/bin/env python3
"""Test flattener directly with problematic structures"""

import sys
import os
import json

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.response_flattener import SimpleIEPFlattener

def test_problematic_structures():
    """Test the exact problematic structures that cause [object Object] errors"""
    
    # Create the exact structures that were causing issues in Maya's case
    problematic_iep = {
        "id": "test-iep-123",
        "student_id": "test-student-456", 
        "content": {
            "student_name": "Maya Rodriguez",
            "grade_level": "7th",
            "case_manager_name": "Ms. Sarah Wilson",
            
            # Triple-nested services (the actual problem structure)
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
            },
            
            # Double-nested present_levels (another problem structure)
            "present_levels": {
                "present_levels": "Based on recent assessments and classroom observations, Maya demonstrates the following present levels of academic achievement and functional performance in reading, writing, and mathematics..."
            },
            
            # Complex assessment_summary object
            "assessment_summary": {
                "current_achievement": "Maya is currently performing below grade level in reading comprehension and written expression.",
                "strengths": ["Strong verbal communication skills", "Problem-solving abilities"],
                "areas_for_growth": ["Reading comprehension", "Written expression", "Organization skills"],
                "learning_profile": {
                    "learning_style": "Visual-kinesthetic",
                    "attention_span": "15-20 minutes",
                    "processing_speed": "Below average"
                },
                "interests": "Art, music, and working with animals"
            },
            
            # Array of complex goal objects
            "goals": [
                {
                    "domain": "Reading",
                    "goal_text": "Student will improve reading comprehension",
                    "baseline": "Currently reading at 2nd grade level",
                    "target_criteria": "80% accuracy on grade-level passages",
                    "measurement_method": "Weekly assessments"
                },
                {
                    "domain": "Math", 
                    "goal_text": "Student will solve multi-step word problems",
                    "baseline": "Currently solves 30% of problems correctly",
                    "target_criteria": "75% accuracy on grade-level problems",
                    "measurement_method": "Bi-weekly assessments"
                }
            ]
        }
    }
    
    print("🧪 Testing Response Flattener with Problematic Structures")
    print("=" * 60)
    
    # Test the original data that would cause [object Object] errors
    print("📋 Original problematic structures:")
    print(f"  services type: {type(problematic_iep['content']['services']).__name__}")
    print(f"  services.services type: {type(problematic_iep['content']['services']['services']).__name__}")
    print(f"  present_levels type: {type(problematic_iep['content']['present_levels']).__name__}")
    print(f"  present_levels.present_levels type: {type(problematic_iep['content']['present_levels']['present_levels']).__name__}")
    print(f"  assessment_summary type: {type(problematic_iep['content']['assessment_summary']).__name__}")
    print(f"  goals type: {type(problematic_iep['content']['goals']).__name__}")
    
    # Check for [object Object] potential
    original_json = json.dumps(problematic_iep)
    print(f"  Original JSON length: {len(original_json)} characters")
    
    print("\n🔧 Applying flattener...")
    
    # Apply flattener
    flattener = SimpleIEPFlattener(enable_detailed_logging=True)
    flattened_iep = flattener.flatten(problematic_iep)
    
    print("\n📊 Flattened structures:")
    print(f"  services type: {type(flattened_iep['content']['services']).__name__}")
    print(f"  present_levels type: {type(flattened_iep['content']['present_levels']).__name__}")
    print(f"  assessment_summary type: {type(flattened_iep['content']['assessment_summary']).__name__}")
    print(f"  goals type: {type(flattened_iep['content']['goals']).__name__}")
    
    # Check results
    flattened_json = json.dumps(flattened_iep)
    print(f"  Flattened JSON length: {len(flattened_json)} characters")
    
    # Verify no [object Object] errors would occur
    has_object_errors = "[object Object]" in flattened_json or "object Object" in flattened_json
    print(f"  [object Object] errors: {'❌ FOUND' if has_object_errors else '✅ NONE'}")
    
    # Show samples of flattened content
    print(f"\n📄 Sample flattened content:")
    content = flattened_iep['content']
    
    if isinstance(content['services'], str):
        print(f"  services (first 100 chars): {content['services'][:100]}...")
    
    if isinstance(content['present_levels'], str):
        print(f"  present_levels (first 100 chars): {content['present_levels'][:100]}...")
    
    if isinstance(content['assessment_summary'], str):
        summary_preview = content['assessment_summary'][:100].replace('\n', ' ')
        print(f"  assessment_summary (first 100 chars): {summary_preview}...")
    
    # Check for transformation metadata
    if '_transformation_metadata' in flattened_iep:
        metadata = flattened_iep['_transformation_metadata']
        print(f"\n📈 Transformation metadata:")
        print(f"  Structures transformed: {metadata['transformation_summary']['total_transformed']}")
        print(f"  Problems detected: {len(metadata['problems_detected'])}")
        
        for problem in metadata['problems_detected']:
            print(f"    - {problem['pattern']}: {problem['key']}")
    
    # Performance check
    print(f"\n⚡ Performance:")
    stats = flattener.get_statistics()
    print(f"  Operations: {stats['total_operations']}")
    print(f"  Average time: {stats['average_time_per_operation_ms']:.2f}ms")
    print(f"  Error rate: {stats['error_rate']:.1%}")
    
    # Save results for inspection
    with open('/tmp/direct_flattener_test.json', 'w') as f:
        json.dump(flattened_iep, f, indent=2)
    print(f"\n💾 Full results saved to /tmp/direct_flattener_test.json")
    
    # Final verdict
    success = (
        isinstance(content['services'], str) and
        isinstance(content['present_levels'], str) and
        isinstance(content['assessment_summary'], str) and
        isinstance(content['goals'], str) and
        not has_object_errors
    )
    
    print(f"\n🎯 Overall Result: {'✅ SUCCESS' if success else '❌ FAILED'}")
    
    if success:
        print("The flattener successfully converts all problematic structures to frontend-safe formats!")
    else:
        print("Some structures were not properly flattened.")
    
    return success

if __name__ == "__main__":
    test_problematic_structures()