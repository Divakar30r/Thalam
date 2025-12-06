import asyncio
import logging
from typing import Dict, Any, List, AsyncIterator, Optional
from datetime import datetime, timedelta
import grpc
from grpc import aio
from queue import Queue, Empty

from shared.models.order_models import ProcessorOrderReqObj
from shared.utils.queue_manager import queue_manager

from ..core.config import settings
from ..core.exceptions import GRPCServiceException, OrderExpiredException
from ..services import SellerService, NotificationService, ProposalService
from shared.proto.generated import order_service_pb2_grpc, order_service_pb2


logger = logging.getLogger(__name__)

#class StreamingServerService(order_service_pb2_grpc.OrderServiceServicer):
class StreamingServerService(order_service_pb2_grpc.OrderStreamingServiceServicer):
    """gRPC streaming server implementation (gRPC_SS) as per grpcdesign.yaml"""
    
    def __init__(self):
        self.seller_service = SellerService()
        self.notification_service = NotificationService()
        self.proposal_service = ProposalService()
        # Use the global shared queue_manager so producer and consumer share queues
        self.queue_manager = queue_manager

        # Reference to centralized order state (shared with HTTP endpoints)
        # This is the same dict instance used by queue_manager.state_mgr
        self.processor_order_req_id_list = queue_manager.get_all_orders()

        # Background task tracking
        self._background_tasks: Dict[str, asyncio.Task] = {}
        # Sweeper task to cleanup expired orders after configured expiry
        self._sweeper_task: Optional[asyncio.Task] = asyncio.create_task(self._sweeper())
    
    async def ProcessOrderStream(
        self, 
        request: order_service_pb2.OrderStreamRequest, 
        context: grpc.aio.ServicerContext
    ) -> AsyncIterator[order_service_pb2.OrderStreamResponse]:
        """
        Implementation of gRPC_SS (server streaming) from grpcdesign.yaml
        
        Args:
            request: OrderStreamRequest with OrderReqID and NotificationType
            context: gRPC service context
        
        Yields:
            OrderStreamResponse with OrderReqId, ProposalId, StreamingResponseStatus, FollowUpID
        """
        logger.info(f"=== ProcessOrderStream called ===")
        logger.info(f"Request type: {type(request)}")
        logger.info(f"Request type name: {type(request).__name__}")
        logger.info(f"Request module: {type(request).__module__}")
        logger.info(f"Has order_req_id attr: {hasattr(request, 'order_req_id')}")
        logger.info(f"Request dir: {[attr for attr in dir(request) if not attr.startswith('_')]}")
        logger.info(f"Request repr: {repr(request)}")
        
        try:
            # Try to access the request fields directly
            logger.info(f"Attempting to access request.order_req_id...")
            order_req_id = request.order_req_id
            logger.info(f"order_req_id: {order_req_id}")
            
            logger.info(f"Attempting to access request.notification_type...")
            notification_type = request.notification_type
            logger.info(f"notification_type: {notification_type}")
            
            logger.info(f"✓ Successfully extracted: order_req_id={order_req_id}, notification_type={notification_type}")
            
        except AttributeError as e:
            logger.error(f"❌ AttributeError: {str(e)}")
            logger.error(f"Request type was: {type(request)}")
            await context.abort(grpc.StatusCode.INVALID_ARGUMENT, f"Invalid request format: {str(e)}")
            return
        except Exception as e:
            logger.error(f"❌ Unexpected error: {str(e)}")
            logger.error(f"Error type: {type(e)}")
            await context.abort(grpc.StatusCode.INTERNAL, f"Internal error: {str(e)}")
            return
        
        try:
            # Step 1: Get or create order entry in centralized state with expiry
            # If HTTP endpoint already created this order, reuse it; otherwise create new
            processor_order_req_obj = self.queue_manager.get_or_create_order(
                order_req_id=order_req_id,
                expiry_minutes=settings.order_expiry_minutes,
                session=""  # Will be populated from external source
            )
            
            # Step 2: Invoke _SelectSellers
            selected_sellers = await self.seller_service.select_sellers(order_req_id, processor_order_req_obj)
            
            # Step 3: Invoke _NotifyGChat for each seller if notification_type = 'GChat'
            if notification_type == 'GChat':
                await self.notification_service.notify_sellers_gchat(
                    selected_sellers, 
                    order_req_id
                )
            
            # Step 4: Send MSK notification
            await self.notification_service.send_seller_notification(
                order_req_id=order_req_id,
                message="Proposal Request",
                key="PRP_REQUEST"
            )
            
            
            # Step 5: Start background task for queue processing - does nothing for now
            task = asyncio.create_task(
                self._process_queue_responses(order_req_id, context)
            )
            self._background_tasks[order_req_id] = task
            
             
            # Step 6: Yield responses from queue until expiry
            async for response in self._stream_responses(order_req_id, context):
                yield response
                
        except Exception as e:
            logger.error(f"Error in streaming for order {order_req_id}: {str(e)}")
            await context.abort(grpc.StatusCode.INTERNAL, f"Streaming error: {str(e)}")
        
        finally:
            # Do not eagerly remove the order on client disconnect — keep the
            # order and its queue alive until expiry so follow-ups or reconnects
            # can still be delivered. The background sweeper will remove the
            # order once its expiry time passes.
            # Cancel any per-order background task started for this stream.
            if order_req_id in self._background_tasks:
                task = self._background_tasks[order_req_id]
                if not task.done():
                    task.cancel()
                del self._background_tasks[order_req_id]
            logger.info(f"Stream ended for order {order_req_id}; scheduled cleanup at expiry {processor_order_req_obj.expiry}")
    
    async def _stream_responses(
        self, 
        order_req_id: str, 
        context: grpc.aio.ServicerContext
    ) -> AsyncIterator[order_service_pb2.OrderStreamResponse]:
        """
        Stream responses from the queue until expiry
        """
        processor_order_req_obj = self.processor_order_req_id_list.get(order_req_id)
        if not processor_order_req_obj:
            return
        
        expiry_ms = processor_order_req_obj.expiry
        # Debug: log whether a global server_manager exists and whether it
        # contains a streaming_service with a processor_order_req_id_list.
        try:
            # Import at runtime to avoid circular imports at module level
            from processor import main as processor_main
            sm = getattr(processor_main, "server_manager", None)
            logger.info(f"Server manager active: {sm is not None}")
            if sm and getattr(sm, "streaming_service", None):
                try:
                    keys = list(sm.streaming_service.processor_order_req_id_list.keys())
                    logger.info(f"Server manager.streaming_service.processor_order_req_id_list keys: {keys}")
                except Exception as _e:
                    logger.warning(f"Unable to read processor_order_req_id_list keys: {_e}")
            else:
                logger.info("Server manager.streaming_service not available or server_manager is None")
        except Exception as e:
            logger.warning(f"Error checking server_manager presence: {e}")
        
        while True:
            current_time_ms = int(datetime.utcnow().timestamp() * 1000)
            
            # Check if order has expired
            if current_time_ms >= expiry_ms:
                logger.info(f"Order {order_req_id} has expired, sending OrderPaused response")
                
                # Invoke _UpdateProposals with mode = 'OrderPaused'
                await self.proposal_service.update_proposals(
                    order_req_id=order_req_id,
                    proposal_dict_arr=processor_order_req_obj.proposal_dict_arr,
                    mode="OrderPaused"
                )
                
                # Send final response
                response = order_service_pb2.OrderStreamResponse(
                    order_req_id=order_req_id,
                    streaming_response_status="OrderPaused",
                    proposal_id="",
                    follow_up_id=""
                )
                yield response
                break
            
            # Check for messages in queue
            try:
                message = await self.queue_manager.get_from_order_queue(order_req_id, timeout=1.0) # queue creation
                if message:
                    logger.info(f"Stream loop: got queue message for {order_req_id}: {message}")
                    response = await self._process_queue_message(order_req_id, message)
                    if response:
                        logger.info(f"Stream loop: yielding response for {order_req_id}: status={response.streaming_response_status}, proposal_id={response.proposal_id}")
                        yield response
            except asyncio.TimeoutError:
                # Continue loop if no message received
                continue
            except Exception as e:
                logger.error(f"Error processing queue message for {order_req_id}: {str(e)}")
                continue
            
            # Small delay to prevent tight loop
            await asyncio.sleep(60)
            print(f"printing current processor_order_req_id_list:")
            print(self.processor_order_req_id_list)
    
    async def _process_queue_message(
        self, 
        order_req_id: str, 
        message: str
    ) -> order_service_pb2.OrderStreamResponse:
        """
        Process queue message and return appropriate streaming response
        
        Message format: "ProposalID/Code" or "ProposalID.FollowUpID/Code"
        """
        try:
            # Split message by '/' into QueueMessageHeader and QueueMessageCode
            if '/' not in message:
                logger.warning(f"Invalid message format: {message}")
                return None
            
            queue_message_header, queue_message_code = message.split('/', 1)
            logger.info(f"_process_queue_message: header={queue_message_header}, code={queue_message_code} for order {order_req_id}")
            
            processor_order_req_obj = self.processor_order_req_id_list.get(order_req_id)
            if not processor_order_req_obj:
                logger.warning(f"Order not found: {order_req_id}")
                return None
            
            # Check if QueueMessageHeader contains a ProposalID in proposal_dict_arr
            proposal_ids = [p.proposal_id for p in processor_order_req_obj.proposal_dict_arr]
    
            
            if queue_message_header in proposal_ids:
                logger.info(f"_process_queue_message: matched proposal_id {queue_message_header} in proposal_ids for order {order_req_id}")
                return self._handle_proposal_message(order_req_id, queue_message_header, queue_message_code)
            
            # Check if QueueMessageHeader contains ProposalID.FollowUpID
            if '.' in queue_message_header:
                proposal_id, follow_up_id = queue_message_header.split('.', 1)
                if proposal_id in proposal_ids:
                    logger.info(f"_process_queue_message: matched followup proposal_id {proposal_id} (follow_up_id={follow_up_id}) for order {order_req_id}")
                    return self._handle_followup_message(order_req_id, proposal_id, follow_up_id, queue_message_code)
            
            logger.warning(f"Unhandled message: {message} for order: {order_req_id}")
            return None
            
        except Exception as e:
            logger.error(f"Error processing queue message {message}: {str(e)}")
            return None
    
    def _handle_proposal_message(
        self, 
        order_req_id: str, 
        proposal_id: str, 
        code: str
    ) -> order_service_pb2.OrderStreamResponse:
        """
        Handle proposal-level messages
        """
        if code == "New":
            logger.info(f"_handle_proposal_message: New proposal {proposal_id} for order {order_req_id}")
            return order_service_pb2.OrderStreamResponse(
                order_req_id=order_req_id,
                streaming_response_status="NewProposal",
                proposal_id=proposal_id,
                follow_up_id=""
            )
        elif code == "Closed":
            logger.info(f"_handle_proposal_message: ProposalClosed {proposal_id} for order {order_req_id}")
            return order_service_pb2.OrderStreamResponse(
                order_req_id=order_req_id,
                streaming_response_status="ProposalClosed",
                proposal_id=proposal_id,
                follow_up_id=""
            )
        elif code == "EditLock":
            logger.info(f"_handle_proposal_message: EditLock {proposal_id} for order {order_req_id}")
            return order_service_pb2.OrderStreamResponse(
                order_req_id=order_req_id,
                streaming_response_status="EditLock",
                proposal_id=proposal_id,
                follow_up_id=""
            )
        else:
            logger.warning(f"Unknown proposal code: {code}")
            return None
    
    def _handle_followup_message(
        self, 
        order_req_id: str, 
        proposal_id: str, 
        follow_up_id: str, 
        code: str
    ) -> order_service_pb2.OrderStreamResponse:
        """
        Handle follow-up level messages
        """
        if code == "Update":
            return order_service_pb2.OrderStreamResponse(
                order_req_id=order_req_id,
                streaming_response_status="ProposalUpdate",
                proposal_id=proposal_id,
                follow_up_id=follow_up_id
            )
        else:
            logger.warning(f"Unknown follow-up code: {code}")
            return None
    
    async def _process_queue_responses(self, order_req_id: str, context: grpc.aio.ServicerContext):
        """
        Background task to process queue responses (placeholder for future logic)
        """
        # This method can be expanded for additional background processing
        pass

    async def _sweeper(self):
        """
        Periodic sweeper that removes expired orders after their expiry timestamp.
        Runs in the background and invokes the cleanup routine for any orders
        whose expiry has passed. This ensures orders remain available until
        settings.order_expiry_minutes have elapsed even if the client
        disconnects.
        """
        try:
            while True:
                # Use centralized order state manager to find expired orders
                expired = self.queue_manager.get_expired_orders()
                for oid in expired:
                    logger.info(f"Sweeper: cleaning up expired order {oid}")
                    await self._cleanup_order(oid)
                # Run every 30 seconds
                await asyncio.sleep(30)
        except asyncio.CancelledError:
            logger.info("Sweeper task cancelled")
        except Exception as e:
            logger.exception(f"Error in sweeper task: {str(e)}")
    
    async def _cleanup_order(self, order_req_id: str):
        """
        Cleanup order from memory and cancel background tasks
        """
        try:
            # Cancel background task
            if order_req_id in self._background_tasks:
                task = self._background_tasks[order_req_id]
                if not task.done():
                    task.cancel()
                del self._background_tasks[order_req_id]
            
            # Remove order from centralized state
            self.queue_manager.remove_order(order_req_id)
            
            logger.info(f"Cleaned up order: {order_req_id}")
            
        except Exception as e:
            logger.error(f"Error cleaning up order {order_req_id}: {str(e)}")
