"""ChromaDB vector store implementation for development"""
from typing import List, Dict, Any
import chromadb
from chromadb.config import Settings

class VectorStore:
    def __init__(self, project_id: str, collection_name: str = "rag_documents"):
        self.project_id = project_id
        self.collection_name = collection_name
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path="./chroma_db",
            settings=Settings(anonymized_telemetry=False)
        )
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )
    
    def add_documents(self, chunks: List[Dict[str, Any]]):
        """Add document chunks to vector store"""
        if not chunks:
            return
        
        # Prepare data - use document_id + chunk_index for better tracking
        ids = []
        embeddings = [chunk["embedding"] for chunk in chunks]
        metadatas = [chunk["metadata"] for chunk in chunks]
        documents = [chunk["content"] for chunk in chunks]
        
        # Create meaningful chunk IDs based on document_id and chunk_index
        for i, chunk in enumerate(chunks):
            doc_id = chunk["metadata"].get("document_id", f"unknown_{i}")
            chunk_idx = chunk["metadata"].get("chunk_index", i)
            chunk_id = f"{doc_id}_chunk_{chunk_idx}"
            ids.append(chunk_id)
        
        # Add to ChromaDB
        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            metadatas=metadatas,
            documents=documents
        )
        print(f"Added {len(chunks)} chunks to ChromaDB")
    
    def search(self, query_embedding: List[float], top_k: int = 5, filters: Dict = None) -> List[Dict]:
        """Search for similar documents"""
        # ChromaDB search
        where_clause = None
        if filters:
            # Convert filters to ChromaDB format
            # Handle special cases like $in operator and complex nested filters
            
            def convert_filter(filter_dict):
                """Convert a filter dictionary to ChromaDB format"""
                if not isinstance(filter_dict, dict):
                    return filter_dict
                
                converted = {}
                for key, value in filter_dict.items():
                    if key in ["$and", "$or"]:
                        # Handle logical operators
                        converted[key] = [convert_filter(f) for f in value]
                    elif isinstance(value, dict):
                        # Handle nested operators like {"$in": [...]} or {"$eq": ...}
                        converted[key] = value
                    else:
                        # Simple equality
                        converted[key] = {"$eq": value}
                return converted
            
            where_clause = convert_filter(filters)
        
        print(f"DEBUG: Vector store search with filters: {filters}")
        print(f"DEBUG: Converted where_clause: {where_clause}")
        
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where_clause if where_clause else None,
            include=["metadatas", "documents", "distances"]
        )
        
        print(f"DEBUG: Vector store found {len(results['ids'][0])} results")
        
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
    
    def clear(self):
        """Clear all documents from the store"""
        # Get all IDs and delete them
        all_ids = self.collection.get()['ids']
        if all_ids:
            self.collection.delete(ids=all_ids)
            print(f"Cleared {len(all_ids)} documents from vector store") 