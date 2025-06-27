# Special Education RAG System

A production-ready microservices-based system for managing Individualized Education Programs (IEPs) using Retrieval-Augmented Generation (RAG) with Google Gemini 2.5 Flash and comprehensive template management.

## Architecture

The system consists of the following microservices:

- **Auth Service** (Port 8003): Handles user authentication and authorization
- **Workflow Service** (Port 8004): Manages approval workflows
- **Special Education Service** (Port 8005): Core IEP management with AI-powered template system
- **MCP Server** (Port 8001): RAG and LLM integration
- **ADK Host** (Port 8002): API Gateway and frontend

## ✨ Key Features

### 🎯 IEP Template System
- **15 Default Templates** covering 5 disability types × 3 grade ranges
- **IDEA-Compliant Structure** with 13 federal disability categories
- **SMART Goal Templates** for personalized goal generation
- **Comprehensive Sections**: Student info, goals, academic areas, accommodations, services

### 🤖 AI-Powered IEP Generation
- **RAG Integration** with Google Gemini 2.5 Flash
- **Context-Aware Generation** using student history and similar IEPs
- **Template-Driven Content** for consistent, professional output
- **Vector Store Integration** with ChromaDB for similarity matching

### 📊 Production-Ready Architecture
- **Async SQLAlchemy** with comprehensive session management
- **Microservices Design** with Docker containerization
- **RESTful APIs** with OpenAPI documentation
- **Real-time Data** with PostgreSQL and Redis

## Prerequisites

- Python 3.9+
- PostgreSQL 15+
- Redis 7+
- Docker and Docker Compose
- Google Cloud Platform account (for production)
- GCP credentials configured

## Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd rag-mcp-backend
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
# Install common package first
cd backend/common
pip install -e .

# Install service-specific dependencies
cd ../auth_service
pip install -r requirements.txt

cd ../workflow_service
pip install -r requirements.txt

cd ../special_education_service
pip install -r requirements.txt

cd ../mcp_server
pip install -r requirements.txt

cd ../adk_host
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. Start the services:
```bash
docker-compose up -d
```

## Dependency Management

The project uses a centralized dependency management strategy:

- **Common Package** (`backend/common/setup.py`): Contains all shared dependencies with pinned versions
- **Service-specific Requirements**: Each service has its own `requirements.txt` that:
  - References the common package using `-e ../common`
  - Only includes service-specific dependencies not in common

### Updating Dependencies

1. To update a shared dependency:
   ```bash
   # Edit backend/common/setup.py
   # Update the version in install_requires
   
   # Reinstall common package in all services
   cd backend/common
   pip install -e .
   ```

2. To add a service-specific dependency:
   ```bash
   # Add to the service's requirements.txt
   # Install in the service directory
   cd backend/<service_name>
   pip install -r requirements.txt
   ```

## 🚀 Quick Start API Testing

### Health Checks
```bash
# Check all services
curl http://localhost:8002/health  # ADK Host
curl http://localhost:8005/health  # Special Education Service
curl http://localhost:8001/health  # MCP Server
```

### IEP Template System
```bash
# List all templates (15 defaults available)
curl http://localhost:8005/api/v1/templates

# List disability types (13 IDEA categories)
curl http://localhost:8005/api/v1/templates/disability-types

# Get specific template
curl http://localhost:8005/api/v1/templates/{template_id}
```

### AI-Powered IEP Creation
```bash
# Create IEP with RAG (replace UUIDs with actual values)
curl -X POST "http://localhost:8005/api/v1/ieps/advanced/create-with-rag?current_user_id=1&current_user_role=teacher" \
  -H "Content-Type: application/json" \
  -d '{
    "student_id": "STUDENT_UUID",
    "template_id": "TEMPLATE_UUID",
    "academic_year": "2025-2026",
    "content": {"assessment_summary": "Student shows strengths in visual learning"},
    "meeting_date": "2025-01-15",
    "effective_date": "2025-01-15", 
    "review_date": "2026-01-15"
  }'
```

### Student Management
```bash
# List students
curl http://localhost:8005/api/v1/students

# Get student's IEPs
curl http://localhost:8005/api/v1/ieps/student/{student_id}
```

### Document RAG (MCP Server)
```bash
# Process documents
curl -X POST http://localhost:8001/documents/process

# Query with AI
curl -X POST http://localhost:8002/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What assessment reports are available?"}'
```

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run specific service tests
pytest tests/auth_service/
pytest tests/workflow_service/
pytest tests/special_education_service/

# Run with coverage
pytest --cov=backend
```

### Code Style

The project uses:
- Black for code formatting
- isort for import sorting
- mypy for type checking
- ruff for linting

```bash
# Format code
black backend/
isort backend/

# Type checking
mypy backend/

# Linting
ruff check backend/
```

### Database Migrations

```bash
# Create a new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head
```

## API Documentation

Once the services are running, you can access the API documentation at:

- Auth Service: http://localhost:8003/docs
- Workflow Service: http://localhost:8004/docs
- Special Education Service: http://localhost:8005/docs
- ADK Host: http://localhost:8002/docs

## Deployment

1. Set up GCP resources:
   - Create a project
   - Enable required APIs
   - Set up Cloud SQL
   - Configure Vector Search
   - Set up Cloud Storage

2. Configure production environment:
   - Update .env with production values
   - Set up SSL certificates
   - Configure monitoring

3. Deploy using Docker:
```bash
docker-compose -f docker-compose.prod.yml up -d
```

## Monitoring

The system includes:
- Health check endpoints
- Prometheus metrics
- Structured logging
- Audit trails

## Security

- JWT-based authentication
- Role-based access control
- Input validation
- Rate limiting
- Secure credential management

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

## License

[License Type] - See LICENSE file for details 