# Django S3 Attachment API

A Django REST Framework application that provides secure file upload and management capabilities using AWS S3 with Server-Side Encryption (SSE) and Keycloak authentication.

## Quick Start Guide

### 1. Install Python Dependencies

First, create a virtual environment and install the required packages:

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration Setup

Copy the example configuration file and update it with your settings:

```bash
copy config.json.example config.json
```

Edit `config.json` with your actual AWS and Keycloak credentials:

```json
{
    "AWS_ACCESS_KEY_ID": "your-aws-access-key",
    "AWS_SECRET_ACCESS_KEY": "your-aws-secret-key",
    "AWS_S3_BUCKET_NAME": "your-s3-bucket-name",
    "AWS_S3_REGION_NAME": "us-east-1",
    "KEYCLOAK_SERVER_URL": "https://your-keycloak-server.com",
    "KEYCLOAK_REALM": "your-realm",
    "KEYCLOAK_CLIENT_ID": "your-client-id",
    "KEYCLOAK_CLIENT_SECRET": "your-client-secret",
    "FASTAPI_APP_BASE_URL": "https://your-fastapi-app.com"
}
```

### 3. Database Setup

```bash
# Run database migrations
python manage.py makemigrations
python manage.py migrate

# Create superuser (optional)
python manage.py createsuperuser
```

### 4. Run the Application

```bash
# Start development server
python manage.py runserver
```

The application will be available at: http://localhost:8000

## Project Structure

```
django_s3_app/
├── manage.py                    # Django management script
├── requirements.txt             # Python dependencies
├── config.json.example         # Configuration template
├── README.md                   # This file
├── django_s3_app/             # Main Django project
│   ├── __init__.py
│   ├── settings.py            # Django settings
│   ├── urls.py               # URL routing
│   ├── wsgi.py               # WSGI configuration
│   └── config.py             # Configuration management
├── attachments/               # Document management app
│   ├── __init__.py
│   ├── apps.py               # App configuration
│   ├── models.py             # Database models
│   ├── views.py              # API views
│   ├── urls.py               # App URLs
│   ├── serializers.py        # API serializers
│   ├── admin.py              # Django admin
│   └── document_handler.py   # Business logic
├── keycloak_auth/             # Keycloak authentication
│   ├── __init__.py
│   ├── service.py            # Keycloak service
│   ├── authentication.py     # Auth backends
│   ├── drf_authentication.py # DRF auth classes
│   └── middleware.py         # Auth middleware
└── s3_service/                # AWS S3 integration
    ├── __init__.py
    └── service.py            # S3 operations
```

## Features

✅ **Presigned S3 Upload URLs** - Secure direct-to-S3 uploads with Server-Side Encryption
✅ **Keycloak Authentication** - OAuth2 integration with user/role management  
✅ **Document Metadata Management** - Complete tracking of file information
✅ **Public URL Generation** - Secure access to uploaded documents
✅ **FastPay Integration** - Automatic order updates with document metadata
✅ **Audit Trail** - Complete logging of document operations
✅ **RESTful API** - Clean, documented endpoints

## API Endpoints

- `POST /api/v1/presigned-upload/` - Generate presigned upload URL
- `POST /api/v1/public-url/` - Generate public access URL
- `POST /api/v1/upload-complete/` - Mark upload as completed
- `PUT /api/v1/update-order-documents/` - Update FastPay order
- `GET /api/v1/document-metadata/` - Get document metadata
- `GET /api/v1/order-req/{order-id}/` - Get order details

## Next Steps

1. **Install Dependencies**: Run `pip install -r requirements.txt`
2. **Configure Settings**: Update `config.json` with your credentials
3. **Setup Database**: Run migrations with `python manage.py migrate`
4. **Start Development**: Run `python manage.py runserver`

For complete documentation, see the full README in the project files.