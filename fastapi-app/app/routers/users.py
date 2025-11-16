"""
API router for UserBase endpoints
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import JSONResponse

from app.models import UserBaseCreate, UserBaseUpdate, UserBaseResponse
from app.services import UserService
from app.core.exceptions import (
    NotFoundError,
    ConflictError,
    ValidationError,
    DatabaseError
)
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/users", tags=["users"])


@router.post(
    "/",
    response_model=UserBaseResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new user",
    description="Create a new user with the provided information. Email must be from the allowed domain."
)
async def create_user(user_data: UserBaseCreate):
    """Create a new user"""
    try:
        return await UserService.create_user(user_data)
    except ConflictError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"message": e.message, "field": e.conflicting_field}
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"message": e.message, "field": e.field}
        )
    except DatabaseError as e:
        logger.error(f"Database error creating user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Internal server error"}
        )


@router.get(
    "/",
    response_model=List[UserBaseResponse],
    summary="List users",
    description="Get a list of users with optional filtering and pagination"
)
async def list_users(
    skip: int = Query(0, ge=0, description="Number of users to skip"),
    limit: int = Query(20, ge=1, le=100, description="Number of users to return"),
    status: Optional[str] = Query(None, description="Filter by user status"),
    search: Optional[str] = Query(None, description="Search in ShortName or EmailID"),
    longitude: Optional[float] = Query(None, description="Longitude for location search"),
    latitude: Optional[float] = Query(None, description="Latitude for location search"),
    max_distance: Optional[float] = Query(None, description="Maximum distance in meters")
):
    """List users with optional filtering"""
    try:
        location_near = None
        if longitude is not None and latitude is not None:
            location_near = {"longitude": longitude, "latitude": latitude}
        
        return await UserService.list_users(
            skip=skip,
            limit=limit,
            status=status,
            search=search,
            location_near=location_near,
            max_distance=max_distance
        )
    except DatabaseError as e:
        logger.error(f"Database error listing users: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Internal server error"}
        )


@router.get(
    "/{user_id}",
    response_model=UserBaseResponse,
    summary="Get user by ID",
    description="Get a specific user by their ID"
)
async def get_user(user_id: str):
    """Get user by ID"""
    try:
        return await UserService.get_user_by_id(user_id)
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"message": e.message}
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"message": e.message, "field": e.field}
        )
    except DatabaseError as e:
        logger.error(f"Database error getting user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Internal server error"}
        )


@router.put(
    "/email/{email}",
    response_model=UserBaseResponse,
    summary="Update user by email",
    description="Update a user's information using their email address. EmailID cannot be modified."
)
async def update_user_by_email(email: str, user_data: UserBaseUpdate):
    """Update user by email"""
    try:
        return await UserService.update_user_by_email(email, user_data)
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"message": e.message}
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"message": e.message, "field": e.field}
        )
    except DatabaseError as e:
        logger.error(f"Database error updating user by email {email}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Internal server error"}
        )


@router.patch(
    "/email/{email}",
    response_model=UserBaseResponse,
    summary="Partially update user by email",
    description="Partially update a user's information using their email address. EmailID cannot be modified."
)
async def patch_user_by_email(email: str, user_data: UserBaseUpdate):
    """Partially update user by email"""
    try:
        return await UserService.update_user_by_email(email, user_data)
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"message": e.message}
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"message": e.message, "field": e.field}
        )
    except DatabaseError as e:
        logger.error(f"Database error updating user by email {email}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Internal server error"}
        )


@router.put(
    "/{user_id}",
    response_model=UserBaseResponse,
    summary="Update user by ID (deprecated)",
    description="Update a user's information by ID. Consider using /email/{email} endpoint instead.",
    deprecated=True
)
async def update_user(user_id: str, user_data: UserBaseUpdate):
    """Update user"""
    try:
        return await UserService.update_user(user_id, user_data)
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"message": e.message}
        )
    except ConflictError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"message": e.message, "field": e.conflicting_field}
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"message": e.message, "field": e.field}
        )
    except DatabaseError as e:
        logger.error(f"Database error updating user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Internal server error"}
        )


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete user",
    description="Delete a user. Cannot delete if user is referenced in roles."
)
async def delete_user(user_id: str):
    """Delete user"""
    try:
        await UserService.delete_user(user_id)
        return JSONResponse(
            status_code=status.HTTP_204_NO_CONTENT,
            content=None
        )
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"message": e.message}
        )
    except ConflictError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"message": e.message, "field": e.conflicting_field}
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"message": e.message, "field": e.field}
        )
    except DatabaseError as e:
        logger.error(f"Database error deleting user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Internal server error"}
        )


@router.get(
    "/email/{email}",
    response_model=UserBaseResponse,
    summary="Get user by email",
    description="Get a user by their email address"
)
async def get_user_by_email(email: str):
    """Get user by email"""
    try:
        user = await UserService.get_user_by_email(email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"message": f"User with email {email} not found"}
            )
        return user
    except DatabaseError as e:
        logger.error(f"Database error getting user by email {email}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Internal server error"}
        )

@router.get(
    "/supabase/{supabase_id}",
    response_model=UserBaseResponse,
    summary="Get user by SupabaseID",
    description="Get a user by their SupabaseID (unique)"
)
async def get_user_by_supabase_id(supabase_id: str):
    """Get user by SupabaseID"""
    try:
        user = await UserService.get_user_by_supabase_id(supabase_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"message": f"User with SupabaseID {supabase_id} not found"}
            )
        return user
    except DatabaseError as e:
        logger.error(f"Database error getting user by SupabaseID {supabase_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Internal server error"}
        )


@router.get(
    "/stats/count",
    summary="Get user count",
    description="Get total count of users with optional status filter"
)
async def get_user_count(
    status: Optional[str] = Query(None, description="Filter by user status")
):
    """Get user count"""
    try:
        count = await UserService.count_users(status=status)
        return {"count": count, "status_filter": status}
    except DatabaseError as e:
        logger.error(f"Database error counting users: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Internal server error"}
        )