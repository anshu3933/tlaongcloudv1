# Special Education RAG System

A microservices-based system for managing Individualized Education Programs (IEPs) using Retrieval-Augmented Generation (RAG).

## Architecture

The system consists of the following microservices:

- **Auth Service** (Port 8003): Handles user authentication and authorization
- **Workflow Service** (Port 8004): Manages approval workflows
- **Special Education Service** (Port 8005): Core IEP management
- **MCP Server** (Port 8001): RAG and LLM integration
- **ADK Host** (Port 8002): API Gateway and frontend

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