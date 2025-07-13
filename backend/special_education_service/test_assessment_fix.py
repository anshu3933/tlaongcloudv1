#!/usr/bin/env python3
"""Test script to verify the assessment document creation fix"""

import asyncio
import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.repositories.assessment_repository import AssessmentRepository
from src.database import get_db
from src.common.enums import AssessmentType

async def test_assessment_creation():
    """Test assessment document creation with the fixed enum handling"""
    
    # Get database session
    async for db in get_db():
        repo = AssessmentRepository(db)
        
        # Test data
        test_data = {
            "student_id": "a5c65e54-29b2-4aaf-a0f2-805049b3169e",
            "document_type": "wisc_v",  # String that should be converted to enum
            "file_name": "test_assessment.pdf",
            "file_path": "/tmp/test.pdf",
            "assessor_name": "Dr. Test"
        }
        
        print(f"Testing assessment creation with data: {test_data}")
        
        try:
            result = await repo.create_assessment_document(test_data)
            print(f"✅ SUCCESS: Created assessment document: {result['id']}")
            return True
        except Exception as e:
            print(f"❌ ERROR: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            await db.close()

async def test_enum_conversion():
    """Test the enum conversion logic directly"""
    print("\n🧪 Testing enum conversion:")
    
    # Test valid conversion
    try:
        enum_val = AssessmentType("wisc_v")
        print(f"✅ Valid enum conversion: 'wisc_v' -> {enum_val}")
    except Exception as e:
        print(f"❌ Valid enum conversion failed: {e}")
    
    # Test invalid conversion
    try:
        enum_val = AssessmentType("invalid_type")
        print(f"❌ Invalid enum should have failed but got: {enum_val}")
    except ValueError as e:
        print(f"✅ Invalid enum properly rejected: {e}")

if __name__ == "__main__":
    print("🚀 Testing Assessment Document Creation Fix")
    print("=" * 50)
    
    # Test enum conversion first
    asyncio.run(test_enum_conversion())
    
    # Test full creation
    print("\n🧪 Testing full assessment creation:")
    success = asyncio.run(test_assessment_creation())
    
    if success:
        print("\n🎉 All tests passed! The fix is working correctly.")
    else:
        print("\n💥 Tests failed. Check the error details above.")
    
    print("=" * 50)