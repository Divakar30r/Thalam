# gRPC Streaming Client - gRPC_SS implementation

import asyncio
import grpc
import logging
from typing import AsyncIterator, Optional

from shared.proto.generated import order_service_pb2, order_service_pb2_grpc
from ..core.config import RequestorConfig
from ..core.exceptions import StreamingConnectionError

logger = logging.getLogger(__name__)

class StreamingClient:
    """gRPC streaming client for server streaming"""
    
    def __init__(self):
        self.config = RequestorConfig()
        self.channel: Optional[grpc.aio.Channel] = None
        self.stub: Optional[order_service_pb2_grpc.OrderStreamingServiceStub] = None
        self._connected = False
    
    async def connect(self):
        """Establish gRPC connection"""
        if not self._connected:
            try:
                server_address = f"{self.config.processor_grpc_host}:{self.config.processor_grpc_port}"
                
                self.channel = grpc.aio.insecure_channel(server_address)
                self.stub = order_service_pb2_grpc.OrderStreamingServiceStub(self.channel)
                
                # Test connection
                await self.channel.channel_ready()
                self._connected = True
                
                logger.info(f"gRPC streaming client connected to {server_address}")
                
            except Exception as e:
                logger.error(f"Failed to connect gRPC streaming client: {str(e)}")
                raise StreamingConnectionError(f"Connection failed: {str(e)}")
    
    async def disconnect(self):
        """Close gRPC connection"""
        if self.channel and self._connected:
            await self.channel.close()
            self._connected = False
            logger.info("gRPC streaming client disconnected")
    
    async def start_stream(
        self, 
        order_req_id: str, 
        notification_type: str
    ) -> AsyncIterator[order_service_pb2.OrderStreamResponse]:
        """
        Start server streaming for order processing
        
        Args:
            order_req_id: Order request ID
            notification_type: Notification type
            
        Yields:
            OrderStreamResponse: Streaming responses from server
        """
        try:
            await self.connect()
            
            # Create streaming request
            request = order_service_pb2.OrderStreamRequest(
                order_req_id=order_req_id,
                notification_type=notification_type
            )
            
            logger.info(
                f"Starting stream for order {order_req_id} with notification type {notification_type}. "
                f"Request type: {type(request)}, has order_req_id: {hasattr(request, 'order_req_id')}"
            )
            
            # Start streaming call with optional timeout. If grpc_request_timeout
            # is falsy (0 or None) we omit the timeout so the stream remains open
            # until the server closes it or an error occurs.
            if getattr(self.config, 'grpc_request_timeout', None):
                call = self.stub.ProcessOrderStream(request, timeout=self.config.grpc_request_timeout)
            else:
                call = self.stub.ProcessOrderStream(request)
            
            logger.info(f"Stream call created, type: {type(call)}")
            
            # Process streaming responses
            async for response in call:
                logger.info(
                    f"Received streaming response for {order_req_id}: "
                    f"status={response.streaming_response_status}, "
                    f"proposal_id={response.proposal_id}"
                )
                yield response
                
        except grpc.RpcError as e:
            logger.error(f"gRPC streaming error for {order_req_id}: {e.code()} - {e.details()}")
            raise StreamingConnectionError(f"Streaming RPC failed: {e.details()}")
            
        except asyncio.TimeoutError:
            logger.error(f"Streaming timeout for order {order_req_id}")
            raise StreamingConnectionError(f"Streaming timeout for order {order_req_id}")
            
        except Exception as e:
            logger.error(f"Unexpected streaming error for {order_req_id}: {str(e)}")
            raise StreamingConnectionError(f"Unexpected streaming error: {str(e)}")
        
        finally:
            await self.disconnect()
    
    async def start_stream_with_retry(
        self, 
        order_req_id: str, 
        notification_type: str,
        max_retries: int = 3
    ) -> AsyncIterator[order_service_pb2.OrderStreamResponse]:
        """
        Start streaming with retry logic
        
        Args:
            order_req_id: Order request ID
            notification_type: Notification type
            max_retries: Maximum retry attempts
            
        Yields:
            OrderStreamResponse: Streaming responses from server
        """
        for attempt in range(max_retries + 1):
            try:
                async for response in self.start_stream(order_req_id, notification_type):
                    yield response
                break  # If successful, exit retry loop
                
            except StreamingConnectionError as e:
                if attempt < max_retries:
                    logger.warning(
                        f"Streaming attempt {attempt + 1} failed for {order_req_id}, "
                        f"retrying in {self.config.streaming_reconnect_delay}s: {str(e)}"
                    )
                    await asyncio.sleep(self.config.streaming_reconnect_delay)
                else:
                    logger.error(f"All streaming attempts failed for {order_req_id}")
                    raise
    
    async def health_check(self) -> bool:
        """Check if gRPC server is healthy"""
        try:
            await self.connect()
            return self._connected
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return False
        finally:
            await self.disconnect()
    
    def is_connected(self) -> bool:
        """Check if client is connected"""
        return self._connected