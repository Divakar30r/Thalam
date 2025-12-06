from typing import Optional, Any
from fastapi import HTTPException
from grpc import StatusCode
import grpc

class ProcessorBaseException(Exception):
    """Base exception class for Processor application"""
    def __init__(self, message: str, details: Optional[dict] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)

class ProposalUpdateException(ProcessorBaseException):
    """Exception raised when proposal update operations fail"""
    pass

class SellerSelectionException(ProcessorBaseException):
    """Exception raised when seller selection process fails"""
    pass

class ExternalAPIException(ProcessorBaseException):
    """Exception raised when external API calls fail"""
    def __init__(self, message: str, status_code: Optional[int] = None, response_data: Optional[dict] = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data

class NotificationException(ProcessorBaseException):
    """Exception raised when notification operations fail"""
    pass

class QueueOperationException(ProcessorBaseException):
    """Exception raised when queue operations fail"""
    pass

class OrderExpiredException(ProcessorBaseException):
    """Exception raised when order has expired"""
    pass

class GRPCServiceException(ProcessorBaseException):
    """Exception raised in gRPC service operations"""
    def __init__(self, message: str, grpc_status_code: StatusCode = StatusCode.INTERNAL):
        super().__init__(message)
        self.grpc_status_code = grpc_status_code

# HTTP Exception mappings
def create_http_exception(exc: ProcessorBaseException, status_code: int = 500) -> HTTPException:
    """Convert processor exception to HTTP exception"""
    return HTTPException(
        status_code=status_code,
        detail={
            "message": exc.message,
            "details": exc.details,
            "type": exc.__class__.__name__
        }
    )

# gRPC Exception mappings
def create_grpc_exception(exc: ProcessorBaseException) -> grpc.RpcError:
    """Convert processor exception to gRPC exception"""
    if isinstance(exc, GRPCServiceException):
        status_code = exc.grpc_status_code
    else:
        status_code = StatusCode.INTERNAL
    
    context = grpc.aio.ServicerContext()
    context.set_code(status_code)
    context.set_details(exc.message)
    return grpc.RpcError()
