"""
Document handler service for attachment management
Handles document metadata, S3 operations, and FastAPI integration
"""

import logging
import requests
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from django.utils import timezone
from s3_service.service import s3_service
from keycloak_auth.service import keycloak_service
from django.conf import settings
from .models import DocumentMetadata
from .dbHandling.order_requests_service import order_requests_service, DocumentObject

logger = logging.getLogger(__name__)

class DocumentHandler:
    """
    Service class for handling document operations including:
    - S3 presigned URL generation
    - Document metadata management
    - Public URL generation
    """
    
    def __init__(self):
        pass
    
    def create_presigned_upload_url(
        self,
        file_name: str,
        content_type: str,
        order_req_id: Optional[str] = None,
        file_size: Optional[int] = None,
        user_email: Optional[str] = None,
        label: Optional[str] = None,
        notes: Optional[str] = None,
        checksum: Optional[str] = None
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Create presigned upload URL and document metadata record

        Args:
            file_name: Original filename
            content_type: MIME type
            order_req_id: Optional order request ID
            file_size: File size in bytes
            user_email: User email address
            label: Optional document label
            notes: Optional document notes
            checksum: Optional file checksum

        Returns:
            Tuple of (presigned_url, metadata_dict)
        """
        try:
            # Generate presigned URL and S3 key
            # Prepare extra metadata to store on S3 object (x-amz-meta-*)
            extra_metadata = {
                'user_email': user_email or 'anonymous',
                'label': label,
                'notes': notes
            }

            # Only add order_req_id to metadata if provided
            if order_req_id:
                extra_metadata['order_req_id'] = order_req_id

            presigned_url, s3_key, s3_metadata = s3_service.generate_presigned_upload_url(
                file_name=file_name,
                content_type=content_type,
                file_size=file_size,
                user_email=user_email,
                extra_metadata=extra_metadata
            )

            # Add document to existing order request via external API (only if order_req_id provided)
            if order_req_id:
                # Create DocumentObject for the order request
                document_object = DocumentObject(
                    s3_key=s3_key,
                    file_name=file_name,
                    content_type=content_type,
                    file_size=file_size,
                    checksum=checksum,
                    user_email=user_email or 'anonymous',
                    order_req_id=order_req_id,
                    label=label,
                    notes=notes,
                    bucket_name=s3_metadata.get('bucket_name'),
                    sse_algorithm=s3_metadata.get('sse_algorithm'),
                    upload_status='Awaiting',
                    presigned_upload_url=presigned_url
                )

                success = order_requests_service.add_document_to_order(order_req_id, document_object)
                if not success:
                    logger.warning(f"Failed to add document to order request: {order_req_id}")
            else:
                logger.info(f"No order_req_id provided - document will be stored under user folder: {user_email}")

            # Prepare response metadata (no local database persistence)
            response_metadata = {
                'document_id': None,  # No local database ID
                's3_key': s3_key,
                'file_name': file_name,
                'content_type': content_type,
                'file_size': file_size,
                'checksum': checksum,
                'user_email': user_email,
                'label': label,
                'notes': notes,
                'order_req_id': order_req_id,
                'upload_fields': s3_metadata.get('fields'),
                'upload_expiry': s3_metadata.get('upload_expiry'),
                'created_at': timezone.now().isoformat()
            }

            logger.info(f"Created presigned upload URL for document: {file_name}")
            return presigned_url, response_metadata

        except Exception as e:
            logger.error(f"Failed to create presigned upload URL: {e}")
            raise
    
    def generate_public_url(
        self,
        s3_key: str,
        user_email: Optional[str] = None,
        expiry_seconds: Optional[int] = None
    ) -> Optional[str]:
        """
        Generate public URL for document access

        Args:
            s3_key: S3 object key
            user_email: User email for access logging
            expiry_seconds: URL expiry time

        Returns:
            Public URL string or None if not found
        """
        try:
            # Verify document exists in S3
            s3_metadata = s3_service.get_object_metadata(s3_key)
            if not s3_metadata:
                logger.error(f"Document not found in S3: {s3_key}")
                return None

            # Generate public URL
            public_url = s3_service.generate_public_url(s3_key, expiry_seconds)

            file_name = s3_metadata.get('metadata', {}).get('file_name', s3_key.split('/')[-1])
            logger.info(f"Generated public URL for document: {file_name}")
            return public_url

        except Exception as e:
            logger.error(f"Failed to generate public URL: {e}")
            raise

# Global document handler instance
document_handler = DocumentHandler()