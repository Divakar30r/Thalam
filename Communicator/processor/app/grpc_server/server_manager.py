import asyncio
import logging
from typing import Optional
import grpc
from grpc import aio
from fastapi import FastAPI
import uvicorn
from shared.proto.generated import order_service_pb2_grpc

from ..core.config import settings
from .streaming_server import StreamingServerService
from .non_streaming_server import NonStreamingServerService
from .interceptors import LoggingInterceptor, ErrorHandlingInterceptor


logger = logging.getLogger(__name__)

class ServerManager:
    """Combined FastAPI + gRPC server management"""
    
    def __init__(self, fastapi_app: FastAPI):
        self.fastapi_app = fastapi_app
        self.grpc_server: Optional[aio.Server] = None
        
        # gRPC services
        self.streaming_service = StreamingServerService()
        self.non_streaming_service = NonStreamingServerService()
        
        # Server task (gRPC only; FastAPI managed externally)
        self._grpc_task: Optional[asyncio.Task] = None
    
    async def start(self):
        """
        Start gRPC server only (FastAPI is already managed by uvicorn in main.py)
        """
        logger.info("Starting server manager...")
        
        try:
            # Try to start gRPC server; if it fails, log but don't raise
            # so the FastAPI HTTP endpoints (managed externally) remain available
            # and we still have an instantiated streaming_service object
            # for in-memory operations.
            try:
                await self._start_grpc_server()
                logger.info("Server manager started successfully (gRPC + FastAPI)")
            except Exception as e:
                logger.error(f"gRPC server failed to start: {str(e)}")
                logger.warning("Server manager started with FastAPI only (gRPC failed to bind)")

        except Exception as e:
            logger.error(f"Error starting server manager: {str(e)}")
            await self.stop()
            raise
    
    async def _start_grpc_server(self):
        """
        Start the gRPC server with both streaming and non-streaming services
        """
        try:
            logger.info(f"Starting gRPC server on {settings.grpc_server_host}:{settings.grpc_server_port}")
            
            # Create gRPC server with interceptors
            interceptors = [
                LoggingInterceptor(),
                ErrorHandlingInterceptor()
            ]
            
            self.grpc_server = aio.server(interceptors=interceptors)
            
            # Add services to server - use correct service registration functions
            order_service_pb2_grpc.add_OrderStreamingServiceServicer_to_server(
                self.streaming_service, 
                self.grpc_server
            )
            order_service_pb2_grpc.add_OrderNonStreamingServiceServicer_to_server(
                self.non_streaming_service, 
                self.grpc_server
            )
            
            # Configure server address and attempt to bind. If binding fails
            # (add_insecure_port returns 0), try a set of fallbacks to handle
            # platform-specific resolution issues (IPv4/IPv6 differences on
            # Windows/macOS/Linux).
            listen_addr = f"{settings.grpc_server_host}:{settings.grpc_server_port}"
            bound_port = self.grpc_server.add_insecure_port(listen_addr)
            if not bound_port:
                logger.warning(f"add_insecure_port returned 0 for {listen_addr}; trying fallback addresses")
                # Try common fallbacks
                fallback_hosts = ["127.0.0.1", "0.0.0.0", "[::1]", "::"]
                for fh in fallback_hosts:
                    try_addr = f"{fh}:{settings.grpc_server_port}"
                    bound_port = self.grpc_server.add_insecure_port(try_addr)
                    if bound_port:
                        listen_addr = try_addr
                        logger.info(f"gRPC server bound to fallback address {listen_addr}")
                        break
            if not bound_port:
                raise RuntimeError(f"Failed to bind to address {settings.grpc_server_host}:{settings.grpc_server_port}; no fallback succeeded")

            # Start server
            await self.grpc_server.start()
            
            # Create background task to keep server running
            self._grpc_task = asyncio.create_task(self._run_grpc_server())
            
            logger.info(f"gRPC server started on {listen_addr}")
            
        except Exception as e:
            logger.error(f"Error starting gRPC server: {str(e)}")
            raise
    
    async def _run_grpc_server(self):
        """
        Keep gRPC server running until stopped
        """
        try:
            await self.grpc_server.wait_for_termination()
        except Exception as e:
            logger.error(f"gRPC server error: {str(e)}")
    
    async def stop(self):
        """
        Stop gRPC server gracefully (FastAPI is managed externally)
        """
        logger.info("Stopping server manager...")
        
        try:
            # Stop gRPC server
            if self.grpc_server:
                logger.info("Stopping gRPC server...")
                await self.grpc_server.stop(grace=5)
                
            # Cancel gRPC task
            if self._grpc_task and not self._grpc_task.done():
                self._grpc_task.cancel()
                try:
                    await self._grpc_task
                except asyncio.CancelledError:
                    pass
            
            logger.info("Server manager stopped successfully")
            
        except Exception as e:
            logger.error(f"Error stopping server manager: {str(e)}")
    
    async def health_check(self) -> dict:
        """
        Perform health check on all services
        
        Returns:
            Dictionary with health status of all components
        """
        health_status = {
            "grpc_server": False,
            "streaming_service": False,
            "non_streaming_service": False
        }
        
        try:
            # Check gRPC server
            health_status["grpc_server"] = self.grpc_server is not None
            
            # Check streaming service
            if self.streaming_service:
                # Basic health check - ensure service is instantiated
                health_status["streaming_service"] = True
            
            # Check non-streaming service
            if self.non_streaming_service:
                health_status["non_streaming_service"] = await self.non_streaming_service.health_check()
            
        except Exception as e:
            logger.error(f"Health check error: {str(e)}")
        
        return health_status
