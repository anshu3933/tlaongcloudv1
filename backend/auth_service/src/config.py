"""Configuration settings for the Authentication Service."""

from typing import List
from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class AuthSettings(BaseSettings):
    """Authentication service specific settings."""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        env_prefix="AUTH_"
    )
    
    # Database
    database_url: str = Field(env="DATABASE_URL")
    
    # JWT Configuration
    jwt_secret_key: str = Field(env="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256")
    access_token_expire_minutes: int = Field(default=60)
    refresh_token_expire_days: int = Field(default=7)
    
    # CORS Settings
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        env="CORS_ORIGINS"
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
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins from string if needed."""
        if isinstance(self.cors_origins, str):
            return [origin.strip() for origin in self.cors_origins.split(",")]
        return self.cors_origins
    
    @property
    def is_production(self) -> bool:
        """Check if environment is production."""
        return self.environment == "production"

@lru_cache()
def get_auth_settings() -> AuthSettings:
    """Get cached authentication settings instance."""
    return AuthSettings()