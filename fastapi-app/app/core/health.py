"""
Health check functions for the FastAPI application
"""

from fastapi import status
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


async def health_check():
    """Health check endpoint"""
    from app.core.database import check_database_health

    try:
        # Check database health
        db_healthy = await check_database_health()

        health_status = {
            "status": "healthy" if db_healthy else "unhealthy",
            "service": "ordermgmt-fastapi"
        }

        status_code = status.HTTP_200_OK if db_healthy else status.HTTP_503_SERVICE_UNAVAILABLE

        return JSONResponse(
            status_code=status_code,
            content=health_status
        )

    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "service": "ordermgmt-fastapi"
            }
        )


def get_api_info():
    """Get basic information about the API"""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "description": "dCent CP Order Management API",
        "documentation": "/docs",
        "health": "/health",
        "endpoints": {
            "users": "/api/v1/users",
            "roles": "/api/v1/roles", 
            "terminals": "/api/v1/terminals"
        }
    }