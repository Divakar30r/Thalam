# Requestor FastAPI Application

import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import orders, health
from app.core.config import RequestorConfig
from shared.utils import kafka_client, queue_manager
from shared.config import get_settings

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    # Startup
    logger.info("Starting Requestor application...")
    
    # Start Kafka client (AWS MSK) - graceful fallback if not configured
    try:
        await kafka_client.start_producer()
        logger.info("Kafka client started successfully")
    except Exception as e:
        logger.warning(f"AWS MSK/Kafka not available: {str(e)}. Continuing without messaging support.")
    
    # Start queue manager
    await queue_manager.start()
    
    logger.info("Requestor application started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Requestor application...")
    
    # Stop queue manager
    await queue_manager.stop()
    
    # Stop Kafka client
    try:
        await kafka_client.stop_producer()
    except Exception as e:
        logger.warning(f"Error stopping Kafka client: {str(e)}")
    
    logger.info("Requestor application stopped")

def create_app() -> FastAPI:
    """Create FastAPI application"""
    settings = get_settings()
    
    app = FastAPI(
        title="dCent Requestor Service",
        description="Order request processing service with gRPC streaming",
        version="1.0.0",
        debug=settings.debug_mode,
        lifespan=lifespan
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include routers
    app.include_router(
        orders.router,
        prefix="/api/v1",
        tags=["orders"]
    )
    
    app.include_router(
        health.router,
        prefix="/api/v1",
        tags=["health"]
    )
    
    return app

app = create_app()

if __name__ == "__main__":
    import uvicorn
    
    config = RequestorConfig()
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8004,
        reload=config.debug_mode,
        log_level=config.log_level.lower()
    )