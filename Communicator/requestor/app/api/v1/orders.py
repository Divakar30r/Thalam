# Order API endpoints for Requestor

import asyncio
import logging
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from typing import Dict, Any

from shared.models import (
    InitiateRequest, FollowUpRequest, OrderResponse, 
    ErrorResponse, MSKTopic, MSKMessageKey
)

from ...services.order_service import OrderService
from ...services.notification_service import NotificationService
from ...services.grpc_client_service import GRPCClientService
from ...services.order_tracking_service import get_order_tracking_service, OrderTrackingService
from ...core.exceptions import OrderServiceError, GRPCClientError

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/orders", tags=["orders"])

# Dependency injection
def get_order_service() -> OrderService:
    return OrderService()

def get_notification_service() -> NotificationService:
    return NotificationService()

def get_grpc_client_service() -> GRPCClientService:
    return GRPCClientService()

def get_order_tracking_service_dependency() -> OrderTrackingService:
    return get_order_tracking_service()

@router.post("/initiate", response_model=OrderResponse)
async def initiate_order(
    request: InitiateRequest,
    background_tasks: BackgroundTasks,
    order_service: OrderService = Depends(get_order_service),
    notification_service: NotificationService = Depends(get_notification_service),
    grpc_client_service: GRPCClientService = Depends(get_grpc_client_service),
    order_tracking: OrderTrackingService = Depends(get_order_tracking_service_dependency)
):
    """
    Initiate order processing
    
    Logic:
    1. Check for duplicate order_req_id to prevent duplicate streams
    2. Create and store OrderReqObj in tracking list
    3. Invoke _UpdateRequests (mode = "RequestSubmissions")
    4. Send AWS MSK acknowledgement
    5. Mark stream as active and trigger gRPC_SS in concurrent mode
    """
    try:
        logger.info(f"Initiating order: {request.order_req_id}")
        
        # 1. Check if order already exists or stream is active
        if order_tracking.has_order(request.order_req_id):
            if order_tracking.is_stream_active(request.order_req_id):
                logger.warning(
                    f"Order {request.order_req_id} already has active gRPC stream. "
                    "Preventing duplicate stream."
                )
                return OrderResponse(
                    success=True,
                    message="Order already being processed",
                    order_req_id=request.order_req_id,
                    session_id=request.session_id
                )
            else:
                logger.info(f"Order {request.order_req_id} exists but stream inactive. Restarting.")
        
        # 2. Create and store OrderReqObj
        order_req_obj = order_tracking.add_order(request.order_req_id, request.session_id)
        logger.info(f"Added order {request.order_req_id} to tracking list")
        
        # 3. Update request status to SUBMITTED
        order_req_dict = {"order_req_id": request.order_req_id}
        update_result = await order_service.update_request(order_req_dict, "RequestSubmissions")
        
        if not update_result:
            # Remove from tracking on failure
            order_tracking.remove_order(request.order_req_id)
            
            # Send failure notification
            await notification_service.send_failure_notification(
                MSKTopic.REQ_FAILURES,
                MSKMessageKey.ORD_SUBMISSION,
                request.order_req_id,
                request.session_id,
                "Order Submission failure"
            )
            raise HTTPException(
                status_code=500,
                detail="Failed to update order request status"
            )
        
        # 4. Send buyer acknowledgement (non-blocking if MSK unavailable)
        try:
            await notification_service.send_buyer_acknowledgement(
                request.order_req_id,
                request.session_id,
                "Order Submitted"
            )
        except Exception as e:
            logger.warning(f"Could not send MSK acknowledgement: {str(e)}")
        
        # 5. Mark stream as active and start gRPC streaming in background
        order_tracking.mark_stream_active(request.order_req_id)
        
        background_tasks.add_task(
            grpc_client_service.start_streaming_client,
            request.order_req_id,
            request.notification_type
        )
        
        logger.info(f"Order {request.order_req_id} initiated successfully")
        
        return OrderResponse(
            success=True,
            message="Order initiated successfully",
            order_req_id=request.order_req_id,
            session_id=request.session_id
        )
        
    except OrderServiceError as e:
        logger.error(f"Order service error for {request.order_req_id}: {str(e)}")
        # Clean up tracking on error
        order_tracking.remove_order(request.order_req_id)
        raise HTTPException(status_code=500, detail=str(e))
    
    except Exception as e:
        logger.error(f"Unexpected error initiating order {request.order_req_id}: {str(e)}")
        # Clean up tracking on error
        order_tracking.remove_order(request.order_req_id)
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/{order_req_id}/followup", response_model=OrderResponse)
async def follow_up_order(
    order_req_id: str,
    request: FollowUpRequest,
    order_service: OrderService = Depends(get_order_service),
    grpc_client_service: GRPCClientService = Depends(get_grpc_client_service),
    order_tracking: OrderTrackingService = Depends(get_order_tracking_service_dependency)
):
    """
    Process follow-up for order
    
    Logic:
    1. Invoke _UpdateRequests (mode = RequestFollowUp)
    2. Add follow-up note to OrderReqObj in tracking list
    3. Trigger gRPC_NS
    """
    try:
        logger.info(f"Processing follow-up for order: {order_req_id}")
        
        # 1. Prepare note data for follow-up
        note_data = {
            "FollowUpID": request.trn_uuid,
            "Audience": request.audience,
            "Content": request.message
        }
        
        # 2. Update request with follow-up via unified update_request method
        order_req_dict = {
            "order_req_id": order_req_id,
            "notes_dict": note_data
        }
        
        follow_up_result = await order_service.update_request(order_req_dict, "RequestUpdate")
        
        if not follow_up_result:
            raise HTTPException(
                status_code=500,
                detail="Failed to add follow-up to order request"
            )
        
        # Extract FollowUpID from the response
        follow_up_id = follow_up_result.get("FollowUpID")
        if not follow_up_id:
            raise HTTPException(
                status_code=500,
                detail="Failed to get follow-up ID from response"
            )
        
        # 3. Add follow-up note to OrderReqObj in tracking list
        if order_tracking.has_order(order_req_id):
            note_added = order_tracking.add_follow_up_note(
                order_req_id,
                follow_up_id,
                request.audience,
                request.message
            )
            if note_added:
                logger.info(f"Added follow-up note to order tracking for {order_req_id}")
            else:
                logger.warning(f"Failed to add follow-up note to order tracking for {order_req_id}")
        else:
            logger.warning(
                f"Order {order_req_id} not found in tracking list. "
                "Follow-up processed but not tracked locally."
            )
        
        # 4. Trigger gRPC non-streaming call
        grpc_response = await grpc_client_service.send_non_streaming_request(
            order_req_id,
            request.audience,
            follow_up_id,
            request.message
        )
        
        logger.info(f"Follow-up for order {order_req_id} processed successfully")
        
        return OrderResponse(
            success=True,
            message="Follow-up added: " + follow_up_id,
            order_req_id=order_req_id
        )
        
    except OrderServiceError as e:
        logger.error(f"Order service error for follow-up {order_req_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    
    except GRPCClientError as e:
        logger.error(f"gRPC client error for follow-up {order_req_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    
    except Exception as e:
        logger.error(f"Unexpected error in follow-up {order_req_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.put("/finalize/{order_req_id}", response_model=OrderResponse)
async def finalize_order(
    order_req_id: str,
    order_service: OrderService = Depends(get_order_service)
):
    """Finalize order by updating status"""
    try:
        logger.info(f"Finalizing order: {order_req_id}")
        
        order_req_dict = {"order_req_id": order_req_id}
        result = await order_service.update_request(order_req_dict, "RequestFinalised")
        
        if not result:
            raise HTTPException(
                status_code=500,
                detail="Failed to finalize order"
            )
        
        return OrderResponse(
            success=True,
            message="Order finalized successfully",
            order_req_id=order_req_id
        )
        
    except OrderServiceError as e:
        logger.error(f"Error finalizing order {order_req_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/pause/{order_req_id}", response_model=OrderResponse)
async def pause_order(
    order_req_id: str,
    order_service: OrderService = Depends(get_order_service)
):
    """Pause order by updating status"""
    try:
        logger.info(f"Pausing order: {order_req_id}")
        
        order_req_dict = {"order_req_id": order_req_id}
        result = await order_service.update_request(order_req_dict, "RequestPaused")
        
        if not result:
            raise HTTPException(
                status_code=500,
                detail="Failed to pause order"
            )
        
        return OrderResponse(
            success=True,
            message="Order paused successfully",
            order_req_id=order_req_id
        )
        
    except OrderServiceError as e:
        logger.error(f"Error pausing order {order_req_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/tracking/status")
async def get_tracking_status(
    order_tracking: OrderTrackingService = Depends(get_order_tracking_service_dependency)
):
    """Get order tracking status - diagnostic endpoint"""
    return {
        "total_orders": order_tracking.get_order_count(),
        "active_streams": order_tracking.get_active_stream_count(),
        "tracked_order_ids": list(order_tracking.order_req_id_list.keys())
    }

@router.get("/tracking/{order_req_id}")
async def get_order_tracking_details(
    order_req_id: str,
    order_tracking: OrderTrackingService = Depends(get_order_tracking_service_dependency)
):
    """Get detailed tracking info for specific order"""
    order_req_obj = order_tracking.get_order(order_req_id)
    
    if not order_req_obj:
        raise HTTPException(
            status_code=404,
            detail=f"Order {order_req_id} not found in tracking list"
        )
    
    return {
        "order_req_id": order_req_obj.order_req_id,
        "session": order_req_obj.session,
        "notes_count": len(order_req_obj.notes_dict_arr),
        "is_stream_active": order_tracking.is_stream_active(order_req_id),
        "notes": [
            {
                "follow_up_id": note.follow_up_id,
                "audience": note.audience,
                "message_type": note.content.message_type,
                "added_time": note.added_time.isoformat() if note.added_time else None
            }
            for note in order_req_obj.notes_dict_arr
        ]
    }