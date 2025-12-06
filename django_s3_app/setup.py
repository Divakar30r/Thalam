#!/usr/bin/env python
"""
Quick setup script for development environment
"""

import os
import sys
import subprocess
import json

def print_header(text):
    """Print formatted header"""
    print(f"\n{'='*60}")
    print(f" {text}")
    print(f"{'='*60}")

def check_python_version():
    """Check Python version compatibility"""
    if sys.version_info < (3, 8):
        print("Error: Python 3.8 or higher is required")
        sys.exit(1)
    print(f"✓ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")

def install_dependencies():
    """Install Python dependencies"""
    print("Installing Python dependencies...")
    try:
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'], 
                      check=True, capture_output=True)
        print("✓ Dependencies installed successfully")
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to install dependencies: {e}")
        return False
    return True

def create_sample_config():
    """Create sample configuration file"""
    config_file = 'config.json.sample'
    
    sample_config = {
        "django": {
            "secret_key": "your-django-secret-key-here-change-in-production",
            "debug": True,
            "allowed_hosts": ["localhost", "127.0.0.1", "0.0.0.0"]
        },
        "database": {
            "url": "postgresql://username:password@localhost:5432/django_s3_app"
        },
        "aws_s3": {
            "access_key_id": "your-aws-access-key-id",
            "secret_access_key": "your-aws-secret-access-key",
            "region_name": "us-east-1",
            "bucket_name": "your-s3-bucket-name",
            "upload_expiry": 3600,
            "public_url_expiry": 3600,
            "sse_algorithm": "AES256"
        },
        "keycloak": {
            "server_url": "https://your-keycloak-server.com",
            "realm": "your-realm-name",
            "client_id": "your-client-id",
            "client_secret": "your-client-secret"
        },
        "fastapi_app": {
            "api_base_url": "https://fastapi-app.example.com"
        }
    }
    
    try:
        with open(config_file, 'w') as f:
            json.dump(sample_config, f, indent=2)
        print(f"✓ Created sample configuration: {config_file}")
        print(f"  Copy to config.json and update with your settings")
    except Exception as e:
        print(f"✗ Failed to create config file: {e}")

def run_migrations():
    """Run Django migrations"""
    print("Running database migrations...")
    try:
        subprocess.run([sys.executable, 'manage.py', 'migrate'], 
                      check=True, capture_output=True)
        print("✓ Database migrations completed")
    except subprocess.CalledProcessError as e:
        print(f"✗ Migration failed: {e}")
        print("  Make sure your database is configured and accessible")
        return False
    return True

def main():
    """Main setup function"""
    print_header("Django S3 Attachment API - Development Setup")
    
    # Check Python version
    check_python_version()
    
    # Install dependencies
    if not install_dependencies():
        print("Setup failed. Please install dependencies manually.")
        return
    
    # Create sample config
    create_sample_config()
    
    # Check if config exists
    if not os.path.exists('config.json'):
        print_header("Configuration Required")
        print("Please create and configure your config.json file:")
        print("1. Copy config.json.sample to config.json")
        print("2. Update all configuration values")
        print("3. Ensure your database is running")
        print("4. Run 'python setup.py' again")
        return
    
    # Run migrations
    if not run_migrations():
        print("Setup incomplete. Please check database configuration.")
        return
    
    print_header("Setup Complete!")
    print("Next steps:")
    print("1. Create a superuser: python manage.py createsuperuser")
    print("2. Start development server: python run_dev.py")
    print("3. Visit http://localhost:8000/ for API info")
    print("4. Visit http://localhost:8000/admin/ for admin interface")
    print("\nAPI Documentation:")
    print("- Presigned Upload: POST /api/v1/attachments/presigned-upload/")
    print("- Public URL: POST /api/v1/attachments/public-url/")
    print("- Document List: GET /api/v1/attachments/documents/")
    print("- Health Check: GET /health/")

if __name__ == '__main__':
    main()