# Authentication Service - Redesigned

A comprehensive, production-ready authentication and user management service built with FastAPI, featuring JWT token authentication, refresh token rotation, comprehensive audit logging, and role-based access control.

## 🚀 Features

### Authentication & Security
- **JWT Access Tokens** (60-minute expiry)
- **Refresh Token Rotation** (7-day expiry with database validation)
- **Password Complexity Validation** (configurable requirements)
- **bcrypt Password Hashing** with automatic salts
- **Session Management** with automatic cleanup
- **Rate Limiting** (configurable per IP)
- **CORS Protection** with configurable origins

### User Management
- **User Registration** with validation
- **Profile Management** (self or admin)
- **Role-Based Access Control** (user, teacher, coordinator, admin, superuser)
- **Account Activation/Deactivation**
- **Password Changes** with session invalidation
- **User Search and Filtering**

### Audit & Monitoring
- **Comprehensive Audit Logging** for all actions
- **IP Address Tracking**
- **Failed Login Monitoring**
- **User Activity Summaries**
- **Audit Log Search and Analytics**
- **Health Check Endpoints**

### Production Ready
- **Structured Error Handling** with consistent responses
- **Request/Response Logging** with timing
- **Security Headers** middleware
- **Database Migrations** with Alembic
- **Docker Support** with health checks
- **Non-root Container** execution

## 📁 Project Structure

```
backend/auth_service/
├── Dockerfile                 # Production container configuration
├── alembic.ini               # Database migration configuration
├── requirements.txt          # Python dependencies
├── scripts/
│   └── run_migrations.py     # Migration runner script
└── src/
    ├── main.py              # FastAPI application entry point
    ├── config.py            # Application configuration
    ├── database.py          # Database connection and setup
    ├── dependencies.py      # FastAPI dependency injection
    ├── schemas.py           # Pydantic data models
    ├── security.py          # Authentication and cryptography
    ├── middleware/          # Custom middleware
    │   └── error_handler.py
    ├── models/              # SQLAlchemy ORM models
    │   ├── user.py
    │   ├── user_session.py
    │   └── audit_log.py
    ├── repositories/        # Data access layer
    │   ├── user_repository.py
    │   └── audit_repository.py
    ├── routers/            # API route handlers
    │   ├── auth.py
    │   └── users.py
    └── migrations/         # Alembic database migrations
        ├── env.py
        └── script.py.mako
```

## 🛠 Setup & Installation

### Prerequisites
- Python 3.11+
- PostgreSQL 13+
- Docker (optional)

### Environment Variables

Create a `.env` file with the following variables:

```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/auth_db

# JWT Configuration
JWT_SECRET_KEY=your-super-secret-jwt-key-here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=7

# CORS Settings
CORS_ORIGINS=http://localhost:3000,http://localhost:8000

# Rate Limiting
RATE_LIMIT_REQUESTS=30
RATE_LIMIT_PERIOD=60

# Security
PASSWORD_MIN_LENGTH=8
PASSWORD_REQUIRE_UPPERCASE=true
PASSWORD_REQUIRE_LOWERCASE=true
PASSWORD_REQUIRE_DIGITS=true

# Environment
ENVIRONMENT=development
LOG_LEVEL=INFO
```

### Local Development

1. **Install Dependencies**
   ```bash
   cd backend/auth_service
   pip install -r requirements.txt
   ```

2. **Run Database Migrations**
   ```bash
   python scripts/run_migrations.py
   ```

3. **Start the Service**
   ```bash
   uvicorn src.main:app --host 0.0.0.0 --port 8003 --reload
   ```

### Docker Deployment

1. **Build Container**
   ```bash
   docker build -t auth-service .
   ```

2. **Run Container**
   ```bash
   docker run -p 8003:8003 \
     -e DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/db \
     -e JWT_SECRET_KEY=your-secret-key \
     auth-service
   ```

## 📚 API Documentation

### Authentication Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/register` | Register new user |
| POST | `/api/v1/auth/login` | Login and get tokens |
| POST | `/api/v1/auth/refresh` | Refresh access token |
| POST | `/api/v1/auth/logout` | Logout and clear sessions |
| GET | `/api/v1/auth/me` | Get current user profile |
| POST | `/api/v1/auth/cleanup-sessions` | Clean expired sessions |

### User Management Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/users/` | List all users (admin) |
| GET | `/api/v1/users/{user_id}` | Get user by ID |
| PUT | `/api/v1/users/{user_id}` | Update user |
| POST | `/api/v1/users/{user_id}/change-password` | Change password |
| POST | `/api/v1/users/{user_id}/activate` | Activate user (admin) |
| POST | `/api/v1/users/{user_id}/deactivate` | Deactivate user (admin) |
| GET | `/api/v1/users/role/{role}` | Get users by role (admin) |
| GET | `/api/v1/users/{user_id}/audit-logs` | Get user audit logs |

### System Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | API information |
| GET | `/health` | Health check |
| GET | `/docs` | API documentation (dev only) |

## 🔐 Authentication Flow

### 1. User Registration
```bash
curl -X POST "http://localhost:8003/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "StrongPass123",
    "full_name": "John Doe",
    "role": "user"
  }'
```

### 2. User Login
```bash
curl -X POST "http://localhost:8003/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "StrongPass123"
  }'
```

Response:
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": {
    "id": 1,
    "email": "user@example.com",
    "full_name": "John Doe",
    "role": "user",
    "is_active": true,
    "created_at": "2024-01-01T00:00:00Z"
  }
}
```

### 3. Authenticated Requests
```bash
curl -X GET "http://localhost:8003/api/v1/auth/me" \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc..."
```

### 4. Token Refresh
```bash
curl -X POST "http://localhost:8003/api/v1/auth/refresh" \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
  }'
```

## 🗄 Database Schema

### Users Table
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR UNIQUE NOT NULL,
    hashed_password VARCHAR NOT NULL,
    full_name VARCHAR,
    role VARCHAR,
    is_active BOOLEAN DEFAULT TRUE,
    is_superuser BOOLEAN DEFAULT FALSE,
    last_login TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);
```

### User Sessions Table
```sql
CREATE TABLE user_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    token_hash VARCHAR UNIQUE NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### Audit Logs Table
```sql
CREATE TABLE audit_logs (
    id SERIAL PRIMARY KEY,
    entity_type VARCHAR NOT NULL,
    entity_id INTEGER NOT NULL,
    action VARCHAR NOT NULL,
    user_id INTEGER,
    user_role VARCHAR,
    ip_address VARCHAR,
    details JSON,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

## 🔧 Configuration

### Security Settings
- **Password Requirements**: Configurable complexity rules
- **Token Expiration**: Separate settings for access and refresh tokens
- **Rate Limiting**: Per-IP request limits
- **Session Management**: Maximum sessions per user

### CORS Configuration
- **Allowed Origins**: Configurable list of trusted domains
- **Credentials**: Support for cookie-based authentication
- **Methods**: Restricted to necessary HTTP methods

### Logging & Monitoring
- **Structured Logging**: JSON format for log aggregation
- **Audit Trails**: Comprehensive action logging
- **Health Checks**: Database connectivity monitoring
- **Performance Metrics**: Request timing and rate limiting

## 🧪 Testing

### Run Unit Tests
```bash
cd backend/auth_service
python -m pytest tests/ -v
```

### Run Basic Validation
```bash
python tests/test_auth_redesign.py
```

### Test Coverage
The test suite covers:
- Password validation
- JWT token creation/verification
- Password hashing
- Schema validation
- Repository operations (mocked)
- Error handling

## 🚀 Deployment

### Production Environment
- Use environment variables for all secrets
- Enable HTTPS/TLS termination at load balancer
- Configure database connection pooling
- Set up log aggregation (ELK stack, etc.)
- Monitor health check endpoints
- Configure backup strategy for user data

### Docker Compose Example
```yaml
version: '3.8'
services:
  auth-service:
    build: .
    ports:
      - "8003:8003"
    environment:
      - DATABASE_URL=postgresql+asyncpg://user:pass@postgres:5432/auth_db
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
      - ENVIRONMENT=production
    depends_on:
      - postgres
    
  postgres:
    image: postgres:15
    environment:
      - POSTGRES_DB=auth_db
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

## 🔍 Monitoring & Maintenance

### Health Monitoring
- `/health` endpoint returns service status
- Database connectivity checks
- Log analysis for error patterns
- Rate limiting effectiveness

### Session Management
- Automatic cleanup of expired sessions
- Monitor session creation patterns
- Alert on unusual login patterns
- Regular audit log analysis

### Security Maintenance
- Regular password policy reviews
- JWT secret rotation procedures
- Failed login attempt monitoring
- Audit log retention policies

## 📝 Migration from Old Service

The redesigned service maintains backward compatibility with the old `/verify-token` endpoint while providing enhanced features through the new API structure.

### Key Improvements
1. **Enhanced Security**: Refresh token rotation, better password policies
2. **Comprehensive Audit**: Detailed logging of all actions
3. **Better Error Handling**: Structured error responses
4. **Production Ready**: Proper middleware, health checks, monitoring
5. **Scalable Architecture**: Repository pattern, dependency injection

For questions or support, please refer to the API documentation at `/docs` (development mode) or contact the development team.