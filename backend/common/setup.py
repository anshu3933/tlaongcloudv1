from setuptools import setup, find_packages

setup(
    name="rag-mcp-common",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        # Web Framework
        "fastapi==0.109.0",
        "uvicorn[standard]==0.27.0",
        "pydantic==2.5.3",
        "pydantic-settings==2.1.0",
        "python-dotenv==1.0.0",
        
        # Google Cloud
        "google-cloud-aiplatform>=1.42.0",
        "google-cloud-storage==2.14.0",
        "vertexai>=1.42.0",
        "google-genai>=1.18.0",
        
        # HTTP & Networking
        "httpx[http2]>=0.28.1",
        "python-multipart==0.0.7",
        
        # Database & Caching
        "redis>=5.0.0",
        "sqlalchemy>=2.0.0",
        "alembic>=1.13.0",
        "psycopg2-binary>=2.9.9",
        
        # Authentication & Security
        "python-jose[cryptography]==3.3.0",
        "passlib[bcrypt]==1.7.4",
        "bcrypt==4.1.2",
        
        # Monitoring & Logging
        "structlog==24.1.0",
        "prometheus-client==0.19.0",
        
        # RAG & Document Processing
        "chromadb>=0.4.22",
        "langchain>=0.1.0",
        "langchain-community>=0.0.10",
        "PyPDF2>=3.0.0",
        "python-docx>=1.0.0",
        "unstructured>=0.10.30",
        
        # Utilities
        "click>=8.1.7",
    ],
    python_requires=">=3.9",
) 