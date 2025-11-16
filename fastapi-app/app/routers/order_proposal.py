"""
Router for OrderProposal endpoints
"""
from typing import List
from fastapi import APIRouter, HTTPException, Query, Path, status
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

from app.models.schemas import OrderProposalCreate, OrderProposalResponse, OrderProposalUpdate, ProposalNote, ProposalUserEdit
from app.services.order_proposal_service import OrderProposalService
from app.core.exceptions import NotFoundError, ConflictError, ValidationError, DatabaseError
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/order-proposal", tags=["OrderProposal"])


@router.post("/", response_model=OrderProposalResponse, status_code=201)
async def create_order_proposal(order_proposal: OrderProposalCreate):
    """
    Create a new OrderProposal.
    - Validates OrderReqID exists in OrderRequest collection
    - Generates unique ProposalID with format: PRP-<1-10>-<OrderReqID>
    - Generates unique FollowUpID for Notes if present: F<1-20>-<ProposalID>
    """
    try:
        created = await OrderProposalService.create_order_proposal(order_proposal)
        return created
    except ValidationError as e:
        logger.warning(f"Validation error creating OrderProposal: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except ConflictError as e:
        logger.warning(f"Conflict creating OrderProposal: {str(e)}")
        raise HTTPException(status_code=409, detail=str(e))
    except DatabaseError as e:
        logger.error(f"Database error creating OrderProposal: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error creating OrderProposal: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{proposal_id}", response_model=OrderProposalResponse)
async def get_proposal_by_id(proposal_id: str = Path(..., description="ProposalID")):
    """Get an OrderProposal by ProposalID (primary key)."""
    try:
        doc = await OrderProposalService.get_proposal_by_id(proposal_id)
        return doc
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DatabaseError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/order/{order_req_id}", response_model=List[OrderProposalResponse])
async def get_proposals_by_order_req_id(order_req_id: str = Path(..., description="OrderReqID")):
    """
    Get all OrderProposals for a given OrderReqID
    """
    try:
        docs = await OrderProposalService.get_proposals_by_order_req_id(order_req_id)
        return docs
    except DatabaseError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/note/{followup_id}", response_model=OrderProposalResponse)
async def get_proposal_by_note_followup_id(followup_id: str = Path(..., description="FollowUpID from Notes array")):
    """
    Get an OrderProposal by Notes[].FollowUpID
    """
    try:
        doc = await OrderProposalService.get_proposal_by_note_followup_id(followup_id)
        return doc
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DatabaseError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/useredit/{followup_id}", response_model=OrderProposalResponse)
async def get_proposal_by_useredit_followup_id(followup_id: str = Path(..., description="FollowUpID from UserEdits array")):
    """
    Get an OrderProposal by UserEdits[].FollowUpID
    """
    try:
        doc = await OrderProposalService.get_proposal_by_useredit_followup_id(followup_id)
        return doc
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DatabaseError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=List[OrderProposalResponse])
async def list_order_proposals(skip: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100)):
    """
    List all OrderProposals with pagination
    """
    try:
        docs = await OrderProposalService.list_order_proposals(skip=skip, limit=limit)
        return docs
    except DatabaseError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{proposal_id}", response_model=OrderProposalResponse)
async def update_order_proposal(proposal_id: str, order_proposal: OrderProposalUpdate):
    """
    Update an OrderProposal by ProposalID
    - ProposalID, OrderReqID, and ProposerEmailID cannot be updated
    """
    try:
        updated = await OrderProposalService.update_order_proposal(proposal_id, order_proposal)
        return updated
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DatabaseError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{proposal_id}", status_code=204)
async def delete_order_proposal(proposal_id: str):
    """
    Delete an OrderProposal by ProposalID
    """
    try:
        await OrderProposalService.delete_order_proposal(proposal_id)
        return JSONResponse(status_code=204, content=None)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DatabaseError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{proposal_id}/notes", status_code=201)
async def append_order_proposal_note(proposal_id: str, note: ProposalNote):
    """Append a note to the given OrderProposal. Returns the resolved FollowUpID."""
    try:
        followup_id = await OrderProposalService.append_order_proposal_notes(proposal_id, note)
        return JSONResponse(status_code=201, content={"FollowUpID": followup_id})
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except DatabaseError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error appending note to {proposal_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/{proposal_id}/useredits", status_code=201)
async def append_order_proposal_useredit(proposal_id: str, useredit: dict):
    """Append a user edit entry to the given OrderProposal.
    Accepts either a direct ProposalUserEdit payload or a wrapper like {"UserEdits": { ... }}.
    Server will add AddedTime and return the created object.
    """
    try:
        # Normalize payload shapes: allow callers to POST either the bare object or a wrapper
        payload = None
        if isinstance(useredit, dict) and 'UserEdits' in useredit:
            # If UserEdits is a list, take the first element; if it's a dict, use it
            ue = useredit.get('UserEdits')
            if isinstance(ue, list):
                if len(ue) == 0:
                    raise HTTPException(status_code=422, detail='UserEdits array is empty')
                payload = ue[0]
            elif isinstance(ue, dict):
                payload = ue
            else:
                raise HTTPException(status_code=422, detail='UserEdits must be an object or array')
        else:
            payload = useredit

        # Normalize keys case-insensitively: accept 'OrderFollowUpID' in any case
        if isinstance(payload, dict):
            for k in list(payload.keys()):
                if k.lower() == 'orderfollowupid' and k != 'OrderFollowUpID':
                    payload['OrderFollowUpID'] = payload.pop(k)

        # Validate/construct ProposalUserEdit model from the normalized payload
        try:
            ue_model = ProposalUserEdit.model_validate(payload)
        except Exception as ve:
            # Let FastAPI return a 422-like response for invalid input
            raise HTTPException(status_code=422, detail=str(ve))

        appended = await OrderProposalService.append_order_proposal_useredit(proposal_id, ue_model)
        # Ensure any non-JSON types (e.g., datetime) are converted to JSON-friendly types
        return JSONResponse(status_code=201, content=jsonable_encoder(appended))
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except DatabaseError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error appending useredit to {proposal_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
