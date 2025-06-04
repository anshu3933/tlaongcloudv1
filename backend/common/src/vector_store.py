"""Vector store management using ChromaDB for development and Vertex AI for production"""
import os
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings
import numpy as np
from vertexai import aiplatform

class VectorStore:
    def __init__(self, project_id: str, collection_name: str = "rag_documents"):
        self.project_id = project_id
        self.collection_name = collection_name
        
        # For development, use ChromaDB
        if os.getenv("ENVIRONMENT") == "development":
            self.client = chromadb.PersistentClient(
                path="./chroma_db",
                settings=Settings(anonymized_telemetry=False)
            )
            self.collection = self.client.get_or_create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"}
            )
        else:
            # For production, use Vertex AI Vector Search
            aiplatform.init(project=project_id, location="us-central1")
            self.index = None  # Will be set up separately
    
    def add_documents(self, chunks: List[Dict[str, Any]]):
        """Add document chunks to vector store"""
        if not chunks:
            return
        
        # Prepare data
        ids = [f"chunk_{i}" for i in range(len(chunks))]
        embeddings = [chunk["embedding"] for chunk in chunks]
        metadatas = [chunk["metadata"] for chunk in chunks]
        documents = [chunk["content"] for chunk in chunks]
        
        # Add to ChromaDB (development)
        if hasattr(self, 'collection'):
            self.collection.add(
                ids=ids,
                embeddings=embeddings,
                metadatas=metadatas,
                documents=documents
            )
            print(f"Added {len(chunks)} chunks to ChromaDB")
    
    def search(self, query_embedding: List[float], top_k: int = 5, filters: Dict = None) -> List[Dict]:
        """Search for similar documents"""
        if hasattr(self, 'collection'):
            # ChromaDB search
            where_clause = None
            if filters:
                # Convert filters to ChromaDB format
                where_clause = {"$and": [
                    {key: {"$eq": value}} for key, value in filters.items()
                ]}
            
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=where_clause if where_clause else None,
                include=["metadatas", "documents", "distances"]
            )
            
            # Format results
            documents = []
            for i in range(len(results['ids'][0])):
                documents.append({
                    "id": results['ids'][0][i],
                    "content": results['documents'][0][i],
                    "metadata": results['metadatas'][0][i],
                    "score": 1 - results['distances'][0][i]  # Convert distance to similarity
                })
            
            return documents
        
        # Production implementation would query Vertex AI Vector Search
        return []
    
    def clear(self):
        """Clear all documents from the store"""
        if hasattr(self, 'collection'):
            # Get all IDs and delete them
            all_ids = self.collection.get()['ids']
            if all_ids:
                self.collection.delete(ids=all_ids)
                print(f"Cleared {len(all_ids)} documents from vector store") 