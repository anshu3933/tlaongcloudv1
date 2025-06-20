"""Test utilities for database setup and cleanup"""
import os
import asyncio
import asyncpg
from pathlib import Path
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text


async def cleanup_test_databases():
    """Clean up test databases after test runs"""
    # Remove SQLite test files
    test_files = [
        'test_special_education.db',
        'test_auth.db',
        'special_education_dev.db',
        'test.db',
        'test_special_ed.db'
    ]
    
    for file in test_files:
        if Path(file).exists():
            Path(file).unlink()
            print(f"✅ Removed test database: {file}")


async def setup_test_postgresql_db(database_name: str = "test_special_education"):
    """Set up PostgreSQL test database (if using PostgreSQL for tests)"""
    try:
        # Connect to default postgres database
        conn = await asyncpg.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            port=os.getenv('DB_PORT', 5432),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD', 'postgres'),
            database='postgres'
        )
        
        # Drop database if exists
        await conn.execute(f'DROP DATABASE IF EXISTS {database_name}')
        
        # Create test database
        await conn.execute(f'CREATE DATABASE {database_name}')
        
        await conn.close()
        print(f"✅ Created PostgreSQL test database: {database_name}")
        
    except Exception as e:
        print(f"⚠️  Could not set up PostgreSQL test database: {e}")
        print("   Using SQLite for tests instead")


async def cleanup_test_postgresql_db(database_name: str = "test_special_education"):
    """Clean up PostgreSQL test database"""
    try:
        conn = await asyncpg.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            port=os.getenv('DB_PORT', 5432),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD', 'postgres'),
            database='postgres'
        )
        
        # Terminate connections to test database
        await conn.execute(f"""
            SELECT pg_terminate_backend(pid) 
            FROM pg_stat_activity 
            WHERE datname = '{database_name}'
        """)
        
        # Drop test database
        await conn.execute(f'DROP DATABASE IF EXISTS {database_name}')
        
        await conn.close()
        print(f"✅ Cleaned up PostgreSQL test database: {database_name}")
        
    except Exception as e:
        print(f"⚠️  Could not clean up PostgreSQL test database: {e}")


async def verify_test_database_connection(database_url: str):
    """Verify test database connection works"""
    try:
        engine = create_async_engine(database_url)
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        await engine.dispose()
        print(f"✅ Test database connection verified: {database_url}")
        return True
    except Exception as e:
        print(f"❌ Test database connection failed: {e}")
        return False


def get_test_database_url(service_name: str = "main") -> str:
    """Get appropriate test database URL based on environment"""
    # Check if we should use PostgreSQL for tests
    if os.getenv('USE_POSTGRESQL_FOR_TESTS', 'false').lower() == 'true':
        return f"postgresql+asyncpg://postgres:postgres@localhost:5432/test_{service_name}"
    else:
        # Use SQLite for fast, isolated tests
        return f"sqlite+aiosqlite:///./test_{service_name}.db"


if __name__ == "__main__":
    """Run cleanup when script is executed directly"""
    print("🧹 Cleaning up test databases...")
    asyncio.run(cleanup_test_databases())
    
    # Optionally clean up PostgreSQL test databases
    if os.getenv('USE_POSTGRESQL_FOR_TESTS', 'false').lower() == 'true':
        asyncio.run(cleanup_test_postgresql_db("test_special_education"))
        asyncio.run(cleanup_test_postgresql_db("test_auth"))
    
    print("✅ Test database cleanup complete")