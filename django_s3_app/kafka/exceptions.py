"""
Kafka exception utilities
Provides decorators and utilities for handling document access exceptions
"""

import functools
import traceback
import logging
from typing import Callable, Any, Dict, Optional

logger = logging.getLogger(__name__)

def kafka_exception_handler(exception_type: str = 'document_access_error'):
    """
    Decorator to catch exceptions and send them to Kafka
    
    Args:
        exception_type: Type of exception for categorization
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Try to extract context from function arguments
                context = _extract_context_from_args(args, kwargs)
                
                # Send exception to Kafka
                _send_exception_to_kafka(
                    exception_type=exception_type,
                    error_message=str(e),
                    function_name=func.__name__,
                    stack_trace=traceback.format_exc(),
                    context=context
                )
                
                # Re-raise the exception
                raise
        return wrapper
    return decorator

def _extract_context_from_args(args, kwargs) -> Dict[str, Any]:
    """Extract relevant context from function arguments"""
    context = {}
    
    # Look for common patterns in arguments
    for arg in args:
        if hasattr(arg, 'order_req_id'):
            context['order_req_id'] = getattr(arg, 'order_req_id')
        if hasattr(arg, 's3_key'):
            context['s3_key'] = getattr(arg, 's3_key')
        if isinstance(arg, str) and arg.startswith('SB'):  # Order ID pattern
            context['order_req_id'] = arg
    
    # Extract from kwargs
    for key in ['order_req_id', 's3_key', 'user_id', 'file_name', 'ip_address', 'session_id']:
        if key in kwargs:
            context[key] = kwargs[key]
    
    return context

def _send_exception_to_kafka(exception_type: str, error_message: str, 
                           function_name: str, stack_trace: str, 
                           context: Dict[str, Any]):
    """Send exception details to Kafka"""
    try:
        from .service import kafka_service
        
        kafka_service.send_document_exception({
            'exception_type': exception_type,
            'error_message': error_message,
            'function_name': function_name,
            'stack_trace': stack_trace,
            'order_req_id': context.get('order_req_id'),
            's3_key': context.get('s3_key'),
            'user_id': context.get('user_id'),
            'file_name': context.get('file_name'),
            'ip_address': context.get('ip_address'),
            'session_id': context.get('session_id'),
            'source': 'django_s3_app',
            'additional_context': context
        })
    except Exception as kafka_error:
        logger.error(f"Failed to send exception to Kafka: {kafka_error}")

def send_document_access_exception(order_req_id: str, s3_key: str, user_id: str,
                                 exception_type: str, error_message: str, **kwargs):
    """
    Utility function to manually send document access exceptions to Kafka
    
    Usage:
        send_document_access_exception(
            order_req_id='SB1029435',
            s3_key='documents/file.pdf',
            user_id='user123',
            exception_type='access_denied',
            error_message='User does not have permission to access this document',
            ip_address='192.168.1.1',
            session_id='sess_123'
        )
    """
    try:
        from .service import kafka_service
        
        kafka_service.send_document_access_exception(
            order_req_id=order_req_id,
            s3_key=s3_key,
            user_id=user_id,
            exception_type=exception_type,
            error_message=error_message,
            **kwargs
        )
    except Exception as e:
        logger.error(f"Failed to send document access exception: {e}")