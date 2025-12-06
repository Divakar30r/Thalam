"""
Service for order requests operations - handles DocumentObjects and external API calls
"""

import requests
import logging
from typing import List, Dict, Any, Optional
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)

class DocumentObject:
    """
    Document object structure for embedding in OrderRequest.Documents[documents_object]
    This is NOT a Django model - it's a data structure for MongoDB embedded documents
    """
    
    UPLOAD_STATUS_CHOICES = [
        'Awaiting',      # Presigned URL generated, waiting for client upload
        'uploading',     # Client is uploading
        'completed',     # Upload confirmed and successful
        'failed'         # Upload failed
    ]
    
    def __init__(self, **kwargs):
        """Initialize document object with provided data"""
        # Primary identifiers
        self.s3_key = kwargs.get('s3_key', '')
        
        # File information
        self.file_name = kwargs.get('file_name', '')
        self.content_type = kwargs.get('content_type', '')
        self.file_size = kwargs.get('file_size')
        self.checksum = kwargs.get('checksum')
        
        # User information
        self.user_email = kwargs.get('user_email', '')
        
        # Order request information
        self.order_req_id = kwargs.get('order_req_id', '')
        
        # Optional metadata
        self.label = kwargs.get('label')
        self.notes = kwargs.get('notes')
        
        # S3 and upload information
        self.bucket_name = kwargs.get('bucket_name', '')
        self.sse_algorithm = kwargs.get('sse_algorithm', 'AES256')
        self.upload_status = kwargs.get('upload_status', 'Awaiting')
        
        # URLs
        self.presigned_upload_url = kwargs.get('presigned_upload_url')
        self.public_url = kwargs.get('public_url')
        self.public_url_expiry = kwargs.get('public_url_expiry')
        
        # Timestamps (as ISO strings for MongoDB)
        self.created_at = kwargs.get('created_at', timezone.now().isoformat())
        self.updated_at = kwargs.get('updated_at', timezone.now().isoformat())
        self.uploaded_at = kwargs.get('uploaded_at')
    
    def to_dict(self) -> dict:
        """Convert document object to dictionary for MongoDB storage"""
        return {
            's3_key': self.s3_key,
            'file_name': self.file_name,
            'content_type': self.content_type,
            'file_size': self.file_size,
            'checksum': self.checksum,
            'user_email': self.user_email,
            'order_req_id': self.order_req_id,
            'label': self.label,
            'notes': self.notes,
            'bucket_name': self.bucket_name,
            'sse_algorithm': self.sse_algorithm,
            'upload_status': self.upload_status,
            'presigned_upload_url': self.presigned_upload_url,
            'public_url': self.public_url,
            'public_url_expiry': self.public_url_expiry,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'uploaded_at': self.uploaded_at
        }
    
    @classmethod
    def from_dict(cls, data: dict):
        """Create DocumentObject from dictionary"""
        return cls(**data)
    
    def mark_upload_completed(self):
        """Mark the document as successfully uploaded"""
        self.upload_status = 'completed'
        self.uploaded_at = timezone.now().isoformat()
        self.updated_at = timezone.now().isoformat()
    
    def mark_upload_failed(self):
        """Mark the document upload as failed"""
        self.upload_status = 'failed'
        self.updated_at = timezone.now().isoformat()
    
    def is_upload_completed(self) -> bool:
        """Check if upload is completed"""
        return self.upload_status == 'completed'
    

class OrderRequestsService:
    """
    Service for order requests operations via external API
    Handles GET/PUT operations to /api/v1/order-req/{order-req-id}
    """
    
    def __init__(self):
        self.api_base_url = getattr(settings, 'FASTAPI_APP_BASE_URL', '')
        
    def get_order_request(self, order_req_id: str) -> Optional[Dict[str, Any]]:
        """
        GET order request from external API
        
        Args:
            order_req_id: Order request ID
            
        Returns:
            Order request data or None if not found
        """
        if not self.api_base_url:
            logger.warning("FastAPI base URL not configured")
            return None
            
        try:
            url = f"{self.api_base_url}/api/v1/order-req/{order_req_id}"
            headers = {
                'Content-Type': 'application/json',
                'User-Agent': 'django_s3_app/1.0'
            }
            
            response = requests.get(url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                logger.info(f"Successfully retrieved order request: {order_req_id}")
                return response.json()
            elif response.status_code == 404:
                logger.warning(f"Order request not found: {order_req_id}")
                return None
            else:
                logger.error(f"Failed to get order request: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error getting order request: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting order request: {e}")
            return None
    
    def update_order_request_documents(self, order_req_id: str, documents: List[DocumentObject]) -> bool:
        """
        PUT order request documents to external API
        
        Args:
            order_req_id: Order request ID
            documents: List of DocumentObject instances
            
        Returns:
            True if successful, False otherwise
        """

            
        try:
            url = f"{self.api_base_url}/api/v1/order-req/{order_req_id}"
            headers = {
                'Content-Type': 'application/json',
                'User-Agent': 'django_s3_app/1.0'
            }
            
            # Convert DocumentObjects to dictionaries
            documents_data = [doc.to_dict() for doc in documents]
            
            payload = {
                'documents': documents_data,
                'updated_at': timezone.now().isoformat()
            }
            
            response = requests.put(url, json=payload, headers=headers, timeout=30)
            
            if response.status_code in [200, 204]:
                logger.info(f"Successfully updated order request documents: {order_req_id}")
                return True
            else:
                logger.error(f"Failed to update order request: {response.status_code} - {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error updating order request: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error updating order request: {e}")
            return False
    
    def add_single_document_to_order(self, order_req_id: str, document: DocumentObject) -> bool:
        """
        POST a single document to order request (new MongoDB API endpoint)
        Endpoint: POST /api/v1/order-req/{order_req_id}/Doc

        Args:
            order_req_id: Order request ID
            document: DocumentObject to add

        Returns:
            True if successful, False otherwise
        """
        if not self.api_base_url:
            logger.warning("FastAPI base URL not configured")
            return False

        try:
            url = f"{self.api_base_url}/api/v1/order-req/{order_req_id}/Doc"
            headers = {
                'Content-Type': 'application/json',
                'User-Agent': 'django_s3_app/1.0'
            }

            # Send document data
            payload = document.to_dict()

            response = requests.post(url, json=payload, headers=headers, timeout=30)

            if response.status_code in [200, 201]:
                logger.info(f"Successfully added document to order: {order_req_id}")
                return True
            else:
                logger.error(f"Failed to add document: {response.status_code} - {response.text}")
                return False

        except requests.exceptions.RequestException as e:
            logger.error(f"Network error adding document: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error adding document: {e}")
            return False

    def add_document_to_order(self, order_req_id: str, document: DocumentObject) -> bool:
        """
        DEPRECATED: Use add_single_document_to_order() instead
        Legacy method for backward compatibility
        """
        logger.warning("add_document_to_order() is deprecated, use add_single_document_to_order()")
        return self.add_single_document_to_order(order_req_id, document)
    
    def remove_document_from_order(self, order_req_id: str, s3_key: str) -> bool:
        """
        Remove a document from an order request by s3_key
        
        Args:
            order_req_id: Order request ID
            s3_key: S3 key of document to remove
            
        Returns:
            True if successful, False otherwise
        """
        # Get current order request
        order_data = self.get_order_request(order_req_id)
        if not order_data:
            logger.error(f"Cannot remove document - order request not found: {order_req_id}")
            return False
        
        # Get existing documents and filter out the one to remove
        existing_documents = order_data.get('documents', [])
        filtered_documents = [
            DocumentObject.from_dict(doc) 
            for doc in existing_documents 
            if doc.get('s3_key') != s3_key
        ]
        
        # Update the order request
        return self.update_order_request_documents(order_req_id, filtered_documents)
    
    def get_document_from_order(self, order_req_id: str, s3_key: str) -> Optional[DocumentObject]:
        """
        Get a specific document from an order request
        
        Args:
            order_req_id: Order request ID
            s3_key: S3 key of document to retrieve
            
        Returns:
            DocumentObject if found, None otherwise
        """
        order_data = self.get_order_request(order_req_id)
        if not order_data:
            return None
        
        documents = order_data.get('documents', [])
        for doc_data in documents:
            if doc_data.get('s3_key') == s3_key:
                return DocumentObject.from_dict(doc_data)

        return None

    def update_document_status_in_order(self, order_req_id: str, s3_key: str, status: str) -> bool:
        """
        PUT document status update to order request (new MongoDB API endpoint)
        Endpoint: PUT /api/v1/order-req/{order_req_id}/Doc/{s3_key}

        Args:
            order_req_id: Order request ID
            s3_key: Document S3 key
            status: New upload status ('pending', 'uploading', 'completed', 'failed')

        Returns:
            True if successful, False otherwise
        """
        if not self.api_base_url:
            logger.warning("FastAPI base URL not configured")
            return False

        try:
            # URL encode the s3_key for the path parameter
            import urllib.parse
            encoded_s3_key = urllib.parse.quote(s3_key, safe='')

            url = f"{self.api_base_url}/api/v1/order-req/{order_req_id}/Doc/{encoded_s3_key}"
            headers = {
                'Content-Type': 'application/json',
                'User-Agent': 'django_s3_app/1.0'
            }

            payload = {
                'upload_status': status,
                'updated_at': timezone.now().isoformat()
            }

            if status == 'completed':
                payload['uploaded_at'] = timezone.now().isoformat()

            response = requests.put(url, json=payload, headers=headers, timeout=30)

            if response.status_code in [200, 204]:
                logger.info(f"Successfully updated document status: {s3_key} -> {status}")
                return True
            else:
                logger.error(f"Failed to update status: {response.status_code} - {response.text}")
                return False

        except requests.exceptions.RequestException as e:
            logger.error(f"Network error updating status: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error updating status: {e}")
            return False

# Global instance
order_requests_service = OrderRequestsService()