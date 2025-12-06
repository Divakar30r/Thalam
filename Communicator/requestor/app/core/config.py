# Requestor-specific configuration

from shared.config import BaseConfig
from pydantic import Field

class RequestorConfig(BaseConfig):
    """Requestor service configuration"""
    
    # FastAPI specific settings
    service_name: str = Field(
        default="requestor",
        env="SERVICE_NAME",
        description="Service name"
    )
    
    fastapi_port: int = Field(
        default=8004,
        env="FASTAPI_PORT",
        description="FastAPI server port"
    )
    
    # gRPC Client settings
    processor_grpc_host: str = Field(
        default="localhost",
        env="PROCESSOR_GRPC_HOST",
        description="Processor gRPC server host"
    )
    
    processor_grpc_port: int = Field(
        default=50051,
        env="PROCESSOR_GRPC_PORT", 
        description="Processor gRPC server port"
    )
    
    # Request timeouts
    grpc_request_timeout: int = Field(
        default=600,
        env="GRPC_REQUEST_TIMEOUT",
        description="gRPC request timeout in seconds"
    )
    
    # Streaming settings
    max_streaming_connections: int = Field(
        default=5,
        env="MAX_STREAMING_CONNECTIONS",
        description="Maximum concurrent streaming connections"
    )
    
    streaming_reconnect_delay: int = Field(
        default=5,
        env="STREAMING_RECONNECT_DELAY",
        description="Delay before reconnecting streaming client in seconds"
    )
    
    class Config:
        env_file = ".env.local"