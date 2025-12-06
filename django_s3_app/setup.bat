@echo off
REM Django S3 App Quick Setup Script for Windows
REM This script helps you get started with the Django S3 application

echo === Django S3 App Quick Setup ===
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8 or later from https://python.org
    pause
    exit /b 1
)

echo Python is installed.
echo.

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
    echo Virtual environment created successfully.
) else (
    echo Virtual environment already exists.
)

echo.
echo Activating virtual environment...
call venv\Scripts\activate

echo.
echo Installing Python dependencies...
pip install --upgrade pip
pip install -r requirements.txt

echo.
echo === Setup Instructions ===
echo.
echo 1. Copy config.json.example to config.json:
echo    copy config.json.example config.json
echo.
echo 2. Edit config.json with your AWS and Keycloak credentials
echo.
echo 3. Run database migration:
echo    python manage.py makemigrations
echo    python manage.py migrate
echo.
echo 4. Start the development server:
echo    python manage.py runserver
echo.
echo 5. Access the application at: http://localhost:8000
echo.
echo === Configuration Required ===
echo.
echo You need to configure the following in config.json:
echo - AWS_ACCESS_KEY_ID: Your AWS access key
echo - AWS_SECRET_ACCESS_KEY: Your AWS secret key  
echo - AWS_S3_BUCKET_NAME: Your S3 bucket name
echo - KEYCLOAK_SERVER_URL: Your Keycloak server URL
echo - KEYCLOAK_REALM: Your Keycloak realm
echo - KEYCLOAK_CLIENT_ID: Your Keycloak client ID
echo - KEYCLOAK_CLIENT_SECRET: Your Keycloak client secret
echo - FASTAPI_APP_BASE_URL: Your FastAPI app URL
echo.
echo See README.md for detailed instructions.
echo.
pause