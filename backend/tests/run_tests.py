#!/usr/bin/env python3
"""Test runner for the RAG-MCP backend services."""

import os
import sys
import subprocess
import argparse
from pathlib import Path
from typing import List, Optional

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

class Colors:
    """ANSI color codes for terminal output."""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_colored(message: str, color: str = Colors.END):
    """Print colored message to terminal."""
    print(f"{color}{message}{Colors.END}")

def run_command(command: List[str], description: str) -> bool:
    """Run a command and return success status."""
    print_colored(f"\n🔄 {description}...", Colors.BLUE)
    print_colored(f"Command: {' '.join(command)}", Colors.YELLOW)
    
    try:
        result = subprocess.run(
            command,
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        if result.returncode == 0:
            print_colored(f"✅ {description} passed", Colors.GREEN)
            if result.stdout:
                print(result.stdout)
            return True
        else:
            print_colored(f"❌ {description} failed", Colors.RED)
            if result.stdout:
                print("STDOUT:", result.stdout)
            if result.stderr:
                print("STDERR:", result.stderr)
            return False
            
    except subprocess.TimeoutExpired:
        print_colored(f"⏰ {description} timed out", Colors.RED)
        return False
    except Exception as e:
        print_colored(f"💥 {description} crashed: {e}", Colors.RED)
        return False

def setup_test_environment():
    """Set up test environment variables."""
    test_env = {
        "ENVIRONMENT": "test",
        "DATABASE_URL": "sqlite+aiosqlite:///./test.db",
        "JWT_SECRET_KEY": "test-secret-key-for-testing",
        "GCP_PROJECT_ID": "test-project",
        "SMTP_ENABLED": "false",
        "LOG_LEVEL": "INFO",
        "PYTHONPATH": str(project_root)
    }
    
    for key, value in test_env.items():
        os.environ[key] = value
    
    print_colored("🔧 Test environment configured", Colors.BLUE)

def run_unit_tests(service: Optional[str] = None) -> bool:
    """Run unit tests for specified service or all services."""
    if service:
        test_paths = [f"{service}/tests/test_*.py"]
        description = f"Unit tests for {service}"
    else:
        test_paths = ["**/tests/test_*.py"]
        description = "All unit tests"
    
    command = [
        "python", "-m", "pytest",
        "-v",
        "--tb=short",
        "--durations=10",
        *test_paths
    ]
    
    return run_command(command, description)

def run_integration_tests() -> bool:
    """Run integration tests."""
    command = [
        "python", "-m", "pytest",
        "tests/integration/",
        "-v",
        "--tb=short",
        "--durations=10"
    ]
    
    return run_command(command, "Integration tests")

def run_api_contract_tests() -> bool:
    """Run API contract tests."""
    command = [
        "python", "-m", "pytest",
        "tests/api_contracts/",
        "-v",
        "--tb=short"
    ]
    
    return run_command(command, "API contract tests")

def run_linting(service: Optional[str] = None) -> bool:
    """Run linting checks."""
    if service:
        paths = [f"{service}/src/"]
        description = f"Linting for {service}"
    else:
        paths = ["*/src/", "tests/", "scripts/"]
        description = "Linting all code"
    
    # Run flake8
    command = ["python", "-m", "flake8", "--max-line-length=100", *paths]
    flake8_result = run_command(command, f"{description} (flake8)")
    
    # Run black check
    command = ["python", "-m", "black", "--check", "--diff", *paths]
    black_result = run_command(command, f"{description} (black)")
    
    return flake8_result and black_result

def run_type_checking(service: Optional[str] = None) -> bool:
    """Run type checking with mypy."""
    if service:
        paths = [f"{service}/src/"]
        description = f"Type checking for {service}"
    else:
        paths = ["*/src/"]
        description = "Type checking all code"
    
    command = [
        "python", "-m", "mypy",
        "--ignore-missing-imports",
        "--disallow-untyped-defs",
        *paths
    ]
    
    return run_command(command, description)

def run_security_scan() -> bool:
    """Run security scanning with bandit."""
    command = [
        "python", "-m", "bandit",
        "-r", "*/src/",
        "-f", "json",
        "--skip", "B101,B601"  # Skip common false positives
    ]
    
    return run_command(command, "Security scan")

def check_dependencies() -> bool:
    """Check for dependency vulnerabilities."""
    command = ["python", "-m", "safety", "check", "--json"]
    return run_command(command, "Dependency vulnerability check")

def generate_coverage_report() -> bool:
    """Generate test coverage report."""
    command = [
        "python", "-m", "pytest",
        "--cov=auth_service/src",
        "--cov=special_education_service/src",
        "--cov=common/src",
        "--cov-report=html",
        "--cov-report=term-missing",
        "tests/"
    ]
    
    return run_command(command, "Coverage report generation")

def main():
    """Main test runner function."""
    parser = argparse.ArgumentParser(description="RAG-MCP Backend Test Runner")
    parser.add_argument(
        "--service",
        choices=["auth_service", "special_education_service", "workflow_service", "mcp_server"],
        help="Run tests for specific service only"
    )
    parser.add_argument("--unit", action="store_true", help="Run unit tests only")
    parser.add_argument("--integration", action="store_true", help="Run integration tests only")
    parser.add_argument("--contracts", action="store_true", help="Run API contract tests only")
    parser.add_argument("--lint", action="store_true", help="Run linting only")
    parser.add_argument("--type-check", action="store_true", help="Run type checking only")
    parser.add_argument("--security", action="store_true", help="Run security scans only")
    parser.add_argument("--coverage", action="store_true", help="Generate coverage report")
    parser.add_argument("--fast", action="store_true", help="Skip slow tests")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    print_colored("🚀 RAG-MCP Backend Test Runner", Colors.BOLD + Colors.BLUE)
    print_colored("=" * 50, Colors.BLUE)
    
    # Setup test environment
    setup_test_environment()
    
    results = []
    
    # Determine what to run
    if args.unit:
        results.append(("Unit Tests", run_unit_tests(args.service)))
    elif args.integration:
        results.append(("Integration Tests", run_integration_tests()))
    elif args.contracts:
        results.append(("API Contract Tests", run_api_contract_tests()))
    elif args.lint:
        results.append(("Linting", run_linting(args.service)))
    elif args.type_check:
        results.append(("Type Checking", run_type_checking(args.service)))
    elif args.security:
        results.append(("Security Scan", run_security_scan()))
        results.append(("Dependency Check", check_dependencies()))
    elif args.coverage:
        results.append(("Coverage Report", generate_coverage_report()))
    else:
        # Run all tests
        results.append(("Unit Tests", run_unit_tests(args.service)))
        if not args.fast:
            results.append(("Integration Tests", run_integration_tests()))
            results.append(("API Contract Tests", run_api_contract_tests()))
        results.append(("Linting", run_linting(args.service)))
        if not args.fast:
            results.append(("Type Checking", run_type_checking(args.service)))
            results.append(("Security Scan", run_security_scan()))
    
    # Print summary
    print_colored("\n📊 Test Results Summary", Colors.BOLD + Colors.BLUE)
    print_colored("=" * 50, Colors.BLUE)
    
    all_passed = True
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        color = Colors.GREEN if passed else Colors.RED
        print_colored(f"{test_name}: {status}", color)
        if not passed:
            all_passed = False
    
    if all_passed:
        print_colored("\n🎉 All tests passed!", Colors.BOLD + Colors.GREEN)
        sys.exit(0)
    else:
        print_colored("\n💥 Some tests failed!", Colors.BOLD + Colors.RED)
        sys.exit(1)

if __name__ == "__main__":
    main()