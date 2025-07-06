"""MCP Server with GCS document retrieval"""
from __future__ import annotations

import os
from typing import Dict, Any, Optional
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel, Field

from config import get_settings
from document_processor import DocumentProcessor
from vector_store import VectorStore
from .middleware.error_handler import ErrorHandlerMiddleware

# Import vertexai with error handling for optional dependency
try:
    from vertexai.language_models import TextEmbeddingModel
except ImportError:
    TextEmbeddingModel = None

settings = get_settings()

# Global resources
vector_store: Optional[VectorStore] = None
embedding_model: Optional[TextEmbeddingModel] = None
document_processor: Optional[DocumentProcessor] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown logic"""
    global vector_store, embedding_model, document_processor
    
    # Initialize vector store based on environment
    if os.getenv("ENVIRONMENT") == "development":
        # Development: Use ChromaDB with collection_name
        vector_store = VectorStore(
            project_id=settings.gcp_project_id,
            collection_name="rag_documents"
        )
    else:
        # Production: Use VertexVectorStore with proper factory method
        try:
            from common.src.vector_store.vertex_vector_store import VertexVectorStore
            vector_store = VertexVectorStore.from_settings(settings)
        except (ValueError, AttributeError) as e:
            # Fallback to ChromaDB if Vertex is not configured
            print(f"Warning: Vertex AI not configured ({e}), falling back to ChromaDB")
            from common.src.vector_store.chroma_vector_store import VectorStore as ChromaVectorStore
            vector_store = ChromaVectorStore(
                project_id=settings.gcp_project_id,
                collection_name="rag_documents"
            )
    
    # Initialize embedding model if available
    if TextEmbeddingModel:
        try:
            import vertexai
            vertexai.init(project=settings.gcp_project_id, location=settings.gcp_region)
            embedding_model = TextEmbeddingModel.from_pretrained("text-embedding-004")
        except Exception as e:
            print(f"Warning: Could not initialize Vertex AI: {e}")
            embedding_model = None
    else:
        print("Warning: Vertex AI not available, embedding model disabled")
        embedding_model = None
    
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

# Add error handling middleware
app.add_middleware(ErrorHandlerMiddleware)

# Implementation functions for MCP tools

async def retrieve_iep_examples_impl(student_id: str, disability_type: Optional[str] = None, top_k: int = 5) -> Dict[str, Any]:
    """Retrieve similar IEP examples for reference"""
    try:
        # Create search query based on parameters
        query_parts = ["IEP"]
        if disability_type:
            query_parts.append(disability_type)
        
        query = " ".join(query_parts)
        
        # Get embeddings for the query
        embeddings = embedding_model.get_embeddings([query])
        query_embedding = embeddings[0].values
        
        # Search vector store for similar IEPs
        results = await vector_store.search(
            query_embedding=query_embedding,
            top_k=top_k,
            filters={"document_type": "iep"}
        )
        
        return {
            "student_id": student_id,
            "examples": results,
            "query": query,
            "count": len(results)
        }
        
    except Exception as e:
        return {
            "error": f"Failed to retrieve IEP examples: {str(e)}",
            "student_id": student_id,
            "examples": [],
            "count": 0
        }

async def analyze_student_progress_impl(student_id: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict[str, Any]:
    """Analyze student progress over time"""
    try:
        # In a real implementation, this would query student data
        # For now, return a mock analysis structure
        
        analysis = {
            "student_id": student_id,
            "analysis_period": {
                "start_date": start_date,
                "end_date": end_date
            },
            "progress_summary": {
                "academic_progress": "On track",
                "goal_completion": "75%",
                "areas_of_strength": ["Reading comprehension", "Math problem solving"],
                "areas_for_improvement": ["Written expression", "Social skills"],
                "recommendations": [
                    "Continue current reading intervention",
                    "Increase focus on writing activities",
                    "Add social skills group sessions"
                ]
            },
            "metrics": {
                "goals_met": 3,
                "goals_in_progress": 1,
                "goals_not_started": 0,
                "assessment_scores": {
                    "reading": 85,
                    "math": 78,
                    "writing": 65
                }
            },
            "generated_at": "2024-01-01T00:00:00Z"
        }
        
        return analysis
        
    except Exception as e:
        return {
            "error": f"Failed to analyze student progress: {str(e)}",
            "student_id": student_id,
            "analysis_period": {"start_date": start_date, "end_date": end_date}
        }

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
    filters: Dict = None,
    context_mode: str = "chat_only"
) -> Dict[str, Any]:
    """Retrieve relevant documents using vector search"""
    if not vector_store or not embedding_model:
        raise ValueError("Vector store not initialized")
    
    # Create query embedding
    query_embedding = embedding_model.get_embeddings([query])[0].values
    
    # Process filters for document_ids and context mode
    search_filters = None
    filter_conditions = []
    
    if filters and "document_ids" in filters and filters["document_ids"]:
        # Convert document_ids filter to ChromaDB format
        filter_conditions.append({
            "document_id": {"$in": filters["document_ids"]}
        })
        print(f"Filtering vector search by document IDs: {filters['document_ids']}")
    
    # Handle context mode filtering
    if context_mode == "chat_only":
        # Only include documents uploaded through chat interface
        filter_conditions.append({
            "source_type": {"$eq": "chat"}
        })
        print("Context mode: chat_only - filtering by source_type='chat'")
    elif context_mode == "include_historical":
        # Include all documents - both chat and historical (no source_type filter)
        print("Context mode: include_historical - including all documents (chat + historical)")
    
    # Combine filters if we have any
    if filter_conditions:
        if len(filter_conditions) == 1:
            search_filters = filter_conditions[0]
        else:
            search_filters = {"$and": filter_conditions}
    
    # Search vector store
    print(f"DEBUG: MCP calling vector store search with filters: {search_filters}")
    documents = vector_store.search(
        query_embedding=query_embedding,
        top_k=top_k,
        filters=search_filters
    )
    print(f"DEBUG: MCP received {len(documents)} documents from vector store")
    
    # Format results
    formatted_docs = []
    for doc in documents:
        # Extract proper source name
        doc_name = doc["metadata"].get("document_name")
        source_path = doc["metadata"].get("source", "unknown")
        final_source = doc_name if doc_name else Path(source_path).name
        
        print(f"DEBUG: doc_name={doc_name}, source_path={source_path}, final_source={final_source}")
        
        formatted_docs.append({
            "id": doc["id"],
            "content": doc["content"],
            "source": final_source,
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
                            "include_goals": {"type": "boolean", "default": True}
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

@app.post("/documents/clear")
async def clear_vector_store():
    """Clear all documents from vector store"""
    if not vector_store:
        raise HTTPException(status_code=500, detail="Vector store not initialized")
    
    vector_store.clear()
    return {
        "status": "success",
        "message": "Vector store cleared successfully"
    }

@app.get("/documents/debug")
async def debug_vector_store():
    """Debug endpoint to check vector store contents"""
    if not vector_store:
        raise HTTPException(status_code=500, detail="Vector store not initialized")
    
    try:
        # Get all documents from ChromaDB
        all_data = vector_store.collection.get()
        
        return {
            "total_documents": len(all_data['ids']) if all_data['ids'] else 0,
            "document_ids": all_data['ids'][:10] if all_data['ids'] else [],  # First 10 IDs
            "sample_metadata": all_data['metadatas'][:3] if all_data['metadatas'] else [],  # First 3 metadata
            "collection_name": vector_store.collection_name
        }
    except Exception as e:
        return {
            "error": str(e),
            "total_documents": 0
        }

@app.post("/documents/seed-historical")
async def seed_historical_documents():
    """Seed some sample historical documents for testing"""
    if not vector_store or not document_processor:
        raise HTTPException(status_code=500, detail="Services not initialized")
    
    # Sample historical documents
    historical_docs = [
        {
            "id": "hist_doc_1",
            "content": "Sample IEP document from the historical archive. This document contains information about reading comprehension goals, math objectives, and social skills development for students with learning disabilities.",
            "metadata": {
                "document_id": "hist_doc_1",
                "source": "gcs://historical-bucket/iep-samples/reading-goals.pdf",
                "document_name": "Reading Goals IEP Template",
                "source_type": "historical",
                "document_type": "iep_template",
                "subject": "reading",
                "grade_level": "elementary"
            }
        },
        {
            "id": "hist_doc_2", 
            "content": "Historical lesson plan template for mathematics instruction. Includes scaffolding strategies, differentiated instruction methods, and assessment rubrics for students with special needs.",
            "metadata": {
                "document_id": "hist_doc_2",
                "source": "gcs://historical-bucket/lesson-plans/math-template.pdf",
                "document_name": "Math Lesson Plan Template",
                "source_type": "historical",
                "document_type": "lesson_plan",
                "subject": "mathematics",
                "grade_level": "middle"
            }
        },
        {
            "id": "hist_doc_3",
            "content": "Behavioral intervention strategies and positive behavior support plans. This document outlines evidence-based practices for managing classroom behavior and supporting students with emotional and behavioral needs.",
            "metadata": {
                "document_id": "hist_doc_3", 
                "source": "gcs://historical-bucket/behavior/intervention-strategies.pdf",
                "document_name": "Behavioral Intervention Strategies",
                "source_type": "historical",
                "document_type": "behavior_plan",
                "subject": "behavior",
                "grade_level": "all"
            }
        }
    ]
    
    try:
        chunks = []
        for doc in historical_docs:
            # Create embeddings for the content
            embeddings = document_processor.create_embeddings([doc["content"]])
            
            chunk = {
                "content": doc["content"],
                "metadata": doc["metadata"],
                "embedding": embeddings[0]
            }
            chunks.append(chunk)
        
        # Add to vector store
        vector_store.add_documents(chunks)
        
        return {
            "status": "success",
            "message": f"Added {len(historical_docs)} historical documents to vector store",
            "documents_added": len(historical_docs)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to seed historical documents: {str(e)}")

from pydantic import BaseModel as PydanticBaseModel

class ProcessSingleDocumentRequest(PydanticBaseModel):
    file_path: str
    document_id: str
    filename: str

@app.post("/documents/process-single")
async def process_single_document(request: ProcessSingleDocumentRequest):
    """Process a single uploaded document and add to vector store"""
    if not document_processor or not vector_store:
        raise HTTPException(status_code=500, detail="Services not initialized")
    
    try:
        # Load and process the document
        documents = document_processor.load_document(request.file_path)
        chunks = []
        
        for doc in documents:
            doc_chunks = document_processor.text_splitter.split_text(doc.page_content)
            
            for i, chunk_text in enumerate(doc_chunks):
                chunk = {
                    "content": chunk_text,
                    "metadata": {
                        "document_id": request.document_id,  # Add document ID for filtering
                        "source": request.file_path,
                        "document_name": request.filename,
                        "chunk_index": i,
                        "total_chunks": len(doc_chunks),
                        "page": doc.metadata.get("page", 0),
                        "source_type": "chat"  # Mark as chat document
                    }
                }
                chunks.append(chunk)
        
        # Create embeddings and add to vector store
        if chunks:
            chunk_texts = [chunk["content"] for chunk in chunks]
            embeddings = document_processor.create_embeddings(chunk_texts)
            
            for chunk, embedding in zip(chunks, embeddings):
                chunk["embedding"] = embedding
            
            vector_store.add_documents(chunks)
        
        return {
            "status": "success",
            "document_id": request.document_id,
            "chunks_created": len(chunks)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process document: {str(e)}")

class RetrieveDocumentsRequest(BaseModel):
    query: str
    top_k: int = 5
    filter: Optional[Dict] = None

@app.post("/retrieve_documents")
async def retrieve_documents_http(request: RetrieveDocumentsRequest):
    """HTTP endpoint for document retrieval"""
    try:
        result = await retrieve_documents_impl(
            query=request.query,
            top_k=request.top_k,
            filters=request.filter,
            context_mode="chat_only"
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve documents: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.mcp_server_port,
        reload=settings.is_development
    ) 