"""MCP Server with GCS document retrieval"""
import os
import json
import time
from typing import Dict, Any, List, Optional
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel, Field

from common.src.config import get_settings
from common.src.document_processor import DocumentProcessor
from common.src.vector_store import VectorStore
from vertexai.language_models import TextEmbeddingModel

settings = get_settings()

# Global resources
vector_store: Optional[VectorStore] = None
embedding_model: Optional[TextEmbeddingModel] = None
document_processor: Optional[DocumentProcessor] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown logic"""
    global vector_store, embedding_model, document_processor
    
    # Initialize components
    vector_store = VectorStore(
        project_id=settings.gcp_project_id,
        collection_name="rag_documents"
    )
    
    # Initialize embedding model
    import vertexai
    vertexai.init(project=settings.gcp_project_id, location=settings.gcp_region)
    embedding_model = TextEmbeddingModel.from_pretrained("text-embedding-004")
    
    # Initialize document processor
    document_processor = DocumentProcessor(
        project_id=settings.gcp_project_id,
        bucket_name=os.getenv("GCS_BUCKET_NAME", "your-rag-documents")
    )
    
    print("MCP Server initialized")
    yield
    print("MCP Server shutting down")

app = FastAPI(
    title="RAG MCP Server",
    version="1.0.0",
    lifespan=lifespan
)

class MCPRequest(BaseModel):
    jsonrpc: str = Field(default="2.0")
    id: str
    method: str
    params: Optional[Dict[str, Any]] = None

class MCPResponse(BaseModel):
    jsonrpc: str = Field(default="2.0")
    id: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None

async def retrieve_documents_impl(
    query: str, 
    top_k: int = 5, 
    filters: Dict = None
) -> Dict[str, Any]:
    """Retrieve relevant documents using vector search"""
    if not vector_store or not embedding_model:
        raise ValueError("Vector store not initialized")
    
    # Create query embedding
    query_embedding = embedding_model.get_embeddings([query])[0].values
    
    # Search vector store
    documents = vector_store.search(
        query_embedding=query_embedding,
        top_k=top_k,
        filters=filters
    )
    
    # Format results
    formatted_docs = []
    for doc in documents:
        formatted_docs.append({
            "id": doc["id"],
            "content": doc["content"],
            "source": doc["metadata"].get("source", "unknown"),
            "score": doc["score"],
            "metadata": doc["metadata"]
        })
    
    return {"documents": formatted_docs}

@app.post("/mcp")
async def mcp_endpoint(request: Request, mcp_request: MCPRequest):
    """Main MCP endpoint"""
    try:
        if mcp_request.method == "tools/list":
            tools = [{
                "name": "retrieve_documents",
                "description": "Retrieves relevant documents from your uploaded content",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"},
                        "top_k": {"type": "integer", "default": 5},
                        "filters": {"type": "object", "description": "Metadata filters"}
                    },
                    "required": ["query"]
                }
            }]
            tools.extend([
                {
                    "name": "retrieve_iep_examples",
                    "description": "Retrieve similar IEP examples for generation",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "disability_type": {"type": "string", "description": "Disability type code"},
                            "grade_level": {"type": "string", "description": "Grade level"},
                            "section": {"type": "string", "description": "Specific IEP section"},
                            "top_k": {"type": "integer", "default": 3, "description": "Number of examples"}
                        },
                        "required": ["disability_type"]
                    }
                },
                {
                    "name": "analyze_student_progress",
                    "description": "Analyze student progress from assessments",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "student_id": {"type": "string", "format": "uuid"},
                            "start_date": {"type": "string", "format": "date"},
                            "end_date": {"type": "string", "format": "date"},
                            "include_goals": {"type": "boolean", "default": true}
                        },
                        "required": ["student_id"]
                    }
                }
            ])
            return MCPResponse(
                jsonrpc="2.0",
                id=mcp_request.id,
                result={"tools": tools}
            )
            
        elif mcp_request.method == "tools/call":
            tool_name = mcp_request.params.get("name")
            
            if tool_name == "retrieve_documents":
                args = mcp_request.params.get("arguments", {})
                result = await retrieve_documents_impl(**args)
                
                return MCPResponse(
                    jsonrpc="2.0",
                    id=mcp_request.id,
                    result=result
                )
            
            elif tool_name == "retrieve_iep_examples":
                args = mcp_request.params.get("arguments", {})
                result = await retrieve_iep_examples_impl(**args)
                return MCPResponse(
                    jsonrpc="2.0",
                    id=mcp_request.id,
                    result=result
                )
            
            elif tool_name == "analyze_student_progress":
                args = mcp_request.params.get("arguments", {})
                result = await analyze_student_progress_impl(**args)
                return MCPResponse(
                    jsonrpc="2.0",
                    id=mcp_request.id,
                    result=result
                )
        
        return MCPResponse(
            jsonrpc="2.0",
            id=mcp_request.id,
            error={"code": -32601, "message": "Method not found"}
        )
        
    except Exception as e:
        return MCPResponse(
            jsonrpc="2.0",
            id=mcp_request.id,
            error={"code": -32603, "message": str(e)}
        )

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "mcp-server",
        "vector_store": "ready" if vector_store else "not initialized"
    }

# Document management endpoints
@app.post("/documents/process")
async def process_documents():
    """Process all documents in GCS bucket"""
    if not document_processor:
        raise HTTPException(status_code=500, detail="Document processor not initialized")
    
    # Process documents
    result = document_processor.process_all_documents()
    
    # Add to vector store
    if result["chunks"]:
        vector_store.add_documents(result["chunks"])
    
    return {
        "status": "success",
        "documents_processed": result["total_documents"],
        "chunks_created": result["total_chunks"]
    }

@app.get("/documents/list")
async def list_documents():
    """List documents in GCS bucket"""
    if not document_processor:
        raise HTTPException(status_code=500, detail="Document processor not initialized")
    
    documents = document_processor.list_documents()
    return {
        "documents": documents,
        "count": len(documents)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.mcp_server_port,
        reload=settings.is_development
    ) 