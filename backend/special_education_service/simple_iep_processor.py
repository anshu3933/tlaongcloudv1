#!/usr/bin/env python3
"""Simple IEP document processor without complex dependencies"""

import os
import sys
import asyncio
import logging
from pathlib import Path
from typing import List, Dict, Any
import json
import re

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def simple_text_chunker(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
    """Simple text chunking without external dependencies"""
    if len(text) <= chunk_size:
        return [text]
    
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        
        # Try to break at a sentence or paragraph boundary
        if end < len(text):
            # Look for sentence endings near the break point
            for break_char in ['\n\n', '\n', '. ', '! ', '? ']:
                break_point = text.rfind(break_char, start, end)
                if break_point > start:
                    end = break_point + len(break_char)
                    break
        
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        
        # Move start position with overlap
        start = max(start + 1, end - overlap)
    
    return chunks

def process_local_iep_simple(file_path: str) -> List[Dict[str, Any]]:
    """Process local IEP file with simple chunking"""
    logger.info(f"📄 Processing: {Path(file_path).name}")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Clean up the content
        content = content.strip()
        
        # Simple text chunking
        chunks = simple_text_chunker(content, chunk_size=800, overlap=150)
        
        # Create chunk objects
        chunk_objects = []
        for i, chunk_text in enumerate(chunks):
            if chunk_text.strip():  # Only process non-empty chunks
                chunk_objects.append({
                    "content": chunk_text,
                    "metadata": {
                        "source": Path(file_path).name,
                        "chunk_index": i,
                        "total_chunks": len(chunks),
                        "document_type": "iep_example",
                        "processed_locally": True,
                        "file_size": len(content)
                    }
                })
        
        logger.info(f"✅ Created {len(chunk_objects)} chunks")
        return chunk_objects
        
    except Exception as e:
        logger.error(f"❌ Error processing {file_path}: {e}")
        return []

def create_dummy_embeddings(texts: List[str]) -> List[List[float]]:
    """Create dummy embeddings for testing (replace with real embeddings later)"""
    logger.info(f"🔢 Creating dummy embeddings for {len(texts)} chunks...")
    
    # Create deterministic dummy embeddings based on text content
    embeddings = []
    for text in texts:
        # Simple hash-based embedding
        hash_value = hash(text) % 1000000
        embedding = []
        for i in range(384):  # Standard smaller embedding dimension
            # Create pseudo-random values based on hash and position
            value = ((hash_value + i * 31) % 1000) / 1000.0 - 0.5
            embedding.append(value)
        embeddings.append(embedding)
    
    logger.info(f"✅ Created {len(embeddings)} dummy embeddings")
    return embeddings

def add_to_vector_store_simple(chunks: List[Dict[str, Any]]):
    """Add chunks to ChromaDB vector store"""
    logger.info(f"📚 Adding {len(chunks)} chunks to vector store...")
    
    if not chunks:
        logger.warning("No chunks to add")
        return False
    
    try:
        # Create embeddings
        texts = [chunk["content"] for chunk in chunks]
        embeddings = create_dummy_embeddings(texts)
        
        # Add embeddings to chunks
        for chunk, embedding in zip(chunks, embeddings):
            chunk["embedding"] = embedding
        
        # Initialize ChromaDB
        import chromadb
        from chromadb.config import Settings
        
        client = chromadb.PersistentClient(
            path="./chroma_db",
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Get or create collection
        collection = client.get_or_create_collection(
            name="rag_documents",
            metadata={"hnsw:space": "cosine"}
        )
        
        # Prepare data
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
        
        logger.info(f"✅ Successfully added {len(chunks)} chunks")
        
        # Verify
        total_count = collection.count()
        logger.info(f"📊 Vector store now contains {total_count} total documents")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error adding to vector store: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def test_vector_store():
    """Test the vector store"""
    logger.info("🧪 Testing vector store...")
    
    try:
        import chromadb
        from chromadb.config import Settings
        
        client = chromadb.PersistentClient(
            path="./chroma_db",
            settings=Settings(anonymized_telemetry=False)
        )
        
        collection = client.get_collection("rag_documents")
        count = collection.count()
        
        if count > 0:
            logger.info(f"✅ Vector store contains {count} documents")
            
            # Get a sample
            sample = collection.get(limit=3, include=["metadatas", "documents"])
            
            logger.info("📋 Sample documents:")
            for i, (doc, metadata) in enumerate(zip(sample['documents'], sample['metadatas'])):
                source = metadata.get('source', 'unknown')
                preview = doc[:100] + "..." if len(doc) > 100 else doc
                logger.info(f"  {i+1}. Source: {source}")
                logger.info(f"     Preview: {preview}")
            
            # Test simple queries
            test_queries = [
                "student information",
                "goals and objectives", 
                "special education services",
                "assessment data"
            ]
            
            for query in test_queries:
                try:
                    results = collection.query(
                        query_texts=[query],
                        n_results=2
                    )
                    
                    if results['documents'] and results['documents'][0]:
                        logger.info(f"🔍 Query '{query}': Found {len(results['documents'][0])} results")
                    else:
                        logger.info(f"🔍 Query '{query}': No results")
                        
                except Exception as e:
                    logger.error(f"Error with query '{query}': {e}")
            
            return True
        else:
            logger.warning("❌ Vector store is empty")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error testing vector store: {e}")
        return False

def analyze_iep_content(file_path: str):
    """Analyze the IEP content structure"""
    logger.info(f"🔍 Analyzing IEP content structure...")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Look for key IEP sections
        sections_found = {}
        
        section_patterns = {
            'Student Information': [r'student.*information', r'student.*name', r'date.*birth'],
            'Disability Information': [r'disability', r'exceptionality', r'primary.*exceptionality'],
            'Present Levels': [r'present.*level', r'current.*performance', r'student.*profile'],
            'Goals': [r'annual.*goal', r'goal.*\d+', r'objectives?'],
            'Services': [r'special.*education.*services?', r'related.*services?', r'resource.*support'],
            'Accommodations': [r'accommodations?', r'modifications?', r'instructional.*accommodations?'],
            'Assessment': [r'assessments?', r'evaluation', r'eqao', r'provincial.*assessment'],
            'Transition': [r'transition.*planning?', r'postsecondary', r'employment']
        }
        
        content_lower = content.lower()
        
        for section_name, patterns in section_patterns.items():
            found = any(re.search(pattern, content_lower) for pattern in patterns)
            sections_found[section_name] = found
            if found:
                # Find sample text for this section
                for pattern in patterns:
                    match = re.search(pattern, content_lower)
                    if match:
                        start = max(0, match.start() - 50)
                        end = min(len(content), match.end() + 200)
                        sample = content[start:end].strip()
                        logger.info(f"  ✅ {section_name}: {sample[:100]}...")
                        break
            else:
                logger.info(f"  ❌ {section_name}: Not found")
        
        quality_score = sum(sections_found.values())
        logger.info(f"📊 IEP Quality Score: {quality_score}/{len(sections_found)}")
        
        return {
            "sections_found": sections_found,
            "quality_score": quality_score,
            "max_score": len(sections_found),
            "content_length": len(content)
        }
        
    except Exception as e:
        logger.error(f"❌ Error analyzing content: {e}")
        return {}

def main():
    """Main processing function"""
    logger.info("🚀 Simple IEP Document Processor")
    logger.info("=" * 60)
    
    # Find the IEP file
    iep_file_path = Path(__file__).parent.parent / "adk_host" / "uploaded_documents" / "bc6672b0-c7be-4d20-ad09-21c0659b1d2f_sampleiep2.txt"
    
    if not iep_file_path.exists():
        logger.error(f"❌ IEP file not found: {iep_file_path}")
        return False
    
    # 1. Analyze content
    logger.info("\n" + "="*40)
    logger.info("1. ANALYZING IEP CONTENT")
    logger.info("="*40)
    
    analysis = analyze_iep_content(str(iep_file_path))
    
    # 2. Process into chunks
    logger.info("\n" + "="*40)
    logger.info("2. PROCESSING INTO CHUNKS")
    logger.info("="*40)
    
    chunks = process_local_iep_simple(str(iep_file_path))
    
    if not chunks:
        logger.error("❌ Failed to create chunks")
        return False
    
    # 3. Add to vector store
    logger.info("\n" + "="*40)
    logger.info("3. ADDING TO VECTOR STORE")
    logger.info("="*40)
    
    success = add_to_vector_store_simple(chunks)
    
    if not success:
        logger.error("❌ Failed to add to vector store")
        return False
    
    # 4. Test vector store
    logger.info("\n" + "="*40)
    logger.info("4. TESTING VECTOR STORE")
    logger.info("="*40)
    
    test_success = test_vector_store()
    
    # 5. Summary
    logger.info("\n" + "="*60)
    logger.info("📊 SUMMARY")
    logger.info("="*60)
    
    logger.info(f"IEP Quality Score: {analysis.get('quality_score', 0)}/{analysis.get('max_score', 8)}")
    logger.info(f"Chunks created: {len(chunks)}")
    logger.info(f"Vector store updated: {'✅' if success else '❌'}")
    logger.info(f"Testing passed: {'✅' if test_success else '❌'}")
    
    if success and test_success:
        logger.info("\n🎉 SUCCESS! IEP example has been processed into vector store")
        logger.info("🎯 Next steps:")
        logger.info("1. Replace dummy embeddings with real Gemini embeddings")
        logger.info("2. Test RAG-based IEP generation")
        logger.info("3. Add more diverse IEP examples")
        
        # Save processing info
        processing_info = {
            "file_processed": str(iep_file_path.name),
            "chunks_created": len(chunks),
            "quality_analysis": analysis,
            "timestamp": "2025-07-02",
            "status": "success"
        }
        
        with open("iep_processing_report.json", "w") as f:
            json.dump(processing_info, f, indent=2)
        
        logger.info("📋 Processing report saved to: iep_processing_report.json")
        
        return True
    else:
        logger.error("\n❌ FAILED! Issues encountered during processing")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)