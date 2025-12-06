# Proposal-related Pydantic Models

from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from .order_models import MessageContent, NotesDictObj,ProcessorNotesDictObj, ProposalStatus

class ProposalDictObj(BaseModel):
    """Proposal dictionary object structure"""
    proposal_id: str = Field(alias="ProposalID")
    price: str = Field(alias="Price")
    delivery_date: str = Field(alias="DeliveryDate")
    notes_arr: List[ProcessorNotesDictObj] = Field(default=[], alias="NotesArr")

    class Config:
        allow_population_by_field_name = True

class ProposalSubmissionRequest(BaseModel):
    order_req_id: str = Field(alias="OrderReqID")
    seller_id: str = Field(alias="Seller")
    proposal_dict_obj: ProposalDictObj = Field(alias="ProposalDictObj")

    class Config:
        allow_population_by_field_name = True

class ProposalFollowUpRequest(BaseModel):
    order_req_id: str = Field(alias="OrderReqId")
    proposal_id: str = Field(alias="ProposalID")
    follow_up_id: str = Field(alias="FollowUpID")
    message: MessageContent = Field(alias="Message")

    class Config:
        allow_population_by_field_name = True

class EditLockRequest(BaseModel):
    order_req_id: str = Field(alias="OrderReqID")
    proposal_id: str = Field(alias="ProposalID")

    class Config:
        allow_population_by_field_name = True

class ProposalResponse(BaseModel):
    proposal_id: str
    status: ProposalStatus
    message: Optional[str] = None

class FollowUpResponseItem(BaseModel):
    audience: str  # ProposalID
    status: str
    added_time: str

class NonStreamingFollowUpResponse(BaseModel):
    ns_follow_up_resp: List[FollowUpResponseItem] = Field(alias="NS_FollowUpResp")

    class Config:
        allow_population_by_field_name = True