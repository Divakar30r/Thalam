"""
Django REST Framework serializers for attachment API
"""

from rest_framework import serializers

class PresignedUploadRequestSerializer(serializers.Serializer):
    """Serializer for presigned upload URL request"""

    order_req_id = serializers.CharField(max_length=255, required=False, allow_blank=True, allow_null=True)
    # Allow service/batch callers to supply user_email directly
    user_email = serializers.CharField(max_length=255, required=False, allow_blank=True)
    file_name = serializers.CharField(max_length=255)
    content_type = serializers.CharField(max_length=100)
    file_size = serializers.IntegerField(required=False, allow_null=True, min_value=1)
    label = serializers.CharField(max_length=255, required=False, allow_blank=True)
    notes = serializers.CharField(required=False, allow_blank=True)
    checksum = serializers.CharField(max_length=64, required=False, allow_blank=True)

class PresignedUploadResponseSerializer(serializers.Serializer):
    """Serializer for presigned upload URL response"""
    
    presigned_url = serializers.URLField()
    # document_id may be missing when running DB-less; accept null/absent
    document_id = serializers.IntegerField(required=False, allow_null=True)
    s3_key = serializers.CharField()
    file_name = serializers.CharField()
    content_type = serializers.CharField()
    file_size = serializers.IntegerField(required=False, allow_null=True)
    checksum = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    # user_email may be provided by the client/request; make optional to be tolerant
    user_email = serializers.CharField(required=False, allow_null=True)
    label = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    notes = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    order_req_id = serializers.CharField(required=False, allow_null=True)
    # upload_fields must be returned so clients can POST; keep required
    upload_fields = serializers.DictField()
    upload_expiry = serializers.DateTimeField(required=False, allow_null=True)
    created_at = serializers.DateTimeField(required=False, allow_null=True)

class PublicUrlRequestSerializer(serializers.Serializer):
    """Serializer for public URL generation request"""

    s3_key = serializers.CharField(max_length=500, required=True)
    expiry_seconds = serializers.IntegerField(required=False, min_value=60, max_value=604800)  # 1 minute to 1 week

class DocumentStatusUpdateSerializer(serializers.Serializer):
    """Serializer for updating document status in MongoDB"""

    upload_status = serializers.CharField(max_length=50)
    label = serializers.CharField(max_length=255, required=False, allow_blank=True)
    notes = serializers.CharField(required=False, allow_blank=True)


class AssignDocumentToOrderSerializer(serializers.Serializer):
    """Serializer for assigning document to order request"""

    s3_key = serializers.CharField(max_length=500)
    order_req_id = serializers.CharField(max_length=255)
    user_email = serializers.EmailField()