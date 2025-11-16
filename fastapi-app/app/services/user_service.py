"""
Service layer for UserBase collection operations
"""

from typing import List, Optional, Dict, Any
from bson import ObjectId
from pymongo.errors import DuplicateKeyError
from beanie.operators import In, RegEx, Near

from app.models import UserBase, UserBaseCreate, UserBaseUpdate, UserBaseResponse
from app.core.exceptions import (
    NotFoundError, 
    ConflictError, 
    ValidationError,
    DatabaseError
)
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def _convert_user_to_response(user: UserBase) -> UserBaseResponse:
    """Convert UserBase document to UserBaseResponse with proper id field"""
    return UserBaseResponse.model_validate({
        **user.model_dump(),
        "id": str(user.id)
    })


class UserService:
    @staticmethod
    async def get_user_by_supabase_id(supabase_id: str) -> Optional[UserBaseResponse]:
        """Get user by SupabaseID (unique)"""
        try:
            user = await UserBase.find_one(UserBase.SupabaseID == supabase_id)
            if not user:
                return None
            return _convert_user_to_response(user)
        except Exception as e:
            logger.error(f"Error getting user by SupabaseID {supabase_id}: {str(e)}")
            raise DatabaseError(f"Failed to get user by SupabaseID: {str(e)}")
    """Service for UserBase operations"""
    
    @staticmethod
    async def create_user(user_data: UserBaseCreate) -> UserBaseResponse:
        """Create a new user"""
        try:
            # Validate email domain
            if not user_data.EmailID.endswith(settings.email_domain):
                raise ValidationError(
                    f"Email must be from domain {settings.email_domain}",
                    field="EmailID"
                )
            
            # Check if user with email already exists
            existing_user = await UserBase.find_one(
                UserBase.EmailID == user_data.EmailID
            )
            if existing_user:
                raise ConflictError(
                    f"User with email {user_data.EmailID} already exists",
                    conflicting_field="EmailID"
                )
            
            # Create user document - exclude SupabaseID during creation
            user_dict = user_data.model_dump(exclude_none=True)
            # Ensure SupabaseID is never included during user creation
            user_dict.pop('SupabaseID', None)
 
            user_doc = UserBase(**user_dict)
            
            # Save to database
            await user_doc.insert()
            
            logger.info(f"Created user: {user_data.EmailID}")
            return _convert_user_to_response(user_doc)
            
        except DuplicateKeyError as de:
            raise ConflictError (
                f"Error details: " + str(de),
                conflicting_field="Any Unique keys"
            )
        except Exception as e:
            logger.error(f"Error creating user: {str(e)}")
            raise DatabaseError(f"Failed to create user: {str(e)}")
    
    @staticmethod
    async def get_user_by_id(user_id: str) -> UserBaseResponse:
        """Get user by ID"""
        try:
            if not ObjectId.is_valid(user_id):
                raise ValidationError("Invalid user ID format", field="user_id")
            
            user = await UserBase.get(user_id)
            if not user:
                raise NotFoundError("User", user_id)
            
            return _convert_user_to_response(user)
            
        except Exception as e:
            if isinstance(e, (NotFoundError, ValidationError)):
                raise
            logger.error(f"Error getting user {user_id}: {str(e)}")
            raise DatabaseError(f"Failed to get user: {str(e)}")
    
    @staticmethod
    async def get_user_by_email(email: str) -> Optional[UserBaseResponse]:
        """Get user by email"""
        # print statement request added for email
        print(f"Getting user by email: {email}")
        try:
            user = await UserBase.find_one(UserBase.EmailID == email)
            if not user:
                return None
            
            return _convert_user_to_response(user)
            
        except Exception as e:
            logger.error(f"Error getting user by email {email}: {str(e)}")
            raise DatabaseError(f"Failed to get user by email: {str(e)}")
    
    @staticmethod
    async def list_users(
        skip: int = 0,
        limit: int = 20,
        status: Optional[str] = None,
        search: Optional[str] = None,
        location_near: Optional[Dict[str, float]] = None,
        max_distance: Optional[float] = None
    ) -> List[UserBaseResponse]:
        """List users with optional filtering"""
        try:
            query = UserBase.find({})
            
            # Apply status filter
            if status:
                query = query.find(UserBase.Status == status)
            
            # Apply search filter (ShortName or EmailID)
            if search:
                search_regex = RegEx(search, "i")  # Case-insensitive
                query = query.find({
                    "$or": [
                        {"ShortName": search_regex},
                        {"EmailID": search_regex}
                    ]
                })
            
            # Apply location-based search
            if location_near and max_distance:
                query = query.find(
                    Near(
                        UserBase.Location,
                        longitude=location_near["longitude"],
                        latitude=location_near["latitude"],
                        max_distance=max_distance
                    )
                )
            
            # Apply pagination
            users = await query.skip(skip).limit(limit).to_list()
            
            return [_convert_user_to_response(user) for user in users]
            
        except Exception as e:
            logger.error(f"Error listing users: {str(e)}")
            raise DatabaseError(f"Failed to list users: {str(e)}")
    
    @staticmethod
    async def update_user_by_email(email: str, user_data: UserBaseUpdate) -> UserBaseResponse:
        """Update user by email - EmailID cannot be changed"""
        try:
            user = await UserBase.find_one(UserBase.EmailID == email)
            if not user:
                raise NotFoundError("User", f"email={email}")
            
            # Update fields (EmailID is excluded from UserBaseUpdate schema)
            update_data = user_data.dict(exclude_unset=True)
            await user.update({"$set": update_data})
            
            # Fetch updated user
            updated_user = await UserBase.find_one(UserBase.EmailID == email)
            
            logger.info(f"Updated user by email: {email}")
            return _convert_user_to_response(updated_user)
            
        except Exception as e:
            if isinstance(e, (NotFoundError, ValidationError)):
                raise
            logger.error(f"Error updating user by email {email}: {str(e)}")
            raise DatabaseError(f"Failed to update user: {str(e)}")
    
    @staticmethod
    async def update_user(user_id: str, user_data: UserBaseUpdate) -> UserBaseResponse:
        """Update user by ID (legacy method - consider using update_user_by_email)"""
        try:
            if not ObjectId.is_valid(user_id):
                raise ValidationError("Invalid user ID format", field="user_id")
            
            user = await UserBase.get(user_id)
            if not user:
                raise NotFoundError("User", user_id)
            
            # Update fields (EmailID is excluded from UserBaseUpdate schema)
            update_data = user_data.dict(exclude_unset=True)
            await user.update({"$set": update_data})
            
            # Fetch updated user
            updated_user = await UserBase.get(user_id)
            
            logger.info(f"Updated user: {user_id}")
            return _convert_user_to_response(updated_user)
            
        except Exception as e:
            if isinstance(e, (NotFoundError, ValidationError)):
                raise
            logger.error(f"Error updating user {user_id}: {str(e)}")
            raise DatabaseError(f"Failed to update user: {str(e)}")
    
    @staticmethod
    async def delete_user(user_id: str) -> bool:
        """Delete user"""
        try:
            if not ObjectId.is_valid(user_id):
                raise ValidationError("Invalid user ID format", field="user_id")
            
            user = await UserBase.get(user_id)
            if not user:
                raise NotFoundError("User", user_id)
            
            # Check if user is referenced in RolesBase
            from app.models import RolesBase
            role_references = await RolesBase.find(
                RolesBase.UserEmailID == user.EmailID
            ).count()
            
            if role_references > 0:
                raise ConflictError(
                    f"Cannot delete user. User is referenced in {role_references} roles.",
                    conflicting_field="UserEmailID"
                )
            
            await user.delete()
            
            logger.info(f"Deleted user: {user_id}")
            return True
            
        except Exception as e:
            if isinstance(e, (NotFoundError, ValidationError, ConflictError)):
                raise
            logger.error(f"Error deleting user {user_id}: {str(e)}")
            raise DatabaseError(f"Failed to delete user: {str(e)}")
    
    @staticmethod
    async def count_users(status: Optional[str] = None) -> int:
        """Count users with optional status filter"""
        try:
            query = {}
            if status:
                query["Status"] = status
            
            return await UserBase.find(query).count()
            
        except Exception as e:
            logger.error(f"Error counting users: {str(e)}")
            raise DatabaseError(f"Failed to count users: {str(e)}")
    
    @staticmethod
    async def validate_user_exists(email: str) -> bool:
        """Validate that a user with the given email exists"""
        try:
            user = await UserBase.find_one(UserBase.EmailID == email)
            return user is not None
            
        except Exception as e:
            logger.error(f"Error validating user existence for {email}: {str(e)}")
            return False