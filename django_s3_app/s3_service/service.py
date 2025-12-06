"""
AWS S3 service for handling presigned URLs, file uploads, and Server-Side Encryption (SSE)
Uses AWS STS AssumeRole for temporary credentials with automatic refresh
"""

import boto3
import uuid
import re
import logging
from datetime import datetime, timedelta
from botocore.exceptions import ClientError, NoCredentialsError, BotoCoreError
from botocore.config import Config
from typing import Dict, Optional, Tuple, Any
from django.conf import settings
from django.utils import timezone
from threading import Lock

logger = logging.getLogger(__name__)

class S3Service:
    """
    Service class for AWS S3 operations with Server-Side Encryption support
    Uses STS AssumeRole for temporary credentials with automatic refresh
    """

    def __init__(self):
        self.bucket_name = settings.AWS_S3_BUCKET_NAME
        self.region_name = settings.AWS_S3_REGION_NAME
        self.sse_algorithm = settings.AWS_S3_SSE_ALGORITHM
        self.sse_kms_key_id = settings.AWS_S3_SSE_KMS_KEY_ID
        self.presigned_url_expiry = settings.AWS_S3_PRESIGNED_URL_EXPIRY
        self.public_url_expiry = settings.AWS_S3_PUBLIC_URL_EXPIRY

        # Role assumption configuration
        self.role_arn = settings.AWS_ROLE_ARN
        self.role_session_name = settings.AWS_ROLE_SESSION_NAME
        self.role_session_duration = settings.AWS_ROLE_SESSION_DURATION

        # Credentials caching
        self._cached_credentials = None
        self._credentials_expiry = None
        self._credentials_lock = Lock()

        # Initialize S3 client
        self.s3_client = self._create_s3_client()
    
    def _assume_role(self) -> Dict[str, str]:
        """
        Assume IAM role and get temporary credentials using STS.

        Returns:
            Dictionary containing temporary AWS credentials
        """
        try:
            # Create STS client using the dedicated IAM user credentials
            logger.info(f"Creating STS client with IAM user: {settings.AWS_ACCESS_KEY_ID}")
            sts_client = boto3.client(
                'sts',
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=self.region_name
            )

            # Assume the role
            logger.info(f"Assuming role: {self.role_arn}")
            logger.info(f"Session name: {self.role_session_name}, Duration: {self.role_session_duration}s")
            response = sts_client.assume_role(
                RoleArn=self.role_arn,
                RoleSessionName=self.role_session_name,
                DurationSeconds=self.role_session_duration
            )

            credentials = response['Credentials']
            logger.info(f"✓ Successfully assumed role")
            logger.info(f"  Temporary Access Key: {credentials['AccessKeyId']}")
            logger.info(f"  Credentials valid until: {credentials['Expiration']}")
            logger.info(f"  Time until expiry: {(credentials['Expiration'] - timezone.now()).total_seconds() / 3600:.2f} hours")

            return {
                'AccessKeyId': credentials['AccessKeyId'],
                'SecretAccessKey': credentials['SecretAccessKey'],
                'SessionToken': credentials['SessionToken'],
                'Expiration': credentials['Expiration']
            }

        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_msg = e.response['Error']['Message']
            logger.error(f"✗ AWS ClientError during role assumption")
            logger.error(f"  Error Code: {error_code}")
            logger.error(f"  Error Message: {error_msg}")
            logger.error(f"  Role ARN: {self.role_arn}")
            logger.error(f"  IAM User: {settings.AWS_ACCESS_KEY_ID}")
            raise
        except Exception as e:
            logger.error(f"✗ Unexpected error during role assumption: {e}")
            raise

    def _get_credentials(self) -> Dict[str, str]:
        """
        Get temporary credentials, refreshing if necessary.
        Thread-safe with caching to avoid unnecessary STS calls.

        Returns:
            Dictionary containing current valid credentials
        """
        with self._credentials_lock:
            now = timezone.now()

            # Check if we need to refresh credentials
            # Refresh 5 minutes before expiry to avoid edge cases
            if (self._cached_credentials is None or
                self._credentials_expiry is None or
                now >= (self._credentials_expiry - timedelta(minutes=5))):

                logger.info("Refreshing temporary credentials")
                self._cached_credentials = self._assume_role()
                self._credentials_expiry = self._cached_credentials['Expiration']

            return self._cached_credentials

    def _create_s3_client(self):
        """
        Create and configure S3 client using temporary credentials from AssumeRole.

        This method uses a dedicated IAM user's credentials to assume a role with S3 permissions.
        The temporary credentials are cached and automatically refreshed before expiration.
        """
        try:
            # Get temporary credentials
            credentials = self._get_credentials()

            # Configure boto3 client with custom settings
            boto_config = Config(
                region_name=self.region_name,
                signature_version='s3v4',
                retries={
                    'max_attempts': 3,
                    'mode': 'adaptive'
                }
            )

            # Create S3 client with temporary credentials
            client = boto3.client(
                's3',
                aws_access_key_id=credentials['AccessKeyId'],
                aws_secret_access_key=credentials['SecretAccessKey'],
                aws_session_token=credentials['SessionToken'],
                config=boto_config
            )

            logger.info(f"S3 client initialized with temporary credentials for region: {self.region_name}")
            return client

        except (NoCredentialsError, Exception) as e:
            logger.error(f"Failed to create S3 client: {e}")
            logger.error("Ensure IAM user credentials are correct and role has S3 permissions")
            raise

    def _refresh_client_if_needed(self):
        """
        Check if credentials are about to expire and refresh S3 client if needed.
        This should be called before any S3 operation.
        """
        now = timezone.now()

        # Refresh client if credentials expire in less than 5 minutes
        if (self._credentials_expiry is None or
            now >= (self._credentials_expiry - timedelta(minutes=5))):
            logger.info("Credentials expiring soon, refreshing S3 client")
            self.s3_client = self._create_s3_client()
    
    def _get_sse_params(self) -> Dict[str, str]:
        """Get Server-Side Encryption parameters based on configuration"""
        sse_params = {
            'ServerSideEncryption': self.sse_algorithm
        }
        
        # Add KMS key if using aws:kms encryption
        if self.sse_algorithm == 'aws:kms' and self.sse_kms_key_id:
            sse_params['SSEKMSKeyId'] = self.sse_kms_key_id
            
        return sse_params
    
    def generate_presigned_upload_url(
        self,
        file_name: str,
        content_type: str,
        file_size: Optional[int] = None,
        user_email: Optional[str] = None,
        extra_metadata: Optional[Dict[str, str]] = None,
    ) -> Tuple[str, str, Dict[str, Any]]:
        """
        Generate presigned URL for file upload with SSE

        Args:
            file_name: Original filename
            content_type: MIME type of the file
            file_size: Size of the file in bytes (optional)
            user_id: ID of the user uploading the file (optional)

        Returns:
            Tuple of (presigned_url, s3_key, metadata)
        """
        try:
            # Refresh credentials if needed
            self._refresh_client_if_needed()

            # Log current credential status
            if self._credentials_expiry:
                time_remaining = (self._credentials_expiry - timezone.now()).total_seconds()
                logger.debug(f"Using credentials that expire in {time_remaining / 3600:.2f} hours")

            # Extract order_req_id from extra_metadata if present and generate unique S3 key
            order_req_id = None
            if isinstance(extra_metadata, dict):
                order_req_id = extra_metadata.get('order_req_id')

            s3_key = self._generate_s3_key(file_name, user_email, order_req_id)
            
            # Prepare conditions and fields for presigned POST
            conditions = []
            fields = {}
            
            # Add content type condition
            conditions.append(["eq", "$Content-Type", content_type])
            fields['Content-Type'] = content_type
            
            # Add file size condition if provided
            if file_size:
                conditions.append(["content-length-range", 0, file_size * 2])  # Allow some buffer
            
            # Add SSE parameters
            sse_params = self._get_sse_params()
            for key, value in sse_params.items():
                if key == 'ServerSideEncryption':
                    conditions.append(["eq", f"${key}", value])
                    fields[key] = value
                elif key == 'SSEKMSKeyId':
                    conditions.append(["eq", f"${key}", value])
                    fields[key] = value

            # Add user-provided metadata as x-amz-meta-<key> fields
            # extra_metadata keys should be short strings (we'll lowercase them)
            if extra_metadata:
                for meta_key, meta_value in (extra_metadata.items() if isinstance(extra_metadata, dict) else []):
                    if meta_value is None:
                        continue
                    # S3 stores metadata keys lowercased; enforce safe string format
                    safe_key = str(meta_key).lower()
                    safe_value = str(meta_value)
                    field_name = f"x-amz-meta-{safe_key}"
                    conditions.append(["eq", f"${field_name}", safe_value])
                    fields[field_name] = safe_value
            
            # Generate presigned POST URL
            response = self.s3_client.generate_presigned_post(
                Bucket=self.bucket_name,
                Key=s3_key,
                Fields=fields,
                Conditions=conditions,
                ExpiresIn=self.presigned_url_expiry
            )
            
            # Prepare metadata
            metadata = {
                's3_key': s3_key,
                'bucket_name': self.bucket_name,
                'file_name': file_name,
                'content_type': content_type,
                'file_size': file_size,
                'user_email': user_email,
                'sse_algorithm': self.sse_algorithm,
                'upload_expiry': (timezone.now() + timedelta(seconds=self.presigned_url_expiry)).isoformat(),
                'fields': response['fields']
            }
            
            logger.info(f"Generated presigned upload URL for: {file_name} + s3_key: {s3_key}")
            return response['url'], s3_key, metadata
            
        except ClientError as e:
            logger.error(f"Failed to generate presigned upload URL: {e}")
            raise
    
    def generate_presigned_download_url(
        self,
        s3_key: str,
        expiry_seconds: Optional[int] = None
    ) -> str:
        """
        Generate presigned URL for file download

        Args:
            s3_key: S3 object key
            expiry_seconds: URL expiry time in seconds (optional)

        Returns:
            Presigned download URL
        """
        try:
            # Refresh credentials if needed
            self._refresh_client_if_needed()
            expiry = expiry_seconds or self.presigned_url_expiry
            
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': s3_key
                },
                ExpiresIn=expiry
            )
            
            logger.info(f"Generated presigned download URL for: {s3_key}")
            return url
            
        except ClientError as e:
            logger.error(f"Failed to generate presigned download URL: {e}")
            raise
    
    def generate_public_url(
        self, 
        s3_key: str, 
        expiry_seconds: Optional[int] = None
    ) -> str:
        """
        Generate public URL for file access (longer expiry for client use)
        
        Args:
            s3_key: S3 object key
            expiry_seconds: URL expiry time in seconds (optional, defaults to public_url_expiry)
        
        Returns:
            Public access URL
        """
        expiry = expiry_seconds or self.public_url_expiry
        return self.generate_presigned_download_url(s3_key, expiry)
    
    def get_object_metadata(self, s3_key: str) -> Optional[Dict[str, Any]]:
        """
        Get object metadata from S3

        Args:
            s3_key: S3 object key

        Returns:
            Object metadata dictionary or None if not found
        """
        try:
            # Refresh credentials if needed
            self._refresh_client_if_needed()
            response = self.s3_client.head_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            
            metadata = {
                'content_length': response.get('ContentLength'),
                'content_type': response.get('ContentType'),
                'last_modified': response.get('LastModified'),
                'etag': response.get('ETag', '').strip('"'),
                'sse_algorithm': response.get('ServerSideEncryption'),
                'sse_kms_key_id': response.get('SSEKMSKeyId'),
                'metadata': response.get('Metadata', {})
            }
            
            logger.info(f"Retrieved metadata for: {s3_key}")
            return metadata
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                logger.warning(f"Object not found: {s3_key}")
                return None
            else:
                logger.error(f"Failed to get object metadata: {e}")
                raise

    def move_document_to_order(self, s3_key: str, order_req_id: str, user_email: str) -> Optional[str]:
        """
        Move document from user_email folder to order_req_id folder
        Updates metadata with order_req_id and returns new S3 key

        Args:
            s3_key: Current S3 key (should be in user_email folder)
            order_req_id: Order request ID to move document to
            user_email: User email for validation

        Returns:
            New S3 key after move, or None if failed
        """
        try:
            # Refresh credentials if needed
            self._refresh_client_if_needed()

            # Get current object metadata
            current_metadata = self.get_object_metadata(s3_key)
            if not current_metadata:
                logger.error(f"Cannot move document - not found: {s3_key}")
                return None

            # Validate that document is currently in user_email folder (not already in order folder)
            import re
            def _sanitize_key_part(value: str) -> str:
                sanitized = re.sub(r'[^A-Za-z0-9_\-]', '_', value)
                return sanitized[:128]

            sanitized_email = _sanitize_key_part(user_email)
            if not s3_key.startswith(f"{sanitized_email}/"):
                logger.warning(f"Document not in user folder - cannot move: {s3_key}")
                return None

            # Extract filename from current s3_key
            filename = s3_key.split('/')[-1]

            # Generate new S3 key under order_req_id folder
            sanitized_order_id = _sanitize_key_part(order_req_id)
            new_s3_key = f"{sanitized_order_id}/{filename}"

            # Prepare updated metadata
            new_metadata = dict(current_metadata.get('metadata', {}))
            new_metadata['order_req_id'] = order_req_id

            # Copy object to new location with updated metadata
            copy_source = {
                'Bucket': self.bucket_name,
                'Key': s3_key
            }

            sse_params = self._get_sse_params()
            copy_args = {
                'Bucket': self.bucket_name,
                'Key': new_s3_key,
                'CopySource': copy_source,
                'Metadata': new_metadata,
                'MetadataDirective': 'REPLACE',  # Replace metadata
                'ContentType': current_metadata.get('content_type', 'application/octet-stream'),
                **sse_params
            }

            self.s3_client.copy_object(**copy_args)
            logger.info(f"Copied document to new location: {s3_key} -> {new_s3_key}")

            # Delete old object
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=s3_key)
            logger.info(f"Deleted old document: {s3_key}")

            return new_s3_key

        except ClientError as e:
            logger.error(f"Failed to move document: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error moving document: {e}")
            return None

    def _generate_s3_key(self, file_name: str, user_email: Optional[str] = None, order_req_id: Optional[str] = None) -> str:
        """
        Generate unique S3 key for file storage
        
        Args:
            file_name: Original filename
            user_id: User ID (optional)
        
        Returns:
            Unique S3 key
        """
    # Extract file extension and base name
        file_parts = file_name.rsplit('.', 1)
        if len(file_parts) == 2:
            base_name, extension = file_parts
            extension = f".{extension.lower()}"
        else:
            base_name = file_name
            extension = ""

        # Sanitize the original filename for use in S3 key
        def _sanitize_filename(name: str, max_length: int = 50) -> str:
            # Keep only alphanumerics, dashes, underscores; replace others with underscore
            sanitized = re.sub(r'[^A-Za-z0-9_\-]', '_', name)
            # Remove consecutive underscores
            sanitized = re.sub(r'_+', '_', sanitized)
            # Trim to max length
            return sanitized[:max_length].strip('_')

        # Sanitize for directory prefixes
        def _sanitize_key_part(value: str) -> str:
            # Keep only alphanumerics, dashes and underscores; replace others with underscore
            sanitized = re.sub(r'[^A-Za-z0-9_\-]', '_', value)
            # Trim excessive length to avoid very long keys
            return sanitized[:128]

        # Generate unique identifier and timestamp
        unique_id = str(uuid.uuid4())[:8]  # Use shorter UUID for readability
        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
        sanitized_name = _sanitize_filename(base_name)

        # Construct S3 key with original filename for easy identification
        # Format: {prefix}/{original_filename}_{date}_{uuid}{extension}
        if order_req_id:
            prefix = _sanitize_key_part(str(order_req_id))
            s3_key = f"{prefix}/{sanitized_name}_{timestamp}_{unique_id}{extension}"
        else:
            if user_email:
                # Sanitize user_email for use as folder name
                sanitized_email = _sanitize_key_part(user_email)
                s3_key = f"{sanitized_email}/{sanitized_name}_{timestamp}_{unique_id}{extension}"
            else:
                s3_key = f"anonymous/{sanitized_name}_{timestamp}_{unique_id}{extension}"

        logger.debug(f"Generated S3 key: {s3_key} (from original: {file_name})")
        return s3_key

# Global S3 service instance
s3_service = S3Service()