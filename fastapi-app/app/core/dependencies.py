"""
FastAPI dependencies for the application
"""

from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.database import Database, get_database
from app.core.config import get_settings, Settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# Security scheme (for future authentication)
security = HTTPBearer(auto_error=False)


async def get_current_settings() -> Settings:
    """Get current application settings"""
    return get_settings()


async def get_database_dependency() -> Database:
    """Get database dependency"""
    return await get_database()


async def verify_database_connection(
    database: Database = Depends(get_database_dependency)
) -> None:
    """Verify database connection is healthy"""
    if not await database.health_check():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"message": "Database connection is not available"}
        )


# Future authentication dependency (placeholder)
async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
):
    """Get current authenticated user (placeholder for future implementation)"""
    # For now, we'll skip authentication
    # In production, you would validate the JWT token here
    return None


# Admin role dependency (placeholder)
async def require_admin_role(
    current_user = Depends(get_current_user)
):
    """Require admin role for certain operations (placeholder)"""
    # For now, we'll allow all operations
    # In production, you would check user roles here
    return current_user


# Manager role dependency (placeholder)
async def require_manager_role(
    current_user = Depends(get_current_user)
):
    """Require manager role for certain operations (placeholder)"""
    # For now, we'll allow all operations
    # In production, you would check user roles here
    return current_user


# Pagination dependency
async def get_pagination_params(
    skip: int = 0,
    limit: int = 20
) -> dict:
    """Get pagination parameters with validation"""
    from app.core.validation import validate_pagination_params
    
    try:
        validate_pagination_params(skip, limit)
        return {"skip": skip, "limit": limit}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"message": str(e)}
        )


# Location search dependency
async def get_location_params(
    longitude: Optional[float] = None,
    latitude: Optional[float] = None,
    max_distance: Optional[float] = None
) -> dict:
    """Get location search parameters with validation"""
    from app.core.validation import validate_location_search_params
    
    try:
        validate_location_search_params(longitude, latitude, max_distance)
        
        location_near = None
        if longitude is not None and latitude is not None:
            location_near = {"longitude": longitude, "latitude": latitude}
        
        return {
            "location_near": location_near,
            "max_distance": max_distance
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"message": str(e)}
        )