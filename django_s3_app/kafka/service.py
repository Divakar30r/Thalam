"""
Kafka service for AWS MSK integration
Handles sending document access exceptions to Kafka topics
"""

import json
import logging
from typing import Dict, Any, Optional
from kafka import KafkaProducer
from kafka.errors import KafkaError
from django.utils import timezone
from django.conf import settings

logger = logging.getLogger(__name__)

class KafkaService:
    """Service for sending messages to AWS MSK (Kafka)"""
    
    def __init__(self):
        self.producer = None
        self._initialize_producer()
    
    def _initialize_producer(self):
        """Initialize Kafka producer with AWS MSK configuration"""
        try:
            kafka_config = {
                'bootstrap_servers': settings.KAFKA_BOOTSTRAP_SERVERS,
                'value_serializer': lambda v: json.dumps(v).encode('utf-8'),
                'key_serializer': lambda k: k.encode('utf-8') if k else None,
                'acks': 'all',  # Wait for all replicas to acknowledge
                'retries': 3,
                'retry_backoff_ms': 1000,
                'request_timeout_ms': 30000,
                'delivery_timeout_ms': 120000,
            }
            
            # Add security configuration if credentials are provided
            if settings.KAFKA_SECURITY_PROTOCOL:
                kafka_config.update({
                    'security_protocol': settings.KAFKA_SECURITY_PROTOCOL,
                    'sasl_mechanism': settings.KAFKA_SASL_MECHANISM,
                    'sasl_username': settings.KAFKA_SASL_USERNAME,
                    'sasl_password': settings.KAFKA_SASL_PASSWORD,
                })
            
            self.producer = KafkaProducer(**kafka_config)
            logger.info("Kafka producer initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Kafka producer: {e}")
            self.producer = None
    
    def send_document_exception(self, exception_data: Dict[str, Any]) -> bool:
        """
        Send document access exception to DocumentExceptions topic
        
        Args:
            exception_data: Dictionary containing exception details
            
        Returns:
            bool: True if message sent successfully, False otherwise
        """
        if not self.producer:
            logger.warning("Kafka producer not available, skipping message")
            return False
        
        try:
            # Prepare the message
            message = {
                'timestamp': timezone.now().isoformat(),
                'topic': 'DocumentExceptions',
                'key': 'DocumentAccessLog',
                **exception_data
            }
            
            # Send to Kafka topic
            future = self.producer.send(
                topic='DocumentExceptions',
                key='DocumentAccessLog',
                value=message
            )
            
            # Wait for the message to be sent (with timeout)
            record_metadata = future.get(timeout=10)
            
            logger.info(
                f"Exception message sent to topic {record_metadata.topic} "
                f"partition {record_metadata.partition} offset {record_metadata.offset}"
            )
            return True
            
        except KafkaError as e:
            logger.error(f"Failed to send exception to Kafka: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending to Kafka: {e}")
            return False
    
    def send_document_access_exception(self, order_req_id: str, s3_key: str, 
                                     user_id: str, exception_type: str, 
                                     error_message: str, **kwargs) -> bool:
        """
        Convenience method to send document access exceptions
        
        Args:
            order_req_id: Order request ID
            s3_key: S3 key of the document
            user_id: User ID who attempted access
            exception_type: Type of exception (e.g., 'access_denied', 'file_not_found')
            error_message: Human readable error message
            **kwargs: Additional context data
            
        Returns:
            bool: True if sent successfully
        """
        exception_data = {
            'order_req_id': order_req_id,
            's3_key': s3_key,
            'user_id': user_id,
            'exception_type': exception_type,
            'error_message': error_message,
            'source': 'django_s3_app',
            'access_type': kwargs.get('access_type', 'unknown'),
            'ip_address': kwargs.get('ip_address'),
            'user_agent': kwargs.get('user_agent'),
            'session_id': kwargs.get('session_id'),
            'file_name': kwargs.get('file_name'),
            'http_status_code': kwargs.get('http_status_code'),
            'stack_trace': kwargs.get('stack_trace'),
            'additional_context': kwargs.get('additional_context', {})
        }
        
        return self.send_document_exception(exception_data)
    
    def close(self):
        """Close the Kafka producer"""
        if self.producer:
            try:
                self.producer.flush()
                self.producer.close()
                logger.info("Kafka producer closed successfully")
            except Exception as e:
                logger.error(f"Error closing Kafka producer: {e}")

# Global instance
kafka_service = KafkaService()