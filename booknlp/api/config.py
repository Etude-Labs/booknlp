"""Production configuration for BookNLP API."""

from enum import Enum
from functools import lru_cache
from typing import Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class Environment(str, Enum):
    """Application environment."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Application
    app_name: str = "BookNLP API"
    app_version: str = "0.2.0"
    environment: Environment = Environment.DEVELOPMENT
    debug: bool = False
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 1  # GPU constraint - single worker
    
    # Authentication
    auth_required: bool = False
    api_key: Optional[str] = None
    
    # CORS
    cors_origins: list[str] = ["*"]
    cors_allow_credentials: bool = True
    cors_allow_methods: list[str] = ["*"]
    cors_allow_headers: list[str] = ["*"]
    
    # Rate Limiting
    rate_limit_enabled: bool = False
    rate_limit_default: str = "60/minute"
    rate_limit_analyze: str = "10/minute"
    rate_limit_jobs: str = "10/minute"
    
    # Job Queue
    max_queue_size: int = 10
    job_ttl_seconds: int = 3600
    shutdown_grace_period: float = 30.0
    
    # Model
    default_model: str = "small"
    available_models: list[str] = ["small", "big"]
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "json"  # "json" or "console"
    log_include_timestamp: bool = True
    
    # Metrics
    metrics_enabled: bool = True
    metrics_path: str = "/metrics"
    
    # Request tracing
    request_id_header: str = "X-Request-ID"
    
    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse comma-separated CORS origins from environment."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    @field_validator("available_models", mode="before")
    @classmethod
    def parse_available_models(cls, v):
        """Parse comma-separated model list from environment."""
        if isinstance(v, str):
            return [model.strip() for model in v.split(",")]
        return v
    
    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.environment == Environment.PRODUCTION
    
    @property
    def is_development(self) -> bool:
        """Check if running in development."""
        return self.environment == Environment.DEVELOPMENT
    
    model_config = {
        "env_prefix": "BOOKNLP_",
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
    }


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance.
    
    Returns:
        Singleton Settings instance.
    """
    return Settings()
