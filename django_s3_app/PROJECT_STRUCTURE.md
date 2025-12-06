# Django S3 Document Service - Project Structure

## Overview

A Django REST API service for managing document uploads to AWS S3 with MongoDB metadata storage, Keycloak authentication, and role-based access control.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     External Services                            │
├─────────────────────────────────────────────────────────────────┤
│  Cloudflare DNS → API Gateway → ALB → NGINX → Docker (Django)  │
│  ├─ AWS S3 (Document Storage)                                   │
│  ├─ Keycloak (Authentication & Authorization)                   │
│  └─ MongoDB via FastAPI (Metadata & Order Management)           │
└─────────────────────────────────────────────────────────────────┘
```

## Technology Stack

- **Framework**: Django 5.0 + Django REST Framework
- **Authentication**: Keycloak (JWT tokens, JWKS verification)
- **Storage**: AWS S3 (with STS AssumeRole for temporary credentials)
- **Database**: MongoDB (via external FastAPI service)
- **Server**: Gunicorn + NGINX
- **Deployment**: Docker + Docker Compose

## Project Structure

```
django_s3_app/
│
├── django_s3_app/                  # Main Django project
│   ├── __init__.py
│   ├── settings.py                 # Django settings (CORS, API prefix, AWS, Keycloak)
│   ├── urls.py                     # Root URL configuration (API_PREFIX configurable)
│   ├── wsgi.py                     # WSGI entry point
│   └── asgi.py                     # ASGI entry point
│
├── attachments/                    # Main application module
│   ├── __init__.py
│   ├── apps.py
│   ├── models.py                   # DocumentMetadata (plain Python class, no DB)
│   ├── views.py                    # REST API views
│   │   ├── PresignedUploadView     # Generate presigned upload URLs
│   │   ├── PublicUrlView           # Generate public download URLs
│   │   ├── DocumentMetadataView    # Get document metadata from S3
│   │   ├── DocumentListView        # List user documents (S3 or MongoDB)
│   │   ├── UpdateOrderDocumentsView # Update document status in MongoDB
│   │   └── AssignDocumentToOrderView # Move document from user to order folder
│   ├── serializers.py              # DRF serializers for request/response validation
│   ├── urls.py                     # App URL patterns + health check endpoint
│   ├── document_handler.py         # Business logic for document operations
│   │
│   └── dbHandling/                 # MongoDB integration via FastAPI
│       ├── __init__.py
│       └── order_requests_service.py # OrderRequestsService, DocumentObject
│
├── keycloak_auth/                  # Keycloak authentication module
│   ├── __init__.py
│   ├── authentication.py           # KeycloakUser, KeycloakAuthenticationBackend
│   ├── drf_authentication.py       # KeycloakAuthentication (DRF)
│   ├── middleware.py               # KeycloakAuthenticationMiddleware
│   ├── permissions.py              # Role-based permissions
│   │   ├── UploadAccess            # DOC_UPL, DOC_UPLALL
│   │   ├── ViewAccess              # DOC_VIEW, DOC_VIEWALL
│   │   ├── AdminAccess             # DOC_UPLALL, DOC_VIEWALL
│   │   ├── InterestedRolesAccess   # Order interested roles + ownership
│   │   ├── DocumentOwnerPermission # Document ownership checks
│   │   └── OwnerOrAdminPermission  # Owner or admin access
│   ├── service.py                  # KeycloakService (token verification, user info)
│   └── session_auth.py             # Session token extraction (Bearer + cookies)
│
├── s3_service/                     # AWS S3 service module
│   ├── __init__.py
│   └── service.py                  # S3Service
│       ├── STS AssumeRole for temporary credentials
│       ├── Automatic credential refresh (4-hour sessions)
│       ├── Presigned upload/download URL generation
│       ├── Object metadata operations
│       ├── S3 key generation with sanitization
│       └── Document move operations (user folder ↔ order folder)
│
├── logs/                           # Application logs
│   └── django_s3_app.log          # Main log file
│
├── staticfiles/                    # Collected static files (for production)
├── media/                          # Media uploads (if needed)
│
├── venv/                           # Virtual environment
│
├── .env                            # Environment variables (secrets, config)
├── .env.example                    # Example environment file
├── .dockerignore                   # Docker ignore patterns
├── .gitignore                      # Git ignore patterns
│
├── Dockerfile                      # Multi-stage Docker build
├── docker-compose.yml              # Docker Compose configuration
├── nginx.conf                      # NGINX reverse proxy configuration
│
├── requirements.txt                # Python dependencies
├── manage.py                       # Django management script
│
├── DOCKER_DEPLOYMENT.md            # Docker deployment guide
├── PROJECT_STRUCTURE.md            # This file
└── README.md                       # Project README

```

## Core Components

### 1. Authentication & Authorization

#### Keycloak Integration (`keycloak_auth/`)

**Authentication Flow:**
```
Client Request → KeycloakAuthentication
    ├─ Extract token from Authorization header (Bearer token)
    ├─ OR Extract from access_token cookie
    ├─ OR Extract from refresh_token and exchange
    └─ Verify JWT token via JWKS (local verification)
        └─ Fetch user info and roles from Keycloak
            └─ Return KeycloakUser object
```

**Key Components:**
- `session_auth.py`: Handles both Bearer tokens (backend) and session cookies (frontend)
- `service.py`: Token verification, user info retrieval, role management
- `permissions.py`: Role-based access control classes

**User Roles:**
- `DOC_UPL`: Upload documents
- `DOC_UPLALL`: Upload any documents (admin)
- `DOC_VIEW`: View own documents
- `DOC_VIEWALL`: View all documents (admin)
- `BUY`, `SEL`, `ADM`: Order management roles

### 2. Document Storage (`s3_service/`)

**S3 Service Features:**
- **STS AssumeRole Pattern**: IAM user assumes role for temporary credentials
- **Auto-refresh**: Credentials refreshed automatically before expiry
- **Presigned URLs**: Upload (1 hour), Download (24 hours)
- **Server-side Encryption**: AES256 (default)
- **Folder Structure**:
  ```
  bucket/
  ├── {order_req_id}/           # Order-specific documents
  │   └── filename_timestamp_uuid.ext
  └── {sanitized_email}/         # User-specific documents (before assignment)
      └── filename_timestamp_uuid.ext
  ```

**S3 Metadata:**
- `file_name`: Original filename
- `user_email`: Uploader email
- `order_req_id`: Associated order (if assigned)
- `label`: Document label/type
- `notes`: Additional notes

### 3. MongoDB Integration (`attachments/dbHandling/`)

**External FastAPI Service:**
- Base URL: `FASTAPI_APP_BASE_URL`
- Endpoints:
  - `GET /api/v1/order-req/{order_req_id}` - Get order request
  - `POST /api/v1/order-req/{order_req_id}/Doc` - Add document to order
  - `PUT /api/v1/order-req/{order_req_id}/Doc/{s3_key}` - Update document status

**DocumentObject Structure:**
```python
{
    's3_key': str,
    'file_name': str,
    'content_type': str,
    'file_size': int,
    'checksum': str,
    'user_email': str,
    'order_req_id': str,
    'label': str,
    'notes': str,
    'bucket_name': str,
    'sse_algorithm': str,
    'upload_status': str,  # Awaiting, uploading, Completed, failed
    'presigned_upload_url': str,
    'created_at': str,
    'updated_at': str,
    'uploaded_at': str
}
```

### 4. API Endpoints

**Base URL:** `http://localhost:8000/{API_PREFIX}` (default: `api/v1/`)

#### Health Check
```
GET /health/
Response: {"status": "healthy"}
```

#### Document Upload
```
POST /presigned-upload/
Authentication: Required (DOC_UPL or DOC_UPLALL)
Permissions: UploadAccess, InterestedRolesAccess

Request Body:
{
    "file_name": "document.pdf",
    "content_type": "application/pdf",
    "file_size": 1024000,
    "order_req_id": "SB1029435",  // Optional
    "user_email": "user@example.com",  // Optional, defaults to authenticated user
    "label": "Invoice",  // Optional
    "notes": "Q4 invoice",  // Optional
    "checksum": "abc123"  // Optional
}

Response:
{
    "presigned_url": "https://s3.amazonaws.com/...",
    "s3_key": "SB1029435/document_20251112_123456_abc123.pdf",
    "file_name": "document.pdf",
    "upload_fields": {...},
    "upload_expiry": "2025-11-12T13:00:00Z"
}
```

#### Generate Public URL
```
POST /public-url/
Authentication: Required (DOC_VIEW or DOC_VIEWALL)
Permissions: ViewAccess, InterestedRolesAccess

Request Body:
{
    "s3_key": "SB1029435/document.pdf",
    "expiry_seconds": 3600  // Optional, default 86400 (24h)
}

Response:
{
    "public_url": "https://s3.amazonaws.com/...?signature=..."
}
```

#### Get Document Metadata
```
GET /metadata/{s3_key}/
Authentication: Required (DOC_VIEW or DOC_VIEWALL)
Permissions: ViewAccess, InterestedRolesAccess

Example: GET /metadata/SB1029435/document.pdf/

Response:
{
    "s3_key": "SB1029435/document.pdf",
    "file_name": "document.pdf",
    "content_type": "application/pdf",
    "file_size": 1024000,
    "user_email": "user@example.com",
    "order_req_id": "SB1029435",
    "label": "Invoice",
    "upload_status": "Completed",
    "created_at": "2025-11-12T12:00:00Z"
}
```

#### List Documents
```
GET /documents/?userEmail={email}&orderReqId={id}
Authentication: Required (DOC_VIEW or DOC_VIEWALL)
Permissions: ViewAccess, InterestedRolesAccess

Query Parameters:
- userEmail: Filter by user email (optional, defaults to current user)
- orderReqId: Filter by order request ID (optional)
- limit: Page size (default 50)
- offset: Pagination offset (default 0)

Behavior:
- With orderReqId: Lists documents from MongoDB for that order
- Without orderReqId: Lists documents from S3 under user's folder
- Non-admin users can only view their own documents

Response:
{
    "documents": [...],
    "totalCount": 10,
    "limit": 50,
    "offset": 0
}
```

#### Update Document Status
```
PUT /status/{s3_key}/
Authentication: Required (DOC_UPLALL or DOC_VIEWALL)
Permissions: AdminAccess

Request Body:
{
    "upload_status": "Completed",  // Awaiting, uploading, Completed, failed
    "label": "Updated Label",  // Optional
    "notes": "Updated notes"  // Optional
}

Response:
{
    "message": "Document status updated successfully",
    "s3_key": "SB1029435/document.pdf",
    "upload_status": "Completed"
}
```

#### Assign Document to Order
```
POST /assign-to-order/
Authentication: Required (DOC_UPL or DOC_UPLALL)
Permissions: UploadAccess

Request Body:
{
    "s3_key": "user@example.com/document.pdf",
    "order_req_id": "SB1029435",
    "user_email": "user@example.com"
}

Behavior:
- Moves document from user_email folder to order_req_id folder in S3
- Updates S3 metadata with order_req_id
- Adds document to MongoDB order via FastAPI
- Non-admin users can only assign their own documents

Response:
{
    "old_s3_key": "user@example.com/document.pdf",
    "new_s3_key": "SB1029435/document.pdf",
    "order_req_id": "SB1029435",
    "user_email": "user@example.com",
    "file_name": "document.pdf",
    "message": "Document successfully assigned to order"
}
```

## Configuration

### Environment Variables (.env)

#### API Configuration
```env
API_PREFIX=api/v1/                    # Configurable API prefix
DEBUG=False
SECRET_KEY=your-secret-key
ALLOWED_HOSTS=localhost,your-domain.com
```

#### AWS S3 Configuration
```env
# IAM User credentials (to assume role)
AWS_ACCESS_KEY_ID=AKIAXXXXXXXXXXXXX
AWS_SECRET_ACCESS_KEY=xxxxxxxxxx

# IAM Role to assume
AWS_ROLE_ARN=arn:aws:iam::account:role/S3ServiceRole
AWS_ROLE_SESSION_NAME=s3-service-session
AWS_ROLE_SESSION_DURATION=14400       # 4 hours

# S3 Bucket
AWS_S3_BUCKET_NAME=your-bucket
AWS_S3_REGION_NAME=us-east-1
AWS_S3_SSE_ALGORITHM=AES256
AWS_S3_PRESIGNED_URL_EXPIRY=3600      # 1 hour
AWS_S3_PUBLIC_URL_EXPIRY=86400        # 24 hours
AWS_S3_VERIFY_ON_INIT=False           # Verify S3 access on startup
```

#### Keycloak Configuration
```env
KEYCLOAK_SERVER_URL=https://keycloak.example.com
KEYCLOAK_REALM=OrderMgmt
KEYCLOAK_CLIENT_ID=DivRealmAdministrator
KEYCLOAK_CLIENT_SECRET=your-client-secret
KEYCLOAK_JWKS_URI=https://keycloak.example.com/realms/OrderMgmt/protocol/openid-connect/certs
KEYCLOAK_ISSUER=https://keycloak.example.com/realms/OrderMgmt
KEYCLOAK_AUDIENCE=account
KEYCLOAK_SERVICE_ACCOUNT_EMAIL=service@example.com
```

#### MongoDB Integration
```env
FASTAPI_APP_BASE_URL=http://fastapi-app:8080
```

#### CORS Configuration
```env
CORS_ALLOWED_ORIGINS=http://localhost:3000,https://frontend.example.com
```

## Security Features

### 1. Authentication
- JWT token verification via JWKS
- Support for Bearer tokens and session cookies
- Service account support for backend operations
- Token caching with automatic refresh

### 2. Authorization
- Role-based access control (RBAC)
- Order interested roles validation
- Document ownership checks
- Admin override capabilities

### 3. AWS Security
- STS AssumeRole pattern (temporary credentials)
- Automatic credential rotation (4-hour sessions)
- Server-side encryption (AES256)
- Presigned URLs with expiration
- IAM role with least-privilege permissions

### 4. API Security
- CORS configuration
- CSRF protection
- Request validation via serializers
- Permission checks on all endpoints
- Non-root container user

## Data Flow Examples

### Upload Flow
```
1. Client → POST /presigned-upload/
   ├─ Keycloak authentication (UploadAccess)
   ├─ Permission check (InterestedRolesAccess)
   └─ Generate S3 key: {order_req_id}/{filename}_{timestamp}_{uuid}.ext

2. DocumentHandler.create_presigned_upload_url()
   ├─ S3Service.generate_presigned_upload_url()
   │   ├─ Refresh STS credentials if needed
   │   └─ Generate presigned POST URL (1 hour expiry)
   └─ If order_req_id provided:
       └─ OrderRequestsService.add_single_document_to_order()
           └─ POST to FastAPI MongoDB service

3. Response → Presigned URL + metadata
   └─ Client uploads directly to S3 using presigned URL
```

### Download Flow
```
1. Client → POST /public-url/ with s3_key

2. DocumentHandler.generate_public_url()
   ├─ Verify document exists in S3
   └─ Generate presigned GET URL (24 hours expiry)

3. Response → Public download URL
   └─ Client downloads directly from S3
```

### Assignment Flow
```
1. Client → POST /assign-to-order/
   ├─ s3_key: "user@example.com/doc.pdf"
   ├─ order_req_id: "SB1029435"
   └─ user_email: "user@example.com"

2. S3Service.move_document_to_order()
   ├─ Copy: user@example.com/doc.pdf → SB1029435/doc.pdf
   ├─ Update S3 metadata (add order_req_id)
   └─ Delete original

3. OrderRequestsService.add_single_document_to_order()
   └─ POST to FastAPI MongoDB service

4. Response → old_s3_key, new_s3_key, success message
```

## Deployment

### Docker
```bash
# Build and run
docker-compose up -d

# View logs
docker-compose logs -f

# Health check
curl http://localhost:8000/api/v1/health/
```

### AWS EC2 with ALB
```
Cloudflare DNS
    ↓
API Gateway (optional)
    ↓
Application Load Balancer
    ↓ (Target Group)
EC2 Instance
    ↓
NGINX (port 80/443)
    ↓
Docker Container (Django on port 8000)
```

**ALB Health Check:**
- Path: `/api/v1/health/`
- Expected: 200 OK with `{"status": "healthy"}`

## Monitoring & Logging

### Logs
- **Application**: `logs/django_s3_app.log`
- **Access**: Gunicorn access logs (stdout)
- **Errors**: Gunicorn error logs (stderr)
- **Container**: `docker-compose logs`

### Health Checks
- **Application**: `GET /api/v1/health/`
- **Docker**: Built-in healthcheck (30s interval)
- **ALB**: Target group health check

### Metrics
- S3 operations (CloudWatch)
- Keycloak authentication (Keycloak metrics)
- MongoDB operations (via FastAPI service)
- Container metrics (`docker stats`)

## Development

### Local Setup
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env
# Edit .env with your credentials

# Run development server
python manage.py runserver

# Run with Docker
docker-compose up
```

### Testing
```bash
# Run tests
pytest

# Check Django configuration
python manage.py check

# Collect static files
python manage.py collectstatic
```

## Future Enhancements

- [ ] Virus scanning integration (ClamAV)
- [ ] Document preview generation (thumbnails)
- [ ] Batch upload support
- [ ] Async processing with Celery
- [ ] Redis caching for metadata
- [ ] WebSocket notifications for upload progress
- [ ] Document versioning
- [ ] Audit logging
- [ ] Metrics dashboard (Prometheus + Grafana)

## Support & Documentation

- **Docker Deployment**: See `DOCKER_DEPLOYMENT.md`
- **API Documentation**: Available at `/api/v1/docs/` (if enabled)
- **Health Check**: `GET /api/v1/health/`

## License

[Your License Here]
