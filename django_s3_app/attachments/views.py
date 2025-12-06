"""
Django REST Framework views for attachment management
"""

import logging
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from attachments.dbHandling.order_requests_service import DocumentObject
from keycloak_auth.drf_authentication import KeycloakAuthentication
from keycloak_auth.permissions import AdminAccess, DocumentOwnerPermission, InterestedRolesAccess, ViewAccess, UploadAccess
from keycloak_auth.service import keycloak_service
from .models import DocumentMetadata
from .serializers import (
    PresignedUploadRequestSerializer,
    PresignedUploadResponseSerializer,
    PublicUrlRequestSerializer,
    DocumentStatusUpdateSerializer,
    AssignDocumentToOrderSerializer
)
from .document_handler import document_handler

logger = logging.getLogger(__name__)


class PresignedUploadView(APIView):
    """
    Generate presigned upload URL for S3
    
    POST /api/v1/presigned-upload/
    """
    authentication_classes = [KeycloakAuthentication]
    permission_classes = [IsAuthenticated, UploadAccess, InterestedRolesAccess]
    
    def post(self, request):
        serializer = PresignedUploadRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {'error': 'Invalid request data', 'details': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Extract validated data (use snake_case keys from serializer)
            data = serializer.validated_data
            user_email = keycloak_service.get_user_email_from_request(request)
            
            # Create presigned upload URL
            presigned_url, metadata = document_handler.create_presigned_upload_url(
                file_name=data['file_name'],
                content_type=data['content_type'],
                order_req_id=data.get('order_req_id'),
                file_size=data.get('file_size'),
                user_email=user_email,
                label=data.get('label'),
                notes=data.get('notes'),
                checksum=data.get('checksum')
            )
            
            # Prepare response so serializer finds expected top-level keys
            # metadata returned from the handler already contains the keys the serializer expects
            response_data = dict(metadata) if isinstance(metadata, dict) else {}
            response_data['presigned_url'] = presigned_url

            # Return serialized response (treating response_data as the instance to be serialized)
            response_serializer = PresignedUploadResponseSerializer(response_data)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Failed to create presigned upload URL: {e}")
            return Response(
                {'error': 'Failed to generate upload URL'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class PublicUrlView(APIView):
    """
    #DIV: Not important, as it is making a doc open for public access without any token/keys
    Generate public URL for document access

    POST /api/v1/public-url/
    """
    authentication_classes = [KeycloakAuthentication]
    permission_classes = [IsAuthenticated, ViewAccess, InterestedRolesAccess]
    
    def post(self, request):
        serializer = PublicUrlRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {'error': 'Invalid request data', 'details': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            data = serializer.validated_data
            user_email = keycloak_service.get_user_email_from_request(request)
            
            # Generate public URL (use snake_case keys)
            public_url = document_handler.generate_public_url(
                s3_key=data['s3_key'],
                user_email=user_email,
                expiry_seconds=data.get('expiry_seconds')
            )
            
            if not public_url:
                return Response(
                    {'error': 'Document not found or not ready'},
                    status=status.HTTP_404_NOT_FOUND
                )

            response_data = {'public_url': public_url}
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Failed to generate public URL: {e}")
            return Response(
                {'error': 'Failed to generate public URL'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class DocumentMetadataView(APIView):
    """
    Retrieve document metadata from S3 and MongoDB

    GET /api/v1/metadata/<s3_key>/
    """
    authentication_classes = [KeycloakAuthentication]
    permission_classes = [IsAuthenticated, ViewAccess, InterestedRolesAccess]

    @method_decorator(cache_page(300))  # Cache for 5 minutes
    def get(self, request, s3_key):
        try:
            from s3_service.service import s3_service
            from .dbHandling.order_requests_service import order_requests_service

            # Get document metadata from S3
            s3_metadata = s3_service.get_object_metadata(s3_key)
            if not s3_metadata:
                return Response(
                    {'error': 'Document not found in S3'},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Extract order_req_id from S3 metadata
            order_req_id = s3_metadata.get('metadata', {}).get('order_req_id')

            # Get additional metadata from MongoDB if order_req_id is available
            mongo_doc = None
            if order_req_id:
                mongo_doc = order_requests_service.get_document_from_order(order_req_id, s3_key)

            # Create DocumentMetadata object from S3 + MongoDB data
            document = DocumentMetadata.from_s3_metadata(s3_key, s3_metadata, mongo_doc.to_dict() if mongo_doc else None)

            # Return document data
            response_data = document.to_dict()
            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Failed to retrieve document metadata: {e}")
            return Response(
                {'error': 'Document not found'},
                status=status.HTTP_404_NOT_FOUND
            )

class DocumentListView(APIView):
    """
    List documents for a user from S3 or MongoDB
    Users can view their own documents or documents for orders they have access to
    Admins (DOC_VIEWALL, DOC_UPLALL) can view any documents

    GET /api/v1/documents/?userEmail=<email>&orderReqId=<id>
    """
    authentication_classes = [KeycloakAuthentication]
    permission_classes = [IsAuthenticated, ViewAccess]

    def get(self, request):
        try:
            from .dbHandling.order_requests_service import order_requests_service
            from s3_service.service import s3_service
            from keycloak_auth.permissions import DocumentOwnerPermission
            import re

            # Swap parameter priority: userEmail is primary, orderReqId is optional
            user_email = request.query_params.get('userEmail')
            order_req_id = request.query_params.get('orderReqId')

            current_user_email = keycloak_service.get_user_email_from_request(request)
            user_roles = keycloak_service.get_user_roles_from_request(request)

            # Check if user has admin access
            is_admin = any(role in user_roles for role in ['DOC_VIEWALL', 'DOC_UPLALL'])

            # Default to current user if no userEmail provided
            if not user_email:
                user_email = current_user_email

            # Non-admin users can only view their own documents
            if not is_admin and user_email != current_user_email:
                return Response(
                    {'error': 'You can only view your own documents'},
                    status=status.HTTP_403_FORBIDDEN
                )

            # If order_req_id is provided, get documents from MongoDB for that order
            if order_req_id:
                order_data = order_requests_service.get_order_request(order_req_id)
                if not order_data:
                    return Response(
                        {'error': 'Order request not found'},
                        status=status.HTTP_404_NOT_FOUND
                    )

                documents_data = order_data.get('Documents', [])

                # Filter by user_email
                documents_data = [doc for doc in documents_data if doc.get('user_email') == user_email and doc.get('upload_status')=="Completed"]

            else:
                # No order_req_id: List documents from S3 under user_email folder

                # Sanitize user_email for S3 prefix (same logic as in s3_service)
                def _sanitize_key_part(value: str) -> str:
                    sanitized = re.sub(r'[^A-Za-z0-9_\-]', '_', value)
                    return sanitized[:128]

                sanitized_email = _sanitize_key_part(user_email)

                # List objects from S3 with user_email prefix
                try:
                    response = s3_service.s3_client.list_objects_v2(
                        Bucket=s3_service.bucket_name,
                        Prefix=f'{sanitized_email}/'
                    )

                    documents_data = []
                    if 'Contents' in response:
                        for obj in response['Contents']:
                            s3_key = obj['Key']

                            # Get object metadata
                            s3_metadata = s3_service.get_object_metadata(s3_key)
                            if s3_metadata:
                                doc_data = {
                                    's3_key': s3_key,
                                    'file_name': s3_metadata.get('metadata', {}).get('file_name', s3_key.split('/')[-1]),
                                    'content_type': s3_metadata.get('content_type', ''),
                                    'file_size': s3_metadata.get('content_length'),
                                    'checksum': s3_metadata.get('etag'),
                                    'user_email': s3_metadata.get('metadata', {}).get('user_email', user_email),
                                    'label': s3_metadata.get('metadata', {}).get('label'),
                                    'upload_status': 'completed',  # If in S3, it's completed
                                    'created_at': obj.get('LastModified').isoformat() if obj.get('LastModified') else None,
                                    'updated_at': obj.get('LastModified').isoformat() if obj.get('LastModified') else None
                                }
                                documents_data.append(doc_data)

                except Exception as e:
                    logger.error(f"Failed to list S3 objects for user {user_email}: {e}")
                    documents_data = []

            # Paginate results
            limit = int(request.query_params.get('limit', 50))
            offset = int(request.query_params.get('offset', 0))

            total_count = len(documents_data)
            paginated_documents = documents_data[offset:offset + limit]

            response_data = {
                'documents': paginated_documents,
                'totalCount': total_count,
                'limit': limit,
                'offset': offset
            }

            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Failed to list documents: {e}")
            return Response(
                {'error': 'Failed to retrieve documents'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class UpdateOrderDocumentsView(APIView):
    """
    Update document status and order documents

    PUT /api/v1/status/<s3_key>/
    """
    authentication_classes = [KeycloakAuthentication]
    permission_classes = [IsAuthenticated, AdminAccess]

    def put(self, request, s3_key):
        try:
            # Verify document exists in S3 before updating MongoDB
            from s3_service.service import s3_service
            from .dbHandling.order_requests_service import order_requests_service

             


            s3_metadata = s3_service.get_object_metadata(s3_key)
            if not s3_metadata:
                logger.error(f"Document not found in S3: {s3_key}")
                return Response(
                    {'error': 'Document not found in S3', 's3_key': s3_key},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Extract order_req_id from S3 metadata
            order_req_id = s3_metadata.get('metadata', {}).get('order_req_id')
            if not order_req_id:
                logger.warning(f"S3 object missing order_req_id metadata: {s3_key}")
                return Response(
                    {'error': 'Document missing order request metadata'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Check permissions using new permission system
            # Create temporary DocumentMetadata object for permission checking
            temp_document = DocumentMetadata(
                s3_key=s3_key,
                user_email=s3_metadata.get('metadata', {}).get('user_email', ''),
                order_req_id=order_req_id
            )
            permission_checker = DocumentOwnerPermission()
            if not permission_checker.check_document_access(request, temp_document):
                return Response(
                    {'error': 'Insufficient permissions'},
                    status=status.HTTP_403_FORBIDDEN
                )

            # Determine new status: if client provided a body validate it,
            # otherwise assume Completed for the uploaded object.
            if request.data:
                serializer = DocumentStatusUpdateSerializer(data=request.data)
                if not serializer.is_valid():
                    return Response(
                        {'error': 'Invalid request data', 'details': serializer.errors},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                # Update document status in MongoDB
                data = serializer.validated_data
                new_status = data.get('upload_status')
            else:
                # No body provided by client; treat as successful upload completion
                new_status = 'Completed'

            success = order_requests_service.update_document_status_in_order(
                order_req_id,
                s3_key,
                new_status
            )

            if not success:
                logger.error(f"Failed to update document status in MongoDB: {s3_key}")
                return Response(
                    {'error': 'Failed to update document status in database'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            # Return updated document metadata from S3
            response_data = {
                's3_key': s3_key,
                'file_name': s3_metadata.get('metadata', {}).get('file_name', s3_key.split('/')[-1]),
                'content_type': s3_metadata.get('content_type', ''),
                'file_size': s3_metadata.get('content_length'),
                'checksum': s3_metadata.get('etag'),
                'user_email': s3_metadata.get('metadata', {}).get('user_email', ''),
                'order_req_id': order_req_id,
                'upload_status': new_status,
                'updated_at': s3_metadata.get('last_modified').isoformat() if s3_metadata.get('last_modified') else None
            }

            logger.info(f"Successfully updated document status: {s3_key} -> {new_status}")
            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Failed to update document status: {e}")
            return Response(
                {'error': 'Failed to update document status'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AssignDocumentToOrderView(APIView):
    """
    Move document from user_email folder to order_req_id folder
    Users with upload access can assign their own documents to orders
    Admins can assign any documents

    POST /api/v1/assign-to-order/
    """
    authentication_classes = [KeycloakAuthentication]
    permission_classes = [IsAuthenticated, UploadAccess]

    def post(self, request):
        try:
            from s3_service.service import s3_service
            from .dbHandling.order_requests_service import order_requests_service

            # Validate request data
            serializer = AssignDocumentToOrderSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(
                    {'error': 'Invalid request data', 'details': serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST
                )

            data = serializer.validated_data
            s3_key = data['s3_key']
            order_req_id = data['order_req_id']
            user_email = data['user_email']

            # Check if user can assign this document
            current_user_email = keycloak_service.get_user_email_from_request(request)
            user_roles = keycloak_service.get_user_roles_from_request(request)
            is_admin = any(role in user_roles for role in ['DOC_UPLALL', 'DOC_VIEWALL'])

            # Non-admin users can only assign their own documents
            if not is_admin and user_email != current_user_email:
                return Response(
                    {'error': 'You can only assign your own documents to orders'},
                    status=status.HTTP_403_FORBIDDEN
                )

            logger.info(f"Assigning document to order: {s3_key} -> {order_req_id}")

            # Verify document exists in S3
            current_metadata = s3_service.get_object_metadata(s3_key)
            if not current_metadata:
                return Response(
                    {'error': 'Document not found in S3', 's3_key': s3_key},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Move document in S3 and update metadata
            new_s3_key = s3_service.move_document_to_order(s3_key, order_req_id, user_email)
            if not new_s3_key:
                return Response(
                    {'error': 'Failed to move document - document may not be in user folder'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Get updated metadata
            updated_metadata = s3_service.get_object_metadata(new_s3_key)
            if not updated_metadata:
                logger.error(f"Failed to retrieve metadata after move: {new_s3_key}")
                return Response(
                    {'error': 'Document moved but failed to retrieve updated metadata'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            # Create DocumentObject for MongoDB
            document_object = DocumentObject(
                s3_key=new_s3_key,
                file_name=updated_metadata.get('metadata', {}).get('file_name', new_s3_key.split('/')[-1]),
                content_type=updated_metadata.get('content_type', ''),
                file_size=updated_metadata.get('content_length'),
                checksum=updated_metadata.get('etag'),
                user_email=user_email,
                order_req_id=order_req_id,
                label=updated_metadata.get('metadata', {}).get('label'),
                notes=updated_metadata.get('metadata', {}).get('notes'),
                bucket_name=s3_service.bucket_name,
                sse_algorithm=updated_metadata.get('sse_algorithm', 'AES256'),
                upload_status='completed',  # Document already uploaded
                presigned_upload_url=None
            )

            # Add document to order in MongoDB
            success = order_requests_service.add_single_document_to_order(order_req_id, document_object)
            if not success:
                logger.warning(f"Failed to add document to MongoDB order: {order_req_id}")
                return Response(
                    {'error': 'Document moved in S3 but failed to update database'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            # Prepare response
            response_data = {
                'old_s3_key': s3_key,
                'new_s3_key': new_s3_key,
                'order_req_id': order_req_id,
                'user_email': user_email,
                'file_name': document_object.file_name,
                'content_type': document_object.content_type,
                'file_size': document_object.file_size,
                'message': 'Document successfully assigned to order'
            }

            logger.info(f"Successfully assigned document to order: {s3_key} -> {new_s3_key}")
            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Failed to assign document to order: {e}")
            return Response(
                {'error': 'Failed to assign document to order'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )