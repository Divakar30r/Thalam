"""
Common document access exception scenarios
Pre-defined exception types and helper functions
"""

class DocumentExceptionTypes:
    """Standard exception types for document access"""
    
    # Access Control Exceptions
    ACCESS_DENIED = 'access_denied'
    AUTHENTICATION_FAILED = 'authentication_failed'
    SESSION_EXPIRED = 'session_expired'
    INSUFFICIENT_PERMISSIONS = 'insufficient_permissions'
    
    # File Operation Exceptions
    FILE_NOT_FOUND = 'file_not_found'
    UPLOAD_FAILED = 'upload_failed'
    DOWNLOAD_FAILED = 'download_failed'
    DELETE_FAILED = 'delete_failed'
    
    # Validation Exceptions
    INVALID_FILE_TYPE = 'invalid_file_type'
    FILE_TOO_LARGE = 'file_too_large'
    INVALID_FILE_NAME = 'invalid_file_name'
    CORRUPTED_FILE = 'corrupted_file'
    
    # System Exceptions
    S3_CONNECTION_ERROR = 's3_connection_error'
    DATABASE_ERROR = 'database_error'
    NETWORK_TIMEOUT = 'network_timeout'
    SERVICE_UNAVAILABLE = 'service_unavailable'
    
    # Rate Limiting
    RATE_LIMIT_EXCEEDED = 'rate_limit_exceeded'
    QUOTA_EXCEEDED = 'quota_exceeded'
    CONCURRENT_LIMIT_EXCEEDED = 'concurrent_limit_exceeded'

def create_access_denied_exception(order_req_id: str, s3_key: str, user_id: str, **kwargs):
    """Helper for access denied exceptions"""
    from .exceptions import send_document_access_exception
    
    return send_document_access_exception(
        order_req_id=order_req_id,
        s3_key=s3_key,
        user_id=user_id,
        exception_type=DocumentExceptionTypes.ACCESS_DENIED,
        error_message=f"User {user_id} denied access to document {s3_key} in order {order_req_id}",
        http_status_code=403,
        **kwargs
    )

def create_file_not_found_exception(order_req_id: str, s3_key: str, user_id: str, **kwargs):
    """Helper for file not found exceptions"""
    from .exceptions import send_document_access_exception
    
    return send_document_access_exception(
        order_req_id=order_req_id,
        s3_key=s3_key,
        user_id=user_id,
        exception_type=DocumentExceptionTypes.FILE_NOT_FOUND,
        error_message=f"Document {s3_key} not found for order {order_req_id}",
        http_status_code=404,
        **kwargs
    )

def create_upload_failed_exception(order_req_id: str, s3_key: str, user_id: str, reason: str, **kwargs):
    """Helper for upload failure exceptions"""
    from .exceptions import send_document_access_exception
    
    return send_document_access_exception(
        order_req_id=order_req_id,
        s3_key=s3_key,
        user_id=user_id,
        exception_type=DocumentExceptionTypes.UPLOAD_FAILED,
        error_message=f"Failed to upload {s3_key} for order {order_req_id}: {reason}",
        http_status_code=500,
        **kwargs
    )

def create_file_too_large_exception(order_req_id: str, s3_key: str, user_id: str, 
                                  file_size: int, max_size: int, **kwargs):
    """Helper for file size limit exceptions"""
    from .exceptions import send_document_access_exception
    
    return send_document_access_exception(
        order_req_id=order_req_id,
        s3_key=s3_key,
        user_id=user_id,
        exception_type=DocumentExceptionTypes.FILE_TOO_LARGE,
        error_message=f"File {s3_key} size {file_size} bytes exceeds limit of {max_size} bytes",
        http_status_code=413,
        additional_context={'file_size': file_size, 'max_size': max_size},
        **kwargs
    )

def create_invalid_file_type_exception(order_req_id: str, s3_key: str, user_id: str, 
                                     file_type: str, allowed_types: list, **kwargs):
    """Helper for invalid file type exceptions"""
    from .exceptions import send_document_access_exception
    
    return send_document_access_exception(
        order_req_id=order_req_id,
        s3_key=s3_key,
        user_id=user_id,
        exception_type=DocumentExceptionTypes.INVALID_FILE_TYPE,
        error_message=f"File type {file_type} not allowed. Allowed types: {', '.join(allowed_types)}",
        http_status_code=415,
        additional_context={'file_type': file_type, 'allowed_types': allowed_types},
        **kwargs
    )