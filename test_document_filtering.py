#!/usr/bin/env python3
"""Test script to verify document filtering is working correctly"""

import requests
import json
import time

BASE_URL = "http://localhost:8002/api/v1"

def test_document_upload_and_filter():
    print("Testing Document Upload and Filtering\n")
    
    # Step 1: Upload a test document
    print("1. Uploading test document...")
    
    # Create a simple text file to upload
    test_content = """
    This is a test document for verifying the document filtering functionality.
    It contains some educational content about special education and IEPs.
    The document discusses assessment strategies and student progress monitoring.
    This is unique content that should be easily identifiable in search results.
    Test marker: UNIQUE_TEST_CONTENT_12345
    """
    
    files = {
        'file': ('test_filtering.txt', test_content, 'text/plain')
    }
    
    upload_response = requests.post(f"{BASE_URL}/documents/upload", files=files)
    print(f"Upload response: {upload_response.status_code}")
    upload_data = upload_response.json()
    print(f"Upload result: {json.dumps(upload_data, indent=2)}")
    
    if upload_response.status_code != 200:
        print("Upload failed!")
        return
    
    document_id = upload_data.get("document_id")
    print(f"\nDocument uploaded with ID: {document_id}")
    
    # Wait for processing
    print("\n2. Waiting for document processing...")
    time.sleep(3)
    
    # Step 2: Query WITH document filter
    print("\n3. Testing query WITH document filter...")
    query_with_filter = {
        "query": "What does this document say about test marker?",
        "options": {
            "documents": [document_id],  # Filter by our uploaded document
            "top_k": 5
        }
    }
    
    response_with_filter = requests.post(
        f"{BASE_URL}/query",
        json=query_with_filter,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"Query response status: {response_with_filter.status_code}")
    if response_with_filter.status_code == 200:
        result = response_with_filter.json()
        print(f"\nAnswer: {result.get('answer', 'No answer')[:200]}...")
        print(f"Sources found: {len(result.get('sources', []))}")
        
        # Check if our document was used
        for source in result.get('sources', []):
            if source.get('metadata', {}).get('document_id') == document_id:
                print(f"✅ SUCCESS: Found content from uploaded document!")
                print(f"   Document ID in source: {source['metadata']['document_id']}")
                print(f"   Snippet: {source['snippet'][:100]}...")
                break
        else:
            print("❌ FAIL: Uploaded document not found in sources!")
    
    # Step 3: Query WITHOUT document filter (should search all documents)
    print("\n\n4. Testing query WITHOUT document filter...")
    query_without_filter = {
        "query": "What assessment reports are available?",
        "options": {
            "top_k": 5
        }
    }
    
    response_without_filter = requests.post(
        f"{BASE_URL}/query",
        json=query_without_filter,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"Query response status: {response_without_filter.status_code}")
    if response_without_filter.status_code == 200:
        result = response_without_filter.json()
        print(f"\nAnswer preview: {result.get('answer', 'No answer')[:200]}...")
        print(f"Sources found: {len(result.get('sources', []))}")
        
        # List document names found
        doc_names = set()
        for source in result.get('sources', []):
            doc_name = source.get('metadata', {}).get('document_name', 'Unknown')
            doc_names.add(doc_name)
        print(f"Documents referenced: {list(doc_names)}")
    
    # Step 4: List all documents to verify
    print("\n\n5. Listing all uploaded documents...")
    list_response = requests.get(f"{BASE_URL}/documents")
    if list_response.status_code == 200:
        docs = list_response.json()
        print(f"Total documents in system: {docs.get('total', 0)}")
        for doc in docs.get('documents', [])[:5]:  # Show first 5
            print(f"  - {doc.get('filename')} (ID: {doc.get('id')})")

if __name__ == "__main__":
    test_document_upload_and_filter()