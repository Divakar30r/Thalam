#!/usr/bin/env python
"""
Development server startup script
Run with: python run_dev.py
"""

import os
import sys
import django
from django.core.management import execute_from_command_line
from django.conf import settings

def setup_environment():
    """Setup development environment"""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_s3_app.settings')
    
    # Add current directory to Python path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)

def run_server():
    """Run Django development server"""
    try:
        setup_environment()
        django.setup()
        
        print("Starting Django S3 Attachment API development server...")
        print(f"Debug mode: {settings.DEBUG}")
        print(f"Database: {settings.DATABASES['default']['ENGINE']}")
        
        # Run migrations first
        print("\nRunning migrations...")
        execute_from_command_line(['manage.py', 'migrate'])
        
        # Create superuser if needed (in development)
        if settings.DEBUG:
            print("\nChecking for superuser...")
            try:
                from django.contrib.auth import get_user_model
                User = get_user_model()
                if not User.objects.filter(is_superuser=True).exists():
                    print("No superuser found. Run 'python manage.py createsuperuser' to create one.")
            except Exception as e:
                print(f"Could not check superuser: {e}")
        
        # Start server
        print("\nStarting development server...")
        execute_from_command_line(['manage.py', 'runserver', '0.0.0.0:8000'])
        
    except KeyboardInterrupt:
        print("\nShutting down development server...")
    except Exception as e:
        print(f"Error starting server: {e}")
        sys.exit(1)

if __name__ == '__main__':
    run_server()