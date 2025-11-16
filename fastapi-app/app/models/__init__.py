"""
Models package for MongoDB collections and API schemas
Separated into Beanie documents and Pydantic schemas for clean architecture
"""

# Import Beanie Documents (for database operations)
from .documents import (
    UserBase,
    RolesBase, 
    TerminalBase,
    RoleDetails,
    OrderReq,
    OrderProposal,
    get_mongodb_validation_message,
    MONGODB_VALIDATION_MESSAGES
)

# Import Pydantic Schemas (for API validation)
from .schemas import (
    # GeoJSON
    GeoJSONPoint,
    
    # UserBase schemas
    UserBaseCreate,
    UserBaseUpdate, 
    UserBaseResponse,
    
    # RolesBase schemas
    RolesBaseCreate,
    RolesBaseUpdate,
    RolesBaseResponse,
    
    # TerminalBase schemas
    TerminalBaseCreate,
    TerminalBaseUpdate,
    TerminalBaseResponse,
    
    # RoleDetails schemas
    RoleDetailsCreate,
    RoleDetailsUpdate,
    RoleDetailsResponse,
    RequiredFactorsResponse,
    
    # Legacy compatibility
    TerminalCapacity,
    TerminalCapabilities,
    
    # Error responses
    MongoValidationError,
    ValidationErrorResponse
)

__all__ = [
    # Beanie Documents
    "UserBase",
    "RolesBase", 
    "TerminalBase",
    "RoleDetails",
    "OrderReq",
    "OrderProposal",
    "get_mongodb_validation_message",
    "MONGODB_VALIDATION_MESSAGES",
    
    # Pydantic Schemas
    "GeoJSONPoint",
    
    # UserBase
    "UserBaseCreate",
    "UserBaseUpdate",
    "UserBaseResponse",
    
    # RolesBase
    "RolesBaseCreate", 
    "RolesBaseUpdate",
    "RolesBaseResponse",
    
    # TerminalBase
    "TerminalBaseCreate",
    "TerminalBaseUpdate", 
    "TerminalBaseResponse",
    
    # RoleDetails
    "RoleDetailsCreate",
    "RoleDetailsUpdate",
    "RoleDetailsResponse",
    "RequiredFactorsResponse",
    
    # Legacy
    "TerminalCapacity",
    "TerminalCapabilities",
    
    # Validation
    "MongoValidationError",
    "ValidationErrorResponse"
]