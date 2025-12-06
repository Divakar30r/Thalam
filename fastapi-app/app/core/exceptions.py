"""
Custom exceptions for the FastAPI application
"""

from typing import Any, Dict, Optional, Union


class BaseAPIException(Exception):
    """Base exception class for API errors"""
    
    def __init__(
        self,
        message: str,
        status_code: int = 400,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(BaseAPIException):
    """Raised when data validation fails"""
    
    def __init__(self, message: str, field: str = None, details: Dict[str, Any] = None):
        super().__init__(message, 422, details)
        self.field = field


class NotFoundError(BaseAPIException):
    """Raised when a requested resource is not found"""
    
    def __init__(self, resource: str, identifier: Union[str, int]):
        message = f"{resource} with identifier '{identifier}' not found"
        super().__init__(message, 404)
        self.resource = resource
        self.identifier = identifier


class ConflictError(BaseAPIException):
    """Raised when there's a conflict with existing data"""
    
    def __init__(self, message: str, conflicting_field: str = None):
        super().__init__(message, 409)
        self.conflicting_field = conflicting_field


class ReferentialIntegrityError(BaseAPIException):
    """Raised when referential integrity constraints are violated"""
    
    def __init__(self, message: str, referenced_collection: str = None):
        super().__init__(message, 400)
        self.referenced_collection = referenced_collection


class DatabaseError(BaseAPIException):
    """Raised when database operations fail"""
    
    def __init__(self, message: str = "Database operation failed"):
        super().__init__(message, 500)


class MongoSchemaValidatorError(BaseAPIException):
    """Raised when MongoDB schema validation fails"""
    
    def __init__(self, message: str, validation_errors: Dict[str, Any] = None):
        super().__init__(message, 422, validation_errors)
        self.validation_errors = validation_errors or {}


class ExceededLimits(BaseAPIException):
    """Raised when an operation exceeds allowed retry/limit attempts"""

    def __init__(self, message: str = "Exceeded generation limits for unique identifier"):
        super().__init__(message, 429)