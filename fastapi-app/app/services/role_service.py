"""
Service layer for RolesBase collection operations
"""

from typing import List, Optional, Dict, Any
from bson import ObjectId
from pymongo.errors import DuplicateKeyError
from beanie.operators import In, RegEx, Near

from app.models import RolesBase, RolesBaseCreate, RolesBaseUpdate, RolesBaseResponse
from app.services.user_service import UserService
from app.core.exceptions import (
    NotFoundError,
    ConflictError,
    ValidationError,
    ReferentialIntegrityError,
    DatabaseError
)
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def _convert_role_to_response(role: RolesBase) -> RolesBaseResponse:
    """Convert RolesBase document to RolesBaseResponse with proper id field"""
    return RolesBaseResponse.model_validate({
        **role.model_dump(),
        "id": str(role.id)
    })


class RoleService:
    """Service for RolesBase operations"""
    
    @staticmethod
    async def create_role(role_data: RolesBaseCreate) -> RolesBaseResponse:
        """Create a new role with validation"""
        try:
            # Validate user exists
            user_exists = await UserService.validate_user_exists(role_data.UserEmailID)
            if not user_exists:
                raise ReferentialIntegrityError(
                    f"User with email {role_data.UserEmailID} does not exist",
                    referenced_collection="UserBase"
                )
            
            # Get the prefix for this role type from config
            pattern = settings.role_id_patterns.get(role_data.Type)
            if not pattern:
                raise ValidationError(f"Invalid role type: {role_data.Type}", field="Type")
            
            # Extract prefix from pattern (e.g., "ADM" from "ADM-{:04d}")
            prefix = pattern.split("-")[0]
            
            # Generate RoleID using format: prefix + '_' + UserID
            # Extract UserID from email (part before @)
            user_id = role_data.UserEmailID.split("@")[0]
            role_id = f"{prefix}_{user_id}"
            
            # Create role document
            role_doc = RolesBase(**role_data.model_dump(exclude_none=True), RoleID=role_id)
            
            # Save to database
            await role_doc.insert()
            
            logger.info(f"Created role: {role_id} for user {role_data.UserEmailID}")
            return _convert_role_to_response(role_doc)
            
        except Exception as e:
            if isinstance(e, (ValidationError, ReferentialIntegrityError)):
                raise
            logger.error(f"Error creating role: {str(e)}")
            raise DatabaseError(f"Failed to create role: {str(e)}")
    
    @staticmethod
    async def get_role_by_role_id(role_id: str) -> RolesBaseResponse:
        """Get role by RoleID field"""
        try:
            role = await RolesBase.find_one(RolesBase.RoleID == role_id)
            if not role:
                raise NotFoundError("Role", role_id)
            
            return _convert_role_to_response(role)
            
        except Exception as e:
            if isinstance(e, NotFoundError):
                raise
            logger.error(f"Error getting role by RoleID {role_id}: {str(e)}")
            raise DatabaseError(f"Failed to get role by RoleID: {str(e)}")
    
    @staticmethod
    async def list_roles(
        skip: int = 0,
        limit: int = 20,
        role_type: Optional[str] = None,
        user_email: Optional[str] = None,
        location_near: Optional[Dict[str, float]] = None,
        max_distance: Optional[float] = None
    ) -> List[RolesBaseResponse]:
        """List roles with optional filtering"""
        try:
            query = RolesBase.find({})
            
            # Apply type filter
            if role_type:
                query = query.find(RolesBase.Type == role_type)
            
            # Apply user email filter
            if user_email:
                query = query.find(RolesBase.UserEmailID == user_email)
            
            # Apply location-based search
            if location_near and max_distance:
                query = query.find(
                    Near(
                        RolesBase.Location,
                        longitude=location_near["longitude"],
                        latitude=location_near["latitude"],
                        max_distance=max_distance
                    )
                )
            
            # Apply pagination
            roles = await query.skip(skip).limit(limit).to_list()
            
            return [_convert_role_to_response(role) for role in roles]
            
        except Exception as e:
            logger.error(f"Error listing roles: {str(e)}")
            raise DatabaseError(f"Failed to list roles: {str(e)}")
    
    @staticmethod
    async def update_role_by_role_id(role_id: str, role_data: RolesBaseUpdate) -> RolesBaseResponse:
        """Update role by RoleID - RoleID cannot be changed"""
        try:
            role = await RolesBase.find_one(RolesBase.RoleID == role_id)
            if not role:
                raise NotFoundError("Role", f"RoleID={role_id}")
            
            # Validate user exists if UserEmailID is being updated
            if role_data.UserEmailID:
                user_exists = await UserService.validate_user_exists(role_data.UserEmailID)
                if not user_exists:
                    raise ReferentialIntegrityError(
                        f"User with email {role_data.UserEmailID} does not exist",
                        referenced_collection="UserBase"
                    )
            
            # Update fields (RoleID is excluded by design)
            update_data = role_data.model_dump(exclude_unset=True, exclude_none=True)
            await role.update({"$set": update_data})
            
            # Fetch updated role
            updated_role = await RolesBase.find_one(RolesBase.RoleID == role_id)
            if not updated_role:
                raise NotFoundError("Role", f"RoleID={role_id}")
            
            logger.info(f"Updated role by RoleID: {role_id}")
            return _convert_role_to_response(updated_role)
            
        except Exception as e:
            if isinstance(e, (NotFoundError, ValidationError, ReferentialIntegrityError)):
                raise
            logger.error(f"Error updating role by RoleID {role_id}: {str(e)}")
            raise DatabaseError(f"Failed to update role: {str(e)}")
    
    @staticmethod
    async def update_role(role_id: str, role_data: RolesBaseUpdate) -> RolesBaseResponse:
        """Update role"""
        try:
            if not ObjectId.is_valid(role_id):
                raise ValidationError("Invalid role ID format", field="role_id")
            
            role = await RolesBase.get(role_id)
            if not role:
                raise NotFoundError("Role", role_id)
            
            # Validate user exists if UserEmailID is being updated
            if role_data.UserEmailID:
                user_exists = await UserService.validate_user_exists(role_data.UserEmailID)
                if not user_exists:
                    raise ReferentialIntegrityError(
                        f"User with email {role_data.UserEmailID} does not exist",
                        referenced_collection="UserBase"
                    )
            
            # Update fields (excluding Type and RoleID which should not change)
            update_data = role_data.model_dump(exclude_unset=True, exclude_none=True, exclude={"Type"})
            await role.update({"$set": update_data})
            
            # Fetch updated role
            updated_role = await RolesBase.get(role_id)
            if not updated_role:
                raise NotFoundError("Role", role_id)
            
            logger.info(f"Updated role: {role_id}")
            return _convert_role_to_response(updated_role)
            
        except Exception as e:
            if isinstance(e, (NotFoundError, ValidationError, ReferentialIntegrityError)):
                raise
            logger.error(f"Error updating role {role_id}: {str(e)}")
            raise DatabaseError(f"Failed to update role: {str(e)}")
    
    @staticmethod
    async def delete_role(role_id: str) -> bool:
        """Delete role"""
        try:
            if not ObjectId.is_valid(role_id):
                raise ValidationError("Invalid role ID format", field="role_id")
            
            role = await RolesBase.get(role_id)
            if not role:
                raise NotFoundError("Role", role_id)
            
            # Check if role is referenced in TerminalBase
            from app.models import TerminalBase
            terminal_references = await TerminalBase.find(
                TerminalBase.RoleID == role.RoleID
            ).count()
            
            if terminal_references > 0:
                raise ConflictError(
                    f"Cannot delete role. Role is referenced in {terminal_references} terminals.",
                    conflicting_field="RoleIDs"
                )
            
            await role.delete()
            
            logger.info(f"Deleted role: {role_id}")
            return True
            
        except Exception as e:
            if isinstance(e, (NotFoundError, ValidationError, ConflictError)):
                raise
            logger.error(f"Error deleting role {role_id}: {str(e)}")
            raise DatabaseError(f"Failed to delete role: {str(e)}")
    
    @staticmethod
    async def count_roles(role_type: Optional[str] = None) -> int:
        """Count roles with optional type filter"""
        try:
            query = {}
            if role_type:
                query["Type"] = role_type
            
            return await RolesBase.find(query).count()
            
        except Exception as e:
            logger.error(f"Error counting roles: {str(e)}")
            raise DatabaseError(f"Failed to count roles: {str(e)}")
    
    @staticmethod
    async def validate_role_id_integrity(role_ids: List[str]) -> Dict[str, bool]:
        """Validate that all role IDs exist and have proper format"""
        try:
            results = {}
            
            # Get valid prefixes from config
            valid_prefixes = [pattern.split("-")[0] for pattern in settings.role_id_patterns.values()]
            
            for role_id in role_ids:
                # Check format (should be prefix_userid format now)
                if not any(role_id.startswith(f"{prefix}_") for prefix in valid_prefixes):
                    results[role_id] = False
                    continue
                
                # Check existence
                role = await RolesBase.find_one(RolesBase.RoleID == role_id)
                results[role_id] = role is not None
            
            return results
            
        except Exception as e:
            logger.error(f"Error validating role ID integrity: {str(e)}")
            return {role_id: False for role_id in role_ids}
    
    @staticmethod
    async def get_roles_by_user_email(user_email: str) -> List[RolesBaseResponse]:
        """Get all roles for a specific user"""
        try:
            roles = await RolesBase.find(RolesBase.UserEmailID == user_email).to_list()
            return [_convert_role_to_response(role) for role in roles]
            
        except Exception as e:
            logger.error(f"Error getting roles for user {user_email}: {str(e)}")
            raise DatabaseError(f"Failed to get roles for user: {str(e)}")
    
    @staticmethod
    async def get_roles_by_type(role_type: str) -> List[RolesBaseResponse]:
        """Get all roles by Type"""
        try:
            roles = await RolesBase.find(RolesBase.Type == role_type).to_list()
            return [_convert_role_to_response(role) for role in roles]
            
        except Exception as e:
            logger.error(f"Error getting roles by type {role_type}: {str(e)}")
            raise DatabaseError(f"Failed to get roles by type: {str(e)}")
    
    @staticmethod
    async def get_roles_by_industry(industry: str) -> List[RolesBaseResponse]:
        """Get all roles by Industry"""
        try:
            roles = await RolesBase.find(RolesBase.Industry == industry).to_list()
            return [_convert_role_to_response(role) for role in roles]
            
        except Exception as e:
            logger.error(f"Error getting roles by industry {industry}: {str(e)}")
            raise DatabaseError(f"Failed to get roles by industry: {str(e)}")