import bcrypt
from typing import Optional, Dict, List
from uuid import UUID
from datetime import datetime, timedelta
from jose import jwt, JWTError
import secrets
import hashlib

from ..repositories.user_repository import UserRepository
from common.src.config import get_settings

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
        
        # Hash password
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        # Create user
        user = await self.repository.create_user({
            "email": email,
            "password_hash": password_hash.decode('utf-8'),
            "full_name": full_name,
            "role": role
        })
        
        # Remove password hash from response
        user.pop('password_hash', None)
        return user
    
    async def authenticate_user(self, email: str, password: str) -> Optional[Dict]:
        """Authenticate user and create session"""
        user = await self.repository.get_user_by_email(email)
        if not user or not user.get('is_active', True):
            return None
        
        # Verify password
        if not bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8')):
            return None
        
        # Create JWT token
        token_data = {
            "user_id": str(user['id']),
            "email": user['email'],
            "role": user['role'],
            "exp": datetime.utcnow() + timedelta(hours=self.ACCESS_TOKEN_EXPIRE_HOURS)
        }
        access_token = jwt.encode(token_data, self.SECRET_KEY, algorithm=self.ALGORITHM)
        
        # Store session
        token_hash = hashlib.sha256(access_token.encode()).hexdigest()
        await self.repository.create_session(
            user_id=user['id'],
            token_hash=token_hash,
            expires_at=datetime.utcnow() + timedelta(hours=self.ACCESS_TOKEN_EXPIRE_HOURS)
        )
        
        # Update last login
        await self.repository.update_last_login(user['id'])
        
        return {
            "user": {k: v for k, v in user.items() if k != 'password_hash'},
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": self.ACCESS_TOKEN_EXPIRE_HOURS * 3600
        }
    
    async def verify_token(self, token: str) -> Optional[Dict]:
        """Verify JWT token and return user data"""
        try:
            # Decode token
            payload = jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            
            # Check if session exists and is valid
            token_hash = hashlib.sha256(token.encode()).hexdigest()
            session = await self.repository.get_session_by_token_hash(token_hash)
            
            if not session or session['expires_at'] < datetime.utcnow():
                return None
            
            # Get user
            user = await self.repository.get_user(UUID(payload['user_id']))
            if not user or not user.get('is_active', True):
                return None
            
            return {k: v for k, v in user.items() if k != 'password_hash'}
            
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
