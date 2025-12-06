"""
API router for TerminalBase endpoints
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import JSONResponse

from app.models import TerminalBaseCreate, TerminalBaseUpdate, TerminalBaseResponse
from app.services import TerminalService
from app.core.exceptions import (
    NotFoundError,
    ConflictError,
    ValidationError,
    ReferentialIntegrityError,
    DatabaseError
)
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/terminals", tags=["terminals"])


@router.post(
    "/",
    response_model=TerminalBaseResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new terminal",
    description="Create a new terminal with capacity and capability configuration. All RoleIDs must exist."
)
async def create_terminal(terminal_data: TerminalBaseCreate):
    """Create a new terminal"""
    try:
        return await TerminalService.create_terminal(terminal_data)
    except ReferentialIntegrityError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": e.message, "referenced_collection": e.referenced_collection}
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
        logger.error(f"Database error creating terminal: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Internal server error"}
        )


@router.get(
    "/",
    response_model=List[TerminalBaseResponse],
    summary="List terminals",
    description="Get a list of terminals with optional filtering and pagination"
)
async def list_terminals(
    skip: int = Query(0, ge=0, description="Number of terminals to skip"),
    limit: int = Query(20, ge=1, le=100, description="Number of terminals to return"),
    role_id: Optional[str] = Query(None, description="Filter by managing role ID"),
    longitude: Optional[float] = Query(None, description="Longitude for location search"),
    latitude: Optional[float] = Query(None, description="Latitude for location search"),
    max_distance: Optional[float] = Query(None, description="Maximum distance in meters"),
    has_capability: Optional[str] = Query(None, description="Filter by capability (e.g., 'Refrigeration', 'Weighing')")
):
    """List terminals with optional filtering"""
    try:
        location_near = None
        if longitude is not None and latitude is not None:
            location_near = {"longitude": longitude, "latitude": latitude}
        
        return await TerminalService.list_terminals(
            skip=skip,
            limit=limit,
            role_id=role_id,
            location_near=location_near,
            max_distance=max_distance,
            has_capability=has_capability
        )
    except DatabaseError as e:
        logger.error(f"Database error listing terminals: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Internal server error"}
        )


@router.get(
    "/{terminal_id}",
    response_model=TerminalBaseResponse,
    summary="Get terminal by ID",
    description="Get a specific terminal by their ID"
)
async def get_terminal_by_id(terminal_id: str):
    """Get terminal by ID"""
    try:
        return await TerminalService.get_terminal_by_id(terminal_id)
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
        logger.error(f"Database error getting terminal {terminal_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Internal server error"}
        )


@router.get(
    "/role-id/{role_id}",
    response_model=List[TerminalBaseResponse],
    summary="Get terminals by RoleID",
    description="Get all terminals managed by a specific RoleID"
)
async def get_terminal_by_roleid(role_id: str):
    """Get terminals by RoleID"""
    try:
        return await TerminalService.get_terminal_by_roleid(role_id)
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
        logger.error(f"Database error getting terminals by RoleID {role_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Internal server error"}
        )


@router.put(
    "/role-id/{role_id}/terminal/{terminal_id}",
    response_model=TerminalBaseResponse,
    summary="Update terminal by RoleID and terminal ID",
    description="Update a specific terminal using RoleID and terminal ID. RoleID cannot be modified."
)
async def update_terminal_by_role_id(role_id: str, terminal_id: str, terminal_data: TerminalBaseUpdate):
    """Update terminal by RoleID and terminal ID"""
    try:
        return await TerminalService.update_terminal_by_role_id(role_id, terminal_id, terminal_data)
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
        logger.error(f"Database error updating terminal {terminal_id} with RoleID {role_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Internal server error"}
        )


@router.patch(
    "/role-id/{role_id}/terminal/{terminal_id}",
    response_model=TerminalBaseResponse,
    summary="Partially update terminal by RoleID and terminal ID",
    description="Partially update a specific terminal using RoleID and terminal ID. RoleID cannot be modified."
)
async def patch_terminal_by_role_id(role_id: str, terminal_id: str, terminal_data: TerminalBaseUpdate):
    """Partially update terminal by RoleID and terminal ID"""
    try:
        return await TerminalService.update_terminal_by_role_id(role_id, terminal_id, terminal_data)
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
        logger.error(f"Database error updating terminal {terminal_id} with RoleID {role_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Internal server error"}
        )


@router.put(
    "/{terminal_id}",
    response_model=TerminalBaseResponse,
    summary="Update terminal by ID (deprecated)",
    description="Update a terminal's information by document ID. Consider using /role-id/{role_id}/terminal/{terminal_id} endpoint instead.",
    deprecated=True
)
async def update_terminal(terminal_id: str, terminal_data: TerminalBaseUpdate):
    """Update terminal"""
    try:
        return await TerminalService.update_terminal(terminal_id, terminal_data)
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
        logger.error(f"Database error updating terminal {terminal_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Internal server error"}
        )


@router.delete(
    "/{terminal_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete terminal",
    description="Delete a terminal"
)
async def delete_terminal(terminal_id: str):
    """Delete terminal"""
    try:
        await TerminalService.delete_terminal(terminal_id)
        return JSONResponse(
            status_code=status.HTTP_204_NO_CONTENT,
            content=None
        )
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
        logger.error(f"Database error deleting terminal {terminal_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Internal server error"}
        )


@router.get(
    "/terminal-id/{terminal_id}",
    response_model=TerminalBaseResponse,
    summary="Get terminal by TerminalID",
    description="Get a terminal by their TerminalID field"
)
async def get_terminal_by_terminal_id(terminal_id: str):
    """Get terminal by TerminalID field"""
    try:
        terminal = await TerminalService.get_terminal_by_terminal_id(terminal_id)
        if not terminal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"message": f"Terminal with TerminalID {terminal_id} not found"}
            )
        return terminal
    except DatabaseError as e:
        logger.error(f"Database error getting terminal by TerminalID {terminal_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Internal server error"}
        )


@router.get(
    "/role/{role_id}",
    response_model=List[TerminalBaseResponse],
    summary="Get terminals by role",
    description="Get all terminals managed by a specific role"
)
async def get_terminals_by_role(role_id: str):
    """Get terminals by role"""
    try:
        return await TerminalService.get_terminals_by_role(role_id)
    except DatabaseError as e:
        logger.error(f"Database error getting terminals for role {role_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Internal server error"}
        )


@router.get(
    "/capability/{capability}",
    response_model=List[TerminalBaseResponse],
    summary="Get terminals by capability",
    description="Get all terminals with a specific capability enabled"
)
async def get_terminals_with_capability(capability: str):
    """Get terminals with specific capability"""
    try:
        return await TerminalService.get_terminals_with_capability(capability)
    except DatabaseError as e:
        logger.error(f"Database error getting terminals with capability {capability}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Internal server error"}
        )


@router.get(
    "/stats/count",
    summary="Get terminal count",
    description="Get total count of terminals"
)
async def get_terminal_count():
    """Get terminal count"""
    try:
        count = await TerminalService.count_terminals()
        return {"count": count}
    except DatabaseError as e:
        logger.error(f"Database error counting terminals: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Internal server error"}
        )


@router.get(
    "/stats/capacity",
    summary="Get capacity statistics",
    description="Get capacity statistics across all terminals"
)
async def get_capacity_stats():
    """Get terminal capacity statistics"""
    try:
        return await TerminalService.get_terminal_capacity_stats()
    except DatabaseError as e:
        logger.error(f"Database error getting capacity stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Internal server error"}
        )