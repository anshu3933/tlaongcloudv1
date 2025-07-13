#!/usr/bin/env python3
"""Simple test to verify enum functionality"""

import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from src.common.enums import AssessmentType
    print("✅ Successfully imported AssessmentType from src.common.enums")
    
    # Test enum values
    print(f"AssessmentType.WISC_V = {AssessmentType.WISC_V}")
    print(f"AssessmentType.WISC_V.value = {AssessmentType.WISC_V.value}")
    
    # Test string conversion
    try:
        enum_val = AssessmentType("wisc_v")
        print(f"✅ String conversion works: 'wisc_v' -> {enum_val}")
    except Exception as e:
        print(f"❌ String conversion failed: {e}")
    
    # Test invalid string
    try:
        enum_val = AssessmentType("invalid")
        print(f"❌ Should have failed: {enum_val}")
    except ValueError:
        print("✅ Invalid string properly rejected")
    
    # Test all enum values
    print(f"\nAll AssessmentType values:")
    for enum_val in AssessmentType:
        print(f"  {enum_val.name} = {enum_val.value}")
        
except ImportError as e:
    print(f"❌ Import failed: {e}")
    import traceback
    traceback.print_exc()