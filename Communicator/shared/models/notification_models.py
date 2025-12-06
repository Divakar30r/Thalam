# Notification and Messaging Models

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum

class MSKMessageKey(str, Enum):
    ORD_SUBMISSION = "ORD_SUBMISSION"
    ORD_UPDATES = "ORD_UPDATES"
    PRP_SUBMISSION = "PRP_SUBMISSION"
    PRP_UPDATES = "PRP_UPDATES"
    PRP_REQUEST = "PRP_REQUEST"

class MSKTopic(str, Enum):
    BUYER_ACKNOWLEDGEMENTS = "BUYER_ACKNOWLEDGEMENTS"
    BUYER_NOTIFY = "BUYER_NOTIFY"
    BUYER_FOLLOWUP = "BUYER_FOLLOWUP"
    REQ_FAILURES = "REQ_failures"
    SELLER_ACKNOWLEDGEMENTS = "SELLER_ACKNOWLEDGEMENTS"
    SELLER_NOTIFY = "SELLER_NOTIFY"
    SELLER_FOLLOWUP = "SELLER_FOLLOWUP"
    PRP_FAILURES = "PRP_FAILURES"

class MSKMessage(BaseModel):
    order_req_id: str = Field(alias="OrderReqID")
    session: str = Field(alias="SessionID")
    message: str
    timestamp: Optional[datetime] = Field(default_factory=datetime.utcnow)

    model_config = {"populate_by_name": True}

class GChatNotification(BaseModel):
    recipient: str
    message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class InitiateRequest(BaseModel):
    order_req_id: str = Field(alias="OrderReqId")
    session_id: str = Field(alias="SessionID")
    notification_type: str = Field(alias="Notification type")

    model_config = {"populate_by_name": True}

class FollowUpRequest(BaseModel):
    trn_uuid: str = Field(alias="TransactionUUID")
    audience: List[str] = Field(alias="Audience")
    message: Dict[str, Any] = Field(alias="Message")

    model_config = {"populate_by_name": True}

class APIResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)