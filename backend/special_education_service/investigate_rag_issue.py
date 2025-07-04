#!/usr/bin/env python3
"""
Investigation script to verify RAG pipeline issues in IEP generation.
This will help diagnose why the RAG system is not working properly.
"""

import os
import asyncio
import logging
import chromadb
from chromadb.config import Settings

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_environment_setup():
    """Check environment variables and configuration"""
    logger.info("=== ENVIRONMENT SETUP INVESTIGATION ===")
    
    env = os.getenv("ENVIRONMENT")
    logger.info(f"ENVIRONMENT variable: {env}")
    
    # Check if we're in development mode
    is_development = env == "development"
    logger.info(f"Development mode: {is_development}")
    
    return is_development

def check_vector_store_contents():
    """Check what's actually in the ChromaDB vector store"""
    logger.info("\n=== VECTOR STORE INVESTIGATION ===")
    
    try:
        # Connect to ChromaDB
        client = chromadb.PersistentClient(
            path="./chroma_db",
            settings=Settings(anonymized_telemetry=False)
        )
        
        # List collections
        collections = client.list_collections()
        logger.info(f"Found {len(collections)} collections:")
        for col in collections:
            logger.info(f"  - {col.name}")
        
        # Check the main RAG collection
        if any(col.name == "rag_documents" for col in collections):
            collection = client.get_collection("rag_documents")
            count = collection.count()
            logger.info(f"Documents in 'rag_documents' collection: {count}")
            
            if count > 0:
                # Get sample documents
                sample = collection.get(limit=3, include=["metadatas", "documents"])
                logger.info("Sample documents:")
                for i, doc in enumerate(sample['documents']):
                    metadata = sample['metadatas'][i] if sample['metadatas'] else {}
                    logger.info(f"  Document {i+1}:")
                    logger.info(f"    ID: {sample['ids'][i]}")
                    logger.info(f"    Content: {doc[:100]}...")
                    logger.info(f"    Metadata: {metadata}")
            else:
                logger.warning("No documents found in the vector store!")
                logger.warning("This explains why RAG retrieval returns 0 similar IEPs")
        else:
            logger.error("rag_documents collection not found!")
            
    except Exception as e:
        logger.error(f"Error checking vector store: {e}")

def analyze_rag_logs():
    """Analyze recent logs for RAG operations"""
    logger.info("\n=== RAG OPERATION LOGS ANALYSIS ===")
    
    log_files = [
        "real_rag_test.log",
        "service.log", 
        "backend.log"
    ]
    
    for log_file in log_files:
        if os.path.exists(log_file):
            try:
                with open(log_file, 'r') as f:
                    lines = f.readlines()
                
                # Look for RAG-related lines
                rag_lines = [line for line in lines if any(keyword in line.lower() for keyword in [
                    'starting rag retrieval',
                    'retrieved.*similar ieps',
                    'vector store',
                    'embed',
                    'chroma'
                ])]
                
                if rag_lines:
                    logger.info(f"RAG operations in {log_file}:")
                    for line in rag_lines[-10:]:  # Last 10 RAG operations
                        logger.info(f"  {line.strip()}")
                else:
                    logger.info(f"No RAG operations found in {log_file}")
                    
            except Exception as e:
                logger.error(f"Error reading {log_file}: {e}")
        else:
            logger.info(f"Log file {log_file} not found")

def check_rag_pipeline_configuration():
    """Check if RAG pipeline is properly configured"""
    logger.info("\n=== RAG PIPELINE CONFIGURATION ===")
    
    try:
        # Import and check configuration
        from common.src.vector_store import VectorStore
        from src.rag.iep_generator import IEPGenerator
        
        # Test vector store initialization
        vector_store = VectorStore(
            project_id="test-project",
            collection_name="rag_documents"
        )
        
        logger.info("Vector store initialized successfully")
        logger.info(f"Vector store type: {type(vector_store)}")
        logger.info(f"Has collection attribute: {hasattr(vector_store, 'collection')}")
        
        # Test IEP generator initialization
        from common.src.config import get_settings
        settings = get_settings()
        
        iep_generator = IEPGenerator(vector_store=vector_store, settings=settings)
        logger.info("IEP generator initialized successfully")
        
        # Test search functionality
        logger.info("Testing vector store search...")
        test_embedding = [0.1] * 768  # Mock embedding
        search_results = vector_store.search(test_embedding, top_k=3)
        logger.info(f"Search returned {len(search_results)} results")
        
    except Exception as e:
        logger.error(f"Error testing RAG configuration: {e}")
        import traceback
        logger.error(traceback.format_exc())

def analyze_iep_generation_flow():
    """Analyze the IEP generation process"""
    logger.info("\n=== IEP GENERATION FLOW ANALYSIS ===")
    
    # Check if _index_iep_content is being called
    logger.info("Checking if IEP content indexing is enabled...")
    
    try:
        from src.services.iep_service import IEPService
        
        # Check the create_iep_with_rag method
        import inspect
        source = inspect.getsource(IEPService.create_iep_with_rag)
        
        if "_index_iep_content" in source:
            if "TODO" in source or "skip" in source.lower():
                logger.warning("Found evidence that IEP indexing is being skipped!")
                logger.warning("Line with TODO or skip found in create_iep_with_rag method")
            else:
                logger.info("IEP indexing appears to be implemented")
        else:
            logger.warning("No IEP indexing found in create_iep_with_rag method")
            
    except Exception as e:
        logger.error(f"Error analyzing IEP generation flow: {e}")

def provide_diagnosis():
    """Provide diagnosis and recommendations"""
    logger.info("\n=== DIAGNOSIS AND RECOMMENDATIONS ===")
    
    logger.info("Based on the investigation, here are the likely issues:")
    logger.info("1. Vector store is empty - no sample IEPs have been indexed")
    logger.info("2. IEP indexing is being skipped in the create_iep_with_rag method")
    logger.info("3. RAG retrieval returns 0 results due to empty vector store")
    logger.info("4. This makes IEP generation essentially template-based instead of RAG-powered")
    
    logger.info("\nRecommendations to fix:")
    logger.info("1. Populate vector store with sample IEP documents")
    logger.info("2. Enable IEP content indexing after creation")
    logger.info("3. Create a script to seed the vector store with existing IEPs")
    logger.info("4. Verify embedding generation is working properly")

def main():
    """Main investigation function"""
    logger.info("Starting RAG Pipeline Investigation...")
    
    check_environment_setup()
    check_vector_store_contents()
    analyze_rag_logs()
    check_rag_pipeline_configuration()
    analyze_iep_generation_flow()
    provide_diagnosis()
    
    logger.info("\nInvestigation complete!")

if __name__ == "__main__":
    main()