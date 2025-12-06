@echo off
REM Windows batch script to set up Google Chat Keycloak Integration

echo ========================================
echo Google Chat Keycloak Integration Setup
echo ========================================

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Please install Python 3.8+ first.
    echo Download from: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo Found Python:
python --version

REM Run the installation script
echo.
echo Running installation script...
python scripts\install.py

if errorlevel 1 (
    echo.
    echo ERROR: Installation failed. Please check the error messages above.
    pause
    exit /b 1
)

echo.
echo ========================================
echo Installation completed successfully!
echo ========================================
echo.
echo To get started:
echo   1. Activate the virtual environment: venv\Scripts\activate
echo   2. Run setup: python -m googlechat_keycloak.setup
echo   3. Test: python -m googlechat_keycloak.cli --help
echo.

pause