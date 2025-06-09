"""Centralized configuration using Pydantic v2"""
from typing import Optional
from functools import lru_cache
from pydantic import Field, EmailStr
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """Application settings with validation"""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Environment
    environment: str = Field(default="development")
    log_level: str = Field(default="INFO")
    
    # Database
    database_url: str = Field(env="DATABASE_URL")
    redis_url: str = Field(default="redis://localhost:6379/0")
    
    # JWT
    jwt_secret_key: str = Field(env="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256")
    jwt_access_token_expire_minutes: int = Field(default=30)
    
    # GCP Configuration
    gcp_project_id: str = Field(env="GCP_PROJECT_ID")
    gcp_region: str = Field(default="us-central1")
    gcs_bucket_name: str = Field(env="GCS_BUCKET_NAME")
    
    # Vector Search
    vector_search_index_id: Optional[str] = Field(default=None)
    vector_search_endpoint_id: Optional[str] = Field(default=None)
    vector_search_deployed_index_id: Optional[str] = Field(default=None)
    
    # Service Configuration
    mcp_server_port: int = Field(default=8001)
    adk_host_port: int = Field(default=8002)
    auth_service_port: int = Field(default=8003)
    workflow_service_port: int = Field(default=8004)
    special_ed_service_port: int = Field(default=8005)
    
    # Service URLs
    mcp_server_url: str = Field(default="http://localhost:8001")
    adk_host_api_url: str = Field(default="http://localhost:8002")
    auth_service_url: str = Field(default="http://localhost:8003")
    workflow_service_url: str = Field(default="http://localhost:8004")
    special_ed_service_url: str = Field(default="http://localhost:8005")
    
    # Model Configuration
    embedding_model: str = Field(default="text-embedding-004")
    gemini_model: str = Field(env="GEMINI_MODEL")
    gemini_temperature: float = Field(default=0.4, ge=0.0, le=2.0)
    gemini_max_tokens: int = Field(default=65536, ge=1, le=65536)
    
    # Cache Configuration
    cache_ttl_embeddings: int = Field(default=86400)
    cache_ttl_queries: int = Field(default=3600)
    
    # Security Configuration
    max_query_length: int = Field(default=1000, ge=1, le=5000)
    rate_limit_requests: int = Field(default=30, ge=1)
    rate_limit_window: int = Field(default=60, ge=1)
    
    # Email Configuration
    smtp_enabled: bool = Field(default=False)
    smtp_host: str = Field(default="smtp.gmail.com")
    smtp_port: int = Field(default=587)
    smtp_username: EmailStr = Field(default="")
    smtp_password: str = Field(default="")
    smtp_from_email: EmailStr = Field(default="noreply@special-ed-system.com")
    
    @property
    def is_production(self) -> bool:
        return self.environment == "production"
    
    @property
    def is_development(self) -> bool:
        return self.environment == "development"
    
    @property
    def is_testing(self) -> bool:
        return self.environment == "testing"

@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings() 