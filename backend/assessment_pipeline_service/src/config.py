"""
Configuration management for Assessment Pipeline Service
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # Service Configuration
    environment: str = "development"
    service_name: str = "assessment_pipeline_service"
    service_version: str = "2.0.0"
    
    # External Service URLs
    auth_service_url: str = "http://localhost:8003"
    special_ed_service_url: str = "http://localhost:8005"
    
    # Redis Configuration
    redis_url: str = "redis://localhost:6379/0"
    
    # GCP Configuration
    gcp_project_id: Optional[str] = None
    gcp_region: str = "us-central1"
    gcs_bucket_name: Optional[str] = None
    google_application_credentials: Optional[str] = None
    
    # Document AI Configuration
    document_ai_project_id: Optional[str] = None
    document_ai_processor_id: Optional[str] = None
    document_ai_location: str = "us"
    
    # JWT Configuration
    jwt_secret_key: str = "development-secret-key"
    
    # Circuit Breaker Configuration
    circuit_breaker_failure_threshold: int = 5
    circuit_breaker_recovery_timeout: int = 60
    circuit_breaker_expected_exception: tuple = (Exception,)
    
    # Service Communication Timeouts
    default_request_timeout: int = 30
    auth_request_timeout: int = 10
    
    # Retry Configuration
    max_retries: int = 3
    retry_backoff_factor: float = 1.0
    retry_statuses: list = [500, 502, 503, 504]
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# Global settings instance
settings = Settings()

def get_settings() -> Settings:
    """Get application settings"""
    return settings