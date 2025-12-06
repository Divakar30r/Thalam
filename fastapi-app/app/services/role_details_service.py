"""
Service layer for RoleDetails collection operations
"""

from typing import List, Optional, Dict, Any
from bson import ObjectId
from pymongo.errors import DuplicateKeyError

from app.models import RoleDetails, RoleDetailsCreate, RoleDetailsUpdate, RoleDetailsResponse, RequiredFactorsResponse
from app.core.exceptions import (
    NotFoundError, 
    ConflictError, 
    ValidationError,
    DatabaseError
)
from app.core.logging import get_logger

logger = get_logger(__name__)


def _convert_role_details_to_response(role_details: RoleDetails) -> RoleDetailsResponse:
    """Convert RoleDetails document to RoleDetailsResponse with proper id field"""
    return RoleDetailsResponse.model_validate({
        **role_details.model_dump(),
        "id": str(role_details.id)
    })


class RoleDetailsService:
    @staticmethod
    async def list_all_industries() -> List[str]:
        """Return a list of all unique industries in the RoleDetails collection"""
        try:
            docs = await RoleDetails.find_all().to_list()
            industries = {doc.Industry for doc in docs if hasattr(doc, "Industry") and doc.Industry}
            return sorted(industries)
        except Exception as e:
            logger.error(f"Error listing industries: {str(e)}")
            raise DatabaseError(f"Failed to list industries: {str(e)}")
    @staticmethod
    async def get_by_industry(industry: str) -> List[RoleDetailsResponse]:
        """Get all RoleDetails by Industry"""
        try:
            role_details_list = await RoleDetails.find(RoleDetails.Industry == industry).to_list()
            if not role_details_list:
                return []
            
            return [_convert_role_details_to_response(rd) for rd in role_details_list]
            
        except Exception as e:
            logger.error(f"Error getting role details by industry {industry}: {str(e)}")
            raise DatabaseError(f"Failed to get role details by industry: {str(e)}")
    
    @staticmethod
    async def get_required_factors_by_industry(industry: str) -> RequiredFactorsResponse:
        """Get required factors (keys with '*' suffix) by Industry"""
        try:
            role_details_list = await RoleDetails.find(RoleDetails.Industry == industry).to_list()
            if not role_details_list:
                raise NotFoundError("RoleDetails", f"industry={industry}")
            
            # Combine all required factors from all matching documents
            required_factors = {}
            
            for role_details in role_details_list:
                factors = role_details.factors or {}
                
                # Extract keys with '*' suffix and their values
                for key, value in factors.items():
                    if key.endswith('*'):
                        # Remove the '*' suffix for the response
                        clean_key = key[:-1]
                        if clean_key not in required_factors:
                            required_factors[clean_key] = value
                        else:
                            # If key already exists, merge values if they're lists
                            if isinstance(required_factors[clean_key], list) and isinstance(value, list):
                                # Merge and deduplicate
                                required_factors[clean_key] = list(set(required_factors[clean_key] + value))
                            else:
                                # If not lists, keep the existing value (first found)
                                pass
            
            return RequiredFactorsResponse(
                Industry=industry,
                required_factors=required_factors
            )
            
        except Exception as e:
            if isinstance(e, NotFoundError):
                raise
            logger.error(f"Error getting required factors for industry {industry}: {str(e)}")
            raise DatabaseError(f"Failed to get required factors: {str(e)}")
    
    @staticmethod
    async def create_role_details(role_details_data: RoleDetailsCreate) -> RoleDetailsResponse:
        """Create a new RoleDetails document"""
        try:
            # Create role details document
            role_details_dict = role_details_data.model_dump(exclude_none=True)
            role_details_doc = RoleDetails(**role_details_dict)
            
            # Save to database
            await role_details_doc.insert()
            
            logger.info(f"Created role details for industry: {role_details_data.Industry}")
            return _convert_role_details_to_response(role_details_doc)
            
        except DuplicateKeyError as de:
            raise ConflictError(
                f"Error details: " + str(de),
                conflicting_field="Industry/Scale combination"
            )
        except Exception as e:
            logger.error(f"Error creating role details: {str(e)}")
            raise DatabaseError(f"Failed to create role details: {str(e)}")
    
    @staticmethod
    async def get_role_details_by_id(role_details_id: str) -> RoleDetailsResponse:
        """Get RoleDetails by ID"""
        try:
            if not ObjectId.is_valid(role_details_id):
                raise ValidationError("Invalid role details ID format", field="role_details_id")
            
            role_details = await RoleDetails.get(role_details_id)
            if not role_details:
                raise NotFoundError("RoleDetails", role_details_id)
            
            return _convert_role_details_to_response(role_details)
            
        except Exception as e:
            if isinstance(e, (NotFoundError, ValidationError)):
                raise
            logger.error(f"Error getting role details {role_details_id}: {str(e)}")
            raise DatabaseError(f"Failed to get role details: {str(e)}")
    
    @staticmethod
    async def update_role_details(role_details_id: str, role_details_data: RoleDetailsUpdate) -> RoleDetailsResponse:
        """Update RoleDetails by ID"""
        try:
            if not ObjectId.is_valid(role_details_id):
                raise ValidationError("Invalid role details ID format", field="role_details_id")
            
            role_details = await RoleDetails.get(role_details_id)
            if not role_details:
                raise NotFoundError("RoleDetails", role_details_id)
            
            # Update fields
            update_data = role_details_data.model_dump(exclude_none=True)
            if update_data:
                # Update updatedAt timestamp
                from datetime import datetime, timezone
                update_data['updatedAt'] = datetime.now(timezone.utc)
                
                await role_details.update({"$set": update_data})
            
            # Fetch updated role details
            updated_role_details = await RoleDetails.get(role_details_id)
            
            logger.info(f"Updated role details: {role_details_id}")
            return _convert_role_details_to_response(updated_role_details)
            
        except Exception as e:
            if isinstance(e, (NotFoundError, ValidationError)):
                raise
            logger.error(f"Error updating role details {role_details_id}: {str(e)}")
            raise DatabaseError(f"Failed to update role details: {str(e)}")
    
    @staticmethod
    async def delete_role_details(role_details_id: str) -> bool:
        """Delete RoleDetails by ID"""
        try:
            if not ObjectId.is_valid(role_details_id):
                raise ValidationError("Invalid role details ID format", field="role_details_id")
            
            role_details = await RoleDetails.get(role_details_id)
            if not role_details:
                raise NotFoundError("RoleDetails", role_details_id)
            
            await role_details.delete()
            
            logger.info(f"Deleted role details: {role_details_id}")
            return True
            
        except Exception as e:
            if isinstance(e, (NotFoundError, ValidationError)):
                raise
            logger.error(f"Error deleting role details {role_details_id}: {str(e)}")
            raise DatabaseError(f"Failed to delete role details: {str(e)}")
    
    @staticmethod
    async def list_all_role_details(
        skip: int = 0,
        limit: int = 20,
        industry: Optional[str] = None,
        scale: Optional[str] = None
    ) -> List[RoleDetailsResponse]:
        """List all RoleDetails with optional filtering"""
        try:
            query = RoleDetails.find({})
            
            # Apply filters
            if industry:
                query = query.find(RoleDetails.Industry == industry)
            if scale:
                query = query.find(RoleDetails.Scale == scale)
            
            # Apply pagination
            role_details_list = await query.skip(skip).limit(limit).to_list()
            
            return [_convert_role_details_to_response(rd) for rd in role_details_list]
            
        except Exception as e:
            logger.error(f"Error listing role details: {str(e)}")
            raise DatabaseError(f"Failed to list role details: {str(e)}")