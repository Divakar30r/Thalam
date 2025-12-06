# Shared Pydantic Models for dCent Communicator

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum

class NotificationType(str, Enum):
    GCHAT = "GChat"
    EMAIL = "Email"
    SMS = "SMS"

class OrderStatus(str, Enum):
    SUBMITTED = "SUBMITTED"
    FINALISED = "FINALISED"
    PAUSED = "PAUSED"

class ProposalStatus(str, Enum):
    SUBMITTED = "SUBMITTED"
    CLOSED = "CLOSED"
    PAUSED = "PAUSED"
    EDITLOCK = "EDITLOCK"
    PROPOSALLOCK = "PROPOSALLOCK"

class StreamingResponseStatus(str, Enum):
    NEW_PROPOSAL = "NewProposal"
    PROPOSAL_CLOSED = "ProposalClosed"
    PROPOSAL_UPDATE = "ProposalUpdate"
    ORDER_PAUSED = "OrderPaused"
    EDIT_LOCK = "EditLock"

class MessageType(str, Enum):
    TEXT = "text"
    HTML = "html"
    MARKDOWN = "markdown"

# Message Content Model
class MessageContent(BaseModel):
    urls: List[str] = Field(default_factory=list, alias="URLs")
    message_type: MessageType = Field(MessageType.TEXT, alias="MessageType")
    message: str = Field(..., alias="Message")

    model_config = {"populate_by_name": True}

# Notes Dictionary Object
class NotesDictObj(BaseModel):
    follow_up_id: str = Field(alias="FollowUpID")
    audience: List[str] = Field(default_factory=list)
    content: MessageContent
    added_time: Optional[datetime] = Field(default=None, alias="AddedTime")

    model_config = {"populate_by_name": True}

# Processor Notes Dictionary Object (optional audience for processor initialization)
class ProcessorNotesDictObj(BaseModel):
    follow_up_id: str = Field(alias="FollowUpID")
    content: Optional[MessageContent] = None
    added_time: Optional[datetime] = Field(default=None, alias="AddedTime")

    model_config = {"populate_by_name": True}

# Order Request Object
class OrderReqObj(BaseModel):
    order_req_id: str = Field(alias="OrderReqID")
    session: Optional[str] = Field(default="", alias="Session")
    notes_dict_arr: List[NotesDictObj] = Field(default_factory=list, alias="NotesDictArr")

    model_config = {"populate_by_name": True}

# Seller Dictionary Object
class SellerDictObj(BaseModel):
    seller_id: str = Field(alias="SellerID")
    distance: float = Field(alias="Distance", description="Distance in kilometers")

    model_config = {"populate_by_name": True}

# Proposal Dictionary Object
class ProposalDictObj(BaseModel):
    proposal_id: str = Field(alias="ProposalID")
    price: float = Field(alias="Price")
    delivery_date: datetime = Field(alias="DeliveryDate")
    notes_arr: List[ProcessorNotesDictObj] = Field(default_factory=list, alias="NotesArr")

    model_config = {"populate_by_name": True}

# Extended Order Request Object for Processor
class ProcessorOrderReqObj(OrderReqObj):
    seller_dict_arr: List[SellerDictObj] = Field(default_factory=list, alias="SellerDictArr")
    proposal_dict_arr: List[ProposalDictObj] = Field(default_factory=list, alias="ProposalDictArr")
    expiry: Optional[int] = Field(default=None, description="Time in milliseconds")
    
    model_config = {"populate_by_name": True}

# User Edits Object
class UserEditsObj(BaseModel):
    follow_up_id: str = Field(alias="FollowUpID")
    added_time: datetime = Field(alias="AddedTime")

    model_config = {"populate_by_name": True}