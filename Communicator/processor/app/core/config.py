from pydantic_settings import BaseSettings
from typing import Optional
import os
from pathlib import Path

# Get the processor directory (where .env.local should be)
PROCESSOR_DIR = Path(__file__).parent.parent.parent

class ProcessorSettings(BaseSettings):
    # API Configuration
    api_base_url: str = os.getenv("API_BASE_URL", "http://localhost:8001")
    api_google_chat_url: str = os.getenv("API_GOOGLE_CHAT_URL", "http://localhost:8006")
    api_google_bot_url: str = os.getenv("API_GOOGLE_BOT_URL", "http://localhost:8007")
    
    # gRPC Configuration
    # Default to all interfaces (0.0.0.0) to avoid binding issues on Windows
    # and to support Docker/container deployments. The server_manager has
    # fallback logic (tries 127.0.0.1, ::1, :: if 0.0.0.0 fails).
    # Override with GRPC_SERVER_HOST=127.0.0.1 for local-only binding.
    grpc_server_host: str = os.getenv("GRPC_SERVER_HOST", "0.0.0.0")
    grpc_server_port: int = int(os.getenv("GRPC_SERVER_PORT", "50051"))
    grpc_verbosity: str = os.getenv("GRPC_VERBOSITY", "debug")
    
    # FastAPI Configuration
    fastapi_host: str = os.getenv("FASTAPI_HOST", "localhost")
    fastapi_port: int = int(os.getenv("FASTAPI_PORT", "8005"))
    
    # Business Logic Configuration
    find_max_sellers: int = int(os.getenv("FIND_MAX_SEL", "3"))
    order_expiry_minutes: int = int(os.getenv("ORDER_EXPIRY_MINUTES", "30"))
    
    # AWS MSK Configuration
    aws_msk_bootstrap_servers: str = os.getenv("AWS_MSK_BOOTSTRAP_SERVERS", "localhost:9092")
    aws_msk_security_protocol: str = os.getenv("AWS_MSK_SECURITY_PROTOCOL", "PLAINTEXT")
    
    # MSK Topics
    seller_acknowledgements_topic: str = "SELLER_ACKNOWLEDGEMENTS"
    seller_notify_topic: str = "SELLER_NOTIFY"
    seller_followup_topic: str = "SELLER_FOLLOWUP"
    prp_failures_topic: str = "PRP_FAILURES"
    
    # Database Configuration
    database_url: Optional[str] = os.getenv("DATABASE_URL")
    
    # Logging Configuration
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    class Config:
        # Look for .env.local in the processor directory (support running from repo root)
        env_file = str(PROCESSOR_DIR / ".env.local")
        env_file_encoding = "utf-8"
        extra = "ignore"  # Ignore extra fields in env file

settings = ProcessorSettings()
