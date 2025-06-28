import asyncio
import pytest
import os
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from src.database import Base
from src.repositories.student_repository import StudentRepository
from src.repositories.iep_repository import IEPRepository
from src.repositories.template_repository import TemplateRepository
from src.services.iep_service import IEPService
from src.rag.iep_generator import IEPGenerator
from common.src.vector_store import VectorStore


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_db_engine():
    """Create test database engine with in-memory SQLite"""
    # Use in-memory SQLite for fast testing
    database_url = "sqlite+aiosqlite:///:memory:"
    
    engine = create_async_engine(
        database_url,
        poolclass=StaticPool,
        connect_args={
            "check_same_thread": False,
        },
        echo=False  # Set to True for SQL debugging
    )
    
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    await engine.dispose()


@pytest.fixture
async def test_session(test_db_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a fresh database session for each test"""
    async_session_maker = async_sessionmaker(
        test_db_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    async with async_session_maker() as session:
        yield session
        await session.rollback()


@pytest.fixture
async def student_repository(test_session):
    """Create student repository for testing"""
    return StudentRepository(test_session)


@pytest.fixture
async def iep_repository(test_session):
    """Create IEP repository for testing"""
    return IEPRepository(test_session)


@pytest.fixture
async def template_repository(test_session):
    """Create template repository for testing"""
    return TemplateRepository(test_session)


@pytest.fixture
async def mock_vector_store():
    """Create mock vector store for testing"""
    class MockVectorStore:
        def __init__(self):
            self.documents = []
        
        def add_documents(self, docs):
            self.documents.extend(docs)
        
        async def similarity_search(self, query, limit=5):
            return []
    
    return MockVectorStore()


@pytest.fixture
async def mock_iep_generator():
    """Create mock IEP generator for testing"""
    class MockIEPGenerator:
        async def generate_iep(self, template, student_data, previous_ieps=None, previous_assessments=None):
            return {
                "academic_goals": [{"goal": "Test academic goal"}],
                "behavioral_goals": [{"goal": "Test behavioral goal"}],
                "transition_goals": [{"goal": "Test transition goal"}],
                "accommodations": ["Extended time", "Small group testing"],
                "modifications": ["Reduced homework load"],
                "services": [{"service": "Speech therapy", "frequency": "2x/week"}]
            }
        
        async def create_embedding(self, text):
            return [0.1] * 768  # Mock embedding
        
        async def _generate_section(self, section_name, section_template, context):
            return {f"{section_name}_content": f"Generated content for {section_name}"}
    
    return MockIEPGenerator()


@pytest.fixture
async def iep_service(iep_repository, template_repository, mock_vector_store, mock_iep_generator):
    """Create IEP service with mocked dependencies"""
    return IEPService(
        repository=iep_repository,
        pl_repository=None,  # Not needed for these tests
        vector_store=mock_vector_store,
        iep_generator=mock_iep_generator,
        workflow_client=None,  # Mock if needed
        audit_client=None      # Mock if needed
    )


@pytest.fixture
async def sample_student_data():
    """Sample student data for testing"""
    return {
        "student_id": "TEST-001",
        "first_name": "John",
        "last_name": "Doe",
        "date_of_birth": "2010-05-15",
        "grade_level": "5",
        "disability_codes": ["SLD"],
        "school_district": "Test District",
        "school_name": "Test Elementary",
        "enrollment_date": "2023-08-15"
    }


@pytest.fixture
async def sample_iep_data():
    """Sample IEP data for testing"""
    return {
        "academic_year": "2025-2026",
        "content": {
            "test": "content",
            "goals": ["goal1", "goal2"]
        },
        "meeting_date": "2025-01-15",
        "effective_date": "2025-01-15",
        "review_date": "2026-01-15"
    }


@pytest.fixture
async def sample_template_data():
    """Sample template data for testing"""
    return {
        "name": "Elementary SLD Template",
        "description": "Template for Specific Learning Disability",
        "grade_levels": ["3", "4", "5"],
        "disability_types": ["SLD"],
        "sections": {
            "academic_goals": {
                "required": True,
                "description": "Academic achievement goals",
                "fields": ["goal_text", "measurement", "timeline"]
            },
            "behavioral_goals": {
                "required": False,
                "description": "Behavioral support goals",
                "fields": ["behavior_target", "intervention", "measurement"]
            }
        },
        "is_active": True
    }