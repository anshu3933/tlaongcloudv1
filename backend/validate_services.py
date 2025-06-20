#!/usr/bin/env python3
"""Final validation script for all backend services."""

import os
import sys
from pathlib import Path

# Set required environment variables for validation
os.environ.update({
    "ENVIRONMENT": "development",
    "DATABASE_URL": "sqlite+aiosqlite:///./test.db",
    "JWT_SECRET_KEY": "test-secret-key-for-validation",
    "GCP_PROJECT_ID": "test-project",
    "GCS_BUCKET_NAME": "test-bucket",
    "GEMINI_MODEL": "gemini-1.5-pro",
    "SMTP_ENABLED": "false",
    "LOG_LEVEL": "INFO"
})

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def validate_service(service_name: str, import_path: str) -> bool:
    """Validate that a service can be imported successfully."""
    try:
        exec(f"from {import_path} import app")
        print(f"✅ {service_name} validates successfully")
        return True
    except Exception as e:
        print(f"❌ {service_name} validation failed: {e}")
        return False

def main():
    """Main validation function."""
    print("🔍 Validating all backend services...")
    print("=" * 50)
    
    services = [
        ("Auth Service", "auth_service.src.main"),
        ("Special Education Service", "special_education_service.src.main"),
        ("Workflow Service", "workflow_service.src.main"),
        ("MCP Server", "mcp_server.src.main"),
    ]
    
    results = []
    for service_name, import_path in services:
        result = validate_service(service_name, import_path)
        results.append((service_name, result))
    
    print("\n📊 Validation Summary")
    print("=" * 30)
    
    all_passed = True
    for service_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{service_name}: {status}")
        if not passed:
            all_passed = False
    
    if all_passed:
        print("\n🎉 All services validate successfully!")
        print("\n📋 Services are ready for:")
        print("  • Development deployment")
        print("  • Testing")
        print("  • Production configuration")
        return 0
    else:
        print("\n💥 Some services failed validation!")
        return 1

if __name__ == "__main__":
    sys.exit(main())