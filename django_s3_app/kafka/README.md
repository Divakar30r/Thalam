# AWS MSK (Kafka) Configuration Guide

## AWS MSK Setup

### 1. Create MSK Cluster
```bash
# Using AWS CLI
aws kafka create-cluster \
    --cluster-name document-exceptions-cluster \
    --broker-node-group-info file://broker-info.json \
    --kafka-version "2.8.1"
```

### 2. Broker Configuration (broker-info.json)
```json
{
    "InstanceType": "kafka.t3.small",
    "ClientSubnets": [
        "subnet-12345678",
        "subnet-87654321"
    ],
    "SecurityGroups": ["sg-12345678"],
    "StorageInfo": {
        "EBSStorageInfo": {
            "VolumeSize": 100
        }
    }
}
```

### 3. Create Topic
```bash
# Connect to MSK cluster and create topic
kafka-topics.sh --create \
    --topic DocumentExceptions \
    --bootstrap-server your-msk-cluster-endpoint:9092 \
    --partitions 3 \
    --replication-factor 2
```

## Django Configuration

### Environment Variables (for production)
```bash
# MSK Cluster endpoints
export KAFKA_BOOTSTRAP_SERVERS='["b-1.your-cluster.kafka.region.amazonaws.com:9092","b-2.your-cluster.kafka.region.amazonaws.com:9092"]'

# For SASL/SCRAM authentication
export KAFKA_SECURITY_PROTOCOL='SASL_SSL'
export KAFKA_SASL_MECHANISM='SCRAM-SHA-512'
export KAFKA_SASL_USERNAME='your-username'
export KAFKA_SASL_PASSWORD='your-password'
```

### config.json (for development)
```json
{
    "KAFKA_BOOTSTRAP_SERVERS": ["localhost:9092"],
    "KAFKA_SECURITY_PROTOCOL": "",
    "KAFKA_SASL_MECHANISM": "",
    "KAFKA_SASL_USERNAME": "",
    "KAFKA_SASL_PASSWORD": ""
}
```

## Usage Examples

### 1. In Views/Services
```python
from attachments.models import OrderRequest
from attachments.document_orders_service import document_orders_service

def upload_document(request, order_req_id):
    try:
        order = OrderRequest.objects.get(order_req_id=order_req_id)
        # ... document upload logic ...
        
        # Post successful upload to document-orders API
        document_orders_service.post_single_document_order(
            order_req_id=order_req_id,
            s3_key='documents/user123/file.pdf',
            file_name='file.pdf',
            user_id=request.user.id,
            source='django_s3_app',
            access_type='upload',
            accessed_at=timezone.now().isoformat(),
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT')
        )
        
    except PermissionError as e:
        order.handle_document_access_exception(
            s3_key='documents/user123/file.pdf',
            user_id=request.user.id,
            exception_type='access_denied',
            error_message=str(e),
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT'),
            access_type='upload'
        )
        raise
```

### 2. Using Decorator
```python
from kafka.exceptions import kafka_exception_handler

@kafka_exception_handler('document_download_error')
def download_document(order_req_id, s3_key, user_id):
    # Function that might raise exceptions
    # Exceptions will be automatically sent to Kafka
    pass
```

### 3. Manual Exception Sending
```python
from kafka.exceptions import send_document_access_exception

send_document_access_exception(
    order_req_id='SB1029435',
    s3_key='documents/file.pdf',
    user_id='user123',
    exception_type='file_not_found',
    error_message='Document not found in S3',
    ip_address='192.168.1.1',
    session_id='sess_123'
)
```

## Message Format

Messages sent to 'DocumentExceptions' topic with key 'DocumentAccessLog':

```json
{
    "timestamp": "2025-10-21T10:30:00Z",
    "topic": "DocumentExceptions",
    "key": "DocumentAccessLog",
    "order_req_id": "SB1029435",
    "s3_key": "documents/user123/contract.pdf",
    "user_id": "sb.user2@drworkplace.microsoft.com",
    "exception_type": "access_denied",
    "error_message": "User does not have permission to access this document",
    "source": "django_s3_app",
    "access_type": "download",
    "ip_address": "192.168.1.100",
    "user_agent": "Mozilla/5.0...",
    "session_id": "sess_abc123def456",
    "file_name": "contract.pdf",
    "http_status_code": 403,
    "stack_trace": "Traceback...",
    "additional_context": {}
}
```

## Exception Types

Common exception types to use:
- `access_denied` - User doesn't have permission
- `file_not_found` - Document not found in S3
- `upload_failed` - File upload to S3 failed
- `download_failed` - File download from S3 failed
- `invalid_file_type` - Unsupported file type
- `file_too_large` - File exceeds size limit
- `quota_exceeded` - User/order quota exceeded
- `authentication_failed` - Invalid authentication
- `session_expired` - User session expired
- `rate_limit_exceeded` - Too many requests