"""Document processor for MCP server"""
import sys
import os
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

# Import the common document processor
from common.src.document_processor import DocumentProcessor