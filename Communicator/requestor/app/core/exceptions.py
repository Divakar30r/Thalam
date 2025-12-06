# Custom exceptions for Requestor service

class RequestorBaseException(Exception):
    """Base exception for Requestor service"""
    pass

class OrderServiceError(RequestorBaseException):
    """Exception raised by OrderService"""
    pass

class NotificationServiceError(RequestorBaseException):
    """Exception raised by NotificationService"""
    pass

class GRPCClientError(RequestorBaseException):
    """Exception raised by gRPC client"""
    pass

class StreamingConnectionError(GRPCClientError):
    """Exception raised when streaming connection fails"""
    pass

class ConfigurationError(RequestorBaseException):
    """Exception raised for configuration errors"""
    pass