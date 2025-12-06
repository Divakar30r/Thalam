"""
Pydantic Models for API Request/Response validation
Separate from Beanie documents to maintain clean separation of concerns
"""

from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field, EmailStr, field_validator, ConfigDict
import re


class GeoJSONPoint(BaseModel):
    """GeoJSON Point for location data"""
    type: str = Field(default="Point", pattern="^Point$")
    coordinates: List[float] = Field(..., min_items=2, max_items=2)
    
    @field_validator('coordinates')
    @classmethod
    def validate_coordinates(cls, v):
        if len(v) != 2:
            raise ValueError('Coordinates must contain exactly 2 values')
        lng, lat = v
        if not (-180 <= lng <= 180):
            raise ValueError('Longitude must be between -180 and 180')
        if not (-90 <= lat <= 90):
            raise ValueError('Latitude must be between -90 and 90')
        return v


# === UserBase API Models ===

class UserBaseCreate(BaseModel):
    """Model for creating UserBase documents via API"""
    ShortName: str = Field(..., min_length=5, description="User short name - minimum 5 characters")
    EmailID: EmailStr = Field(..., description="Email must be from @drworkplace.microsoft.com domain")
    Location: GeoJSONPoint = Field(..., description="GeoSpatial location using GeoJSON Point format")
    Contact: List[str] = Field(..., min_items=2, description="Array of mobile numbers - minimum 2 required")
    AADHAR: Optional[str] = Field(None, description="12-digit AADHAR number - optional field")
    ProximityToTerminal: Optional[float] = Field(None, description="Distance to terminal")
    PackagingProximity: Optional[float] = Field(None, description="Distance to packaging facility")
    Status: str = Field(default="Active", description="User status")
    
    @field_validator('EmailID')
    @classmethod
    def validate_email_domain(cls, v):
        if not str(v).endswith('@drworkplace.microsoft.com'):
            raise ValueError('Email must be from @drworkplace.microsoft.com domain')
        return v
    
    @field_validator('Contact')
    @classmethod
    def validate_contact_numbers(cls, v):
        phone_pattern = re.compile(r'^[+]?[0-9]{10,15}$')
        for number in v:
            if not phone_pattern.match(number):
                raise ValueError(f'Invalid phone number format: {number}. Must be 10-15 digits with optional + prefix')
        return v
    
    @field_validator('AADHAR')
    @classmethod
    def validate_aadhar(cls, v):
        if v is not None:
            if not re.match(r'^[0-9]{12}$', v):
                raise ValueError('AADHAR must be exactly 12 digits')
        return v


class UserBaseUpdate(BaseModel):
    """Model for updating UserBase documents via API"""
    ShortName: Optional[str] = Field(None, min_length=5, description="User short name - minimum 5 characters")
    Location: Optional[GeoJSONPoint] = Field(None, description="GeoSpatial location using GeoJSON Point format")
    Contact: Optional[List[str]] = Field(None, min_items=2, description="Array of mobile numbers - minimum 2 required")
    SupabaseID: Optional[str] = Field(None, description="Supabase user id - optional field")
    AADHAR: Optional[str] = Field(None, description="12-digit AADHAR number - optional field")
    ProximityToTerminal: Optional[float] = Field(None, description="Distance to terminal")
    PackagingProximity: Optional[float] = Field(None, description="Distance to packaging facility")
    Status: Optional[str] = Field(None, description="User status")
    
    # EmailID field removed - updates should be identified by EmailID but cannot change EmailID
    
    @field_validator('Contact')
    @classmethod
    def validate_contact_numbers(cls, v):
        if v is not None:
            phone_pattern = re.compile(r'^[+]?[0-9]{10,15}$')
            for number in v:
                if not phone_pattern.match(number):
                    raise ValueError(f'Invalid phone number format: {number}. Must be 10-15 digits with optional + prefix')
        return v
    
    @field_validator('AADHAR')
    @classmethod
    def validate_aadhar(cls, v):
        if v is not None:
            if not re.match(r'^[0-9]{12}$', v):
                raise ValueError('AADHAR must be exactly 12 digits')
        return v


class UserBaseResponse(BaseModel):
    """Response model for UserBase API"""
    id: str = Field(..., description="Document ID")
    ShortName: str = Field(..., description="User short name")
    EmailID: str = Field(..., description="User email address")
    Location: GeoJSONPoint = Field(..., description="User location")
    Contact: List[str] = Field(..., description="Contact numbers")
    SupabaseID: Optional[str] = Field(None, description="Supabase user id")
    AADHAR: Optional[str] = Field(None, description="AADHAR number")
    ProximityToTerminal: Optional[float] = Field(None, description="Distance to terminal")
    PackagingProximity: Optional[float] = Field(None, description="Distance to packaging facility")
    Status: str = Field(..., description="User status")
    CreatedTime: datetime = Field(..., description="Creation timestamp")
    ModifiedTime: datetime = Field(..., description="Last modification timestamp")
    
    model_config = ConfigDict(from_attributes=True)


# === RolesBase API Models ===

class RolesBaseCreate(BaseModel):
    """Model for creating RolesBase documents via API"""
    Type: str = Field(..., description="Role type - must be one of: Seller, Buyer, TerminalOwner")
    Location: GeoJSONPoint = Field(..., description="GeoSpatial location using GeoJSON Point format")
    UserEmailID: EmailStr = Field(..., description="Email ID from UserBase - used to generate RoleID")
    Industry: Optional[str] = Field(None, description="Industry - mandatory when Type is Seller")
    
    @field_validator('Type')
    @classmethod
    def validate_type(cls, v):
        valid_types = ["Seller", "Buyer", "TerminalOwner"]
        if v not in valid_types:
            raise ValueError(f'Role type must be one of: {", ".join(valid_types)}')
        return v
    
    @field_validator('Industry')
    @classmethod
    def validate_industry(cls, v, info):
        role_type = info.data.get('Type')
        if role_type == 'Seller' and not v:
            raise ValueError('Industry is mandatory when Type is "Seller"')
        return v
    
    @field_validator('UserEmailID')
    @classmethod
    def validate_email_domain(cls, v):
        if not str(v).endswith('@drworkplace.microsoft.com'):
            raise ValueError('Email must be from @drworkplace.microsoft.com domain')
        return v


class RolesBaseUpdate(BaseModel):
    """Model for updating RolesBase documents via API"""
    Location: Optional[GeoJSONPoint] = Field(None, description="GeoSpatial location using GeoJSON Point format")
    UserEmailID: Optional[EmailStr] = Field(None, description="Email ID from UserBase")
    Industry: Optional[str] = Field(None, description="Industry")
    
    @field_validator('UserEmailID')
    @classmethod
    def validate_email_domain(cls, v):
        if v is not None and not str(v).endswith('@drworkplace.microsoft.com'):
            raise ValueError('Email must be from @drworkplace.microsoft.com domain')
        return v


class RolesBaseResponse(BaseModel):
    """Response model for RolesBase API"""
    id: str = Field(..., description="Document ID")
    Type: str = Field(..., description="Role type")
    RoleID: str = Field(..., description="Generated role identifier")
    Location: GeoJSONPoint = Field(..., description="Role location")
    Industry: Optional[str] = Field(None, description="Industry - mandatory for Seller")
    CreatedTime: datetime = Field(..., description="Creation timestamp")
    ModifiedTime: datetime = Field(..., description="Last modification timestamp")
    
    model_config = ConfigDict(from_attributes=True)


# === TerminalBase API Models ===

class TerminalBaseCreate(BaseModel):
    """Model for creating TerminalBase documents via API - matches latest MongoDB schema"""
    RoleID: str = Field(..., description="Role ID - must reference a TerminalOwner from RolesBase collection (TMN_ prefix)")
    ColdStorage: bool = Field(..., description="Cold storage capability - required boolean field")
    Volume: float = Field(..., ge=0, description="Storage volume capacity - required positive number")
    Weight: float = Field(..., ge=0, description="Weight capacity - required positive number") 
    PerishableScope: bool = Field(..., description="Perishable goods handling capability - required boolean field")
    IntegratedCircuit: Optional[bool] = Field(None, description="Integrated circuit capability - optional boolean field")
    
    @field_validator('RoleID')
    @classmethod
    def validate_role_id_format(cls, v):
        # Validate RoleID format matches MongoDB pattern
        pattern = r'^TMN_[a-zA-Z0-9._%+-]+@drworkplace\.microsoft\.com$'
        if not re.match(pattern, v):
            raise ValueError('RoleID must follow format: TMN_email@drworkplace.microsoft.com')
        return v


class TerminalBaseUpdate(BaseModel):
    """Model for updating TerminalBase documents via API"""
    ColdStorage: Optional[bool] = Field(None, description="Cold storage capability")
    Volume: Optional[float] = Field(None, ge=0, description="Storage volume capacity")
    Weight: Optional[float] = Field(None, ge=0, description="Weight capacity")
    PerishableScope: Optional[bool] = Field(None, description="Perishable goods handling capability")
    IntegratedCircuit: Optional[bool] = Field(None, description="Integrated circuit capability")


class TerminalBaseResponse(BaseModel):
    """Response model for TerminalBase API"""
    id: str = Field(..., description="Document ID")
    RoleID: str = Field(..., description="Terminal role identifier")
    ColdStorage: bool = Field(..., description="Cold storage capability")
    Volume: float = Field(..., description="Storage volume capacity")
    Weight: float = Field(..., description="Weight capacity")
    PerishableScope: bool = Field(..., description="Perishable goods handling capability")
    IntegratedCircuit: Optional[bool] = Field(None, description="Integrated circuit capability")
    CreatedTime: datetime = Field(..., description="Creation timestamp")
    ModifiedTime: datetime = Field(..., description="Last modification timestamp")
    
    model_config = ConfigDict(from_attributes=True)


# === OrderReq API Models ===


class OrderReqNoteContent(BaseModel):
    """Content structure for OrderReq notes"""
    URLs: List[str] = Field(default_factory=list, description="List of URLs")
    MessageType: str = Field(default="", description="Message type")
    Message: str = Field(default="", description="Message content")


class OrderReqNote(BaseModel):
    """Note object inside OrderReq"""
    FollowUpID: str = Field(..., description="Follow-up ID - client-supplied UUID placeholder; server will convert to final FollowUpID")
    Audience: List[str] = Field(..., min_items=1, description="List of ProposalIDs - mandatory if notes are present")
    Content: OrderReqNoteContent = Field(..., description="Note content")

    # NOTE: FollowUpID is a required client-supplied UUID placeholder for idempotency/caching.
    # The server will convert this UUID placeholder into the canonical FollowUpID when persisting.


class OrderReqDocument(BaseModel):
    """Document object inside OrderReq for S3 file metadata"""
    S3Key: str = Field(..., alias="s3_key", description="S3 object key - mandatory")
    FileName: str = Field(..., alias="file_name", description="Original file name - mandatory")
    ContentType: str = Field(..., alias="content_type", description="MIME type of the file - mandatory")
    FileSize: Optional[int] = Field(None, alias="file_size", description="File size in bytes - optional")
    Checksum: Optional[str] = Field(None, alias="checksum", description="File checksum - optional")
    UserEmail: Optional[str] = Field(None, alias="user_email", description="Email of user who uploaded - optional")
    OrderReqID: str = Field(..., alias="order_req_id", description="Associated OrderReqID - mandatory")
    Label: Optional[str] = Field(None, alias="label", description="Document label/description - optional")
    Notes: Optional[str] = Field(None, alias="notes", description="Additional notes about the document - optional")
    BucketName: Optional[str] = Field(None, alias="bucket_name", description="S3 bucket name - optional")
    SSEAlgorithm: Optional[str] = Field(None, alias="sse_algorithm", description="Server-side encryption algorithm - optional")
    UploadStatus: Optional[str] = Field(None, alias="upload_status", description="Upload status - optional")
    PresignedUploadURL: Optional[str] = Field(None, alias="presigned_upload_url", description="Presigned URL for upload - optional")
    PublicURL: Optional[str] = Field(None, alias="public_url", description="Public URL for the file - optional")
    PublicURLExpiry: Optional[datetime] = Field(None, alias="public_url_expiry", description="Public URL expiry time - optional")
    CreatedAt: Optional[datetime] = Field(None, alias="created_at", description="Document creation timestamp - optional")
    UpdatedAt: Optional[datetime] = Field(None, alias="updated_at", description="Document update timestamp - optional")
    UploadedAt: Optional[datetime] = Field(None, alias="uploaded_at", description="Upload completion timestamp - optional")
    IsDeleted: Optional[bool] = Field(False, alias="is_deleted", description="Soft delete flag - defaults to False")
    DeletedAt: Optional[datetime] = Field(None, alias="deleted_at", description="Timestamp when document was deleted - optional")
    DeletedBy: Optional[str] = Field(None, alias="deleted_by", description="Email of user who deleted the document - optional")

    model_config = ConfigDict(populate_by_name=True)


class OrderReqDocumentUpdate(BaseModel):
    """Model for updating document metadata - all fields optional for partial updates"""
    FileName: Optional[str] = Field(None, alias="file_name", description="Original file name")
    FileSize: Optional[int] = Field(None, alias="file_size", description="File size in bytes")
    Checksum: Optional[str] = Field(None, alias="checksum", description="File checksum")
    Label: Optional[str] = Field(None, alias="label", description="Document label/description")
    Notes: Optional[str] = Field(None, alias="notes", description="Additional notes about the document")
    UploadStatus: Optional[str] = Field(None, alias="upload_status", description="Upload status (e.g., pending, uploading, completed, failed)")
    PresignedUploadURL: Optional[str] = Field(None, alias="presigned_upload_url", description="Presigned URL for upload")
    PublicURL: Optional[str] = Field(None, alias="public_url", description="Public URL for the file")
    PublicURLExpiry: Optional[datetime] = Field(None, alias="public_url_expiry", description="Public URL expiry time")
    UploadedAt: Optional[datetime] = Field(None, alias="uploaded_at", description="Upload completion timestamp")

    model_config = ConfigDict(populate_by_name=True)


class ProductObj(BaseModel):
    """Product object inside OrderReq"""
    ProductName: str = Field(..., description="Product name - mandatory")
    ProductSeq: str = Field(..., description="Product sequence id - mandatory")
    Quantity: str = Field(..., description="Quantity required - mandatory (string allows units or descriptors)")
    factors: dict = Field(..., description="Dynamic factors for the product - mandatory")


class OrderReqCreate(BaseModel):
    RequestorEmailID: str = Field(..., description="Email of the user who raised the order - mandatory")
    Industry: str = Field(..., description="Industry for the order - mandatory")
    OrderReqStatus: Optional[str] = Field(None, description="Order request status - optional")
    Products: List[ProductObj] = Field(..., min_items=1, description="List of product objects - mandatory")
    DeliveryDate: datetime = Field(..., description="Delivery date - mandatory")
    SubmissionTime: Optional[datetime] = Field(None, description="Submission time - mandatory if OrderReqStatus is not 'Draft'")
    Notes: Optional[List[OrderReqNote]] = Field(None, description="Optional notes array - allowed only if OrderReqStatus is not 'Draft'")
    Documents: Optional[List[OrderReqDocument]] = Field(None, description="Optional documents array - can be empty during creation")
    Interested_Roles: Optional[List[str]] = Field(None, description="List of interested role email IDs")
    
    @field_validator('SubmissionTime')
    @classmethod
    def validate_submission_time(cls, v, info):
        status = info.data.get('OrderReqStatus')
        if status and status != 'Draft' and not v:
            raise ValueError('SubmissionTime is mandatory when OrderReqStatus is not "Draft"')
        return v
    
    @field_validator('Notes')
    @classmethod
    def validate_notes(cls, v, info):
        status = info.data.get('OrderReqStatus')
        if v and status == 'Draft':
            raise ValueError('Notes are not allowed when OrderReqStatus is "Draft"')
        # On create, callers must NOT provide FollowUpID values for notes — server generates them.
        if v:
            for note in v:
                # note may be model instance or dict depending on validation order
                followup = getattr(note, 'FollowUpID', None) if hasattr(note, '__dict__') else note.get('FollowUpID')
                if followup:
                    raise ValueError('FollowUpID must not be provided when creating an OrderReq; it is generated by the server')
        return v


class OrderReqUpdate(BaseModel):
    Industry: Optional[str] = Field(None, description="Industry for the order")
    OrderReqStatus: Optional[str] = Field(None, description="Order request status")
    Products: Optional[List[ProductObj]] = Field(None, description="List of product objects")
    DeliveryDate: Optional[datetime] = Field(None, description="Delivery date")
    SubmissionTime: Optional[datetime] = Field(None, description="Submission time")
    Notes: Optional[List[OrderReqNote]] = Field(None, description="Notes array")
    Documents: Optional[List[OrderReqDocument]] = Field(None, description="Documents array")
    Interested_Roles: Optional[List[str]] = Field(None, description="List of interested role email IDs")


class OrderReqResponse(BaseModel):
    id: str = Field(..., description="Document ID")
    OrderReqID: str = Field(..., description="Generated OrderReq identifier")
    RequestorEmailID: str = Field(..., description="Requestor email")
    OrderReqStatus: Optional[str] = Field(None, description="Order request status")
    Industry: str = Field(..., description="Industry for the order")
    Products: List[ProductObj] = Field(..., description="Product list")
    DeliveryDate: datetime = Field(..., description="Delivery date")
    SubmissionTime: Optional[datetime] = Field(None, description="Submission time")
    Notes: Optional[List[OrderReqNote]] = Field(None, description="Notes")
    Documents: Optional[List[OrderReqDocument]] = Field(None, description="Documents")
    Interested_Roles: Optional[List[str]] = Field(None, description="Interested roles")
    createdAt: datetime = Field(..., description="Creation timestamp")
    updatedAt: datetime = Field(..., description="Update timestamp")

    model_config = ConfigDict(from_attributes=True)


# === Legacy Model Structures (if needed for backward compatibility) ===

class TerminalCapacity(BaseModel):
    """Terminal capacity structure - legacy model"""
    ColdStorageLimit: int = Field(..., ge=0, description="Cold storage capacity limit")
    VolumeLimit: int = Field(..., ge=0, description="Volume capacity limit") 
    WeightLimit: int = Field(..., ge=0, description="Weight capacity limit")


class TerminalCapabilities(BaseModel):
    """Terminal capabilities structure - legacy model"""
    ColdStorage: bool = Field(..., description="Cold storage capability")
    Weighing: bool = Field(..., description="Weighing capability") 
    Packaging: bool = Field(..., description="Packaging capability")
    Sorting: bool = Field(..., description="Sorting capability")


# === RoleDetails API Models ===

class RoleDetailsCreate(BaseModel):
    """Model for creating RoleDetails documents via API"""
    Industry: str = Field(..., description="Industry type (e.g., Pharma, Food)")
    Scale: str = Field(..., description="Scale type (e.g., Retail, Wholesale)")
    factors: dict = Field(..., description="Dynamic factors configuration with keys and values")


class RoleDetailsUpdate(BaseModel):
    """Model for updating RoleDetails documents via API"""
    Industry: Optional[str] = Field(None, description="Industry type")
    Scale: Optional[str] = Field(None, description="Scale type")
    factors: Optional[dict] = Field(None, description="Dynamic factors configuration")


class RoleDetailsResponse(BaseModel):
    """Response model for RoleDetails API"""
    id: str = Field(..., description="Document ID")
    Industry: str = Field(..., description="Industry type")
    Scale: str = Field(..., description="Scale type")
    factors: dict = Field(..., description="Dynamic factors configuration")
    createdAt: datetime = Field(..., description="Creation timestamp")
    updatedAt: datetime = Field(..., description="Last update timestamp")
    
    model_config = ConfigDict(from_attributes=True)


class RequiredFactorsResponse(BaseModel):
    """Response model for required factors by industry"""
    Industry: str = Field(..., description="Industry type")
    required_factors: dict = Field(..., description="Required factors with '*' suffix keys")


# === OrderProposal API Models ===

class ProposalNoteContent(BaseModel):
    """Content structure for proposal notes"""
    URLs: List[str] = Field(default_factory=list, description="List of URLs")
    MessageType: str = Field(default="", description="Message type")
    Message: str = Field(default="", description="Message content")


class ProposalNote(BaseModel):
    """Note object inside OrderProposal"""
    FollowUpID: str = Field(..., description="Follow-up ID - mandatory if Notes is present")
    Content: ProposalNoteContent = Field(..., description="Note content")



class ProposalUserEdit(BaseModel):
    """User edit object inside OrderProposal"""
    OrderFollowUpID: str = Field(..., description="Follow-up ID from order-request Notes - mandatory if UserEdits exists")


class ProposalProduct(BaseModel):
    """Product object inside OrderProposal"""
    ProductName: str = Field(..., description="Product name - mandatory")
    ProductSeq: Optional[str] = Field(None, description="Product sequence id")
    Quantity: Optional[str] = Field(None, description="Quantity required")
    factors: dict = Field(default_factory=dict, description="Dynamic factors for the product")
    Price: float = Field(..., description="Product price - mandatory")
    DeliveryDate: datetime = Field(..., description="Product delivery date - mandatory")


class OrderProposalCreate(BaseModel):
    """Model for creating OrderProposal documents via API"""
    OrderReqID: str = Field(..., description="Order request ID - mandatory, must exist in OrderRequest collection")
    ProposerEmailID: EmailStr = Field(..., description="Email of the user proposing - mandatory")
    ProposalStatus: str = Field(..., description="Proposal status - mandatory")
    SubmissionTime: Optional[datetime] = Field(None, description="Submission time - mandatory if ProposalStatus is not 'Draft'")
    Industry: str = Field(..., description="Industry for the proposal - mandatory")
    Products: List[ProposalProduct] = Field(..., min_items=1, description="List of product objects - mandatory")
    TotalAmount: float = Field(..., description="Total amount - mandatory")
    DeliveryDate: datetime = Field(..., description="Delivery date - mandatory")
    Notes: Optional[List[ProposalNote]] = Field(None, description="Optional notes array")
    UserEdits: Optional[List[ProposalUserEdit]] = Field(None, description="Optional user edits array")
    
    @field_validator('ProposerEmailID')
    @classmethod
    def validate_email_domain(cls, v):
        if not str(v).endswith('@drworkplace.microsoft.com'):
            raise ValueError('Email must be from @drworkplace.microsoft.com domain')
        return v

    @field_validator('SubmissionTime')
    @classmethod
    def validate_submission_time(cls, v, info):
        status = info.data.get('ProposalStatus')
        if status and status != 'Draft' and not v:
            raise ValueError("SubmissionTime is mandatory when ProposalStatus is not 'Draft'")
        return v


class OrderProposalUpdate(BaseModel):
    """Model for updating OrderProposal documents via API"""
    ProposalStatus: Optional[str] = Field(None, description="Proposal status")
    SubmissionTime: Optional[datetime] = Field(None, description="Submission time")
    Industry: Optional[str] = Field(None, description="Industry for the proposal")
    Products: Optional[List[ProposalProduct]] = Field(None, description="List of product objects")
    TotalAmount: Optional[float] = Field(None, description="Total amount")
    DeliveryDate: Optional[datetime] = Field(None, description="Delivery date")
    Notes: Optional[List[ProposalNote]] = Field(None, description="Notes array")
    UserEdits: Optional[List[ProposalUserEdit]] = Field(None, description="User edits array")


class OrderProposalResponse(BaseModel):
    """Response model for OrderProposal API"""
    id: str = Field(..., description="Document ID")
    ProposalID: str = Field(..., description="Generated Proposal identifier")
    OrderReqID: str = Field(..., description="Order request ID")
    ProposerEmailID: str = Field(..., description="Proposer email")
    ProposalStatus: str = Field(..., description="Proposal status")
    Industry: str = Field(..., description="Industry")
    Products: List[ProposalProduct] = Field(..., description="Product list")
    TotalAmount: float = Field(..., description="Total amount")
    DeliveryDate: datetime = Field(..., description="Delivery date")
    SubmissionTime: Optional[datetime] = Field(None, description="Submission time")
    Notes: Optional[List[ProposalNote]] = Field(None, description="Notes")
    UserEdits: Optional[List[ProposalUserEdit]] = Field(None, description="User edits")
    createdAt: datetime = Field(..., description="Creation timestamp")
    updatedAt: datetime = Field(..., description="Update timestamp")
    
    model_config = ConfigDict(from_attributes=True)


# === MongoDB Validation Error Responses ===

class MongoValidationError(BaseModel):
    """MongoDB validation error response"""
    collection: str = Field(..., description="Collection name where validation failed")
    field: str = Field(..., description="Field that failed validation")
    message: str = Field(..., description="MongoDB validation message")
    value: str = Field(..., description="Value that failed validation")
    
    @classmethod
    def from_mongo_error(cls, collection: str, field: str, value: str):
        """Create validation error from MongoDB schema"""
        from .documents import get_mongodb_validation_message
        
        return cls(
            collection=collection,
            field=field,
            message=get_mongodb_validation_message(collection, field),
            value=str(value)
        )


class ValidationErrorResponse(BaseModel):
    """API validation error response"""
    error: str = "validation_error"
    details: List[MongoValidationError] = Field(..., description="Validation error details")
    mongodb_schema_message: str = Field(..., description="Original MongoDB validation message")