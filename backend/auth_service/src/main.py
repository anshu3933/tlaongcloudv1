from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from typing import Optional
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from .services.user_service import UserService
from .services.audit_service import AuditService
from .repositories.user_repository import UserRepository
from .repositories.audit_repository import AuditRepository
from common.src.config import get_settings

settings = get_settings()

# Database setup
DATABASE_URL = settings.database_url
engine = create_async_engine(DATABASE_URL)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# Global instances
user_service: Optional[UserService] = None
audit_service: Optional[AuditService] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize services on startup"""
    global user_service, audit_service
    
    # Create database tables
    async with engine.begin() as conn:
        from .models.user import Base as UserBase
        from .models.audit_log import Base as AuditBase
        await conn.run_sync(UserBase.metadata.create_all)
        await conn.run_sync(AuditBase.metadata.create_all)
    
    # Initialize repositories
    async with async_session() as session:
        user_repo = UserRepository(session)
        audit_repo = AuditRepository(session)
        
        # Initialize services
        user_service = UserService(user_repo)
        audit_service = AuditService(audit_repo)
    
    print("Auth service initialized")
    yield
    print("Auth service shutting down")

app = FastAPI(
    title="Authentication Service",
    version="1.0.0",
    lifespan=lifespan
)

# Request/Response models
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class TokenVerify(BaseModel):
    token: str

# Endpoints
@app.post("/api/v1/auth/register")
async def register_user(
    user_data: UserCreate,
    request: Request
):
    """Register new user (admin/coordinator only)"""
    # In production, add authentication check here
    try:
        user = await user_service.create_user(
            email=user_data.email,
            password=user_data.password,
            full_name=user_data.full_name,
            role=user_data.role
        )
        
        # Log registration
        await audit_service.log_action(
            entity_type="user",
            entity_id=user['id'],
            action="user_registered",
            user_id=user['id'],  # Self-registration for initial admin
            user_role=user['role'],
            ip_address=request.client.host
        )
        
        return {"user": user, "message": "User registered successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/v1/auth/login")
async def login(
    credentials: UserLogin,
    request: Request
):
    """Login and receive access token"""
    result = await user_service.authenticate_user(
        email=credentials.email,
        password=credentials.password
    )
    
    if not result:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Log login
    await audit_service.log_action(
        entity_type="user",
        entity_id=result['user']['id'],
        action="user_login",
        user_id=result['user']['id'],
        user_role=result['user']['role'],
        ip_address=request.client.host
    )
    
    return result

@app.post("/verify-token")
async def verify_token(token_data: TokenVerify):
    """Verify JWT token - used by other services"""
    user = await user_service.verify_token(token_data.token)
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    return user

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "auth-service",
        "version": "1.0.0"
    }
