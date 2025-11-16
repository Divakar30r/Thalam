"""
Router for OrderReq endpoints
"""
from typing import List
from fastapi import APIRouter, HTTPException, Query, Path, status
from fastapi.responses import JSONResponse

from app.models.schemas import OrderReqCreate, OrderReqResponse, OrderReqUpdate, OrderReqNote, OrderReqDocument, OrderReqDocumentUpdate
from app.services.order_req_service import OrderReqService
from app.core.exceptions import NotFoundError, ConflictError, ValidationError, DatabaseError
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/order-req", tags=["OrderReq"])


@router.post("/", response_model=OrderReqResponse, status_code=201)
async def create_order_req(order_req: OrderReqCreate):
    try:
            created = await OrderReqService.create_order_req(order_req)
            # Return Pydantic model instance so FastAPI will serialize datetimes correctly
            return created
    except ConflictError as e:
        logger.warning(f"Conflict creating OrderReq: {str(e)}")
        raise HTTPException(status_code=409, detail=str(e))
    except DatabaseError as e:
        logger.error(f"Database error creating OrderReq: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error creating OrderReq: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/search", response_model=List[OrderReqResponse])
async def search_order_reqs(requestor_email: str = Query(..., description="Requestor email to filter"),
                            status: str | None = Query(None, description="Optional OrderReqStatus to filter")):
    try:
        docs = await OrderReqService.find_by_requestor_and_status(requestor_email, status)
        return docs
    except DatabaseError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{order_req_id}", response_model=OrderReqResponse)
async def get_order_req(order_req_id: str = Path(..., description="OrderReqID")):
    try:
        doc = await OrderReqService.get_order_req(order_req_id)
        return doc
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DatabaseError as e:
        raise HTTPException(status_code=500, detail=str(e))


# ...removed duplicate by-order-req-id endpoint (use GET /{order_req_id} instead)


@router.get("/", response_model=List[OrderReqResponse])
async def list_order_reqs(skip: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100)):
    try:
        docs = await OrderReqService.list_order_reqs(skip=skip, limit=limit)
        return docs
    except DatabaseError as e:
        raise HTTPException(status_code=500, detail=str(e))



@router.get("/search", response_model=List[OrderReqResponse])
async def search_order_reqs(requestor_email: str = Query(..., description="Requestor email to filter"),
                            status: str | None = Query(None, description="Optional OrderReqStatus to filter")):
    try:
        docs = await OrderReqService.find_by_requestor_and_status(requestor_email, status)
        return docs
    except DatabaseError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{order_req_id}", response_model=OrderReqResponse)
async def update_order_req(order_req_id: str, order_req: OrderReqUpdate):
    try:
        updated = await OrderReqService.update_order_req(order_req_id, order_req)
        return updated
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DatabaseError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{order_req_id}", status_code=204)
async def delete_order_req(order_req_id: str):
    try:
        await OrderReqService.delete_order_req(order_req_id)
        return JSONResponse(status_code=204, content=None)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DatabaseError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{order_req_id}/notes", status_code=201)
async def append_order_req_note(order_req_id: str, note: OrderReqNote):
    """Append a note to the given OrderReq. Returns the resolved FollowUpID."""
    try:
        followup_id = await OrderReqService.append_order_request_notes(order_req_id, note)
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
        logger.error(f"Unexpected error appending note to {order_req_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/note/{followup_id}", response_model=OrderReqResponse)
async def get_order_req_by_note_followup_id(followup_id: str = Path(..., description="FollowUpID from Notes array")):
    """
    Get an OrderReq by Notes[].FollowUpID
    """
    try:
        doc = await OrderReqService.get_order_req_by_note_followup_id(followup_id)
        return doc
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DatabaseError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/audience/{proposal_id}", response_model=List[OrderReqResponse])
async def get_order_reqs_by_audience(proposal_id: str = Path(..., description="ProposalID in Notes.Audience array")):
    """
    Get all OrderReqs that have the given ProposalID in their Notes[].Audience array
    """
    try:
        docs = await OrderReqService.get_order_reqs_by_audience(proposal_id)
        return docs
    except DatabaseError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{order_req_id}/Doc/{s3_key:path}")
async def get_order_req_document(
    order_req_id: str = Path(..., description="OrderReqID"),
    s3_key: str = Path(..., description="S3 key of the document (may include '/')")
):
    """
    Get a specific document from an OrderReq by s3_key
    """
    logger.info(f"GET /{order_req_id}/Doc/{s3_key} - Incoming request: order_req_id={order_req_id}, s3_key={s3_key}")

    try:
        document = await OrderReqService.get_order_req_document_by_s3_key(order_req_id, s3_key)
        logger.info(f"GET /{order_req_id}/Doc/{s3_key} - Successfully retrieved document")
        return JSONResponse(status_code=200, content=document)
    except NotFoundError as e:
        logger.warning(f"GET /{order_req_id}/Doc/{s3_key} - Not found: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))
    except DatabaseError as e:
        logger.error(f"GET /{order_req_id}/Doc/{s3_key} - Database error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{order_req_id}/Doc", status_code=201)
async def append_order_req_document(order_req_id: str, document: OrderReqDocument):
    """Append a document to the given OrderReq Documents array. Returns the appended document."""
    # Log incoming request
    logger.info(f"POST /{order_req_id}/Doc - Incoming request: order_req_id={order_req_id}")
    logger.debug(f"POST /{order_req_id}/Doc - Document payload: {document.model_dump(by_alias=True)}")

    try:
        appended_doc = await OrderReqService.append_order_req_document(order_req_id, document)
        logger.info(f"POST /{order_req_id}/Doc - Successfully appended document with s3_key={document.S3Key}")
        return JSONResponse(status_code=201, content=appended_doc)
    except NotFoundError as e:
        logger.warning(f"POST /{order_req_id}/Doc - Not found: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))
    except ConflictError as e:
        logger.warning(f"POST /{order_req_id}/Doc - Conflict: {str(e)}")
        raise HTTPException(status_code=409, detail=str(e))
    except ValidationError as e:
        logger.warning(f"POST /{order_req_id}/Doc - Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except DatabaseError as e:
        logger.error(f"POST /{order_req_id}/Doc - Database error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"POST /{order_req_id}/Doc - Unexpected error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/{order_req_id}/Doc/{s3_key:path}", status_code=200)
async def update_order_req_document(
    order_req_id: str = Path(..., description="OrderReqID"),
    s3_key: str = Path(..., description="S3 key of the document to update (may include '/')"),
    update_data: OrderReqDocumentUpdate = ...
):
    """
    Update document metadata in an OrderReq.
    Commonly used to update upload_status and other metadata fields.
    Returns the updated document.
    """
    # Log incoming request
    logger.info(f"PUT /{order_req_id}/Doc/{s3_key} - Incoming request: order_req_id={order_req_id}, s3_key={s3_key}")
    logger.debug(f"PUT /{order_req_id}/Doc/{s3_key} - Update payload: {update_data.model_dump(by_alias=True, exclude_none=True)}")

    try:
        updated_doc = await OrderReqService.update_order_req_document(order_req_id, s3_key, update_data)
        logger.info(f"PUT /{order_req_id}/Doc/{s3_key} - Successfully updated document")
        return JSONResponse(status_code=200, content=updated_doc)
    except NotFoundError as e:
        logger.warning(f"PUT /{order_req_id}/Doc/{s3_key} - Not found: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))
    except ConflictError as e:
        logger.warning(f"PUT /{order_req_id}/Doc/{s3_key} - Conflict: {str(e)}")
        raise HTTPException(status_code=409, detail=str(e))
    except ValidationError as e:
        logger.warning(f"PUT /{order_req_id}/Doc/{s3_key} - Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except DatabaseError as e:
        logger.error(f"PUT /{order_req_id}/Doc/{s3_key} - Database error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"PUT /{order_req_id}/Doc/{s3_key} - Unexpected error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/{order_req_id}/Doc/{s3_key:path}", status_code=204)
async def soft_delete_order_req_document(
    order_req_id: str = Path(..., description="OrderReqID"),
    s3_key: str = Path(..., description="S3 key of the document to delete (may include '/')"),
    deleted_by: str = Query(..., description="Email of the user performing the deletion")
):
    """
    Soft delete a document from an OrderReq by marking it as deleted.
    The document will no longer appear in GET requests but remains in the database for audit purposes.
    """
    logger.info(f"DELETE /{order_req_id}/Doc/{s3_key} - Incoming request: order_req_id={order_req_id}, s3_key={s3_key}, deleted_by={deleted_by}")

    try:
        await OrderReqService.soft_delete_order_req_document(order_req_id, s3_key, deleted_by)
        logger.info(f"DELETE /{order_req_id}/Doc/{s3_key} - Successfully soft deleted document")
        return JSONResponse(status_code=204, content=None)
    except NotFoundError as e:
        logger.warning(f"DELETE /{order_req_id}/Doc/{s3_key} - Not found: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))
    except ConflictError as e:
        logger.warning(f"DELETE /{order_req_id}/Doc/{s3_key} - Conflict: {str(e)}")
        raise HTTPException(status_code=409, detail=str(e))
    except DatabaseError as e:
        logger.error(f"DELETE /{order_req_id}/Doc/{s3_key} - Database error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"DELETE /{order_req_id}/Doc/{s3_key} - Unexpected error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

