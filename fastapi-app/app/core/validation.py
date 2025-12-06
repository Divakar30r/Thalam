"""
Custom validation functions for the FastAPI application
"""

import re
from typing import List, Dict, Any, Optional
from email_validator import validate_email, EmailNotValidError

from app.core.config import settings
from app.core.exceptions import ValidationError


class ValidationFunctions:
    """Collection of custom validation functions"""
    
    @staticmethod
    def validate_email_domain(email: str) -> bool:
        """Validate that email belongs to the required domain"""
        try:
            # Validate email format first
            validated_email = validate_email(email)
            normalized_email = validated_email.email
            
            # Check domain
            if not normalized_email.endswith(settings.email_domain):
                return False
            
            return True
            
        except EmailNotValidError:
            return False
    
    @staticmethod
    def validate_role_id_format(role_id: str, role_type: str) -> bool:
        """Validate RoleID format matches the expected pattern for role type"""
        try:
            pattern = settings.role_id_patterns.get(role_type)
            if not pattern:
                return False
            
            # Extract prefix from pattern (e.g., "ADM" from "ADM-{:04d}")
            prefix = pattern.split("-")[0]
            
            # Check if role_id matches the pattern
            role_pattern = f"^{prefix}-\\d{{4}}$"
            return bool(re.match(role_pattern, role_id))
            
        except Exception:
            return False
    
    @staticmethod
    def validate_contact_numbers(contact_numbers: List[str]) -> bool:
        """Validate contact number format"""
        if not contact_numbers:
            return False
        
        # Basic phone number validation (can be enhanced)
        phone_pattern = r"^\+?[\d\-\s\(\)]+$"
        
        for number in contact_numbers:
            if not re.match(phone_pattern, number):
                return False
            
            # Check length (basic validation)
            digits_only = re.sub(r"[^\d]", "", number)
            if len(digits_only) < 7 or len(digits_only) > 15:
                return False
        
        return True
    
    @staticmethod
    def validate_aadhar_number(aadhar: str) -> bool:
        """Validate AADHAR number format"""
        if not aadhar:
            return True  # AADHAR is optional
        
        # AADHAR should be 12 digits
        aadhar_pattern = r"^\d{12}$"
        
        if not re.match(aadhar_pattern, aadhar):
            return False
        
        # Basic checksum validation (simplified)
        # In production, you might want to implement the full Verhoeff algorithm
        return True
    
    @staticmethod
    def validate_terminal_id_format(terminal_id: str) -> bool:
        """Validate TerminalID format"""
        # Terminal ID should be alphanumeric with possible hyphens/underscores
        terminal_pattern = r"^[A-Za-z0-9_-]{3,20}$"
        return bool(re.match(terminal_pattern, terminal_id))
    
    @staticmethod
    def validate_coordinates(longitude: float, latitude: float) -> bool:
        """Validate geographic coordinates"""
        return (-180 <= longitude <= 180) and (-90 <= latitude <= 90)
    
    @staticmethod
    def validate_capacity_values(
        cold_storage: int,
        volume: int,
        weight: int
    ) -> bool:
        """Validate capacity values are positive"""
        return all(value > 0 for value in [cold_storage, volume, weight])
    
    @staticmethod
    def validate_status_value(status: str) -> bool:
        """Validate status is either Active or Inactive"""
        return status in ["Active", "Inactive"]
    
    @staticmethod
    def validate_role_type(role_type: str) -> bool:
        """Validate role type is one of the allowed types"""
        allowed_types = ["Admin", "Manager", "Operator", "TerminalOwner"]
        return role_type in allowed_types


# MongoDB validation helper functions (replicate JavaScript validation logic)
class MongoValidationHelpers:
    """Helper functions that replicate MongoDB validation logic"""
    
    @staticmethod
    async def validate_user_exists_by_email(email: str) -> bool:
        """Validate that a user with the given email exists"""
        from app.services import UserService
        try:
            user = await UserService.get_user_by_email(email)
            return user is not None
        except Exception:
            return False
    
    @staticmethod
    async def validate_role_id_integrity(role_ids: List[str]) -> Dict[str, bool]:
        """Validate that all role IDs exist and have proper format"""
        from app.services import RoleService
        try:
            return await RoleService.validate_role_id_integrity(role_ids)
        except Exception:
            return {role_id: False for role_id in role_ids}
    
    @staticmethod
    async def create_role_with_validation(
        role_type: str,
        location_coords: Dict[str, float],
        user_email: str
    ) -> Dict[str, Any]:
        """Create role with comprehensive validation (replicates MongoDB function)"""
        from app.services import RoleService
        from app.models import RolesBaseCreate, GeoJSONPoint
        
        try:
            # Validate user exists
            user_exists = await MongoValidationHelpers.validate_user_exists_by_email(user_email)
            if not user_exists:
                return {
                    "success": False,
                    "error": f"User with email {user_email} does not exist"
                }
            
            # Validate role type
            if not ValidationFunctions.validate_role_type(role_type):
                return {
                    "success": False,
                    "error": f"Invalid role type: {role_type}"
                }
            
            # Validate coordinates
            if not ValidationFunctions.validate_coordinates(
                location_coords["longitude"],
                location_coords["latitude"]
            ):
                return {
                    "success": False,
                    "error": "Invalid coordinates"
                }
            
            # Create role
            role_data = RolesBaseCreate(
                Type=role_type,
                Location=GeoJSONPoint(
                    coordinates=[
                        location_coords["longitude"],
                        location_coords["latitude"]
                    ]
                ),
                UserEmailID=user_email
            )
            
            role = await RoleService.create_role(role_data)
            
            return {
                "success": True,
                "role_id": role.RoleID,
                "message": f"Role {role.RoleID} created successfully"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


# Validation utility functions
def validate_request_data(data: Dict[str, Any], required_fields: List[str]) -> List[str]:
    """Validate that all required fields are present in request data"""
    missing_fields = []
    for field in required_fields:
        if field not in data or data[field] is None:
            missing_fields.append(field)
    return missing_fields


def validate_pagination_params(skip: int, limit: int) -> None:
    """Validate pagination parameters"""
    if skip < 0:
        raise ValidationError("Skip parameter must be non-negative", field="skip")
    
    if limit < 1:
        raise ValidationError("Limit parameter must be positive", field="limit")
    
    if limit > settings.max_page_size:
        raise ValidationError(
            f"Limit parameter cannot exceed {settings.max_page_size}",
            field="limit"
        )


def validate_location_search_params(
    longitude: Optional[float],
    latitude: Optional[float],
    max_distance: Optional[float]
) -> None:
    """Validate location search parameters"""
    if (longitude is None) != (latitude is None):
        raise ValidationError(
            "Both longitude and latitude must be provided for location search",
            field="location"
        )
    
    if longitude is not None and latitude is not None:
        if not ValidationFunctions.validate_coordinates(longitude, latitude):
            raise ValidationError("Invalid coordinates", field="location")
    
    if max_distance is not None and max_distance <= 0:
        raise ValidationError(
            "Max distance must be positive", 
            field="max_distance"
        )