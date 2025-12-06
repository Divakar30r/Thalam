# Response Models for API endpoints

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from .order_models import StreamingResponseStatus

class BaseResponse(BaseModel):
    success: bool
    message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class OrderResponse(BaseResponse):
    order_req_id: Optional[str] = None
    session_id: Optional[str] = None

class ProposalResponse(BaseResponse):
    proposal_id: Optional[str] = None
    order_req_id: Optional[str] = None

class StreamingResponse(BaseModel):
    order_req_id: str
    streaming_response_status: StreamingResponseStatus
    proposal_id: Optional[str] = None
    follow_up_id: Optional[str] = None
    message: Optional[str] = None

class HealthResponse(BaseModel):
    status: str = "healthy"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    service: str
    version: str = "1.0.0"

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class ErrorResponse(BaseModel):
    error: bool = True
    message: str
    error_code: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }