"""Simplified ADK Host for local development without Google Cloud dependencies"""

import os
import time
from typing import Dict, Any, List, Optional
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import httpx
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
class Settings:
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8002"))
    environment = os.getenv("ENVIRONMENT", "development")
    mcp_server_url = os.getenv("MCP_SERVER_URL", "http://localhost:8006")
    auth_service_url = os.getenv("AUTH_SERVICE_URL", "http://localhost:8001")
    mock_mode = os.getenv("MOCK_MODE", "true").lower() == "true"
    max_query_length = int(os.getenv("MAX_QUERY_LENGTH", "1000"))
    max_tokens = int(os.getenv("MAX_TOKENS", "1000"))
    temperature = float(os.getenv("TEMPERATURE", "0.7"))

settings = Settings()

# Global HTTP client
http_client: Optional[httpx.AsyncClient] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    global http_client
    
    # Initialize HTTP client
    http_client = httpx.AsyncClient(
        timeout=httpx.Timeout(30.0, connect=5.0),
        limits=httpx.Limits(
            max_keepalive_connections=20,
            max_connections=100
        )
    )
    
    print(f"ADK Host started in {'mock' if settings.mock_mode else 'production'} mode")
    yield
    
    # Shutdown
    if http_client:
        await http_client.aclose()

app = FastAPI(
    title="Educational IEP ADK Host",
    version="1.0.0",
    description="Backend-for-Frontend service for AI-powered educational content generation",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/Response models
class GenerateIEPRequest(BaseModel):
    student_id: str
    student_name: str
    grade_level: str
    disability_type: Optional[str] = None
    current_performance: Optional[str] = None
    goals: Optional[List[str]] = None
    additional_context: Optional[str] = None

class GenerateIEPResponse(BaseModel):
    iep_content: str
    sections: Dict[str, Any]
    metadata: Dict[str, Any]

class AnalyzeDocumentRequest(BaseModel):
    document_text: str
    analysis_type: str = "general"
    context: Optional[str] = None

class AnalyzeDocumentResponse(BaseModel):
    analysis: str
    key_points: List[str]
    recommendations: List[str]
    metadata: Dict[str, Any]

class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000)
    context: Optional[str] = None

class QueryResponse(BaseModel):
    response: str
    sources: List[Dict[str, Any]] = []
    metadata: Dict[str, Any]

def generate_mock_iep_content(request: GenerateIEPRequest) -> str:
    """Generate mock IEP content for development"""
    return f"""
# INDIVIDUALIZED EDUCATION PROGRAM (IEP)

## Student Information
- **Name:** {request.student_name}
- **Grade Level:** {request.grade_level}
- **Disability Category:** {request.disability_type or 'Not specified'}

## Present Level of Academic Achievement and Functional Performance
{request.current_performance or 'Student demonstrates varying levels of academic and functional performance across different domains.'}

## Annual Goals
"""
    + (f"""
### Goal 1: Academic Performance
By the end of the IEP year, {request.student_name} will improve reading comprehension skills from current level to grade-appropriate level with 80% accuracy on curriculum-based assessments.

### Goal 2: Social-Emotional Development  
{request.student_name} will demonstrate improved self-regulation strategies in classroom settings, reducing disruptive behaviors by 70% as measured by teacher observations.

### Goal 3: Functional Skills
The student will develop independence in transitioning between activities with minimal prompting in 4 out of 5 opportunities.
""" if not request.goals else '\n'.join(f"### Goal {i+1}: {goal}" for i, goal in enumerate(request.goals)))

@app.post("/generate-iep", response_model=GenerateIEPResponse)
async def generate_iep(request: GenerateIEPRequest):
    """Generate IEP content for a student"""
    start_time = time.time()
    
    if settings.mock_mode:
        # Mock response for development
        iep_content = generate_mock_iep_content(request)
        
        return GenerateIEPResponse(
            iep_content=iep_content,
            sections={
                "student_info": {
                    "name": request.student_name,
                    "grade": request.grade_level,
                    "disability": request.disability_type
                },
                "present_level": request.current_performance or "Baseline assessment needed",
                "goals": request.goals or ["Academic improvement", "Social-emotional development"],
                "services": ["Special education support", "Accommodations"]
            },
            metadata={
                "generated_at": time.time(),
                "processing_time_ms": int((time.time() - start_time) * 1000),
                "model": "mock-development",
                "student_id": request.student_id
            }
        )
    
    # In production, this would call actual AI services
    raise HTTPException(status_code=501, detail="Production AI integration not implemented")

@app.post("/analyze-document", response_model=AnalyzeDocumentResponse)
async def analyze_document(request: AnalyzeDocumentRequest):
    """Analyze uploaded documents for IEP insights"""
    start_time = time.time()
    
    if settings.mock_mode:
        # Mock analysis
        doc_length = len(request.document_text)
        word_count = len(request.document_text.split())
        
        return AnalyzeDocumentResponse(
            analysis=f"This document contains {word_count} words and appears to be educational content. "
                    f"The analysis type '{request.analysis_type}' has been applied. "
                    f"Key themes include student assessment, educational goals, and instructional strategies.",
            key_points=[
                "Document contains educational assessment data",
                f"Approximately {word_count} words of content",
                "Relevant for IEP development process",
                "Contains structured information suitable for analysis"
            ],
            recommendations=[
                "Use this document as baseline data for IEP goals",
                "Cross-reference with current curriculum standards",
                "Consider student's individual learning profile",
                "Incorporate findings into present level statements"
            ],
            metadata={
                "document_length": doc_length,
                "word_count": word_count,
                "analysis_type": request.analysis_type,
                "processing_time_ms": int((time.time() - start_time) * 1000)
            }
        )
    
    raise HTTPException(status_code=501, detail="Production document analysis not implemented")

@app.post("/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    """Process general queries about education and IEPs"""
    start_time = time.time()
    
    if settings.mock_mode:
        # Mock educational responses
        query_lower = request.query.lower()
        
        if "iep" in query_lower:
            response = "An Individualized Education Program (IEP) is a legally binding document that outlines specialized instruction and services for students with disabilities. It includes present levels of performance, annual goals, special education services, and accommodations."
        elif "goal" in query_lower:
            response = "IEP goals should be SMART: Specific, Measurable, Achievable, Relevant, and Time-bound. They should address the student's unique needs and be based on present level of performance data."
        elif "assessment" in query_lower:
            response = "Educational assessments help determine a student's current performance levels and guide IEP development. They can include academic, behavioral, and functional assessments."
        else:
            response = f"Thank you for your question about '{request.query}'. In an educational context, this relates to supporting student learning and development through individualized approaches."
        
        return QueryResponse(
            response=response,
            sources=[
                {
                    "title": "Mock Educational Resource",
                    "type": "reference",
                    "relevance": 0.85
                }
            ],
            metadata={
                "query": request.query,
                "processing_time_ms": int((time.time() - start_time) * 1000),
                "mode": "mock-development"
            }
        )
    
    raise HTTPException(status_code=501, detail="Production query processing not implemented")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    health_status = {
        "status": "healthy",
        "service": "adk-host",
        "version": "1.0.0",
        "environment": settings.environment,
        "mode": "mock" if settings.mock_mode else "production"
    }
    
    # Check auth service connectivity
    if http_client:
        try:
            auth_response = await http_client.get(
                f"{settings.auth_service_url}/health",
                timeout=5.0
            )
            health_status["dependencies"] = {
                "auth_service": {
                    "status": "connected" if auth_response.status_code == 200 else "disconnected",
                    "status_code": auth_response.status_code
                }
            }
        except Exception as e:
            health_status["dependencies"] = {
                "auth_service": {
                    "status": "disconnected",
                    "error": str(e)
                }
            }
    
    return health_status

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Educational IEP ADK Host",
        "version": "1.0.0",
        "description": "Backend-for-Frontend service for AI-powered IEP generation and educational content",
        "mode": "mock" if settings.mock_mode else "production",
        "endpoints": {
            "generate_iep": "/generate-iep",
            "analyze_document": "/analyze-document", 
            "query": "/query",
            "health": "/health"
        }
    }

if __name__ == "__main__":
    import uvicorn
    
    print(f"Starting ADK Host on port {settings.port}")
    print(f"Environment: {settings.environment}")
    print(f"Mock mode: {settings.mock_mode}")
    
    uvicorn.run(
        "simple_main:app",
        host=settings.host,
        port=settings.port,
        reload=True
    )