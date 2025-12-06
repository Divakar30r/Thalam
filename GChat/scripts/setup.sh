#!/bin/bash
# Linux/macOS setup script for Google Chat Keycloak Integration

set -e

echo "========================================"
echo "Google Chat Keycloak Integration Setup"
echo "========================================"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 not found. Please install Python 3.8+ first."
    exit 1
fi

echo "Found Python:"
python3 --version

# Run the installation script
echo ""
echo "Running installation script..."
python3 scripts/install.py

if [ $? -ne 0 ]; then
    echo ""
    echo "ERROR: Installation failed. Please check the error messages above."
    exit 1
fi

echo ""
echo "========================================"
echo "Installation completed successfully!"
echo "========================================"
echo ""
echo "To get started:"
echo "  1. Activate the virtual environment: source venv/bin/activate"
echo "  2. Run setup: python -m googlechat_keycloak.setup"
echo "  3. Test: python -m googlechat_keycloak.cli --help"
echo ""