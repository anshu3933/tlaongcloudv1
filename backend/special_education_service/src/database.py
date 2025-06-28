"""Database connection and session management for Special Education Service

IMPORTANT: For atomic operations and version constraint safety, use the
request-scoped session middleware instead of the legacy get_db dependency.
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import text, select
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

# Create session factory with safe defaults
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=True  # Safer default - prevents lazy loading issues
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
    """Legacy dependency for FastAPI to get database session (DEPRECATED)
    
    This creates a new session per dependency injection, which can lead to
    race conditions in version constraint scenarios. Use get_request_session
    from middleware instead for atomic operations.
    """
    async with async_session_factory() as session:
        try:
            yield session
        except Exception as e:
            logger.error(f"Database session error: {e}")
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_request_scoped_db(request) -> AsyncSession:
    """Get the request-scoped database session from middleware
    
    This ensures all operations within a single HTTP request use the same
    database session, preventing race conditions and ensuring atomicity.
    """
    from .middleware.session_middleware import get_request_session
    return await get_request_session(request)

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
            
            # Create default IEP templates
            from .models.special_education_models import IEPTemplate
            
            # Check if templates already exist
            existing_templates = await session.execute(select(IEPTemplate))
            if existing_templates.scalar_one_or_none():
                logger.info("Default templates already exist, skipping creation")
                return
            
            # Get created disability types for foreign key references
            sld_disability = await session.execute(
                select(DisabilityType).where(DisabilityType.code == "SLD")
            )
            sld_id = sld_disability.scalar_one().id
            
            autism_disability = await session.execute(
                select(DisabilityType).where(DisabilityType.code == "AU")
            )
            autism_id = autism_disability.scalar_one().id
            
            ed_disability = await session.execute(
                select(DisabilityType).where(DisabilityType.code == "ED")
            )
            ed_id = ed_disability.scalar_one().id
            
            # Template structure with comprehensive sections
            template_sections = {
                "present_levels": {
                    "required": True,
                    "description": "Present levels of academic achievement and functional performance",
                    "fields": ["academic_performance", "functional_performance", "strengths", "needs"]
                },
                "goals": {
                    "required": True,
                    "description": "Annual goals and short-term objectives",
                    "fields": ["academic_goals", "functional_goals", "behavioral_goals"]
                },
                "services": {
                    "required": True,
                    "description": "Special education and related services",
                    "fields": ["special_education_services", "related_services", "supplementary_aids"]
                },
                "accommodations": {
                    "required": True,
                    "description": "Accommodations and modifications",
                    "fields": ["testing_accommodations", "classroom_accommodations", "behavioral_supports"]
                },
                "transition": {
                    "required": False,
                    "description": "Transition services (for age 16+)",
                    "fields": ["post_secondary_goals", "transition_activities", "agency_linkages"]
                },
                "behavior_plan": {
                    "required": False,
                    "description": "Behavior intervention plan",
                    "fields": ["target_behaviors", "interventions", "data_collection"]
                }
            }
            
            # Default goals for different disabilities
            sld_goals = [
                {
                    "domain": "Reading",
                    "goal_template": "By [date], when given grade-level text, [student] will read with accuracy and fluency as measured by [measurement]",
                    "measurement_suggestions": ["oral reading fluency", "comprehension questions", "running records"]
                },
                {
                    "domain": "Writing", 
                    "goal_template": "By [date], when given a writing prompt, [student] will compose a paragraph with topic sentence and supporting details as measured by [measurement]",
                    "measurement_suggestions": ["writing rubric", "teacher observation", "work samples"]
                },
                {
                    "domain": "Math",
                    "goal_template": "By [date], when given grade-level math problems, [student] will solve with [accuracy]% accuracy as measured by [measurement]",
                    "measurement_suggestions": ["curriculum-based assessments", "progress monitoring", "standardized tests"]
                }
            ]
            
            autism_goals = [
                {
                    "domain": "Communication",
                    "goal_template": "By [date], [student] will initiate communication with peers/adults in [context] as measured by [measurement]",
                    "measurement_suggestions": ["data collection sheets", "video analysis", "teacher observation"]
                },
                {
                    "domain": "Social Skills",
                    "goal_template": "By [date], [student] will demonstrate appropriate social interactions during [activity] as measured by [measurement]",
                    "measurement_suggestions": ["social skills checklist", "peer ratings", "behavioral observations"]
                },
                {
                    "domain": "Adaptive Behavior",
                    "goal_template": "By [date], [student] will independently complete [task] in [setting] as measured by [measurement]",
                    "measurement_suggestions": ["task analysis", "independence scale", "time sampling"]
                }
            ]
            
            ed_goals = [
                {
                    "domain": "Behavioral",
                    "goal_template": "By [date], [student] will demonstrate appropriate behaviors during [activity] as measured by [measurement]",
                    "measurement_suggestions": ["behavior frequency charts", "ABC data", "functional behavior assessment"]
                },
                {
                    "domain": "Social-Emotional",
                    "goal_template": "By [date], [student] will use coping strategies when experiencing [trigger] as measured by [measurement]",
                    "measurement_suggestions": ["self-monitoring sheets", "counselor observations", "incident reports"]
                },
                {
                    "domain": "Academic",
                    "goal_template": "By [date], [student] will complete academic tasks with minimal behavioral interruptions as measured by [measurement]",
                    "measurement_suggestions": ["on-task behavior data", "work completion rates", "teacher ratings"]
                }
            ]
            
            # Create templates for different grade levels and disabilities
            default_templates = [
                # Elementary SLD templates
                {
                    "name": "Elementary SLD Template (K-5)",
                    "disability_type_id": sld_id,
                    "grade_level": "K-5",
                    "sections": template_sections,
                    "default_goals": sld_goals,
                    "version": 1,
                    "created_by_auth_id": 1  # System user
                },
                {
                    "name": "Middle School SLD Template (6-8)",
                    "disability_type_id": sld_id,
                    "grade_level": "6-8", 
                    "sections": template_sections,
                    "default_goals": sld_goals,
                    "version": 1,
                    "created_by_auth_id": 1
                },
                {
                    "name": "High School SLD Template (9-12)",
                    "disability_type_id": sld_id,
                    "grade_level": "9-12",
                    "sections": {**template_sections, "transition": {**template_sections["transition"], "required": True}},
                    "default_goals": sld_goals,
                    "version": 1,
                    "created_by_auth_id": 1
                },
                # Autism templates
                {
                    "name": "Elementary Autism Template (K-5)",
                    "disability_type_id": autism_id,
                    "grade_level": "K-5",
                    "sections": template_sections,
                    "default_goals": autism_goals,
                    "version": 1,
                    "created_by_auth_id": 1
                },
                {
                    "name": "Middle School Autism Template (6-8)",
                    "disability_type_id": autism_id,
                    "grade_level": "6-8",
                    "sections": template_sections,
                    "default_goals": autism_goals,
                    "version": 1,
                    "created_by_auth_id": 1
                },
                {
                    "name": "High School Autism Template (9-12)",
                    "disability_type_id": autism_id,
                    "grade_level": "9-12",
                    "sections": {**template_sections, "transition": {**template_sections["transition"], "required": True}},
                    "default_goals": autism_goals,
                    "version": 1,
                    "created_by_auth_id": 1
                },
                # Emotional Disturbance templates
                {
                    "name": "Elementary ED Template (K-5)",
                    "disability_type_id": ed_id,
                    "grade_level": "K-5",
                    "sections": {**template_sections, "behavior_plan": {**template_sections["behavior_plan"], "required": True}},
                    "default_goals": ed_goals,
                    "version": 1,
                    "created_by_auth_id": 1
                },
                {
                    "name": "Middle School ED Template (6-8)",
                    "disability_type_id": ed_id,
                    "grade_level": "6-8",
                    "sections": {**template_sections, "behavior_plan": {**template_sections["behavior_plan"], "required": True}},
                    "default_goals": ed_goals,
                    "version": 1,
                    "created_by_auth_id": 1
                },
                {
                    "name": "High School ED Template (9-12)",
                    "disability_type_id": ed_id,
                    "grade_level": "9-12",
                    "sections": {
                        **template_sections, 
                        "transition": {**template_sections["transition"], "required": True},
                        "behavior_plan": {**template_sections["behavior_plan"], "required": True}
                    },
                    "default_goals": ed_goals,
                    "version": 1,
                    "created_by_auth_id": 1
                },
                # Generic templates
                {
                    "name": "General Elementary Template (K-5)",
                    "disability_type_id": None,
                    "grade_level": "K-5",
                    "sections": template_sections,
                    "default_goals": [],
                    "version": 1,
                    "created_by_auth_id": 1
                },
                {
                    "name": "General Middle School Template (6-8)",
                    "disability_type_id": None,
                    "grade_level": "6-8",
                    "sections": template_sections,
                    "default_goals": [],
                    "version": 1,
                    "created_by_auth_id": 1
                },
                {
                    "name": "General High School Template (9-12)",
                    "disability_type_id": None,
                    "grade_level": "9-12",
                    "sections": {**template_sections, "transition": {**template_sections["transition"], "required": True}},
                    "default_goals": [],
                    "version": 1,
                    "created_by_auth_id": 1
                }
            ]
            
            for template_data in default_templates:
                template = IEPTemplate(**template_data)
                session.add(template)
            
            await session.commit()
            logger.info(f"Created {len(default_templates)} default IEP templates")

async def check_database_connection() -> bool:
    """Check if database connection is working"""
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False