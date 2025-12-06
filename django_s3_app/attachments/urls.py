"""
URL configuration for attachments app
"""

from django.urls import path
from django.http import JsonResponse
from .views import (
    PresignedUploadView,
    PublicUrlView,
    DocumentMetadataView,
    DocumentListView,
    UpdateOrderDocumentsView,
    AssignDocumentToOrderView
)

def health_check(request):
    """Simple health check endpoint"""
    return JsonResponse({'status': 'healthy'})

app_name = 'attachments'

urlpatterns = [
    # Health check
    path('health/', health_check, name='health_check'),
    
    # Document upload and management
    path('presigned-upload/', PresignedUploadView.as_view(), name='presigned_upload'),
    path('public-url/', PublicUrlView.as_view(), name='public_url'),
    
    # Document metadata and listing
    path('metadata/<path:s3_key>/', DocumentMetadataView.as_view(), name='document_metadata'),
    path('documents/', DocumentListView.as_view(), name='document_list'),

    # Document status updates (path: converter matches slashes in S3 keys)
    path('status/<path:s3_key>/', UpdateOrderDocumentsView.as_view(), name='update_order_documents'),

    # Assign document to order (AdminAccess required)
    path('assign-to-order/', AssignDocumentToOrderView.as_view(), name='assign_document_to_order'),
]