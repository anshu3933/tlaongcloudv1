#!/usr/bin/env python3
"""
Integration Test Runner for Special Education Service

This script runs comprehensive integration tests to validate:
- Concurrent IEP creation and version conflict resolution
- Load performance under stress
- Version integrity and constraint enforcement
- Retry mechanism behavior
"""

import asyncio
import os
import sys
import subprocess
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def run_pytest_command(test_pattern: str = None, verbose: bool = True, coverage: bool = False):
    """Run pytest with specified options"""
    
    # Base command
    cmd = ["python", "-m", "pytest"]
    
    # Add verbosity
    if verbose:
        cmd.append("-v")
    
    # Add coverage if requested
    if coverage:
        cmd.extend(["--cov=src", "--cov-report=html", "--cov-report=term"])
    
    # Add specific test pattern if provided
    if test_pattern:
        cmd.append(test_pattern)
    else:
        cmd.append("tests/")
    
    # Run in project directory
    print(f"Running command: {' '.join(cmd)}")
    print(f"Working directory: {project_root}")
    
    try:
        result = subprocess.run(
            cmd,
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        print("STDOUT:")
        print(result.stdout)
        
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
        
        return result.returncode == 0
    
    except subprocess.TimeoutExpired:
        print("ERROR: Tests timed out after 5 minutes")
        return False
    except Exception as e:
        print(f"ERROR: Failed to run tests: {e}")
        return False

def check_dependencies():
    """Check if required dependencies are installed"""
    required_packages = [
        "pytest",
        "pytest-asyncio", 
        "pytest-cov",
        "sqlalchemy",
        "fastapi"
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
            print(f"✓ {package} is installed")
        except ImportError:
            missing_packages.append(package)
            print(f"✗ {package} is missing")
    
    if missing_packages:
        print(f"\nPlease install missing packages:")
        print(f"pip install {' '.join(missing_packages)}")
        return False
    
    return True

def setup_test_environment():
    """Setup test environment variables"""
    os.environ["ENVIRONMENT"] = "test"
    os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
    os.environ["LOG_LEVEL"] = "INFO"
    os.environ["SQLALCHEMY_ECHO"] = "false"
    os.environ["GEMINI_MODEL"] = "mock"
    os.environ["SMTP_ENABLED"] = "false"
    print("✓ Test environment variables set")

def main():
    """Main test runner"""
    print("=" * 60)
    print("Special Education Service Integration Tests")
    print("=" * 60)
    
    # Check dependencies
    print("\n1. Checking dependencies...")
    if not check_dependencies():
        print("❌ Dependency check failed")
        return False
    
    # Setup environment
    print("\n2. Setting up test environment...")
    setup_test_environment()
    
    # Run specific test suites
    test_suites = [
        {
            "name": "Concurrent IEP Creation Tests",
            "pattern": "tests/test_concurrent_iep_creation.py",
            "description": "Tests concurrent IEP creation and version conflict resolution"
        },
        {
            "name": "Version Integrity Tests", 
            "pattern": "tests/test_version_integrity.py",
            "description": "Tests version integrity and constraint enforcement"
        },
        {
            "name": "Load Performance Tests",
            "pattern": "tests/test_load_performance.py", 
            "description": "Tests system performance under load"
        }
    ]
    
    results = {}
    
    for suite in test_suites:
        print(f"\n3. Running {suite['name']}...")
        print(f"   Description: {suite['description']}")
        print("-" * 40)
        
        start_time = time.time()
        success = run_pytest_command(suite["pattern"], verbose=True, coverage=False)
        duration = time.time() - start_time
        
        results[suite["name"]] = {
            "success": success,
            "duration": duration
        }
        
        if success:
            print(f"✅ {suite['name']} passed in {duration:.2f}s")
        else:
            print(f"❌ {suite['name']} failed after {duration:.2f}s")
    
    # Run all tests with coverage
    print(f"\n4. Running all tests with coverage...")
    print("-" * 40)
    
    start_time = time.time()
    coverage_success = run_pytest_command(coverage=True)
    coverage_duration = time.time() - start_time
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    total_tests = len(test_suites)
    passed_tests = sum(1 for r in results.values() if r["success"])
    
    for name, result in results.items():
        status = "✅ PASSED" if result["success"] else "❌ FAILED"
        print(f"{name}: {status} ({result['duration']:.2f}s)")
    
    print(f"\nCoverage Report: {'✅ PASSED' if coverage_success else '❌ FAILED'} ({coverage_duration:.2f}s)")
    
    print(f"\nOverall: {passed_tests}/{total_tests} test suites passed")
    
    if passed_tests == total_tests and coverage_success:
        print("🎉 All integration tests passed successfully!")
        return True
    else:
        print("⚠️  Some tests failed. Please review the output above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)