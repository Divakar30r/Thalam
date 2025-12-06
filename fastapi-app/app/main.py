"""
Main FastAPI application
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import time

from app.core import (
    settings,
    setup_logging,
    get_logger,
    connect_to_database,
    disconnect_from_database
)
from app.core.health import health_check, get_api_info
from app.core.exception_handlers import register_exception_handlers
from app.routers import users_router, roles_router, terminals_router, role_details_router
from app.routers import order_req as order_req_router
from app.routers import order_proposal as order_proposal_router

# Setup logging
setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("Starting up dCent CP Order Management API")
    logger.info(f"Environment: {settings.debug and 'Development' or 'Production'}")
    
    try:
        # Connect to database
        await connect_to_database()
        logger.info("✅ Database connection established")
        
        # Log application info
        logger.info(f"Application: {settings.app_name} v{settings.app_version}")
        logger.info(f"Host: {settings.host}:{settings.port}")
        
        yield
        
    except Exception as e:
        logger.error(f"❌ Startup failed: {str(e)}")
        raise
    finally:
        # Shutdown
        logger.info("Shutting down dCent CP Order Management API")
        await disconnect_from_database()
        logger.info("✅ Database connection closed")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="""
    dCent CP Order Management API
    
    A comprehensive FastAPI application for managing UserBase, RolesBase, and TerminalBase collections
    with MongoDB and Beanie ODM.
    
    ## Features
    
    * **User Management**: Create, read, update, delete user profiles with location tracking
    * **Role Management**: Role-based access control with automatic ID generation
    * **Terminal Management**: Terminal capacity and capability management
    * **Geospatial Queries**: Location-based searching and filtering
    * **Data Validation**: Comprehensive input validation and referential integrity
    * **Async Operations**: Full async/await support with Beanie ODM
    
    ## Authentication
    
    Currently, the API does not require authentication. This is a placeholder for future implementation.
    """,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)
 
# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_credentials,
    allow_methods=settings.cors_methods,
    allow_headers=settings.cors_headers,
)
  
# Add trusted host middleware for production
if not settings.debug:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=[
            "localhost", 
            "127.0.0.1", 
            "drapps.dev",
            "www.drapps.dev",
            "*.drapps.dev"
        ]
    )


# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add response time to headers"""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


# Register all exception handlers
register_exception_handlers(app)


# Health check endpoint
@app.get(
    "/health",
    tags=["health"],
    summary="Health check",
    description="Check if the API and database are healthy"
)
async def health_endpoint():
    """Health check endpoint"""
    return await health_check()


# Root endpoint
@app.get(
    "/",
    tags=["root"],
    summary="API Information",
    description="Get basic information about the API"
)
async def root():
    """Root endpoint with API information"""
    return get_api_info()


# Include routers with configurable API prefix
# Use settings.api_prefix for dev (/api/v1) or empty string for production
app.include_router(
    users_router,
    prefix=settings.api_prefix,
    dependencies=[]  # Add auth dependencies here in future
)

app.include_router(
    roles_router,
    prefix=settings.api_prefix,
    dependencies=[]  # Add auth dependencies here in future
)

app.include_router(
    terminals_router,
    prefix=settings.api_prefix,
    dependencies=[]  # Add auth dependencies here in future
)

app.include_router(
    role_details_router,
    prefix=settings.api_prefix,
    dependencies=[]  # Add auth dependencies here in future
)

app.include_router(
    order_req_router.router,
    prefix=settings.api_prefix,
    dependencies=[]
)

app.include_router(
    order_proposal_router.router,
    prefix=settings.api_prefix,
    dependencies=[]
)


if __name__ == "__main__":
    import uvicorn
    
    logger.info(f"Starting {settings.app_name} on {settings.host}:{settings.port}")
    
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        log_level=settings.log_level.lower()
    )