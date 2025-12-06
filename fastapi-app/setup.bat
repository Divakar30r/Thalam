@echo off
echo ========================================
echo  dCent CP Order Management API Setup
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed or not in PATH
    echo Please install Python 3.8+ and try again
    pause
    exit /b 1
)

echo ✅ Python found
echo.

REM Create virtual environment
echo 📦 Creating virtual environment...
python -m venv venv
if errorlevel 1 (
    echo ❌ Failed to create virtual environment
    pause
    exit /b 1
)

echo ✅ Virtual environment created
echo.

REM Activate virtual environment
echo 🔄 Activating virtual environment...
call venv\Scripts\activate
if errorlevel 1 (
    echo ❌ Failed to activate virtual environment
    pause
    exit /b 1
)

echo ✅ Virtual environment activated
echo.

REM Install dependencies
echo 📥 Installing dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo ❌ Failed to install dependencies
    pause
    exit /b 1
)

echo ✅ Dependencies installed
echo.

REM Copy environment file
echo ⚙️  Setting up environment configuration...
if not exist .env (
    copy .env.example .env
    echo ✅ Environment file created (.env)
    echo ⚠️  Please edit .env file with your MongoDB connection string
) else (
    echo ℹ️  Environment file already exists
)
echo.

REM Check MongoDB connection (optional)
echo 🔗 Checking MongoDB connection...
python -c "import pymongo; print('✅ MongoDB driver available')" 2>nul
if errorlevel 1 (
    echo ⚠️  MongoDB driver not properly installed
)

echo.
echo ========================================
echo  Setup Complete!
echo ========================================
echo.
echo 🚀 To start the development server:
echo    python run.py
echo.
echo 🌱 To seed sample data:
echo    python seed_data.py
echo.
echo 📚 API Documentation will be available at:
echo    http://localhost:8000/docs
echo.
echo 🔍 Health check:
echo    http://localhost:8000/health
echo.
echo ⚠️  Make sure MongoDB is running before starting the server
echo.
pause