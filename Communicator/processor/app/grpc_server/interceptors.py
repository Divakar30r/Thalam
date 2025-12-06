import logging
import time
from typing import Callable, Any, Awaitable
import grpc
from grpc import aio

logger = logging.getLogger(__name__)

class LoggingInterceptor(aio.ServerInterceptor):
    """gRPC interceptor for logging requests and responses"""
    
    async def intercept_service(
        self,
        continuation: Callable[[grpc.HandlerCallDetails], Awaitable[grpc.RpcMethodHandler]],
        handler_call_details: grpc.HandlerCallDetails,
    ) -> grpc.RpcMethodHandler:
        """
        Intercept gRPC service calls for logging
        """
        method_name = handler_call_details.method
        start_time = time.time()
        
        logger.info(f"gRPC call started: {method_name}")
        
        try:
            # Continue with the actual service call
            handler = await continuation(handler_call_details)
            
            # Wrap the handler to log completion
            if handler and handler.response_streaming:
                # Streaming response handler
                # Distinguish unary_stream (single request -> stream responses)
                # from stream_stream (stream requests -> stream responses)
                if getattr(handler, 'unary_stream', None) is not None:
                    original_handler = handler.unary_stream

                    async def logged_unary_streaming_handler(request, context):
                        try:
                            async for response in original_handler(request, context):
                                yield response

                            elapsed_time = time.time() - start_time
                            logger.info(f"gRPC streaming call completed: {method_name} in {elapsed_time:.3f}s")

                        except Exception as e:
                            elapsed_time = time.time() - start_time
                            logger.error(f"gRPC streaming call failed: {method_name} in {elapsed_time:.3f}s - {str(e)}")
                            raise

                    return grpc.unary_stream_rpc_method_handler(
                        logged_unary_streaming_handler,
                        request_deserializer=handler.request_deserializer,
                        response_serializer=handler.response_serializer,
                    )
                else:
                    original_handler = handler.stream_stream

                    async def logged_stream_streaming_handler(request_iterator, context):
                        try:
                            async for response in original_handler(request_iterator, context):
                                yield response

                            elapsed_time = time.time() - start_time
                            logger.info(f"gRPC streaming call completed: {method_name} in {elapsed_time:.3f}s")

                        except Exception as e:
                            elapsed_time = time.time() - start_time
                            logger.error(f"gRPC streaming call failed: {method_name} in {elapsed_time:.3f}s - {str(e)}")
                            raise

                    return grpc.stream_stream_rpc_method_handler(
                        logged_stream_streaming_handler,
                        request_deserializer=handler.request_deserializer,
                        response_serializer=handler.response_serializer,
                    )
            
            elif handler:
                # Unary response handler (could be unary_unary or stream_unary)
                if getattr(handler, 'unary_unary', None) is not None:
                    original_handler = handler.unary_unary

                    async def logged_unary_unary_handler(request, context):
                        try:
                            response = await original_handler(request, context)

                            elapsed_time = time.time() - start_time
                            logger.info(f"gRPC unary call completed: {method_name} in {elapsed_time:.3f}s")

                            return response

                        except Exception as e:
                            elapsed_time = time.time() - start_time
                            logger.error(f"gRPC unary call failed: {method_name} in {elapsed_time:.3f}s - {str(e)}")
                            raise

                    return grpc.unary_unary_rpc_method_handler(
                        logged_unary_unary_handler,
                        request_deserializer=handler.request_deserializer,
                        response_serializer=handler.response_serializer,
                    )
                else:
                    original_handler = handler.stream_unary

                    async def logged_stream_unary_handler(request_iterator, context):
                        try:
                            response = await original_handler(request_iterator, context)

                            elapsed_time = time.time() - start_time
                            logger.info(f"gRPC unary call completed: {method_name} in {elapsed_time:.3f}s")

                            return response

                        except Exception as e:
                            elapsed_time = time.time() - start_time
                            logger.error(f"gRPC unary call failed: {method_name} in {elapsed_time:.3f}s - {str(e)}")
                            raise

                    return grpc.stream_unary_rpc_method_handler(
                        logged_stream_unary_handler,
                        request_deserializer=handler.request_deserializer,
                        response_serializer=handler.response_serializer,
                    )
            
            return handler
            
        except Exception as e:
            elapsed_time = time.time() - start_time
            logger.error(f"gRPC call interceptor error: {method_name} in {elapsed_time:.3f}s - {str(e)}")
            raise

class ErrorHandlingInterceptor(aio.ServerInterceptor):
    """gRPC interceptor for error handling and status code management"""
    
    async def intercept_service(
        self,
        continuation: Callable[[grpc.HandlerCallDetails], Awaitable[grpc.RpcMethodHandler]],
        handler_call_details: grpc.HandlerCallDetails,
    ) -> grpc.RpcMethodHandler:
        """
        Intercept gRPC service calls for error handling
        """
        method_name = handler_call_details.method
        
        try:
            handler = await continuation(handler_call_details)
            
            if handler and handler.response_streaming:
                # Streaming response handler - distinguish unary_stream vs stream_stream
                if getattr(handler, 'unary_stream', None) is not None:
                    original_handler = handler.unary_stream

                    async def error_handled_unary_streaming_handler(request, context):
                        try:
                            async for response in original_handler(request, context):
                                yield response

                        except grpc.RpcError:
                            # Re-raise gRPC errors as-is
                            raise
                        except Exception as e:
                            logger.error(f"Unhandled error in {method_name}: {str(e)}")
                            await context.abort(
                                grpc.StatusCode.INTERNAL,
                                f"Internal server error: {str(e)}"
                            )

                    return grpc.unary_stream_rpc_method_handler(
                        error_handled_unary_streaming_handler,
                        request_deserializer=handler.request_deserializer,
                        response_serializer=handler.response_serializer,
                    )
                else:
                    original_handler = handler.stream_stream

                    async def error_handled_stream_streaming_handler(request_iterator, context):
                        try:
                            async for response in original_handler(request_iterator, context):
                                yield response

                        except grpc.RpcError:
                            # Re-raise gRPC errors as-is
                            raise
                        except Exception as e:
                            logger.error(f"Unhandled error in {method_name}: {str(e)}")
                            await context.abort(
                                grpc.StatusCode.INTERNAL,
                                f"Internal server error: {str(e)}"
                            )

                    return grpc.stream_stream_rpc_method_handler(
                        error_handled_stream_streaming_handler,
                        request_deserializer=handler.request_deserializer,
                        response_serializer=handler.response_serializer,
                    )
            
            elif handler:
                # Unary response handler - distinguish unary_unary vs stream_unary
                if getattr(handler, 'unary_unary', None) is not None:
                    original_handler = handler.unary_unary

                    async def error_handled_unary_unary_handler(request, context):
                        try:
                            return await original_handler(request, context)

                        except grpc.RpcError:
                            # Re-raise gRPC errors as-is
                            raise
                        except Exception as e:
                            logger.error(f"Unhandled error in {method_name}: {str(e)}")
                            await context.abort(
                                grpc.StatusCode.INTERNAL,
                                f"Internal server error: {str(e)}"
                            )

                    return grpc.unary_unary_rpc_method_handler(
                        error_handled_unary_unary_handler,
                        request_deserializer=handler.request_deserializer,
                        response_serializer=handler.response_serializer,
                    )
                else:
                    original_handler = handler.stream_unary

                    async def error_handled_stream_unary_handler(request_iterator, context):
                        try:
                            return await original_handler(request_iterator, context)

                        except grpc.RpcError:
                            # Re-raise gRPC errors as-is
                            raise
                        except Exception as e:
                            logger.error(f"Unhandled error in {method_name}: {str(e)}")
                            await context.abort(
                                grpc.StatusCode.INTERNAL,
                                f"Internal server error: {str(e)}"
                            )

                    return grpc.stream_unary_rpc_method_handler(
                        error_handled_stream_unary_handler,
                        request_deserializer=handler.request_deserializer,
                        response_serializer=handler.response_serializer,
                    )
            
            return handler
            
        except Exception as e:
            logger.error(f"Error in interceptor for {method_name}: {str(e)}")
            raise

class MetricsInterceptor(aio.ServerInterceptor):
    """gRPC interceptor for collecting metrics (optional)"""
    
    def __init__(self):
        self.call_count = 0
        self.error_count = 0
        self.total_duration = 0.0
    
    async def intercept_service(
        self,
        continuation: Callable[[grpc.HandlerCallDetails], Awaitable[grpc.RpcMethodHandler]],
        handler_call_details: grpc.HandlerCallDetails,
    ) -> grpc.RpcMethodHandler:
        """
        Intercept gRPC service calls for metrics collection
        """
        method_name = handler_call_details.method
        start_time = time.time()
        
        self.call_count += 1
        
        try:
            handler = await continuation(handler_call_details)
            
            if handler and handler.response_streaming:
                # Streaming response handler - distinguish unary_stream vs stream_stream
                if getattr(handler, 'unary_stream', None) is not None:
                    original_handler = handler.unary_stream

                    async def metrics_unary_streaming_handler(request, context):
                        try:
                            async for response in original_handler(request, context):
                                yield response

                            elapsed_time = time.time() - start_time
                            self.total_duration += elapsed_time

                        except Exception as e:
                            self.error_count += 1
                            elapsed_time = time.time() - start_time
                            self.total_duration += elapsed_time
                            raise

                    return grpc.unary_stream_rpc_method_handler(
                        metrics_unary_streaming_handler,
                        request_deserializer=handler.request_deserializer,
                        response_serializer=handler.response_serializer,
                    )
                else:
                    original_handler = handler.stream_stream

                    async def metrics_stream_streaming_handler(request_iterator, context):
                        try:
                            async for response in original_handler(request_iterator, context):
                                yield response

                            elapsed_time = time.time() - start_time
                            self.total_duration += elapsed_time

                        except Exception as e:
                            self.error_count += 1
                            elapsed_time = time.time() - start_time
                            self.total_duration += elapsed_time
                            raise

                    return grpc.stream_stream_rpc_method_handler(
                        metrics_stream_streaming_handler,
                        request_deserializer=handler.request_deserializer,
                        response_serializer=handler.response_serializer,
                    )
            
            elif handler:
                # Unary response handler - distinguish unary_unary vs stream_unary
                if getattr(handler, 'unary_unary', None) is not None:
                    original_handler = handler.unary_unary

                    async def metrics_unary_unary_handler(request, context):
                        try:
                            response = await original_handler(request, context)

                            elapsed_time = time.time() - start_time
                            self.total_duration += elapsed_time

                            return response

                        except Exception as e:
                            self.error_count += 1
                            elapsed_time = time.time() - start_time
                            self.total_duration += elapsed_time
                            raise

                    return grpc.unary_unary_rpc_method_handler(
                        metrics_unary_unary_handler,
                        request_deserializer=handler.request_deserializer,
                        response_serializer=handler.response_serializer,
                    )
                else:
                    original_handler = handler.stream_unary

                    async def metrics_stream_unary_handler(request_iterator, context):
                        try:
                            response = await original_handler(request_iterator, context)

                            elapsed_time = time.time() - start_time
                            self.total_duration += elapsed_time

                            return response

                        except Exception as e:
                            self.error_count += 1
                            elapsed_time = time.time() - start_time
                            self.total_duration += elapsed_time
                            raise

                    return grpc.stream_unary_rpc_method_handler(
                        metrics_stream_unary_handler,
                        request_deserializer=handler.request_deserializer,
                        response_serializer=handler.response_serializer,
                    )
            
            return handler
            
        except Exception as e:
            self.error_count += 1
            elapsed_time = time.time() - start_time
            self.total_duration += elapsed_time
            raise
    
    def get_metrics(self) -> dict:
        """
        Get collected metrics
        
        Returns:
            Dictionary with metrics data
        """
        avg_duration = self.total_duration / self.call_count if self.call_count > 0 else 0
        error_rate = self.error_count / self.call_count if self.call_count > 0 else 0
        
        return {
            "total_calls": self.call_count,
            "total_errors": self.error_count,
            "error_rate": error_rate,
            "total_duration": self.total_duration,
            "average_duration": avg_duration
        }
    
    def reset_metrics(self):
        """
        Reset all metrics to zero
        """
        self.call_count = 0
        self.error_count = 0
        self.total_duration = 0.0
