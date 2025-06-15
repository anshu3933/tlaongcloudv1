"""Minimal test service to check basic functionality"""
import os
import sys
from pathlib import Path

# Add project to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Set minimal environment
os.environ.update({
    "ENVIRONMENT": "development",
    "DATABASE_URL": "sqlite+aiosqlite:///./test.db",
    "JWT_SECRET_KEY": "test-key",
    "GCP_PROJECT_ID": "test-project",
    "GCS_BUCKET_NAME": "test-bucket",
    "GEMINI_MODEL": "gemini-1.5-pro",
    "SMTP_ENABLED": "false",
    "SMTP_USERNAME": "test@example.com",
    "SMTP_FROM_EMAIL": "test@example.com"
})

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Create minimal app
app = FastAPI(title="Test Special Education Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "test-special-education"}

@app.get("/")
async def root():
    return {"message": "Test Special Education Service is running"}

if __name__ == "__main__":
    print("🧪 Starting Minimal Test Service...")
    print("🌐 URL: http://localhost:8007")
    print("=" * 40)
    
    uvicorn.run(
        "__main__:app",
        host="0.0.0.0", 
        port=8007,
        reload=False
    )