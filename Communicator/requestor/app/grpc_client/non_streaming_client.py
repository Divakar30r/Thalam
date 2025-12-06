# gRPC Non-Streaming Client - gRPC_NS implementation

import grpc
import logging
from typing import Dict, Any, List, Optional

from shared.proto.generated import order_service_pb2, order_service_pb2_grpc
from ..core.config import RequestorConfig
from ..core.exceptions import GRPCClientError

logger = logging.getLogger(__name__)

class NonStreamingClient:
    """gRPC non-streaming client for follow-up requests"""
    
    def __init__(self):
        self.config = RequestorConfig()
    
    async def send_follow_up_request(
        self,
        order_req_id: str,
        audience: List[str],
        order_follow_up_id: str,
        message: Dict[str, Any]
    ) -> Optional[order_service_pb2.FollowUpResponse]:
        """
        Send follow-up request via gRPC non-streaming
        
        Args:
            order_req_id: Order request ID
            audience: List of audience IDs
            follow_up_id: Follow-up ID
            message: Message content
            
        Returns:
            FollowUpResponse or None if failed
        """
        channel = None
        try:
            server_address = f"{self.config.processor_grpc_host}:{self.config.processor_grpc_port}"
            
            # Create channel and stub
            channel = grpc.aio.insecure_channel(server_address)
            stub = order_service_pb2_grpc.OrderNonStreamingServiceStub(channel)
            
            # Wait for channel to be ready
            await channel.channel_ready()
            
            # Create message content
            message_content = order_service_pb2.MessageContent(
                urls=message.get("urls", []),
                message_type=message.get("message_type", "text"),
                message=message.get("message", "")
            )
            
            # Create follow-up request
            request = order_service_pb2.FollowUpRequest(
                order_req_id=order_req_id,
                audience=audience,
                order_follow_up_id=order_follow_up_id,
                message=message_content
            )
            
            logger.info(f"Sending follow-up request for order {order_req_id}")
            
            # Send request with timeout
            response = await stub.ProcessFollowUp(
                request,
                timeout=self.config.grpc_request_timeout
            )
            
            logger.info(f"Received follow-up response for order {order_req_id}")
            return response
            
        except grpc.RpcError as e:
            logger.error(f"gRPC follow-up error for {order_req_id}: {e.code()} - {e.details()}")
            raise GRPCClientError(f"Follow-up RPC failed: {e.details()}")
            
        except Exception as e:
            logger.error(f"Unexpected follow-up error for {order_req_id}: {str(e)}")
            raise GRPCClientError(f"Unexpected follow-up error: {str(e)}")
        
        finally:
            if channel:
                await channel.close()
    
    async def send_follow_up_with_retry(
        self,
        order_req_id: str,
        audience: List[str],
        follow_up_id: str,
        message: Dict[str, Any],
        max_retries: int = 3
    ) -> Optional[order_service_pb2.FollowUpResponse]:
        """
        Send follow-up request with retry logic
        
        Args:
            order_req_id: Order request ID
            audience: List of audience IDs
            follow_up_id: Follow-up ID
            message: Message content
            max_retries: Maximum retry attempts
            
        Returns:
            FollowUpResponse or None if failed
        """
        last_exception = None
        
        for attempt in range(max_retries + 1):
            try:
                return await self.send_follow_up_request(
                    order_req_id, audience, follow_up_id, message
                )
                
            except GRPCClientError as e:
                last_exception = e
                
                if attempt < max_retries:
                    logger.warning(
                        f"Follow-up attempt {attempt + 1} failed for {order_req_id}, "
                        f"retrying: {str(e)}"
                    )
                    await asyncio.sleep(1)  # Simple delay between retries
                else:
                    logger.error(f"All follow-up attempts failed for {order_req_id}")
        
        if last_exception:
            raise last_exception
        
        return None
    
    async def health_check(self) -> bool:
        """Check if gRPC server is healthy for non-streaming calls"""
        channel = None
        try:
            server_address = f"{self.config.processor_grpc_host}:{self.config.processor_grpc_port}"
            
            channel = grpc.aio.insecure_channel(server_address)
            await channel.channel_ready()
            
            return True
            
        except Exception as e:
            logger.error(f"Non-streaming health check failed: {str(e)}")
            return False
        
        finally:
            if channel:
                await channel.close()