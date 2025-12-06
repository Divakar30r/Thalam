# gRPC Client Service coordination

import asyncio
import logging
from typing import Dict, Any, List, Optional

from shared.utils import queue_manager, TaskPriority
from shared.models import StreamingResponseStatus, MSKTopic, MSKMessageKey
from ..grpc_client.streaming_client import StreamingClient
from ..grpc_client.non_streaming_client import NonStreamingClient
from ..services.notification_service import NotificationService
from ..services.order_tracking_service import get_order_tracking_service
from ..core.exceptions import GRPCClientError

logger = logging.getLogger(__name__)

class GRPCClientService:
    """gRPC client coordination service"""
    
    def __init__(self):
        self.queue_manager = queue_manager
        self.streaming_client = StreamingClient()
        self.non_streaming_client = NonStreamingClient()
        self.notification_service = NotificationService()
        self.order_tracking = get_order_tracking_service()
        self.active_streams: Dict[str, asyncio.Task] = {}
    
    async def start_streaming_client(
        self, 
        order_req_id: str, 
        notification_type: str
    ) -> str:
        """
        Start gRPC streaming client with concurrency management
        
        Args:
            order_req_id: Order request ID
            notification_type: Type of notification
            
        Returns:
            task_id: Task identifier for tracking
        """
        try:
            logger.info(f"Starting streaming client for order {order_req_id}")
            
            # Add streaming task to priority queue
            # Use w_ prefix for kwargs to avoid conflict with add_priority_task params
            task_id = await self.queue_manager.add_priority_task(
                order_req_id=order_req_id,
                task_func=self._handle_streaming_responses,
                priority=TaskPriority.HIGH,
                w_order_req_id=order_req_id,
                w_notification_type=notification_type
            )
            
            logger.info(f"Streaming task {task_id} added to queue for order {order_req_id}")
            return task_id
            
        except Exception as e:
            logger.error(f"Failed to start streaming client for {order_req_id}: {str(e)}")
            raise GRPCClientError(f"Streaming client start failed: {str(e)}")
    
    async def _handle_streaming_responses(
        self, 
        order_req_id: str, 
        notification_type: str
    ):
        """Handle gRPC streaming responses in concurrent mode"""
        try:
            # Start streaming connection - this returns an async generator
            async for response in self.streaming_client.start_stream(order_req_id, notification_type):
                await self._process_streaming_response(response, order_req_id)
            
            # Stream completed successfully
            logger.info(f"Stream completed successfully for order {order_req_id}")
            
        except Exception as e:
            logger.error(f"Error in streaming response handler for {order_req_id}: {str(e)}")
            raise
        
        finally:
            # Always mark stream as inactive when done
            self.order_tracking.mark_stream_inactive(order_req_id)
            logger.info(f"Marked stream as inactive for order {order_req_id}")
    
    async def _process_streaming_response(
        self, 
        response, 
        order_req_id: str
    ):
        """Process individual streaming response"""
        try:
            status = response.streaming_response_status
            proposal_id = response.proposal_id
            
            # Determine notification message and topic
            notification_data = self._get_notification_data(status, proposal_id)
            
            if notification_data:
                await self.notification_service.send_buyer_notification(
                    order_req_id,
                    "",  # Session ID would be retrieved from order context
                    notification_data["message"]
                )
                logger.info(f"Sent notification for {order_req_id}: {notification_data['message']}")
            
        except Exception as e:
            logger.error(f"Error processing streaming response for {order_req_id}: {str(e)}")
    
    def _get_notification_data(self, status: str, proposal_id: str) -> Optional[Dict[str, str]]:
        """Get notification data based on streaming response status"""
        
        notification_map = {
            StreamingResponseStatus.NEW_PROPOSAL: {
                "message": "New Proposal received",
                "topic": MSKTopic.BUYER_NOTIFY,
                "key": MSKMessageKey.ORD_UPDATES
            },
            StreamingResponseStatus.PROPOSAL_CLOSED: {
                "message": f"Proposal closed {proposal_id}",
                "topic": MSKTopic.BUYER_NOTIFY,
                "key": MSKMessageKey.ORD_UPDATES
            },
            StreamingResponseStatus.PROPOSAL_UPDATE: {
                "message": f"Proposal updates {proposal_id}",
                "topic": MSKTopic.BUYER_NOTIFY,
                "key": MSKMessageKey.ORD_UPDATES
            },
            StreamingResponseStatus.ORDER_PAUSED: {
                "message": f"Choose one proposal {proposal_id}",
                "topic": MSKTopic.BUYER_NOTIFY,
                "key": MSKMessageKey.ORD_UPDATES
            },
            StreamingResponseStatus.EDIT_LOCK: {
                "message": f"Proposal updates in progress {proposal_id}",
                "topic": MSKTopic.BUYER_NOTIFY,
                "key": MSKMessageKey.ORD_UPDATES
            }
        }
        
        return notification_map.get(status)
    
    async def send_non_streaming_request(
        self,
        order_req_id: str,
        audience: List[str],
        follow_up_id: str,
        message: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Send gRPC non-streaming request
        
        Args:
            order_req_id: Order request ID
            audience: List of audience IDs
            follow_up_id: Follow-up ID
            message: Message content
            
        Returns:
            gRPC response or None if failed
        """
        try:
            logger.info(f"Sending non-streaming request for order {order_req_id}")
            
            response = await self.non_streaming_client.send_follow_up_request(
                order_req_id, audience, follow_up_id, message
            )
            
            if response:
                await self._process_non_streaming_response(response, order_req_id)
            
            return response
            
        except Exception as e:
            logger.error(f"Non-streaming request failed for {order_req_id}: {str(e)}")
            raise GRPCClientError(f"Non-streaming request failed: {str(e)}")
    
    async def _process_non_streaming_response(
        self, 
        response, 
        order_req_id: str
    ):
        """Process non-streaming response"""
        try:
            # Process NS_FollowUpResp list
            locked_responses = []
            
            for item in response.ns_follow_up_resp:
                if item.status == "Locked":
                    locked_responses.append(item)
            
            if locked_responses:
                logger.info(f"Found {len(locked_responses)} locked responses for {order_req_id}")
                # Placeholder for additional logic with locked responses
            
        except Exception as e:
            logger.error(f"Error processing non-streaming response for {order_req_id}: {str(e)}")
    
    async def stop_streaming_client(self, order_req_id: str) -> bool:
        """Stop streaming client for specific order"""
        try:
            if order_req_id in self.active_streams:
                task = self.active_streams[order_req_id]
                task.cancel()
                
                try:
                    await task
                except asyncio.CancelledError:
                    pass
                
                del self.active_streams[order_req_id]
                
                # Mark stream as inactive in tracking
                self.order_tracking.mark_stream_inactive(order_req_id)
                
                logger.info(f"Stopped streaming client for order {order_req_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error stopping streaming client for {order_req_id}: {str(e)}")
            return False
    
    async def get_active_streams(self) -> List[str]:
        """Get list of active streaming order IDs"""
        return list(self.active_streams.keys())
    
    async def cleanup_completed_streams(self):
        """Cleanup completed streaming tasks"""
        completed_orders = []
        
        for order_req_id, task in self.active_streams.items():
            if task.done():
                completed_orders.append(order_req_id)
        
        for order_req_id in completed_orders:
            del self.active_streams[order_req_id]
            logger.info(f"Cleaned up completed stream for order {order_req_id}")
        
        return len(completed_orders)