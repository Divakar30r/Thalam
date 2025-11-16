#!/bin/bash

echo "========================================"
echo " dCent CP Order Management API Setup"
echo "========================================"
echo

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed or not in PATH"
    echo "Please install Python 3.8+ and try again"
    exit 1
fi

echo "✅ Python found"
echo

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv
if [ $? -ne 0 ]; then
    echo "❌ Failed to create virtual environment"
    exit 1
fi

echo "✅ Virtual environment created"
echo

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate
if [ $? -ne 0 ]; then
    echo "❌ Failed to activate virtual environment"
    exit 1
fi

echo "✅ Virtual environment activated"
echo

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "❌ Failed to install dependencies"
    exit 1
fi

echo "✅ Dependencies installed"
echo

# Copy environment file
echo "⚙️  Setting up environment configuration..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo "✅ Environment file created (.env)"
    echo "⚠️  Please edit .env file with your MongoDB connection string"
else
    echo "ℹ️  Environment file already exists"
fi
echo

# Check MongoDB connection (optional)
echo "🔗 Checking MongoDB connection..."
python3 -c "import pymongo; print('✅ MongoDB driver available')" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "⚠️  MongoDB driver not properly installed"
fi

echo
echo "========================================"
echo " Setup Complete!"
echo "========================================"
echo
echo "🚀 To start the development server:"
echo "   python3 run.py"
echo
echo "🌱 To seed sample data:"
echo "   python3 seed_data.py"
echo
echo "📚 API Documentation will be available at:"
echo "   http://localhost:8000/docs"
echo
echo "🔍 Health check:"
echo "   http://localhost:8000/health"
echo
echo "⚠️  Make sure MongoDB is running before starting the server"
echo