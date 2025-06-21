"""Start the Special Education Service for testing"""
import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Set environment variables for testing
os.environ.update({
    "ENVIRONMENT": "development",
    "DATABASE_URL": "sqlite+aiosqlite:///./test_special_ed.db",
    "JWT_SECRET_KEY": "test_secret_key_for_development_only",
    "GCP_PROJECT_ID": "thela002",
    "GCS_BUCKET_NAME": "betrag-data-test-a",
    "GEMINI_MODEL": "gemini-2.5-flash",
    "LOG_LEVEL": "INFO",
    "AUTH_SERVICE_URL": "http://localhost:8003",
    "MCP_SERVER_URL": "http://localhost:8001",
    "WORKFLOW_SERVICE_URL": "http://localhost:8004",
    "SMTP_ENABLED": "false",
    "SMTP_USERNAME": "test@example.com",
    "SMTP_FROM_EMAIL": "test@example.com"
})

if __name__ == "__main__":
    import uvicorn
    
    print("🚀 Starting Special Education Service for testing...")
    print("📊 Environment: development")
    print("💾 Database: SQLite (test_special_ed.db)")
    print("🌐 URL: http://localhost:8006")
    print("📖 Docs: http://localhost:8006/docs")
    print("=" * 50)
    
    try:
        uvicorn.run(
            "src.main:app",
            host="0.0.0.0",
            port=8006,
            reload=False,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n👋 Service stopped by user")
    except Exception as e:
        print(f"❌ Error starting service: {e}")
        sys.exit(1)