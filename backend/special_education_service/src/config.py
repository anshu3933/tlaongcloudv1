"""Configuration settings for the Special Education Service"""
import os
from typing import Optional
from pydantic import BaseModel


class Settings(BaseModel):
    """Application settings"""
    # Database configuration
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./test_special_ed.db")
    
    # Environment
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    
    # JWT Configuration
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "your-secret-key-here")
    
    # GCP Configuration
    GCP_PROJECT_ID: str = os.getenv("GCP_PROJECT_ID", "thela002")
    GCS_BUCKET_NAME: str = os.getenv("GCS_BUCKET_NAME", "betrag-data-test-a")
    GCP_REGION: str = os.getenv("GCP_REGION", "us-central1")
    
    # AI Configuration
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-1.5-pro")
    GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY")
    
    # Email Configuration
    SMTP_ENABLED: bool = os.getenv("SMTP_ENABLED", "false").lower() == "true"
    SMTP_HOST: Optional[str] = os.getenv("SMTP_HOST")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER: Optional[str] = os.getenv("SMTP_USER")
    SMTP_PASSWORD: Optional[str] = os.getenv("SMTP_PASSWORD")
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Features
    ENABLE_FLATTENER: bool = os.getenv("ENABLE_FLATTENER", "true").lower() == "true"
    FLATTENER_DETAILED_LOGGING: bool = os.getenv("FLATTENER_DETAILED_LOGGING", "false").lower() == "true"
    
    # Computed properties
    @property
    def is_development(self) -> bool:
        """Check if running in development mode"""
        return self.ENVIRONMENT.lower() == "development"
    
    @property
    def database_url(self) -> str:
        """Get database URL"""
        return self.DATABASE_URL
    
    @property
    def gcp_project_id(self) -> str:
        """Get GCP project ID"""
        return self.GCP_PROJECT_ID
    
    @property
    def gcp_region(self) -> str:
        """Get GCP region"""
        return self.GCP_REGION
    
    @property
    def gemini_model(self) -> str:
        """Get Gemini model"""
        return self.GEMINI_MODEL


# Global settings instance
_settings = None


def get_settings() -> Settings:
    """Get settings instance (singleton)"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings