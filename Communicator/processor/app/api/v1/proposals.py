from typing import List, Dict, Any, Optional
import asyncio
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from pydantic import BaseModel, Field
import logging

from shared.models.order_models import ProcessorNotesDictObj
from ...core.exceptions import ProposalUpdateException, create_http_exception
from ...services import ProposalService, NotificationService
from shared.utils.queue_manager import queue_manager
from shared.models.proposal_models import ProposalDictObj
from ..dependencies import (
    get_proposal_service, 
    get_notification_service,
    validate_order_req_id,
    validate_proposal_id,
    get_current_user
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/proposals", tags=["proposals"])

# Request/Response models
class ProposalSubmissionRequest(BaseModel):
    order_req_id: str = Field(..., alias="OrderReqId", description="Order request ID")
    seller_id: str = Field(..., alias="SellerId", description="Seller ID")
    proposal: Dict[str, Any] = Field(..., alias="Proposal", description="Proposal data")

class ProposalSubmissionResponse(BaseModel):
    success: bool = Field(..., alias="Success")
    message: str = Field(..., alias="Message")
    proposal_id: Optional[str] = Field(None, alias="ProposalId")

class FollowUpRequest(BaseModel):
    order_req_id: str = Field(..., alias="OrderReqId", description="Order request ID")
    trn_uuid: str = Field(..., alias="TransactionUUID", description="Transaction UUID / Follow-up ID")
    message: Dict[str, Any] = Field(..., alias="Message", description="Message content with URLs, MessageType, Message")

class FollowUpResponse(BaseModel):
    # Use alias FollowUpID (capital D) to match external API / internal usage
    follow_up_id: Optional[str] = Field(None, alias="FollowUpID")

class EditLockRequest(BaseModel):
    order_req_id: str = Field(..., alias="OrderReqId", description="Order request ID")
    proposal_id: str = Field(..., alias="ProposalId", description="Proposal ID")

class EditLockResponse(BaseModel):
    success: bool = Field(..., alias="Success")
    message: str = Field(..., alias="Message")

@router.post("/proposal-submissions", response_model=ProposalSubmissionResponse)
async def proposal_submissions(
    request: ProposalSubmissionRequest,
    background_tasks: BackgroundTasks,
    proposal_service: ProposalService = Depends(get_proposal_service),
    notification_service: NotificationService = Depends(get_notification_service),
    current_user: Optional[dict] = Depends(get_current_user)
):
    """
    Handle proposal submissions as per grpcdesign.yaml
    
    Logic:
    1) Invoke _UpdateProposals (mode ="ProposalSubmissions")
    2) Through AWS MSK topic 'SELLER_ACKNOWLEDGEMENTS' with message
    3) Update OrderReqIDList[].ProposalDictObj with request.ProposalDictObj
    4) Add message to OrderReqIDList[].Queuename
    """
    try:
        logger.info(f"Processing proposal submission for order: {request.order_req_id}, seller: {request.seller_id}")
        
        # Validate inputs
        order_req_id = validate_order_req_id(request.order_req_id)
        proposal_id = request.proposal.get("ProposalID", "")
        
        if not proposal_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="ProposalID is required in proposal data"
            )
        
        # Step 1: Invoke _UpdateProposals (mode ="ProposalSubmissions")
        # Create a simple proposal structure for the update and convert to ProposalDictObj
        proposal_data = [{
            "ProposalID": proposal_id,
            "Price": request.proposal.get("Price", ""),
            "DeliveryDate": request.proposal.get("DeliveryDate", ""),
            "NotesArr": request.proposal.get("NotesArr", [])
        }]

        # Convert dict(s) to ProposalDictObj instances so the service can access attributes
        try:
            proposal_objs = [ProposalDictObj.parse_obj(p) for p in proposal_data]
        except Exception:
            # Fallback to trying direct construction (handles slightly different pydantic versions)
            proposal_objs = [ProposalDictObj(**p) for p in proposal_data]

        update_result = await proposal_service.update_proposals(
            order_req_id=order_req_id,
            proposal_dict_arr=proposal_objs,
            mode="ProposalSubmissions",
            session_id=request.proposal.get("session_id")
        )
        
        # Step 2: Send acknowledgement through AWS MSK
        background_tasks.add_task(
            notification_service.send_seller_acknowledgement,
            order_req_id,
            request.proposal.get("session_id", ""),
            "Proposal Submitted"
        )

        # Step 3: Update in-memory ProcessorOrderReqObj for this order (so
        # streaming server can immediately see the new proposal and deliver
        # a NewProposal event). Uses centralized order state manager which is
        # shared between HTTP endpoints and gRPC streaming server.
        logger.info(f"Step 3: Updating in-memory order state for {order_req_id} with proposal {proposal_id}")
        try:
            # Get or create the order in centralized state (lazy init)
            # This works whether gRPC stream connected first, HTTP arrived first,
            # or stream disconnected and HTTP is adding proposals
            processor_order_req_obj = queue_manager.get_or_create_order(
                order_req_id=order_req_id,
                expiry_minutes=30,  # Will use existing expiry if order already exists
                session=request.proposal.get("session_id", "")
            )
            
            # Append the new proposal(s) to the order's proposal array
            processor_order_req_obj.proposal_dict_arr.extend(proposal_objs)
            logger.info(f"In-memory order updated: appended {len(proposal_objs)} proposal(s) to order {order_req_id}")
            
        except Exception as e:
            logger.exception(f"Failed to update in-memory order state for {order_req_id}: {str(e)}")
        
        
        
        # Step 4: Add message to queue (proposal_id + '/New')
        await queue_manager.add_to_order_queue(order_req_id, f"{proposal_id}/New")
        logger.info(f"Added queue message: {proposal_id}/New to order queue {order_req_id}")
        
        logger.info(f"Proposal submission processed successfully for order: {order_req_id}")
        
        return ProposalSubmissionResponse(
            success=True,
            message="Proposal submitted successfully",
            proposal_id=proposal_id
        )
        
    except ProposalUpdateException as e:
        logger.error(f"Proposal update error: {str(e)}")
        raise create_http_exception(e, status.HTTP_400_BAD_REQUEST)
    except HTTPException:
        # Re-raise HTTPExceptions (validation/client errors) so they are returned as intended
        raise
    except Exception as e:
        logger.exception("Unexpected error in proposal submission")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred"
        )

@router.post("/{proposal_id}/followup", response_model=FollowUpResponse)
async def ProposalFollowup(
    proposal_id: str,
    request: FollowUpRequest,
    background_tasks: BackgroundTasks,
    proposal_service: ProposalService = Depends(get_proposal_service),
    current_user: Optional[dict] = Depends(get_current_user)
):
    """
    Handle follow-up requests as per grpcdesign.yaml
    
    Logic:
    1) Update OrderReqIDList[].ProposalDictArr[].NotesDictObj
    2) Invoke _UpdateProposals with mode = ProposalUpdate
    3) Insert into OrderReqIDList[].ProposalDictArr[].NotesDictArr
    4) Add message to OrderReqIDList[].Queuename
    """
    try:
        logger.info(f"Processing follow-up for order: {request.order_req_id}, proposal: {proposal_id}")
        
        # Validate inputs
        order_req_id = validate_order_req_id(request.order_req_id)
        proposal_id = validate_proposal_id(proposal_id)
        
        # 1. Prepare note data for follow-up
        notes_data = ProcessorNotesDictObj(
            follow_up_id=request.trn_uuid,
            content=request.message
        )

        print(f"notes_data: {notes_data}    ")
        
        # Step 2: Invoke _UpdateProposals with mode = ProposalUpdate
        # Build ProposalDictObj expected by the service
        proposal_data = {
            "ProposalID": proposal_id,
            "Price": "",  # Not needed for follow-up
            "DeliveryDate": "",  # Not needed for follow-up
            "NotesArr": [notes_data]  # Will be updated with new note
        }

        try:
            proposal_obj = ProposalDictObj.parse_obj(proposal_data)
        except Exception:
            proposal_obj = ProposalDictObj(**proposal_data)

        follow_up_id_result = await proposal_service.update_proposals(
            order_req_id=order_req_id,
            proposal_dict=proposal_obj,
            mode="ProposalUpdate"
        )
        
        # Extract follow_up_id from the result
        print(f"Follow-up ID result: {follow_up_id_result}")
        follow_up_id = follow_up_id_result.get("result", {}).get("FollowUpID")
        
        if not follow_up_id:
            raise ProposalUpdateException("Failed to retrieve FollowUpID from proposal update result")
        
        # Step 4: Add message to queue (proposal_id.follow_up_id + '/Update')
        queue_message = f"{proposal_id}.{follow_up_id}/Update"
        await queue_manager.add_to_order_queue(order_req_id, queue_message)
        logger.info(f"Added queue message: {queue_message} to order queue {order_req_id}")
        
        logger.info(f"Follow-up processed successfully for order: {order_req_id}")
        
        return FollowUpResponse(
            follow_up_id=str(follow_up_id) + " successfully added"
        )
        
    except ProposalUpdateException as e:
        logger.error(f"Follow-up update error: {str(e)}")
        raise create_http_exception(e, status.HTTP_400_BAD_REQUEST)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Unexpected error in follow-up")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred"
        )

@router.post("/edit-lock", response_model=EditLockResponse)
async def edit_lock(
    request: EditLockRequest,
    background_tasks: BackgroundTasks,
    proposal_service: ProposalService = Depends(get_proposal_service),
    current_user: Optional[dict] = Depends(get_current_user)
):
    """
    Handle edit lock requests as per grpcdesign.yaml
    
    Logic:
    1) Invoke _UpdateProposals(mode = "EditLock") with request.ProposalID
    2) Add message to OrderReqIDList[].Queuename
    """
    try:
        logger.info(f"Processing edit lock for order: {request.order_req_id}, proposal: {request.proposal_id}")
        
        # Validate inputs
        order_req_id = validate_order_req_id(request.order_req_id)
        proposal_id = validate_proposal_id(request.proposal_id)
        
        # Step 1: Invoke _UpdateProposals(mode = "EditLock")
        proposal_data = [{
            "ProposalID": proposal_id,
            "Price": "",  # Not needed for edit lock
            "DeliveryDate": "",  # Not needed for edit lock
            "NotesArr": []  # Not needed for edit lock
        }]

        try:
            proposal_objs = [ProposalDictObj.parse_obj(p) for p in proposal_data]
        except Exception:
            proposal_objs = [ProposalDictObj(**p) for p in proposal_data]

        update_result = await proposal_service.update_proposals(
            order_req_id=order_req_id,
            proposal_dict_arr=proposal_objs,
            mode="EditLock"
        )
        
        # Step 2: Add message to queue (proposal_id + '/EditLock')
        await queue_manager.add_to_order_queue(order_req_id, f"{proposal_id}/EditLock")
        logger.info(f"Added queue message: {proposal_id}/EditLock to order queue {order_req_id}")
        
        logger.info(f"Edit lock processed successfully for order: {order_req_id}")
        
        return EditLockResponse(
            success=True,
            message="Edit lock applied successfully"
        )
        
    except ProposalUpdateException as e:
        logger.error(f"Edit lock update error: {str(e)}")
        raise create_http_exception(e, status.HTTP_400_BAD_REQUEST)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Unexpected error in edit lock")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred"
        )

# Additional utility endpoints
@router.get("/proposal/{proposal_id}/status")
async def get_proposal_status(
    proposal_id: str,
    current_user: Optional[dict] = Depends(get_current_user)
):
    """Get the status of a specific proposal"""
    try:
        proposal_id = validate_proposal_id(proposal_id)
        
        # This would typically fetch from database
        # For now, return a placeholder response
        return {
            "proposal_id": proposal_id,
            "status": "ACTIVE",
            "last_updated": "2025-10-26T12:00:00Z"
        }
        
    except Exception as e:
        logger.error(f"Error getting proposal status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get proposal status"
        )

@router.get("/order/{order_req_id}/proposals")
async def get_order_proposals(
    order_req_id: str,
    current_user: Optional[dict] = Depends(get_current_user)
):
    """Get all proposals for a specific order"""
    try:
        order_req_id = validate_order_req_id(order_req_id)
        
        # This would typically fetch from database
        # For now, return a placeholder response
        return {
            "order_req_id": order_req_id,
            "proposals": [],
            "total_count": 0
        }
        
    except Exception as e:
        logger.error(f"Error getting order proposals: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get order proposals"
        )