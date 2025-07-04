#!/usr/bin/env python3
"""Quick script to check vector store contents"""

import chromadb
from chromadb.config import Settings

def check_vector_store():
    print("Checking ChromaDB vector store...")
    
    try:
        # Connect to ChromaDB
        client = chromadb.PersistentClient(
            path="./chroma_db",
            settings=Settings(anonymized_telemetry=False)
        )
        
        # List all collections
        collections = client.list_collections()
        print(f"Found {len(collections)} collections:")
        for col in collections:
            print(f"  - {col.name}")
        
        # Check the main collection
        try:
            collection = client.get_collection("rag_documents")
            print(f"\nCollection 'rag_documents' found!")
            
            # Get count
            count = collection.count()
            print(f"Documents in collection: {count}")
            
            if count > 0:
                # Get a sample
                sample = collection.get(limit=3, include=["metadatas", "documents"])
                print(f"\nSample documents:")
                for i, doc in enumerate(sample['documents']):
                    metadata = sample['metadatas'][i] if sample['metadatas'] else {}
                    print(f"  Document {i+1}:")
                    print(f"    ID: {sample['ids'][i]}")
                    print(f"    Content: {doc[:100]}...")
                    print(f"    Metadata: {metadata}")
                    print()
            else:
                print("No documents found in the collection!")
                
        except Exception as e:
            print(f"Error accessing 'rag_documents' collection: {e}")
            
            # Try to create and check if it works
            print("Attempting to create collection...")
            try:
                collection = client.get_or_create_collection(
                    name="rag_documents",
                    metadata={"hnsw:space": "cosine"}
                )
                print("Collection created successfully!")
                print(f"Collection count: {collection.count()}")
            except Exception as create_err:
                print(f"Failed to create collection: {create_err}")
        
    except Exception as e:
        print(f"Error connecting to ChromaDB: {e}")

if __name__ == "__main__":
    check_vector_store()