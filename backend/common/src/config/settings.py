"""Centralized configuration using Pydantic v2"""
from typing import Optional
from functools import lru_cache
from pydantic import Field
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
    
    # GCP Configuration
    gcp_project_id: str = Field(default="")
    gcp_region: str = Field(default="us-central1")
    
    # Service Configuration
    mcp_server_port: int = Field(default=8001)
    adk_host_port: int = Field(default=8002)
    mcp_server_url: str = Field(default="http://localhost:8001")
    adk_host_api_url: str = Field(default="http://localhost:8002")
    
    # Model Configuration
    embedding_model: str = Field(default="text-embedding-004")
    gemini_model: str = Field(env="GEMINI_MODEL")
    gemini_temperature: float = Field(default=0.4, ge=0.0, le=2.0)
    gemini_max_tokens: int = Field(default=65536, ge=1, le=65536)
    
    # Redis Configuration
    redis_url: str = Field(default="redis://localhost:6379/0")
    cache_ttl_embeddings: int = Field(default=86400)
    cache_ttl_queries: int = Field(default=3600)
    
    # Security Configuration
    max_query_length: int = Field(default=1000, ge=1, le=5000)
    rate_limit_requests: int = Field(default=30, ge=1)
    rate_limit_window: int = Field(default=60, ge=1)
    
    @property
    def is_production(self) -> bool:
        return self.environment == "production"
    
    @property
    def is_development(self) -> bool:
        return self.environment == "development"

@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings() 