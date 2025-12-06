import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import proposals, health
from app.core.config import settings
from app.grpc_server.server_manager import ServerManager

# Setup logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format=settings.log_format
)
logger = logging.getLogger(__name__)

# Global server manager
server_manager = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    global server_manager
    
    # Startup
    logger.info("Starting Processor application...")
    
    try:
        # Create and start server manager (both FastAPI and gRPC)
        server_manager = ServerManager(app)
        await server_manager.start()
        
        logger.info("Processor application started successfully")
        
        yield
        
    except Exception as e:
        logger.error(f"Error during startup: {str(e)}")
        raise
    finally:
        # Shutdown
        logger.info("Shutting down Processor application...")
        
        if server_manager:
            await server_manager.stop()
        
        logger.info("Processor application stopped")

def create_app() -> FastAPI:
    """Create FastAPI application"""
    
    app = FastAPI(
        title="dCent Processor Service",
        description="Order processing service with gRPC server and proposal management",
        version="1.0.0",
        lifespan=lifespan
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure based on your needs
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include routers
    app.include_router(
        proposals.router,
        prefix="/api/v1",
        tags=["proposals"]
    )
    
    app.include_router(
        health.router,
        prefix="/api/v1",
        tags=["health"]
    )
    
    @app.get("/")
    async def root():
        """Root endpoint"""
        return {
            "service": "dCent Processor",
            "version": "1.0.0",
            "status": "running"
        }
    
    return app

app = create_app()

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=settings.fastapi_host,
        port=settings.fastapi_port,
        reload=False,  # Set to True for development
        log_level=settings.log_level.lower()
    )