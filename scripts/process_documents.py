#!/usr/bin/env python3
"""Process documents from GCS and create embeddings"""
import os
import sys
import asyncio
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from dotenv import load_dotenv
load_dotenv()

import httpx

async def process_documents():
    """Call the MCP server to process documents"""
    mcp_url = os.getenv("MCP_SERVER_URL", "http://localhost:8001")
    
    async with httpx.AsyncClient(timeout=300.0) as client:
        # List documents
        print("Listing documents in GCS...")
        response = await client.get(f"{mcp_url}/documents/list")
        documents = response.json()
        print(f"Found {documents['count']} documents")
        
        # Process documents
        print("\nProcessing documents and creating embeddings...")
        response = await client.post(f"{mcp_url}/documents/process")
        result = response.json()
        
        print(f"\n✅ Processed {result['documents_processed']} documents")
        print(f"📦 Created {result['chunks_created']} chunks with embeddings")

if __name__ == "__main__":
    asyncio.run(process_documents()) 