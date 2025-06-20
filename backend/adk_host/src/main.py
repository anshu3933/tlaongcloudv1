"""ADK Host - API layer for your frontend"""
import time
from typing import Dict, Any, List, Optional
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import httpx
from google.cloud import aiplatform
from vertexai.generative_models import GenerativeModel
from google import genai
from google.genai import types

from common.src.config import get_settings

settings = get_settings()

# Global resources
http_client: Optional[httpx.AsyncClient] = None
gemini_model: Optional[GenerativeModel] = None

# Initialize the Gemini client
client = genai.Client(
    vertexai=True,
    project=settings.gcp_project_id,
    location=settings.gcp_region,
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    global http_client, gemini_model
    
    # Initialize HTTP client
    http_client = httpx.AsyncClient(
        timeout=httpx.Timeout(30.0, connect=5.0),
        limits=httpx.Limits(
            max_keepalive_connections=20,
            max_connections=100,
            keepalive_expiry=30
        ),
        http2=True
    )
    
    # Initialize Vertex AI
    try:
        aiplatform.init(
            project=settings.gcp_project_id,
            location=settings.gcp_region
        )
        gemini_model = GenerativeModel(settings.gemini_model)
        print(f"Initialized Gemini model: {settings.gemini_model}")
    except Exception as e:
        print(f"Warning: Failed to initialize Vertex AI: {str(e)}")
        print("Continuing without Gemini - will use mock responses for development")
    
    yield
    
    # Shutdown
    if http_client:
        await http_client.aclose()

app = FastAPI(
    title="RAG ADK Host",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration for your Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",      # Next.js dev server
        "http://127.0.0.1:3000",      # Alternative localhost
        "https://*.vercel.app",       # Vercel preview deployments
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)

# Request/Response models
class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=settings.max_query_length)
    options: Optional[Dict[str, Any]] = Field(default_factory=dict)

class Source(BaseModel):
    id: str
    source: str
    score: float
    snippet: str
    metadata: Dict[str, Any] = Field(default_factory=dict)

class QueryResponse(BaseModel):
    answer: str
    sources: List[Source]
    metadata: Dict[str, Any] = Field(default_factory=dict)

async def call_mcp_tool(
    tool_name: str, 
    arguments: Dict[str, Any],
    request_id: str
) -> Dict[str, Any]:
    """Call MCP server tool"""
    if not http_client:
        raise HTTPException(status_code=500, detail="HTTP client not initialized")
    
    mcp_url = f"{settings.mcp_server_url}/mcp"
    payload = {
        "jsonrpc": "2.0",
        "id": request_id,
        "method": "tools/call",
        "params": {
            "name": tool_name,
            "arguments": arguments
        }
    }
    
    try:
        response = await http_client.post(
            mcp_url,
            json=payload,
            headers={"X-Request-ID": request_id}
        )
        response.raise_for_status()
        print(f"DEBUG: MCP raw response content: {response.text}")
        data = response.json()
        if data is None:
            print("DEBUG: MCP response JSON is None!")
            raise HTTPException(status_code=502, detail="MCP server returned empty or invalid JSON response.")
        if "error" in data and data["error"] is not None:
            error = data["error"]
            raise HTTPException(
                status_code=500,
                detail=f"MCP error {error.get('code', 'unknown')}: {error.get('message', 'Unknown error')}"
            )
        return data.get("result", {})

    except Exception as e:
        print(f"DEBUG: Exception type: {type(e)}; Exception: {e}")
        print(f"DEBUG: httpx module: {httpx}")
        print(f"DEBUG: hasattr(httpx, 'TimeoutException'): {hasattr(httpx, 'TimeoutException')}")
        if hasattr(httpx, 'TimeoutException'):
            print(f"DEBUG: httpx.TimeoutException: {httpx.TimeoutException}")
            print(f"DEBUG: issubclass(httpx.TimeoutException, BaseException): {issubclass(httpx.TimeoutException, BaseException)}")
        raise

async def generate_rag_response(
    query: str,
    documents: List[Dict[str, Any]],
    request_id: str
) -> str:
    """Generate response using Gemini with retrieved documents"""
    
    # If Gemini is not available (local dev without GCP), return a formatted response
    # if not client:
    #     if documents:
    #         # Create a mock response that combines the document content
    #         response_parts = [
    #             f"Based on the available information about '{query}':",
    #             ""
    #         ]
    #         
    #         for i, doc in enumerate(documents[:3], 1):
    #             response_parts.append(f"{i}. From {doc.get('source', 'Unknown source')}:" )
    #             response_parts.append(f"   {doc['content'][:200]}...")
    #             response_parts.append("")
    #         
    #         return "\n".join(response_parts)
    #     else:
    #         return f"I couldn't find specific information about '{query}' in the available documents."
    
    # Format context from documents
    context_parts = []
    for i, doc in enumerate(documents, 1):
        context_parts.append(
            f"[Document {i} - Source: {doc.get('source', 'Unknown')}]\n"
            f"{doc['content']}\n"
        )
    
    context_str = "\n".join(context_parts)
    
    # Construct prompt for Gemini
    prompt = f"""You are an educational assistant helping teachers with IEPs, lesson planning, and student support.

Based on the following documents, provide a comprehensive answer to this question: {query}

Documents:
{context_str}

Instructions:
1. Provide a clear, well-structured answer. Your answer should be based on the provided documents, but you can also use your own knowledge to answer the question.
2. Reference specific documents when making claims (e.g., "According to Document 1...")
3. If the documents don't contain enough information, acknowledge this
4. Focus on practical, actionable information for educators
5. Keep the response concise but thorough
6. If the documents do not contain a direct answer, use your own knowledge as an educational assistant to provide a complete answer.

Answer:"""

    try:
        # Generate response with Gemini
        contents = [
            types.Content(
                role="user",
                parts=[types.Part(text=prompt)]
            )
        ]

        generate_content_config = types.GenerateContentConfig(
            temperature=settings.gemini_temperature,
            top_p=0.8,
            max_output_tokens=settings.gemini_max_tokens,
            safety_settings=[
                types.SafetySetting(
                    category="HARM_CATEGORY_HATE_SPEECH",
                    threshold="OFF"
                ),
                types.SafetySetting(
                    category="HARM_CATEGORY_DANGEROUS_CONTENT",
                    threshold="OFF"
                ),
                types.SafetySetting(
                    category="HARM_CATEGORY_SEXUALLY_EXPLICIT",
                    threshold="OFF"
                ),
                types.SafetySetting(
                    category="HARM_CATEGORY_HARASSMENT",
                    threshold="OFF"
                )
            ],
        )

        response = client.models.generate_content(
            model=settings.gemini_model,
            contents=contents,
            config=generate_content_config,
        )
        
        answer = getattr(response, 'text', None)
        if not answer or not isinstance(answer, str) or answer.strip() == "":
            print(f"DEBUG: Gemini returned None or empty answer. Raw response: {response}")
            return "No answer was generated by the Gemini model for your query. Please try rephrasing or check model configuration."
        return answer
        
    except Exception as e:
        print(f"Gemini generation error: {str(e)}")
        # Fallback to a simple response
        return f"I found {len(documents)} relevant documents about '{query}'. " \
               f"The most relevant information comes from: {documents[0].get('source', 'unknown source')}."

@app.post("/api/v1/query", response_model=QueryResponse)
async def process_query(request: Request, query_request: QueryRequest):
    """Main query endpoint for your frontend"""
    # Generate request ID
    request_id = request.headers.get("X-Request-ID", f"adk-{int(time.time() * 1000)}")
    start_time = time.time()
    
    print(f"Processing query: '{query_request.query}' (request_id: {request_id})")
    
    try:
        # Call MCP to retrieve relevant documents
        retrieval_result = await call_mcp_tool(
            "retrieve_documents",
            {
                "query": query_request.query,
                "top_k": query_request.options.get("top_k", 5),
                "filters": query_request.options.get("filters", {})
            },
            request_id
        )
        
        documents = retrieval_result.get("documents", [])
        
        if not documents:
            print(f"No documents found for query: {query_request.query}")
            return QueryResponse(
                answer="I couldn't find any relevant information in the knowledge base for your question. Please try rephrasing or asking a different question.",
                sources=[],
                metadata={
                    "request_id": request_id,
                    "processing_time_ms": int((time.time() - start_time) * 1000),
                    "documents_retrieved": 0
                }
            )
        
        # Generate response using retrieved documents
        answer = await generate_rag_response(
            query_request.query,
            documents,
            request_id
        )
        
        # Format sources for frontend
        sources = []
        for doc in documents[:5]:  # Limit to top 5 sources
            sources.append(Source(
                id=doc["id"],
                source=doc.get("source", "Unknown"),
                score=round(doc.get("score", 0), 3),
                snippet=doc["content"][:200] + "..." if len(doc["content"]) > 200 else doc["content"],
                metadata=doc.get("metadata", {})
            ))
        
        # Build response
        processing_time = int((time.time() - start_time) * 1000)
        
        return QueryResponse(
            answer=answer,
            sources=sources,
            metadata={
                "request_id": request_id,
                "processing_time_ms": processing_time,
                "documents_retrieved": len(documents),
                "model_used": settings.gemini_model if gemini_model else "mock",
                "top_k": query_request.options.get("top_k", 5)
            }
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        print(f"Error processing query: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "An error occurred processing your query",
                "request_id": request_id,
                "message": str(e) if settings.is_development else "Internal server error"
            }
        )

@app.get("/health")
async def health():
    """Health check endpoint"""
    health_status = {
        "status": "healthy",
        "service": "adk-host",
        "version": "1.0.0",
        "environment": settings.environment,
        "dependencies": {}
    }
    
    # Check MCP server health
    try:
        if http_client:
            mcp_response = await http_client.get(
                f"{settings.mcp_server_url}/health",
                timeout=5.0
            )
            health_status["dependencies"]["mcp_server"] = {
                "status": "healthy" if mcp_response.status_code == 200 else "unhealthy",
                "status_code": mcp_response.status_code
            }
        else:
            health_status["dependencies"]["mcp_server"] = {
                "status": "unhealthy",
                "error": "HTTP client not initialized"
            }
    except Exception as e:
        health_status["dependencies"]["mcp_server"] = {
            "status": "unhealthy",
            "error": str(e)
        }
    
    # Check Gemini availability
    health_status["dependencies"]["gemini"] = {
        "status": "available" if client else "not configured",
        "model": settings.gemini_model if gemini_model else None
    }
    
    # Overall health
    all_healthy = all(
        dep.get("status") in ["healthy", "available"]
        for dep in health_status["dependencies"].values()
    )
    
    if not all_healthy:
        health_status["status"] = "degraded"
    
    return health_status

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "RAG ADK Host",
        "version": "1.0.0",
        "description": "API layer for RAG-powered educational assistant",
        "endpoints": {
            "query": "/api/v1/query",
            "health": "/health",
            "docs": "/docs"
        }
    }

# Entry point for running directly
if __name__ == "__main__":
    import uvicorn
    
    print(f"Starting ADK Host on port {settings.adk_host_port}")
    print(f"Environment: {settings.environment}")
    print(f"MCP Server URL: {settings.mcp_server_url}")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.adk_host_port,
        reload=settings.is_development,
        log_level=settings.log_level.lower()
    ) 