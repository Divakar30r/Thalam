"""
API Router for RoleDetails endpoints
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, Path
from fastapi.responses import JSONResponse

from app.models import (
    RoleDetailsCreate, 
    RoleDetailsUpdate, 
    RoleDetailsResponse,
    RequiredFactorsResponse
)
from app.services.role_details_service import RoleDetailsService

from fastapi import status


# ... router definition is below ...

 
from app.core.exceptions import (
    NotFoundError,
    ConflictError, 
    ValidationError,
    DatabaseError
)
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/role-details", tags=["Role Details"])


@router.get("/by-industry/{industry}", response_model=List[RoleDetailsResponse])
async def get_role_details_by_industry(
    industry: str = Path(..., description="Industry name to filter by")
):
    """
    Get all RoleDetails documents by Industry
    """
    try:
        role_details_list = await RoleDetailsService.get_by_industry(industry)
        return role_details_list
    
    except DatabaseError as e:
        logger.error(f"Database error getting role details by industry: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error getting role details by industry: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/required-factors/{industry}", response_model=RequiredFactorsResponse)
async def get_required_factors_by_industry(
    industry: str = Path(..., description="Industry name to get required factors for")
):
    """
    Get required factors (keys with '*' suffix) by Industry
    Returns all factor keys that have '*' suffix with their possible values
    """
    try:
        required_factors = await RoleDetailsService.get_required_factors_by_industry(industry)
        return required_factors
    
    except NotFoundError as e:
        logger.warning(f"Role details not found for industry {industry}: {str(e)}")
        raise HTTPException(status_code=404, detail=f"No role details found for industry: {industry}")
    except DatabaseError as e:
        logger.error(f"Database error getting required factors: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error getting required factors: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/industries", response_model=List[str], status_code=status.HTTP_200_OK)
async def list_industries():
    """
    Get a list of all unique industries in the RoleDetails collection
    """
    try:
        industries = await RoleDetailsService.list_all_industries()
        return industries
    except Exception as e:
        logger.error(f"Error listing industries: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to list industries")

@router.post("/", response_model=RoleDetailsResponse, status_code=201)
async def create_role_details(role_details_data: RoleDetailsCreate):
    """
    Create a new RoleDetails document
    """
    try:
        role_details = await RoleDetailsService.create_role_details(role_details_data)
        logger.info(f"Created role details for industry: {role_details_data.Industry}")
        return role_details
    
    except ConflictError as e:
        logger.warning(f"Conflict creating role details: {str(e)}")
        raise HTTPException(status_code=409, detail=str(e))
    except ValidationError as e:
        logger.warning(f"Validation error creating role details: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except DatabaseError as e:
        logger.error(f"Database error creating role details: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error creating role details: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{role_details_id}", response_model=RoleDetailsResponse)
async def get_role_details_by_id(
    role_details_id: str = Path(..., description="RoleDetails document ID")
):
    """
    Get a specific RoleDetails document by ID
    """
    try:
        role_details = await RoleDetailsService.get_role_details_by_id(role_details_id)
        return role_details
    
    except NotFoundError as e:
        logger.warning(f"Role details not found: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        logger.warning(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except DatabaseError as e:
        logger.error(f"Database error getting role details: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error getting role details: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/{role_details_id}", response_model=RoleDetailsResponse)
async def update_role_details(
    role_details_id: str = Path(..., description="RoleDetails document ID"),
    role_details_data: RoleDetailsUpdate = ...
):
    """
    Update a RoleDetails document by ID
    """
    try:
        role_details = await RoleDetailsService.update_role_details(role_details_id, role_details_data)
        logger.info(f"Updated role details: {role_details_id}")
        return role_details
    
    except NotFoundError as e:
        logger.warning(f"Role details not found for update: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        logger.warning(f"Validation error updating role details: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except DatabaseError as e:
        logger.error(f"Database error updating role details: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error updating role details: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/{role_details_id}", status_code=204)
async def delete_role_details(
    role_details_id: str = Path(..., description="RoleDetails document ID")
):
    """
    Delete a RoleDetails document by ID
    """
    try:
        await RoleDetailsService.delete_role_details(role_details_id)
        logger.info(f"Deleted role details: {role_details_id}")
        return JSONResponse(status_code=204, content=None)
    
    except NotFoundError as e:
        logger.warning(f"Role details not found for deletion: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        logger.warning(f"Validation error deleting role details: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except DatabaseError as e:
        logger.error(f"Database error deleting role details: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error deleting role details: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/", response_model=List[RoleDetailsResponse])
async def list_role_details(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Number of records to return"),
    industry: Optional[str] = Query(None, description="Filter by industry"),
    scale: Optional[str] = Query(None, description="Filter by scale")
):
    """
    List all RoleDetails documents with optional filtering and pagination
    """
    try:
        role_details_list = await RoleDetailsService.list_all_role_details(
            skip=skip, 
            limit=limit,
            industry=industry,
            scale=scale
        )
        return role_details_list
    
    except DatabaseError as e:
        logger.error(f"Database error listing role details: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error listing role details: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")