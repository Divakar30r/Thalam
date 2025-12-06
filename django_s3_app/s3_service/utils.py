"""
Additional S3 utilities and helpers
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import mimetypes
from django.utils import timezone
from .service import s3_service

logger = logging.getLogger(__name__)

class S3DocumentUtils:
    """Utility functions for S3 document operations"""
    
    @staticmethod
    def generate_s3_key(file_name: str, user_email: Optional[str] = None) -> str:
        """
        Generate a structured S3 key for file storage
        
        Args:
            file_name: Original filename
            user_id: User ID for organizing files
            
        Returns:
            S3 key string
        """
        import uuid
        import os
        
        now = datetime.now()
        
        # Extract file extension
        name, ext = os.path.splitext(file_name)
        if not ext:
            ext = '.bin'  # Default extension
        
        # Generate unique identifier
        unique_id = str(uuid.uuid4())
        
        # Build structured path
        year = now.strftime('%Y')
        month = now.strftime('%m')
        day = now.strftime('%d')
        
        if user_email:
            # Include user email in path for organization
            # sanitize email for path (replace @ and other chars)
            safe_user = user_email.replace('@', '_at_').replace('.', '_')
            s3_key = f"documents/{safe_user}/{year}/{month}/{day}/{unique_id}{ext}"
        else:
            s3_key = f"documents/{year}/{month}/{day}/{unique_id}{ext}"
        
        return s3_key
    
    @staticmethod
    def get_content_type(file_name: str, default: str = 'application/octet-stream') -> str:
        """
        Get MIME type for file
        
        Args:
            file_name: Filename to analyze
            default: Default MIME type if not detected
            
        Returns:
            MIME type string
        """
        content_type, _ = mimetypes.guess_type(file_name)
        return content_type or default
    
    @staticmethod
    def validate_file_type(content_type: str, allowed_types: Optional[List[str]] = None) -> bool:
        """
        Validate if file type is allowed
        
        Args:
            content_type: MIME type to validate
            allowed_types: List of allowed MIME types (None = allow all)
            
        Returns:
            True if allowed, False otherwise
        """
        if not allowed_types:
            return True
        
        # Check exact match
        if content_type in allowed_types:
            return True
        
        # Check wildcard patterns (e.g., "image/*")
        for allowed_type in allowed_types:
            if '*' in allowed_type:
                category = allowed_type.split('/')[0]
                if content_type.startswith(f"{category}/"):
                    return True
        
        return False
    
    @staticmethod
    def format_file_size(size_bytes: int) -> str:
        """
        Format file size in human readable format
        
        Args:
            size_bytes: Size in bytes
            
        Returns:
            Formatted size string
        """
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
        
        return f"{size_bytes:.1f} {size_names[i]}"
    
    @staticmethod
    def extract_metadata_from_s3_object(s3_response: Dict) -> Dict:
        """
        Extract metadata from S3 object response
        
        Args:
            s3_response: S3 GetObject response
            
        Returns:
            Dictionary of extracted metadata
        """
        metadata = {}
        
        # Basic metadata
        if 'ContentLength' in s3_response:
            metadata['file_size'] = s3_response['ContentLength']
        
        if 'ContentType' in s3_response:
            metadata['content_type'] = s3_response['ContentType']
        
        if 'ETag' in s3_response:
            metadata['etag'] = s3_response['ETag'].strip('"')
        
        if 'LastModified' in s3_response:
            metadata['last_modified'] = s3_response['LastModified']
        
        # Server-side encryption
        if 'ServerSideEncryption' in s3_response:
            metadata['sse_algorithm'] = s3_response['ServerSideEncryption']
        
        if 'SSEKMSKeyId' in s3_response:
            metadata['sse_kms_key_id'] = s3_response['SSEKMSKeyId']
        
        # Custom metadata
        if 'Metadata' in s3_response:
            for key, value in s3_response['Metadata'].items():
                metadata[f'custom_{key}'] = value
        
        return metadata