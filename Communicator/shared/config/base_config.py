# Base Configuration using Pydantic Settings

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List, Optional
import os

class BaseConfig(BaseSettings):
    """Base configuration class"""
    
    # API URLs
    api_base_url: str = Field(
        default="http://localhost:8001",
        env="API_BASE_URL",
        description="Base URL for main API"
    )
    
    api_google_bot_url: str = Field(
        default="http://localhost:8006",
        env="API_GOOGLE_BOT_URL", 
        description="Google Bot API URL"
    )
    
    api_google_chat_url: str = Field(
        default="http://localhost:8007",
        env="API_GOOGLE_CHAT_URL",
        description="Google Chat API URL"
    )
    
    # Kafka/MSK Configuration
    kafka_bootstrap_servers: List[str] = Field(
        default=["localhost:9092"],
        env="KAFKA_BOOTSTRAP_SERVERS",
        description="Kafka bootstrap servers"
    )
    
    # HTTP Settings
    http_timeout: int = Field(
        default=30,
        env="HTTP_TIMEOUT",
        description="HTTP request timeout in seconds"
    )
    
    # gRPC Settings
    grpc_server_port: int = Field(
        default=50051,
        env="GRPC_SERVER_PORT",
        description="gRPC server port"
    )
    
    grpc_max_workers: int = Field(
        default=10,
        env="GRPC_MAX_WORKERS",
        description="Maximum gRPC worker threads"
    )
    
    # Queue Settings
    max_concurrent_tasks: int = Field(
        default=10,
        env="MAX_CONCURRENT_TASKS",
        description="Maximum concurrent gRPC tasks"
    )
    
    order_expiry_minutes: int = Field(
        default=30,
        env="ORDER_EXPIRY_MINUTES",
        description="Order expiry time in minutes"
    )
    
    # Seller Selection
    find_max_sellers: int = Field(
        default=3,
        env="FIND_MAX_SEL",
        description="Maximum number of sellers to find"
    )
    
    # Logging
    log_level: str = Field(
        default="INFO",
        env="LOG_LEVEL",
        description="Logging level"
    )
    
    log_format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        env="LOG_FORMAT",
        description="Log message format"
    )
    
    # FastAPI Settings
    debug_mode: bool = Field(
        default=False,
        env="DEBUG_MODE",
        description="Enable debug mode"
    )
    
    cors_origins: List[str] = Field(
        default=["*"],
        env="CORS_ORIGINS",
        description="CORS allowed origins"
    )
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# Global settings instance
_settings: Optional[BaseConfig] = None

def get_settings() -> BaseConfig:
    """Get global settings instance"""
    global _settings
    if _settings is None:
        _settings = BaseConfig()
    return _settings

def reload_settings():
    """Reload settings from environment"""
    global _settings
    _settings = BaseConfig()