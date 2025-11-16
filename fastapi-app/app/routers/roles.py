"""
API router for RolesBase endpoints
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import JSONResponse

from app.models import RolesBaseCreate, RolesBaseUpdate, RolesBaseResponse
from app.services import RoleService
from app.core.exceptions import (
    NotFoundError,
    ConflictError,
    ValidationError,
    ReferentialIntegrityError,
    DatabaseError
)
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/roles", tags=["roles"])


@router.post(
    "/",
    response_model=RolesBaseResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new role",
    description="Create a new role with automatic RoleID generation. User must exist."
)
async def create_role(role_data: RolesBaseCreate):
    """Create a new role"""
    try:
        return await RoleService.create_role(role_data)
    except ReferentialIntegrityError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": e.message, "referenced_collection": e.referenced_collection}
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"message": e.message, "field": e.field}
        )
    except DatabaseError as e:
        logger.error(f"Database error creating role: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Internal server error"}
        )


@router.get(
    "/",
    response_model=List[RolesBaseResponse],
    summary="List roles",
    description="Get a list of roles with optional filtering and pagination"
)
async def list_roles(
    skip: int = Query(0, ge=0, description="Number of roles to skip"),
    limit: int = Query(20, ge=1, le=100, description="Number of roles to return"),
    role_type: Optional[str] = Query(None, description="Filter by role type"),
    user_email: Optional[str] = Query(None, description="Filter by user email"),
    longitude: Optional[float] = Query(None, description="Longitude for location search"),
    latitude: Optional[float] = Query(None, description="Latitude for location search"),
    max_distance: Optional[float] = Query(None, description="Maximum distance in meters")
):
    """List roles with optional filtering"""
    try:
        location_near = None
        if longitude is not None and latitude is not None:
            location_near = {"longitude": longitude, "latitude": latitude}
        
        return await RoleService.list_roles(
            skip=skip,
            limit=limit,
            role_type=role_type,
            user_email=user_email,
            location_near=location_near,
            max_distance=max_distance
        )
    except DatabaseError as e:
        logger.error(f"Database error listing roles: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Internal server error"}
        )


@router.get(
    "/{role_id}",
    response_model=RolesBaseResponse,
    summary="Get role by ID",
    description="Get a specific role by their ID"
)
async def get_role(role_id: str):
    """Get role by ID"""
    try:
        return await RoleService.get_role_by_role_id(role_id)
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
        logger.error(f"Database error getting role {role_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Internal server error"}
        )


@router.put(
    "/role-id/{role_id}",
    response_model=RolesBaseResponse,
    summary="Update role by RoleID",
    description="Update a role's information using their RoleID. RoleID cannot be modified."
)
async def update_role_by_role_id(role_id: str, role_data: RolesBaseUpdate):
    """Update role by RoleID"""
    try:
        return await RoleService.update_role_by_role_id(role_id, role_data)
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"message": e.message}
        )
    except ReferentialIntegrityError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": e.message, "referenced_collection": e.referenced_collection}
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"message": e.message, "field": e.field}
        )
    except DatabaseError as e:
        logger.error(f"Database error updating role by RoleID {role_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Internal server error"}
        )


@router.patch(
    "/role-id/{role_id}",
    response_model=RolesBaseResponse,
    summary="Partially update role by RoleID",
    description="Partially update a role's information using their RoleID. RoleID cannot be modified."
)
async def patch_role_by_role_id(role_id: str, role_data: RolesBaseUpdate):
    """Partially update role by RoleID"""
    try:
        return await RoleService.update_role_by_role_id(role_id, role_data)
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"message": e.message}
        )
    except ReferentialIntegrityError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": e.message, "referenced_collection": e.referenced_collection}
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"message": e.message, "field": e.field}
        )
    except DatabaseError as e:
        logger.error(f"Database error updating role by RoleID {role_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Internal server error"}
        )


@router.put(
    "/{role_id}",
    response_model=RolesBaseResponse,
    summary="Update role by ID (deprecated)",
    description="Update a role's information by document ID. Consider using /role-id/{role_id} endpoint instead.",
    deprecated=True
)
async def update_role(role_id: str, role_data: RolesBaseUpdate):
    """Update role"""
    try:
        return await RoleService.update_role(role_id, role_data)
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"message": e.message}
        )
    except ReferentialIntegrityError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": e.message, "referenced_collection": e.referenced_collection}
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"message": e.message, "field": e.field}
        )
    except DatabaseError as e:
        logger.error(f"Database error updating role {role_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Internal server error"}
        )


@router.delete(
    "/{role_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete role",
    description="Delete a role. Cannot delete if role is referenced in terminals."
)
async def delete_role(role_id: str):
    """Delete role"""
    try:
        await RoleService.delete_role(role_id)
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
        logger.error(f"Database error deleting role {role_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Internal server error"}
        )


@router.get(
    "/role-id/{role_id}",
    response_model=RolesBaseResponse,
    summary="Get role by RoleID",
    description="Get a role by their RoleID field (e.g., ADM-0001)"
)
async def get_role_by_role_id(role_id: str):
    """Get role by RoleID field"""
    try:
        role = await RoleService.get_role_by_role_id(role_id)
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"message": f"Role with RoleID {role_id} not found"}
            )
        return role
    except DatabaseError as e:
        logger.error(f"Database error getting role by RoleID {role_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Internal server error"}
        )


@router.get(
    "/user/{user_email}",
    response_model=List[RolesBaseResponse],
    summary="Get roles by user email",
    description="Get all roles assigned to a specific user"
)
async def get_roles_by_user_email(user_email: str):
    """Get roles by user email"""
    try:
        return await RoleService.get_roles_by_user_email(user_email)
    except DatabaseError as e:
        logger.error(f"Database error getting roles for user {user_email}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Internal server error"}
        )


@router.get(
    "/stats/count",
    summary="Get role count",
    description="Get total count of roles with optional type filter"
)
async def get_role_count(
    role_type: Optional[str] = Query(None, description="Filter by role type")
):
    """Get role count"""
    try:
        count = await RoleService.count_roles(role_type=role_type)
        return {"count": count, "type_filter": role_type}
    except DatabaseError as e:
        logger.error(f"Database error counting roles: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Internal server error"}
        )


@router.post(
    "/validate-integrity",
    summary="Validate role ID integrity",
    description="Validate that a list of role IDs exist and have proper format"
)
async def validate_role_id_integrity(role_ids: List[str]):
    """Validate role ID integrity"""
    try:
        validation_results = await RoleService.validate_role_id_integrity(role_ids)
        
        valid_roles = [role_id for role_id, valid in validation_results.items() if valid]
        invalid_roles = [role_id for role_id, valid in validation_results.items() if not valid]
        
        return {
            "validation_results": validation_results,
            "valid_roles": valid_roles,
            "invalid_roles": invalid_roles,
            "all_valid": len(invalid_roles) == 0
        }
    except DatabaseError as e:
        logger.error(f"Database error validating role ID integrity: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Internal server error"}
        )


@router.get(
    "/Type/{role_type}",
    response_model=List[RolesBaseResponse],
    summary="Get roles by Type",
    description="Get all roles with a specific Type (Seller, Buyer, or TerminalOwner)"
)
async def get_roles_by_type(role_type: str):
    """Get roles by Type"""
    try:
        return await RoleService.get_roles_by_type(role_type)
    except DatabaseError as e:
        logger.error(f"Database error getting roles by type {role_type}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Internal server error"}
        )


@router.get(
    "/Industry/{industry}",
    response_model=List[RolesBaseResponse],
    summary="Get roles by Industry",
    description="Get all roles with a specific Industry"
)
async def get_roles_by_industry(industry: str):
    """Get roles by Industry"""
    try:
        return await RoleService.get_roles_by_industry(industry)
    except DatabaseError as e:
        logger.error(f"Database error getting roles by industry {industry}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Internal server error"}
        )