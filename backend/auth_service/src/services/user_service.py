from typing import Optional, Dict, List
from uuid import UUID
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
import secrets
import hashlib
from passlib.context import CryptContext

from ..repositories.user_repository import UserRepository
from common.src.config import get_settings
from ..models.user import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class UserService:
    def __init__(self, repository: UserRepository):
        self.repository = repository
        self.settings = get_settings()
        self.SECRET_KEY = self.settings.jwt_secret_key or secrets.token_urlsafe(32)
        self.ALGORITHM = "HS256"
        self.ACCESS_TOKEN_EXPIRE_HOURS = 24
    
    async def create_user(
        self, 
        email: str, 
        password: str,
        full_name: str, 
        role: str,
        created_by: Optional[UUID] = None
    ) -> Dict:
        """Create new user with hashed password"""
        # Validate creator permissions
        if created_by:
            creator = await self.repository.get_user(created_by)
            if creator['role'] not in ['coordinator', 'admin']:
                raise PermissionError("Only coordinators and admins can create users")
        
        # Check if user exists
        existing_user = await self.repository.get_by_email(email)
        if existing_user:
            raise ValueError("User with this email already exists")
        
        # Create new user
        hashed_password = pwd_context.hash(password)
        user = User(
            email=email,
            hashed_password=hashed_password,
            full_name=full_name,
            role=role
        )
        
        created_user = await self.repository.create(user)
        return {
            "id": created_user.id,
            "email": created_user.email,
            "full_name": created_user.full_name,
            "role": created_user.role
        }
    
    async def authenticate_user(self, email: str, password: str) -> Optional[Dict]:
        """Authenticate user and create session"""
        user = await self.repository.get_by_email(email)
        if not user or not user.hashed_password:
            return None
        
        if not pwd_context.verify(password, user.hashed_password):
            return None
        
        # Create access token
        access_token = self.create_access_token(
            data={"sub": user.email, "role": user.role}
        )
        
        # Store session
        token_hash = hashlib.sha256(access_token.encode()).hexdigest()
        await self.repository.create_session(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=self.ACCESS_TOKEN_EXPIRE_HOURS)
        )
        
        # Update last login
        await self.repository.update_last_login(user.id)
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role
            }
        }
    
    def create_access_token(self, data: dict) -> str:
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + timedelta(minutes=self.ACCESS_TOKEN_EXPIRE_HOURS)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM)
        return encoded_jwt
    
    async def verify_token(self, token: str) -> Optional[Dict]:
        """Verify JWT token and return user data"""
        try:
            payload = jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            email: str = payload.get("sub")
            if email is None:
                return None
            
            user = await self.repository.get_by_email(email)
            if user is None:
                return None
            
            return {
                "id": user.id,
                "email": user.email,
                "role": user.role
            }
        except JWTError:
            return None
    
    async def get_users_by_role(self, role: str) -> List[Dict]:
        """Get all active users with a specific role"""
        return await self.repository.get_users_by_role(role)
    
    def get_role_hierarchy(self) -> Dict[str, int]:
        """Define role hierarchy for permissions"""
        return {
            "teacher": 1,
            "co_coordinator": 2,
            "coordinator": 3,
            "admin": 4
        }
    
    def can_perform_action(self, user_role: str, required_role: str) -> bool:
        """Check if user role can perform action requiring specific role"""
        hierarchy = self.get_role_hierarchy()
        return hierarchy.get(user_role, 0) >= hierarchy.get(required_role, 0)
