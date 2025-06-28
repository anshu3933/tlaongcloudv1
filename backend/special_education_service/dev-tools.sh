#!/bin/bash
# Development tools script for Special Education Service

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper function for colored output
log() {
    echo -e "${GREEN}[DEV]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

# Check if docker-compose is available
check_docker() {
    if ! command -v docker-compose &> /dev/null; then
        error "docker-compose is not installed or not in PATH"
        exit 1
    fi
}

# Development environment commands
dev_up() {
    log "Starting development environment..."
    check_docker
    docker-compose -f docker-compose.dev.yml up -d
    
    # Wait for services to be ready
    log "Waiting for services to start..."
    sleep 5
    
    # Check service health
    if curl -s http://localhost:8006/health > /dev/null 2>&1; then
        log "Development environment is ready!"
        info "API: http://localhost:8006"
        info "API Docs: http://localhost:8006/docs"
        info "Redis: localhost:6379 (password: devpassword)"
    else
        warn "Service may still be starting. Check logs with: ./dev-tools.sh logs"
    fi
}

dev_down() {
    log "Stopping development environment..."
    docker-compose -f docker-compose.dev.yml down
}

dev_restart() {
    log "Restarting development environment..."
    dev_down
    dev_up
}

dev_logs() {
    log "Showing service logs (press Ctrl+C to exit)..."
    docker-compose -f docker-compose.dev.yml logs -f --tail=100 special-education-service
}

dev_logs_all() {
    log "Showing all service logs (press Ctrl+C to exit)..."
    docker-compose -f docker-compose.dev.yml logs -f --tail=50
}

dev_shell() {
    log "Opening shell in development container..."
    docker-compose -f docker-compose.dev.yml exec special-education-service bash
}

dev_test() {
    log "Running basic tests in development environment..."
    docker-compose -f docker-compose.dev.yml exec special-education-service pytest -v tests/ -m "not performance"
}

dev_test_coverage() {
    log "Running tests with coverage..."
    docker-compose -f docker-compose.dev.yml exec special-education-service pytest --cov=src --cov-report=html --cov-report=term tests/ -m "not performance"
}

dev_test_integration() {
    log "Running integration tests..."
    docker-compose -f docker-compose.dev.yml exec special-education-service python tests/run_integration_tests.py
}

dev_test_concurrent() {
    log "Running concurrent IEP creation tests..."
    docker-compose -f docker-compose.dev.yml exec special-education-service pytest -v tests/test_concurrent_iep_creation.py
}

dev_test_performance() {
    log "Running performance tests (may take a while)..."
    docker-compose -f docker-compose.dev.yml exec special-education-service pytest -v tests/test_load_performance.py -m performance
}

dev_test_all() {
    log "Running ALL tests including performance tests..."
    docker-compose -f docker-compose.dev.yml exec special-education-service pytest -v tests/
}

dev_lint() {
    log "Running linting..."
    docker-compose -f docker-compose.dev.yml exec special-education-service black --check src/
    docker-compose -f docker-compose.dev.yml exec special-education-service isort --check-only src/
    docker-compose -f docker-compose.dev.yml exec special-education-service flake8 src/
}

dev_format() {
    log "Formatting code..."
    docker-compose -f docker-compose.dev.yml exec special-education-service black src/
    docker-compose -f docker-compose.dev.yml exec special-education-service isort src/
}

dev_db_shell() {
    log "Opening SQLite database shell..."
    docker-compose -f docker-compose.dev.yml exec db-admin sqlite3 test_special_ed.db
}

dev_db_reset() {
    warn "This will delete all data in the development database!"
    read -p "Are you sure? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log "Resetting development database..."
        docker-compose -f docker-compose.dev.yml exec special-education-service rm -f test_special_ed.db
        log "Database reset. Restart the service to recreate tables."
    else
        info "Database reset cancelled."
    fi
}

dev_status() {
    log "Development environment status:"
    docker-compose -f docker-compose.dev.yml ps
    
    echo
    info "Service endpoints:"
    echo "  API Health: $(curl -s http://localhost:8006/health 2>/dev/null && echo "✅ UP" || echo "❌ DOWN")"
    echo "  Redis: $(redis-cli -h localhost -p 6379 -a devpassword ping 2>/dev/null && echo "✅ UP" || echo "❌ DOWN")"
}

dev_clean() {
    warn "This will remove all development containers, volumes, and images!"
    read -p "Are you sure? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log "Cleaning development environment..."
        docker-compose -f docker-compose.dev.yml down -v --rmi all
        docker system prune -f
        log "Development environment cleaned."
    else
        info "Clean cancelled."
    fi
}

# Load testing
dev_load_test() {
    log "Running basic load test..."
    docker-compose -f docker-compose.dev.yml exec special-education-service python -c "
import asyncio
import aiohttp
import time

async def create_iep():
    async with aiohttp.ClientSession() as session:
        data = {
            'student_id': 'a5c65e54-29b2-4aaf-a0f2-805049b3169e',
            'academic_year': '2025-2026',
            'content': {'test': 'load test'},
            'meeting_date': '2025-01-15',
            'effective_date': '2025-01-15',
            'review_date': '2026-01-15'
        }
        async with session.post('http://localhost:8005/api/v1/ieps?current_user_id=1', json=data) as resp:
            return resp.status

async def load_test():
    print('Running 10 concurrent IEP creation requests...')
    start = time.time()
    tasks = [create_iep() for _ in range(10)]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    duration = time.time() - start
    
    successes = sum(1 for r in results if r == 201)
    print(f'Results: {successes}/10 successful in {duration:.2f}s')
    print(f'Status codes: {[r for r in results if isinstance(r, int)]}')

asyncio.run(load_test())
"
}

# Help function
show_help() {
    echo "Development Tools for Special Education Service"
    echo ""
    echo "Usage: ./dev-tools.sh <command>"
    echo ""
    echo "Environment commands:"
    echo "  up              Start development environment"
    echo "  down            Stop development environment"
    echo "  restart         Restart development environment"
    echo "  status          Show environment status"
    echo "  clean           Remove all containers, volumes, and images"
    echo ""
    echo "Development commands:"
    echo "  logs            Show service logs"
    echo "  logs-all        Show all service logs"
    echo "  shell           Open shell in service container"
    echo "  test            Run basic tests (excludes performance)"
    echo "  test-cov        Run tests with coverage"
    echo "  test-integration Run integration test suite"
    echo "  test-concurrent  Run concurrent IEP creation tests"
    echo "  test-performance Run performance tests"
    echo "  test-all        Run ALL tests including performance"
    echo "  lint            Run linting checks"
    echo "  format          Format code with black and isort"
    echo ""
    echo "Database commands:"
    echo "  db-shell        Open SQLite database shell"
    echo "  db-reset        Reset development database"
    echo ""
    echo "Testing commands:"
    echo "  load-test       Run basic load test"
    echo ""
    echo "Examples:"
    echo "  ./dev-tools.sh up           # Start development environment"
    echo "  ./dev-tools.sh logs         # Watch service logs"
    echo "  ./dev-tools.sh test         # Run tests"
    echo "  ./dev-tools.sh db-shell     # Access database"
}

# Main command handler
case "${1:-help}" in
    "up")
        dev_up
        ;;
    "down")
        dev_down
        ;;
    "restart")
        dev_restart
        ;;
    "logs")
        dev_logs
        ;;
    "logs-all")
        dev_logs_all
        ;;
    "shell")
        dev_shell
        ;;
    "test")
        dev_test
        ;;
    "test-cov")
        dev_test_coverage
        ;;
    "test-integration")
        dev_test_integration
        ;;
    "test-concurrent")
        dev_test_concurrent
        ;;
    "test-performance")
        dev_test_performance
        ;;
    "test-all")
        dev_test_all
        ;;
    "lint")
        dev_lint
        ;;
    "format")
        dev_format
        ;;
    "db-shell")
        dev_db_shell
        ;;
    "db-reset")
        dev_db_reset
        ;;
    "status")
        dev_status
        ;;
    "clean")
        dev_clean
        ;;
    "load-test")
        dev_load_test
        ;;
    "help")
        show_help
        ;;
    *)
        error "Unknown command: $1"
        echo ""
        show_help
        exit 1
        ;;
esac