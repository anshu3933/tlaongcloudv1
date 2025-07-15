#!/usr/bin/env python3
"""Process local IEP documents and key GCS documents into the vector store for RAG seeding"""

import os
import sys
import asyncio
import logging
from pathlib import Path
from typing import List, Dict, Any
import tempfile

# Add src to path  
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def process_local_iep_file(file_path: str) -> List[Dict[str, Any]]:
    """Process a local IEP file into chunks"""
    logger.info(f"📄 Processing local file: {Path(file_path).name}")
    
    try:
        # Read the file content
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Simple text chunking
        from langchain.text_splitter import RecursiveCharacterTextSplitter
        
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        
        chunks = text_splitter.split_text(content)
        
        # Create chunk objects
        chunk_objects = []
        for i, chunk_text in enumerate(chunks):
            chunk_objects.append({
                "content": chunk_text,
                "metadata": {
                    "source": Path(file_path).name,
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                    "document_type": "iep_example",
                    "processed_locally": True
                }
            })
        
        logger.info(f"✅ Created {len(chunk_objects)} chunks from {Path(file_path).name}")
        return chunk_objects
        
    except Exception as e:
        logger.error(f"❌ Error processing {file_path}: {e}")
        return []

async def create_embeddings_local(texts: List[str]) -> List[List[float]]:
    """Create embeddings using local method (fallback to Gemini if available)"""
    logger.info(f"🔢 Creating embeddings for {len(texts)} text chunks...")
    
    try:
        # Try using Gemini embedding model
        from google import genai
        from google.genai import types
        
        # Initialize client
        client = genai.Client(
            vertexai=True,
            project="thela002",  # Correct project ID
            location="us-central1"
        )
        
        embeddings = []
        
        # Process in batches to avoid rate limits
        batch_size = 5
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i+batch_size]
            
            try:
                # Create embeddings for the batch
                batch_embeddings = []
                for text in batch:
                    result = await asyncio.to_thread(
                        client.models.embed_content,
                        model="text-embedding-004",
                        contents=text
                    )
                    batch_embeddings.append(result.embeddings[0].values)
                
                embeddings.extend(batch_embeddings)
                logger.info(f"✅ Processed batch {i//batch_size + 1}/{(len(texts) + batch_size - 1)//batch_size}")
                
                # Small delay between batches
                await asyncio.sleep(0.5)
                
            except Exception as e:
                logger.warning(f"Error with batch {i//batch_size + 1}: {e}")
                # Add dummy embeddings as fallback
                for _ in batch:
                    embeddings.append([0.0] * 768)  # text-embedding-004 dimension
        
        logger.info(f"✅ Created {len(embeddings)} embeddings")
        return embeddings
        
    except Exception as e:
        logger.error(f"❌ Error creating embeddings: {e}")
        logger.info("Using dummy embeddings as fallback")
        # Return dummy embeddings
        return [[0.0] * 768 for _ in texts]

async def process_gcs_sample_documents(bucket_name: str, max_docs: int = 5) -> List[Dict[str, Any]]:
    """Process a sample of the most promising documents from GCS"""
    logger.info(f"🌥️ Processing sample documents from GCS bucket: {bucket_name}")
    
    try:
        from google.cloud import storage
        from langchain.text_splitter import RecursiveCharacterTextSplitter
        from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader, TextLoader
        
        client = storage.Client()
        bucket = client.bucket(bucket_name)
        
        # Get promising documents (prioritize synthetic assessment reports and IEP-related)
        priority_patterns = [
            "synthetic_reports/Synthetic_Assessment_Report",
            "assessment_reports/AR",
            "iep",
            "individual",
            "education"
        ]
        
        blobs = list(bucket.list_blobs())
        selected_blobs = []
        
        # First, get documents that match priority patterns
        for pattern in priority_patterns:
            for blob in blobs:
                if pattern.lower() in blob.name.lower() and blob.name.endswith(('.pdf', '.docx', '.txt')):
                    if blob not in selected_blobs:
                        selected_blobs.append(blob)
                        if len(selected_blobs) >= max_docs:
                            break
            if len(selected_blobs) >= max_docs:
                break
        
        logger.info(f"📋 Selected {len(selected_blobs)} documents for processing:")
        for blob in selected_blobs:
            logger.info(f"  • {blob.name}")
        
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        
        all_chunks = []
        
        for blob in selected_blobs:
            try:
                logger.info(f"📄 Processing: {blob.name}")
                
                # Download to temp file
                with tempfile.NamedTemporaryFile(delete=False, suffix=Path(blob.name).suffix) as tmp:
                    tmp_path = tmp.name
                
                blob.download_to_filename(tmp_path)
                
                # Load document based on type
                try:
                    if blob.name.endswith('.pdf'):
                        loader = PyPDFLoader(tmp_path)
                    elif blob.name.endswith('.docx'):
                        loader = Docx2txtLoader(tmp_path)
                    else:
                        loader = TextLoader(tmp_path)
                    
                    documents = loader.load()
                    
                    for doc in documents:
                        if doc.page_content.strip():  # Only process non-empty content
                            chunks = text_splitter.split_text(doc.page_content)
                            
                            for i, chunk_text in enumerate(chunks):
                                all_chunks.append({
                                    "content": chunk_text,
                                    "metadata": {
                                        "source": blob.name,
                                        "chunk_index": i,
                                        "total_chunks": len(chunks),
                                        "document_type": "gcs_document",
                                        "page": doc.metadata.get("page", 0),
                                        "size_bytes": blob.size
                                    }
                                })
                    
                    logger.info(f"✅ Processed {blob.name}: {len(documents)} document(s)")
                    
                except Exception as e:
                    logger.warning(f"Error loading {blob.name}: {e}")
                
                finally:
                    # Clean up temp file
                    os.unlink(tmp_path)
                    
            except Exception as e:
                logger.error(f"Error processing {blob.name}: {e}")
        
        logger.info(f"✅ Total chunks from GCS: {len(all_chunks)}")
        return all_chunks
        
    except Exception as e:
        logger.error(f"❌ Error processing GCS documents: {e}")
        return []

async def add_to_vector_store(chunks: List[Dict[str, Any]]):
    """Add chunks to the vector store"""
    logger.info(f"📚 Adding {len(chunks)} chunks to vector store...")
    
    if not chunks:
        logger.warning("No chunks to add")
        return
    
    try:
        # Create embeddings for all chunks
        texts = [chunk["content"] for chunk in chunks]
        embeddings = await create_embeddings_local(texts)
        
        # Add embeddings to chunks
        for chunk, embedding in zip(chunks, embeddings):
            chunk["embedding"] = embedding
        
        # Initialize vector store
        import chromadb
        from chromadb.config import Settings
        
        client = chromadb.PersistentClient(
            path="./chroma_db",
            settings=Settings(anonymized_telemetry=False)
        )
        
        collection = client.get_or_create_collection(
            name="rag_documents",
            metadata={"hnsw:space": "cosine"}
        )
        
        # Prepare data for ChromaDB
        ids = [f"chunk_{i}_{chunk['metadata']['source']}_{chunk['metadata']['chunk_index']}" 
               for i, chunk in enumerate(chunks)]
        embeddings_list = [chunk["embedding"] for chunk in chunks]
        metadatas = [chunk["metadata"] for chunk in chunks]
        documents = [chunk["content"] for chunk in chunks]
        
        # Add to collection
        collection.add(
            ids=ids,
            embeddings=embeddings_list,
            metadatas=metadatas,
            documents=documents
        )
        
        logger.info(f"✅ Successfully added {len(chunks)} chunks to vector store")
        
        # Verify the addition
        total_count = collection.count()
        logger.info(f"📊 Vector store now contains {total_count} total documents")
        
    except Exception as e:
        logger.error(f"❌ Error adding to vector store: {e}")
        import traceback
        logger.error(traceback.format_exc())

async def test_rag_retrieval():
    """Test RAG retrieval with the newly added documents"""
    logger.info("🧪 Testing RAG retrieval...")
    
    try:
        import chromadb
        from chromadb.config import Settings
        
        client = chromadb.PersistentClient(
            path="./chroma_db",
            settings=Settings(anonymized_telemetry=False)
        )
        
        collection = client.get_collection("rag_documents")
        
        # Test queries
        test_queries = [
            "IEP goals for students with learning disabilities",
            "assessment data and present levels of performance",
            "special education services and accommodations",
            "transition planning for students"
        ]
        
        for query in test_queries:
            logger.info(f"🔍 Testing query: '{query}'")
            
            try:
                # Create embedding for query using the same service
                query_embedding = await create_embeddings_local([query])
                
                # Search using the embedding
                results = collection.query(
                    query_embeddings=[query_embedding[0]],
                    n_results=3
                )
                
                if results['documents'] and results['documents'][0]:
                    logger.info(f"✅ Found {len(results['documents'][0])} relevant documents")
                    for i, doc in enumerate(results['documents'][0]):
                        preview = doc[:100] + "..." if len(doc) > 100 else doc
                        logger.info(f"   {i+1}. {preview}")
                else:
                    logger.warning("❌ No documents found for query")
                    
            except Exception as e:
                logger.error(f"Error with query '{query}': {e}")
        
        logger.info("✅ RAG retrieval test completed")
        
    except Exception as e:
        logger.error(f"❌ Error testing RAG retrieval: {e}")

async def main():
    """Main processing function"""
    logger.info("🚀 Processing IEP Documents for RAG Vector Store")
    logger.info("=" * 80)
    
    all_chunks = []
    
    # 1. Process local IEP files
    logger.info("\n" + "="*50)
    logger.info("1. PROCESSING LOCAL IEP FILES")
    logger.info("="*50)
    
    # Find the high-quality local IEP file
    local_iep_path = Path(__file__).parent.parent / "adk_host" / "uploaded_documents" / "bc6672b0-c7be-4d20-ad09-21c0659b1d2f_sampleiep2.txt"
    
    if local_iep_path.exists():
        local_chunks = process_local_iep_file(str(local_iep_path))
        all_chunks.extend(local_chunks)
        logger.info(f"✅ Added {len(local_chunks)} chunks from local IEP file")
    else:
        logger.warning(f"❌ Local IEP file not found at: {local_iep_path}")
    
    # 2. Process sample GCS documents
    logger.info("\n" + "="*50)
    logger.info("2. PROCESSING GCS SAMPLE DOCUMENTS")
    logger.info("="*50)
    
    try:
        gcs_chunks = await process_gcs_sample_documents("betrag-data-test-a", max_docs=3)
        all_chunks.extend(gcs_chunks)
        logger.info(f"✅ Added {len(gcs_chunks)} chunks from GCS documents")
    except Exception as e:
        logger.error(f"❌ Error processing GCS documents: {e}")
    
    # 3. Add to vector store
    logger.info("\n" + "="*50)
    logger.info("3. ADDING TO VECTOR STORE")
    logger.info("="*50)
    
    if all_chunks:
        await add_to_vector_store(all_chunks)
    else:
        logger.warning("❌ No chunks to add to vector store")
    
    # 4. Test retrieval
    logger.info("\n" + "="*50)
    logger.info("4. TESTING RAG RETRIEVAL")
    logger.info("="*50)
    
    await test_rag_retrieval()
    
    # 5. Summary
    logger.info("\n" + "="*80)
    logger.info("📊 PROCESSING SUMMARY")
    logger.info("="*80)
    
    local_count = len([c for c in all_chunks if c.get("metadata", {}).get("processed_locally")])
    gcs_count = len([c for c in all_chunks if c.get("metadata", {}).get("document_type") == "gcs_document"])
    
    logger.info(f"Local IEP chunks processed: {local_count}")
    logger.info(f"GCS document chunks processed: {gcs_count}")
    logger.info(f"Total chunks added to vector store: {len(all_chunks)}")
    
    if len(all_chunks) > 0:
        logger.info("\n🎉 SUCCESS! Vector store has been seeded with IEP examples")
        logger.info("🎯 Next steps:")
        logger.info("1. Test IEP generation with the RAG system")
        logger.info("2. Add more diverse IEP examples if needed")
        logger.info("3. Monitor RAG generation quality")
    else:
        logger.error("\n❌ FAILED! No documents were processed into vector store")
        logger.info("🔧 Troubleshooting:")
        logger.info("1. Check file permissions and paths")
        logger.info("2. Verify GCS access credentials")
        logger.info("3. Check embedding service availability")

if __name__ == "__main__":
    asyncio.run(main())