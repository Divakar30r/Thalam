"""
Configuration settings and environment variables for the FastAPI application
"""

import os
from typing import List
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings"""
    
    # Application settings
    app_name: str = "dCent CP Order Management API"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # Server settings
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = False
    api_prefix: str = "/api/v1"  # Set to "" to disable prefix in production
    
    # Database settings
    mongodb_url: str = "mongodb://localhost:27017"
    database_name: str = "CP_OrderManagement"
    min_pool_size: int = 10
    max_pool_size: int = 100
    max_idle_time_ms: int = 30000

    # CORS settings - Updated for drapps.dev domain
    cors_origins: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000", 
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "https://drapps.dev",
        "https://www.drapps.dev",
        "https://*.drapps.dev"
    ]
    cors_credentials: bool = True
    cors_methods: List[str] = ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH", "HEAD"]
    cors_headers: List[str] = ["*"]
    
    # Logging settings
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Validation settings
    email_domain: str = "@drworkplace.microsoft.com"
    role_id_patterns: dict = {
        "Admin": "ADM-{:04d}",
        "Manager": "MGR-{:04d}",
        "Operator": "OPR-{:04d}",
        "TerminalOwner": "TOW-{:04d}"
    }
    
    # Pagination settings
    default_page_size: int = 20
    max_page_size: int = 100
    
    @field_validator('debug', mode='before')
    @classmethod
    def parse_debug(cls, v):
        if isinstance(v, str):
            return v.lower() in ['true', '1', 'yes', 'on']
        return bool(v)
    
    @field_validator('cors_origins', mode='before')
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(',')]
        return v
    
    @field_validator('cors_methods', mode='before')
    @classmethod
    def parse_cors_methods(cls, v):
        if isinstance(v, str):
            return [method.strip() for method in v.split(',')]
        return v
    
    @field_validator('cors_headers', mode='before')
    @classmethod
    def parse_cors_headers(cls, v):
        if isinstance(v, str):
            return [header.strip() for header in v.split(',')]
        return v
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


# Environment-specific configurations
class DevelopmentSettings(Settings):
    """Development environment settings"""
    debug: bool = True
    reload: bool = True
    log_level: str = "DEBUG"


class ProductionSettings(Settings):
    """Production environment settings"""
    debug: bool = False
    reload: bool = False
    log_level: str = "INFO"
    cors_origins: List[str] = [
        "https://drapps.dev",
        "https://www.drapps.dev",
        "https://*.drapps.dev"
    ]


class TestingSettings(Settings):
    """Testing environment settings"""
    database_name: str = "CP_OrderManagement_Test"
    mongodb_url: str = "mongodb://localhost:27017"


def get_environment_settings():
    """Get settings based on environment"""
    env = os.getenv("ENVIRONMENT", "development").lower()
    
    if env == "production":
        return ProductionSettings()
    elif env == "testing":
        return TestingSettings()
    else:
        return DevelopmentSettings()


# Export the settings instance
settings = get_environment_settings()