"""Simple test runner that bypasses complex configuration"""
import os
import sys
import asyncio
from pathlib import Path

# Add project to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Set environment
os.environ.update({
    "ENVIRONMENT": "development",
    "DATABASE_URL": "sqlite+aiosqlite:///./test.db",
    "JWT_SECRET_KEY": "test-key", 
    "GCP_PROJECT_ID": "test-project",
    "GCS_BUCKET_NAME": "test-bucket",
    "GEMINI_MODEL": "gemini-2.5-flash",
    "SMTP_ENABLED": "false",
    "SMTP_USERNAME": "test@example.com",
    "SMTP_FROM_EMAIL": "test@example.com"
})

async def test_simple_operations():
    """Test basic database operations without full service"""
    print("🧪 Testing Special Education Service Components")
    print("=" * 50)
    
    try:
        # Test 1: Import and create models
        print("1. Testing model imports...")
        from special_education_service.src.models.special_education_models import (
            Base
        )
        print("✅ Models imported successfully")
        
        # Test 2: Test database connection
        print("\n2. Testing database connection...")
        from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
        
        # Simple engine for SQLite
        engine = create_async_engine("sqlite+aiosqlite:///./test.db", echo=True)
        
        # Create tables
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("✅ Database tables created")
        
        # Test 3: Test repository
        print("\n3. Testing repository operations...")
        async_session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        
        async with async_session_factory() as session:
            from special_education_service.src.repositories.student_repository import StudentRepository
            student_repo = StudentRepository(session)
            
            # Create test student
            from datetime import date
            import time
            student_data = {
                "student_id": f"TEST{int(time.time())}",
                "first_name": "John",
                "last_name": "Doe", 
                "date_of_birth": date(2010, 5, 15),
                "grade_level": "5th",
                "disability_codes": ["SLD"]
            }
            
            student = await student_repo.create_student(student_data)
            print(f"✅ Created student: {student['full_name']}")
            
            # Test retrieval - convert string ID to UUID
            import uuid
            student_uuid = uuid.UUID(student["id"]) if isinstance(student["id"], str) else student["id"]
            retrieved = await student_repo.get_student(student_uuid)
            print(f"✅ Retrieved student: {retrieved['student_id']}")
        
        print("\n🎉 All component tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_simple_operations())
    if success:
        print("\n✨ Components are working correctly!")
        print("💡 The issue is likely in the service startup configuration")
    else:
        print("\n💥 Component tests failed - need to fix basic functionality first")