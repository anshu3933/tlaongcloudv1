"""Process and chunk documents from GCS"""
import os
from typing import List, Dict, Any
from pathlib import Path
import tempfile
import datetime
import traceback

from google.cloud import storage
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import (
    PyPDFLoader,
    Docx2txtLoader,
    TextLoader,
    UnstructuredMarkdownLoader
)
import vertexai
from vertexai.language_models import TextEmbeddingModel

DEBUG_LOG_PATH = "/tmp/document_processor_debug.log"
def log_debug(msg):
    with open(DEBUG_LOG_PATH, "a") as f:
        f.write(f"[{datetime.datetime.now()}] {msg}\n")

class DocumentProcessor:
    def __init__(self, project_id: str, bucket_name: str):
        self.project_id = project_id
        self.bucket_name = bucket_name
        self.storage_client = storage.Client(project=project_id)
        self.bucket = self.storage_client.bucket(bucket_name)
        
        # Initialize Vertex AI
        vertexai.init(project=project_id, location="us-central1")
        self.embedding_model = TextEmbeddingModel.from_pretrained("text-embedding-004")
        
        # Text splitter for chunking
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
    
    def list_documents(self, prefix: str = "") -> List[str]:
        """List all documents in the bucket"""
        blobs = self.bucket.list_blobs(prefix=prefix)
        return [blob.name for blob in blobs if self._is_supported_file(blob.name)]
    
    def _is_supported_file(self, filename: str) -> bool:
        """Check if file type is supported"""
        supported_extensions = ['.pdf', '.docx', '.txt', '.md']
        return any(filename.lower().endswith(ext) for ext in supported_extensions)
    
    def download_document(self, blob_name: str, local_path: str) -> str:
        """Download document from GCS"""
        blob = self.bucket.blob(blob_name)
        blob.download_to_filename(local_path)
        return local_path
    
    def load_document(self, file_path: str) -> List[Dict[str, Any]]:
        """Load document using appropriate loader"""
        file_extension = Path(file_path).suffix.lower()
        
        if file_extension == '.pdf':
            loader = PyPDFLoader(file_path)
        elif file_extension == '.docx':
            loader = Docx2txtLoader(file_path)
        elif file_extension == '.md':
            loader = UnstructuredMarkdownLoader(file_path)
        else:
            loader = TextLoader(file_path)
        
        return loader.load()
    
    def process_document(self, blob_name: str) -> List[Dict[str, Any]]:
        """Process a single document from GCS"""
        chunks = []
        
        # Download to temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(blob_name).suffix) as tmp:
            tmp_path = tmp.name
        
        try:
            log_debug(f"Downloading: {blob_name} to {tmp_path}")
            self.download_document(blob_name, tmp_path)
            try:
                documents = self.load_document(tmp_path)
                log_debug(f"Loaded {len(documents)} document(s) from {blob_name}")
                if len(documents) == 0:
                    log_debug(f"WARNING: Loader returned zero documents for {blob_name}")
                for idx, doc in enumerate(documents):
                    content_len = len(getattr(doc, 'page_content', ''))
                    log_debug(f"  Document {idx}: content length = {content_len}")
            except Exception as e:
                log_debug(f"ERROR loading document {blob_name}: {str(e)}")
                log_debug(traceback.format_exc())
                return chunks
            for doc in documents:
                try:
                    doc_chunks = self.text_splitter.split_text(doc.page_content)
                    log_debug(f"  Split into {len(doc_chunks)} chunk(s)")
                except Exception as e:
                    log_debug(f"ERROR splitting document {blob_name}: {str(e)}")
                    log_debug(traceback.format_exc())
                    continue
                for i, chunk_text in enumerate(doc_chunks):
                    # Merge metadata but ensure source is always the blob name
                    metadata = {
                        **doc.metadata,
                        "source": blob_name,
                        "chunk_index": i,
                        "total_chunks": len(doc_chunks),
                        "document_name": Path(blob_name).name,
                        "page": doc.metadata.get("page", 0)
                    }
                    chunk = {
                        "content": chunk_text,
                        "metadata": metadata
                    }
                    chunks.append(chunk)
        except Exception as e:
            log_debug(f"ERROR processing document {blob_name}: {str(e)}")
            log_debug(traceback.format_exc())
        finally:
            # Clean up temp file
            os.unlink(tmp_path)
        
        log_debug(f"Returning {len(chunks)} chunk(s) for {blob_name}")
        return chunks
    
    def create_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Create embeddings using Vertex AI"""
        # Process in batches of 5 (API limit)
        embeddings = []
        
        for i in range(0, len(texts), 5):
            batch = texts[i:i+5]
            batch_embeddings = self.embedding_model.get_embeddings(batch)
            embeddings.extend([emb.values for emb in batch_embeddings])
        
        return embeddings
    
    def process_all_documents(self) -> Dict[str, Any]:
        """Process all documents in the bucket"""
        all_chunks = []
        
        # Get all documents
        documents = self.list_documents()
        print(f"Found {len(documents)} documents to process")
        
        # Process each document
        for doc_name in documents:
            print(f"Processing: {doc_name}")
            try:
                chunks = self.process_document(doc_name)
                all_chunks.extend(chunks)
                print(f"  Created {len(chunks)} chunks")
            except Exception as e:
                print(f"  Error processing {doc_name}: {str(e)}")
        
        # Create embeddings for all chunks
        print(f"\nCreating embeddings for {len(all_chunks)} chunks...")
        chunk_texts = [chunk["content"] for chunk in all_chunks]
        embeddings = self.create_embeddings(chunk_texts)
        
        # Add embeddings to chunks
        for chunk, embedding in zip(all_chunks, embeddings):
            chunk["embedding"] = embedding
        
        return {
            "chunks": all_chunks,
            "total_documents": len(documents),
            "total_chunks": len(all_chunks)
        } 