"""Database connection and session management for Special Education Service"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import text
from contextlib import asynccontextmanager
from typing import AsyncGenerator
import logging

from common.src.config import get_settings
from .models.special_education_models import Base

logger = logging.getLogger(__name__)

# Get settings
settings = get_settings()

# Create async engine with conditional parameters based on database type
engine_kwargs = {
    "echo": settings.is_development,  # SQL debugging in development
}

# Add PostgreSQL-specific options only if not using SQLite
if not settings.database_url.startswith("sqlite"):
    engine_kwargs.update({
        "pool_pre_ping": True,
        "pool_recycle": 300,
        "pool_size": 20,
        "max_overflow": 30
    })

engine = create_async_engine(settings.database_url, **engine_kwargs)

# Create session factory
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Get database session with automatic cleanup"""
    async with async_session_factory() as session:
        try:
            yield session
        except Exception as e:
            logger.error(f"Database session error: {e}")
            await session.rollback()
            raise
        finally:
            await session.close()

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for FastAPI to get database session"""
    async with get_db_session() as session:
        yield session

async def create_tables():
    """Create all database tables"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    logger.info("Special education database tables created successfully")

async def drop_tables():
    """Drop all database tables (use with caution)"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    logger.warning("All special education database tables dropped")

async def init_database():
    """Initialize database with default data"""
    from .models.special_education_models import DisabilityType
    from sqlalchemy import text
    
    async with get_db_session() as session:
        # Check if disability types already exist
        result = await session.execute(
            text("SELECT COUNT(*) FROM disability_types")
        )
        count = result.scalar()
        
        if count == 0:
            # Create default disability types based on IDEA categories
            default_disabilities = [
                {
                    "code": "AU", 
                    "name": "Autism",
                    "federal_category": "Autism",
                    "description": "A developmental disability significantly affecting verbal and nonverbal communication and social interaction"
                },
                {
                    "code": "DB", 
                    "name": "Deaf-Blindness", 
                    "federal_category": "Deaf-blindness",
                    "description": "Concomitant hearing and visual impairments"
                },
                {
                    "code": "DD", 
                    "name": "Developmental Delay",
                    "federal_category": "Developmental delay",
                    "description": "Delays in development for children aged 3-9"
                },
                {
                    "code": "ED", 
                    "name": "Emotional Disturbance",
                    "federal_category": "Emotional disturbance", 
                    "description": "A condition exhibiting emotional or behavioral difficulties"
                },
                {
                    "code": "HI", 
                    "name": "Hearing Impairment",
                    "federal_category": "Hearing impairments",
                    "description": "An impairment in hearing that adversely affects educational performance"
                },
                {
                    "code": "ID", 
                    "name": "Intellectual Disability",
                    "federal_category": "Intellectual disabilities",
                    "description": "Significantly subaverage general intellectual functioning"
                },
                {
                    "code": "MD", 
                    "name": "Multiple Disabilities",
                    "federal_category": "Multiple disabilities",
                    "description": "Concomitant impairments that cause severe educational needs"
                },
                {
                    "code": "OI", 
                    "name": "Orthopedic Impairment",
                    "federal_category": "Orthopedic impairments",
                    "description": "A severe orthopedic impairment that adversely affects educational performance"
                },
                {
                    "code": "OHI", 
                    "name": "Other Health Impairment",
                    "federal_category": "Other health impairments",
                    "description": "Limited strength, vitality, or alertness due to chronic or acute health problems"
                },
                {
                    "code": "SLD", 
                    "name": "Specific Learning Disability",
                    "federal_category": "Specific learning disabilities",
                    "description": "A disorder in basic psychological processes involving understanding or using language"
                },
                {
                    "code": "SLI", 
                    "name": "Speech or Language Impairment",
                    "federal_category": "Speech or language impairments",
                    "description": "A communication disorder that adversely affects educational performance"
                },
                {
                    "code": "TBI", 
                    "name": "Traumatic Brain Injury",
                    "federal_category": "Traumatic brain injury",
                    "description": "An acquired injury to the brain caused by external physical force"
                },
                {
                    "code": "VI", 
                    "name": "Visual Impairment",
                    "federal_category": "Visual impairments",
                    "description": "An impairment in vision that adversely affects educational performance"
                }
            ]
            
            for disability_data in default_disabilities:
                disability = DisabilityType(**disability_data)
                session.add(disability)
            
            await session.commit()
            logger.info(f"Created {len(default_disabilities)} default disability types")

async def check_database_connection() -> bool:
    """Check if database connection is working"""
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False