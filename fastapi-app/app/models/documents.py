"""
Beanie ODM Document Models for MongoDB Collections
These mirror the exact MongoDB schema validations from the collection scripts
"""

from typing import List, Optional
from datetime import datetime, timezone
from beanie import Document
from pymongo import IndexModel
from pydantic import Field


class GeoJSONPoint:
    """GeoJSON Point structure - matches MongoDB schema exactly"""
    def __init__(self, coordinates: List[float]):
        self.type = "Point"
        self.coordinates = coordinates


class UserBase(Document):
    """
    UserBase collection document
    Mirrors MongoDB validation: required=["ShortName", "EmailID", "Location", "Contact"]
    """
    
    # Required fields - exactly as defined in MongoDB schema
    ShortName: str  # minLength: 5 (validated by MongoDB)
    EmailID: str    # pattern: ^[a-zA-Z0-9._%+-]+@drworkplace\.microsoft\.com$ (validated by MongoDB)
    Location: dict  # GeoJSON Point structure (validated by MongoDB)
    Contact: List[str]  # minItems: 2, pattern: ^[+]?[0-9]{10,15}$ (validated by MongoDB)
    
    # Optional fields
    SupabaseID: Optional[str] = None  # Supabase user id, defaults to EmailID
    AADHAR: Optional[str] = None  # pattern: ^[0-9]{12}$ when present (validated by MongoDB)
    ProximityToTerminal: Optional[float] = None
    PackagingProximity: Optional[float] = None
    Status: str = "Active"  # Default status
    
    # Audit fields - fixed datetime usage
    CreatedTime: datetime = None
    ModifiedTime: datetime = None
    
    def __init__(self, **data):
        # Set SupabaseID to EmailID if not provided
        if 'SupabaseID' not in data or data['SupabaseID'] is None:
            data['SupabaseID'] = data.get('EmailID')
        
        if 'CreatedTime' not in data:
            data['CreatedTime'] = datetime.now(timezone.utc)
        if 'ModifiedTime' not in data:
            data['ModifiedTime'] = datetime.now(timezone.utc)
        super().__init__(**data)
    
    class Settings:
        name = "UserBase"
        # Only essential indexes - geospatial and unique constraints
        indexes = [
            IndexModel([("EmailID", 1)], unique=True),  # Business requirement
            IndexModel([("Location", "2dsphere")]),     # Geospatial queries
            IndexModel([("AADHAR", 1)], unique=True, sparse=True),  # Unique when present
        ]


class RolesBase(Document):
    """
    RolesBase collection document
    Mirrors MongoDB validation: required=["Type", "RoleID", "Location"]
    """
    
    # Required fields - exactly as defined in MongoDB schema
    Type: str       # enum: ["Seller", "Buyer", "TerminalOwner"] (validated by MongoDB)
    RoleID: str     # pattern: ^(SEL|BUYER|TMN)_[a-zA-Z0-9._%+-]+@drworkplace\.microsoft\.com$ (validated by MongoDB)
    Location: dict  # GeoJSON Point structure (validated by MongoDB)
    
    # Conditional mandatory field
    Industry: Optional[str] = None  # Mandatory when Type is "Seller"
    
    # Audit fields - fixed datetime usage
    CreatedTime: datetime = None
    ModifiedTime: datetime = None
    
    def __init__(self, **data):
        if 'CreatedTime' not in data:
            data['CreatedTime'] = datetime.now(timezone.utc)
        if 'ModifiedTime' not in data:
            data['ModifiedTime'] = datetime.now(timezone.utc)
        super().__init__(**data)
    
    class Settings:
        name = "RolesBase"
        # Only essential indexes - unique constraints and geospatial
        indexes = [
            IndexModel([("RoleID", 1)], unique=True),   # Business requirement
            IndexModel([("Location", "2dsphere")]),     # Geospatial queries
            IndexModel([("Type", 1)]),                  # Common filter
            IndexModel([("Industry", 1)]),              # Query by industry
        ]


class TerminalBase(Document):
    """
    TerminalBase collection document
    Mirrors MongoDB validation: required=["RoleID", "ColdStorage", "Volume", "Weight", "PerishableScope"]
    Updated to match the latest collection script schema
    """
    
    # Required fields - exactly as defined in MongoDB schema
    RoleID: str             # pattern: ^TMN_[a-zA-Z0-9._%+-]+@drworkplace\.microsoft\.com$ (validated by MongoDB)
    ColdStorage: bool       # boolean (validated by MongoDB)
    Volume: float           # minimum: 0 (validated by MongoDB) 
    Weight: float           # minimum: 0 (validated by MongoDB)
    PerishableScope: bool   # boolean (validated by MongoDB)
    
    # Optional fields
    IntegratedCircuit: Optional[bool] = None  # nullable boolean (validated by MongoDB)
    
    # Audit fields - fixed datetime usage
    CreatedTime: datetime = None
    ModifiedTime: datetime = None
    
    def __init__(self, **data):
        if 'CreatedTime' not in data:
            data['CreatedTime'] = datetime.now(timezone.utc)
        if 'ModifiedTime' not in data:
            data['ModifiedTime'] = datetime.now(timezone.utc)
        super().__init__(**data)
    
    class Settings:
        name = "TerminalBase"
        # Only essential indexes - unique constraints and common filters
        indexes = [
            IndexModel([("RoleID", 1)], unique=True),   # Business requirement
            IndexModel([("ColdStorage", 1)]),           # Common filter
            IndexModel([("PerishableScope", 1)]),       # Common filter
        ]


class RoleDetails(Document):
    """
    RoleDetails collection document
    Contains industry-specific configuration for role details and factors
    """
    
    # Required fields
    Industry: str    # Industry type (e.g., "Pharma", "Food", etc.)
    Scale: str       # Scale type (e.g., "Retail", "Wholesale", etc.)
    factors: dict    # Factors configuration with dynamic keys and values
    
    # Audit fields
    createdAt: datetime = None
    updatedAt: datetime = None
    
    def __init__(self, **data):
        if 'createdAt' not in data:
            data['createdAt'] = datetime.now(timezone.utc)
        if 'updatedAt' not in data:
            data['updatedAt'] = datetime.now(timezone.utc)
        super().__init__(**data)
    
    class Settings:
        name = "RoleDetails"
        # Indexes for common queries
        indexes = [
            IndexModel([("Industry", 1)]),              # Query by industry
            IndexModel([("Industry", 1), ("Scale", 1)]), # Query by industry and scale
        ]


class OrderReq(Document):
    """
    OrderReq collection document
    """

    # Generated primary key (not supplied by create request)
    OrderReqID: str

    # Requestor email (who raised the order) - mandatory on create
    RequestorEmailID: str

    # Optional status
    OrderReqStatus: Optional[str] = None

    # Industry for the order
    Industry: str

    # List of product objects
    Products: list

    # Delivery date
    DeliveryDate: datetime

    # Submission time - mandatory if ProposalStatus is not 'Draft'
    SubmissionTime: Optional[datetime] = None

    # Submission time - mandatory if OrderReqStatus is not 'Draft'
    SubmissionTime: Optional[datetime] = None

    # Notes array - optional, allowed only if OrderReqStatus is not 'Draft'
    Notes: Optional[list] = None

    # Documents array - optional, can be empty during creation
    Documents: Optional[list] = None

    # Interested roles
    Interested_Roles: Optional[list] = None

    # Audit fields
    createdAt: datetime = None
    updatedAt: datetime = None

    def __init__(self, **data):
        if 'createdAt' not in data:
            data['createdAt'] = datetime.now(timezone.utc)
        if 'updatedAt' not in data:
            data['updatedAt'] = datetime.now(timezone.utc)
        super().__init__(**data)

    class Settings:
        name = "OrderRequest"
        indexes = [
            IndexModel([("OrderReqID", 1)], unique=True),
        ]


class OrderProposal(Document):
    """
    OrderProposal collection document
    """

    # Generated primary key (not supplied by create request)
    ProposalID: str

    # Order request ID - must exist in OrderRequest collection
    OrderReqID: str

    # Proposer email (who proposed) - mandatory on create
    ProposerEmailID: str

    # Proposal status - mandatory
    ProposalStatus: str

    # Industry for the proposal
    Industry: str

    # List of product objects
    Products: list

    # Total amount - mandatory
    TotalAmount: float

    # Delivery date
    DeliveryDate: datetime

    # Optional notes array
    Notes: Optional[list] = None

    # Optional user edits array
    UserEdits: Optional[list] = None

    # Audit fields
    createdAt: datetime = None
    updatedAt: datetime = None

    def __init__(self, **data):
        if 'createdAt' not in data:
            data['createdAt'] = datetime.now(timezone.utc)
        if 'updatedAt' not in data:
            data['updatedAt'] = datetime.now(timezone.utc)
        super().__init__(**data)

    class Settings:
        name = "OrderProposal"
        indexes = [
            IndexModel([("ProposalID", 1)], unique=True),
            IndexModel([("OrderReqID", 1)]),
            IndexModel([("ProposerEmailID", 1)]),
        ]


# MongoDB Schema Validation Messages - extracted from collection scripts
MONGODB_VALIDATION_MESSAGES = {
    "UserBase": {
        "ShortName": "User short name - required field, minimum 5 characters",
        "EmailID": "Email ID - required field, must be valid email with domain @drworkplace.microsoft.com",
        "Location": "GeoSpatial location using GeoJSON Point format",
        "Contact": "Array of mobile numbers - minimum 2 required",
        "AADHAR": "12-digit AADHAR number - optional field",
        "ProximityToTerminal": "Distance to terminal - null for now",
        "PackagingProximity": "Distance to packaging facility - null for now"
    },
    "RolesBase": {
        "Type": "Role type - must be one of: Seller, Buyer, TerminalOwner",
        "RoleID": "Role ID - prefix based on type (SEL/BUYER/TMN) + underscore + EmailID from UserBase",
        "Location": "GeoSpatial location using GeoJSON Point format"
    },
    "TerminalBase": {
        "RoleID": "Role ID - must reference a TerminalOwner from RolesBase collection (TMN_ prefix)",
        "ColdStorage": "Cold storage capability - required boolean field",
        "Volume": "Storage volume capacity - required positive number",
        "Weight": "Weight capacity - required positive number",
        "PerishableScope": "Perishable goods handling capability - required boolean field",
        "IntegratedCircuit": "Integrated circuit capability - optional boolean field"
    },
    "RoleDetails": {
        "Industry": "Industry type - required field",
        "Scale": "Scale type - required field", 
        "factors": "Dynamic factors configuration with keys and values"
    }
}


def get_mongodb_validation_message(collection: str, field: str) -> str:
    """Get the exact validation message from MongoDB collection schema"""
    return MONGODB_VALIDATION_MESSAGES.get(collection, {}).get(field, f"Validation failed for {field}")