# Educational IEP Generator - System Integration Guide

## Overview

This guide provides comprehensive instructions for deploying and running the integrated Educational IEP Generator system, which consists of:

- **Backend**: FastAPI microservices (Auth, Workflow, Special Education, MCP Server, ADK Host)
- **Frontend**: Next.js 14+ application with TypeScript and shadcn/ui
- **Database**: PostgreSQL with SQLAlchemy async ORM
- **AI/RAG**: ChromaDB/Vertex Vector Store integration via ADK Host (BFF pattern)

## Architecture

The system follows a Backend-for-Frontend (BFF) pattern where:
- Frontend communicates with backend APIs for data operations
- AI/RAG operations go through ADK Host as a specialized BFF
- Request-response pattern (not streaming) for AI generation
- JWT-based authentication with role-based access control

## Prerequisites

### Required Software
- Docker & Docker Compose
- Node.js 18+ (for local development)
- Python 3.11+ (for backend development)
- PostgreSQL 15+ (if not using Docker)

### Environment Setup
1. Clone the repository
2. Set up environment variables (see below)
3. Initialize Docker network: `docker network create tla-network`

## Environment Configuration

### Backend Services
Each microservice requires its own `.env` file. Key variables:

```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/tla_db
TEST_DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/tla_test_db

# Security
SECRET_KEY=your-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# AI Services
ANTHROPIC_API_KEY=your-anthropic-key
VERTEX_PROJECT_ID=your-gcp-project
VERTEX_LOCATION=us-central1
CHROMADB_HOST=localhost
CHROMADB_PORT=8000

# Service URLs
AUTH_SERVICE_URL=http://localhost:8001
WORKFLOW_SERVICE_URL=http://localhost:8004
SPECIAL_ED_SERVICE_URL=http://localhost:8005
MCP_SERVER_URL=http://localhost:8006
ADK_HOST_URL=http://localhost:8002
```

### Frontend Configuration
Create `/frontend/v0-tla-front-endv01-main 2/.env.local`:

```bash
# Backend API endpoints
NEXT_PUBLIC_API_BASE_URL=http://localhost:8003/v1
NEXT_PUBLIC_ADK_HOST_URL=http://localhost:8002
NEXT_PUBLIC_ENVIRONMENT=development

# Optional: API timeout
NEXT_PUBLIC_API_TIMEOUT=30000
```

## Deployment Options

### Option 1: Docker Compose (Recommended)

#### Full System Deployment
1. Navigate to project root
2. Create integrated docker-compose.yml:

```yaml
version: '3.8'

services:
  # Database
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: tla_db
      POSTGRES_USER: tla_user
      POSTGRES_PASSWORD: tla_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    networks:
      - tla-network

  # ChromaDB for vector storage
  chromadb:
    image: chromadb/chroma:latest
    ports:
      - "8000:8000"
    networks:
      - tla-network

  # Backend Services (add each microservice)
  auth-service:
    build: ./backend/auth_service
    ports:
      - "8001:8001"
    environment:
      - DATABASE_URL=postgresql+asyncpg://tla_user:tla_password@postgres:5432/tla_db
    depends_on:
      - postgres
    networks:
      - tla-network

  adk-host:
    build: ./backend/adk_host
    ports:
      - "8002:8002"
    environment:
      - CHROMADB_HOST=chromadb
      - AUTH_SERVICE_URL=http://auth-service:8001
    depends_on:
      - chromadb
      - auth-service
    networks:
      - tla-network

  api-gateway:
    build: ./backend/api_gateway
    ports:
      - "8003:8003"
    environment:
      - AUTH_SERVICE_URL=http://auth-service:8001
      - WORKFLOW_SERVICE_URL=http://workflow-service:8004
      - SPECIAL_ED_SERVICE_URL=http://special-ed-service:8005
    depends_on:
      - auth-service
    networks:
      - tla-network

  # Frontend
  frontend:
    build: ./frontend/v0-tla-front-endv01-main\ 2
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_BASE_URL=http://localhost:8003/v1
      - NEXT_PUBLIC_ADK_HOST_URL=http://localhost:8002
    depends_on:
      - api-gateway
      - adk-host
    networks:
      - tla-network

  # Nginx Reverse Proxy
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./frontend/v0-tla-front-endv01-main\ 2/nginx.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - frontend
    networks:
      - tla-network

networks:
  tla-network:
    driver: bridge

volumes:
  postgres_data:
```

3. Run: `docker-compose up --build`

#### Frontend-Only Development
For frontend development with existing backend:

```bash
cd "frontend/v0-tla-front-endv01-main 2"
docker-compose up --build
```

### Option 2: Local Development

#### Backend Services
1. Set up Python virtual environment for each service
2. Install dependencies: `pip install -r requirements.txt`
3. Run database migrations
4. Start each service on its designated port

#### Frontend
1. Install dependencies:
```bash
cd "frontend/v0-tla-front-endv01-main 2"
npm install
```

2. Run development server:
```bash
npm run dev
```

## Service Health Monitoring

### Health Check Endpoints
- Frontend: `http://localhost:3000/api/health`
- API Gateway: `http://localhost:8003/v1/health`
- ADK Host: `http://localhost:8002/health`
- Auth Service: `http://localhost:8001/health`

### Monitoring Commands
```bash
# Check all services
curl http://localhost:3000/api/health
curl http://localhost:8003/v1/health
curl http://localhost:8002/health

# Check Docker containers
docker ps
docker-compose logs -f [service-name]
```

## Testing

### Integration Tests
Run API integration tests:
```bash
cd "frontend/v0-tla-front-endv01-main 2"
npm test
npm run test:integration
```

### Manual Testing Workflow
1. Access frontend at `http://localhost:3000`
2. Login with test credentials
3. Verify authentication works
4. Test student management features
5. Test IEP generation via ADK Host
6. Verify document upload functionality

## API Integration Details

### Authentication Flow
1. POST `/auth/login` with credentials
2. Receive JWT access token
3. Include `Authorization: Bearer <token>` in all subsequent requests
4. Token auto-refresh handled by frontend auth service

### Key API Endpoints

#### Student Management
- `GET /v1/students` - List students with filtering
- `POST /v1/students` - Create new student
- `GET /v1/students/{id}` - Get student details
- `PATCH /v1/students/{id}` - Update student
- `DELETE /v1/students/{id}` - Delete student

#### IEP Management
- `GET /v1/students/{id}/ieps` - List student IEPs
- `GET /v1/ieps/{id}` - Get IEP details
- `PATCH /v1/ieps/{id}` - Update IEP

#### AI/RAG Operations (via ADK Host)
- `POST /generate-iep` - Generate IEP content
- `POST /analyze-document` - Analyze uploaded documents
- `GET /health` - Service health check

### Error Handling
All APIs return standardized error format:
```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable message",
    "details": [
      {
        "field": "field_name",
        "issue": "validation error"
      }
    ]
  }
}
```

## Security Configuration

### CORS Settings
Configure CORS in backend services to allow frontend origin:
- Development: `http://localhost:3000`
- Production: Your domain

### Rate Limiting
Nginx configuration includes:
- API requests: 100 requests/minute
- Login attempts: 5 requests/minute
- File uploads: 50MB max size

### Security Headers
- Content Security Policy (CSP)
- X-Frame-Options: DENY
- X-Content-Type-Options: nosniff
- X-XSS-Protection: 1; mode=block
- Strict-Transport-Security (HTTPS only)

## Troubleshooting

### Common Issues

#### Backend Connection Errors
- Verify all services are running
- Check environment variables
- Ensure database is accessible
- Check network connectivity between services

#### Authentication Issues
- Verify JWT secret key consistency across services
- Check token expiration settings
- Ensure auth service is running

#### AI/RAG Issues
- Verify Anthropic API key
- Check ChromaDB connectivity
- Ensure ADK Host is properly configured
- Check vector store initialization

#### Frontend Build Issues
- Clear Next.js cache: `rm -rf .next`
- Reinstall dependencies: `rm -rf node_modules && npm install`
- Check TypeScript compilation

### Logs and Debugging
```bash
# Docker logs
docker-compose logs -f [service-name]

# Frontend logs
npm run dev  # Development mode with hot reload

# Backend logs
# Check individual service logs for detailed error information
```

### Performance Optimization
- Enable Redis caching for frequent queries
- Implement connection pooling for database
- Use CDN for static assets in production
- Enable gzip compression in Nginx

## Production Deployment

### Additional Considerations
1. **SSL/TLS**: Configure certificates in Nginx
2. **Environment Secrets**: Use Docker secrets or external secret management
3. **Database Backups**: Implement automated backup strategy
4. **Monitoring**: Add application monitoring (e.g., Prometheus/Grafana)
5. **Load Balancing**: Scale services horizontally as needed
6. **CI/CD**: Implement automated deployment pipeline

### Production Environment Variables
```bash
# Use production values
NODE_ENV=production
NEXT_PUBLIC_ENVIRONMENT=production
DATABASE_URL=postgresql+asyncpg://user:pass@prod-db:5432/tla_prod
ANTHROPIC_API_KEY=prod-api-key
# ... other production configs
```

## Support and Maintenance

### Regular Tasks
- Monitor service health endpoints
- Review and rotate API keys
- Update dependencies regularly
- Backup database and configurations
- Monitor disk space and performance metrics

### Version Updates
- Test updates in staging environment first
- Perform rolling updates to minimize downtime
- Keep rollback procedures ready

This guide provides the complete setup for running the integrated Educational IEP Generator system. For specific issues, check the individual service documentation and logs.