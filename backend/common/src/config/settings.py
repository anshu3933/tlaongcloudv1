"""Centralized configuration using Pydantic v2"""
from typing import Optional, List, Union
from functools import lru_cache
import sys
import json
from pydantic import Field, EmailStr, field_validator, model_validator
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
    gemini_max_tokens: int = Field(default=8192, ge=1, le=8192)
    
    # Cache Configuration
    cache_ttl_embeddings: int = Field(default=86400)
    cache_ttl_queries: int = Field(default=3600)
    
    # Security Configuration
    max_query_length: int = Field(default=1000, ge=1, le=5000)
    rate_limit_requests: int = Field(default=30, ge=1)
    rate_limit_window: int = Field(default=60, ge=1)
    
    # CORS Configuration
    cors_origins: Union[str, List[str]] = Field(
        default="http://localhost:3000,http://localhost:3001,http://localhost:3002",
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
    
    # Email Configuration
    smtp_enabled: bool = Field(default=False)
    smtp_host: str = Field(default="smtp.gmail.com")
    smtp_port: int = Field(default=587)
    smtp_username: Optional[str] = Field(default=None)
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
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Get CORS origins as list"""
        return self.cors_origins if isinstance(self.cors_origins, list) else self.cors_origins
    
    @property
    def cors_methods_list(self) -> List[str]:
        """Get CORS methods as list"""
        return self.cors_allow_methods if isinstance(self.cors_allow_methods, list) else self.cors_allow_methods
    
    @property
    def cors_headers_list(self) -> List[str]:
        """Get CORS headers as list"""
        return self.cors_allow_headers if isinstance(self.cors_allow_headers, list) else self.cors_allow_headers
    
    @field_validator('environment')
    @classmethod
    def validate_environment(cls, v):
        """Validate environment is one of allowed values"""
        allowed = ['development', 'staging', 'production', 'testing']
        if v not in allowed:
            raise ValueError(f'Environment must be one of: {allowed}')
        return v
    
    @field_validator('log_level')
    @classmethod
    def validate_log_level(cls, v):
        """Validate log level is valid"""
        allowed = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in allowed:
            raise ValueError(f'Log level must be one of: {allowed}')
        return v.upper()
    
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
    
    @model_validator(mode='after')
    def validate_production_requirements(self):
        """Validate required settings for production environment"""
        if self.environment == 'production':
            # Check critical production requirements
            if self.jwt_secret_key == 'your-super-secure-jwt-secret-key-change-this-in-production':
                raise ValueError('JWT_SECRET_KEY must be changed from default value in production')
            
            if len(self.jwt_secret_key) < 32:
                raise ValueError('JWT_SECRET_KEY must be at least 32 characters in production')
            
            if self.gcp_project_id in ['test-project', 'your-gcp-project-id']:
                raise ValueError('GCP_PROJECT_ID must be set to actual project ID in production')
            
            if self.gcs_bucket_name in ['test-bucket', 'your-special-education-documents-bucket']:
                raise ValueError('GCS_BUCKET_NAME must be set to actual bucket name in production')
        
        return self
    
    def validate_critical_env_vars(self) -> List[str]:
        """Check for missing critical environment variables"""
        missing = []
        critical_vars = [
            ('DATABASE_URL', self.database_url),
            ('JWT_SECRET_KEY', self.jwt_secret_key),
            ('GCP_PROJECT_ID', self.gcp_project_id),
            ('GCS_BUCKET_NAME', self.gcs_bucket_name),
            ('GEMINI_MODEL', self.gemini_model)
        ]
        
        for var_name, var_value in critical_vars:
            if not var_value or var_value in ['', 'None', 'null']:
                missing.append(var_name)
        
        return missing

def validate_environment() -> None:
    """Validate environment configuration on startup"""
    try:
        settings = Settings()
        missing_vars = settings.validate_critical_env_vars()
        
        if missing_vars:
            print(f"❌ CRITICAL: Missing required environment variables: {', '.join(missing_vars)}")
            print("💡 Please check your .env file and ensure all required variables are set.")
            print("📖 See .env.example for reference.")
            sys.exit(1)
        
        if settings.environment == 'production':
            print("✅ Production environment validation passed")
        else:
            print(f"✅ {settings.environment.title()} environment loaded successfully")
            
    except Exception as e:
        print(f"❌ Environment validation failed: {e}")
        print("💡 Please check your .env file configuration.")
        sys.exit(1)

@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings() 