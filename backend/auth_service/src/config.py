"""Configuration settings for the Authentication Service."""

from typing import List, Union
from functools import lru_cache
import json
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class AuthSettings(BaseSettings):
    """Authentication service specific settings."""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Environment
    environment: str = Field(default="development", env="ENVIRONMENT")
    
    # Database
    database_url: str = Field(env="DATABASE_URL")
    
    # JWT Configuration
    jwt_secret_key: str = Field(env="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256")
    access_token_expire_minutes: int = Field(default=60)
    refresh_token_expire_days: int = Field(default=7)
    
    # CORS Settings
    cors_origins: Union[str, List[str]] = Field(
        default="http://localhost:3000,http://localhost:8000",
        env="CORS_ORIGINS"
    )
    cors_allow_credentials: bool = Field(default=True, env="CORS_ALLOW_CREDENTIALS")
    cors_allow_methods: Union[str, List[str]] = Field(
        default="GET,POST,PUT,DELETE,PATCH,OPTIONS",
        env="CORS_ALLOW_METHODS"
    )
    cors_allow_headers: Union[str, List[str]] = Field(
        default="*",
        env="CORS_ALLOW_HEADERS"
    )
    
    # Rate Limiting
    rate_limit_requests: int = Field(default=30)
    rate_limit_period: int = Field(default=60)
    
    # Logging
    log_level: str = Field(default="INFO")
    
    # Security
    password_min_length: int = Field(default=8)
    password_require_uppercase: bool = Field(default=True)
    password_require_lowercase: bool = Field(default=True)
    password_require_digits: bool = Field(default=True)
    password_require_special_chars: bool = Field(default=False)
    
    # Session Management
    max_sessions_per_user: int = Field(default=5)
    session_cleanup_interval_hours: int = Field(default=24)
    
    @field_validator('cors_origins', mode='before')
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS origins from various formats"""
        if isinstance(v, str):
            # Try to parse as JSON array first
            if v.strip().startswith('[') and v.strip().endswith(']'):
                try:
                    return json.loads(v)
                except json.JSONDecodeError:
                    pass
            # Parse as comma-separated string
            return [origin.strip() for origin in v.split(',') if origin.strip()]
        elif isinstance(v, list):
            return v
        else:
            return [str(v)]
    
    @field_validator('cors_allow_methods', mode='before')
    @classmethod
    def parse_cors_methods(cls, v):
        """Parse CORS methods from string or list"""
        if isinstance(v, str):
            return [method.strip().upper() for method in v.split(',') if method.strip()]
        elif isinstance(v, list):
            return [method.upper() for method in v]
        return [str(v).upper()]
    
    @field_validator('cors_allow_headers', mode='before')
    @classmethod
    def parse_cors_headers(cls, v):
        """Parse CORS headers from string or list"""
        if isinstance(v, str):
            if v.strip() == '*':
                return ['*']
            return [header.strip() for header in v.split(',') if header.strip()]
        elif isinstance(v, list):
            return v
        return [str(v)]
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Get CORS origins as list (backward compatibility)"""
        return self.cors_origins if isinstance(self.cors_origins, list) else self.cors_origins
    
    @property
    def cors_methods_list(self) -> List[str]:
        """Get CORS methods as list"""
        return self.cors_allow_methods if isinstance(self.cors_allow_methods, list) else self.cors_allow_methods
    
    @property
    def cors_headers_list(self) -> List[str]:
        """Get CORS headers as list"""
        return self.cors_allow_headers if isinstance(self.cors_allow_headers, list) else self.cors_allow_headers
    
    @property
    def is_production(self) -> bool:
        """Check if environment is production."""
        return self.environment == "production"

@lru_cache()
def get_auth_settings() -> AuthSettings:
    """Get cached authentication settings instance."""
    return AuthSettings()