#!/usr/bin/env python3
"""
Installation script for Google Chat Keycloak Integration
Run this script to set up the project environment
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(command, description, allow_soft_failure=False):
    """Run a shell command and handle errors"""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✓ {description} completed")
        return True
    except subprocess.CalledProcessError as e:
        # Check for soft failures (like pip already up-to-date)
        if allow_soft_failure and e.stdout and ("already satisfied" in e.stdout.lower() or "requirement already satisfied" in e.stdout.lower()):
            print(f"⚠️ {description} - already up-to-date")
            return True
        
        print(f"❌ {description} failed: {e}")
        if e.stdout:
            print("STDOUT:", e.stdout)
        if e.stderr:
            print("STDERR:", e.stderr)
        return False

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print(f"❌ Python 3.8+ required, but you have {sys.version}")
        return False
    print(f"✓ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    return True

def setup_virtual_environment():
    """Set up Python virtual environment"""
    venv_path = Path("venv")
    
    if venv_path.exists():
        print("✓ Virtual environment already exists")
        return True
    
    return run_command("python -m venv venv", "Creating virtual environment")

def install_dependencies():
    """Install Python dependencies"""
    # Determine pip command based on OS
    if sys.platform == "win32":
        pip_cmd = r"venv\Scripts\pip"
    else:
        pip_cmd = "venv/bin/pip"
    
    # Commands with their descriptions and whether soft failures are allowed
    commands = [
        (f"{pip_cmd} install --upgrade pip", "Upgrading pip", True),  # Allow soft failure for pip upgrade
        (f"{pip_cmd} install -r requirements.txt", "Installing dependencies", False),
        (f"{pip_cmd} install -e .", "Installing package in development mode", False)
    ]
    
    for cmd, desc, allow_soft_failure in commands:
        if not run_command(cmd, desc, allow_soft_failure):
            return False
    
    return True

def main():
    """Main installation process"""
    print("🚀 Google Chat Keycloak Integration - Installation Script")
    print("=" * 60)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Setup virtual environment
    if not setup_virtual_environment():
        print("❌ Failed to set up virtual environment")
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        print("❌ Failed to install dependencies")
        sys.exit(1)
    
    print("\n🎉 Installation completed successfully!")
    print("\n📋 Next steps:")
    print("1. Activate the virtual environment:")
    if sys.platform == "win32":
        print("   venv\\Scripts\\activate")
    else:
        print("   source venv/bin/activate")
    
    print("2. Run the setup:")
    print("   python -m googlechat_keycloak.setup")
    
    print("3. Test the installation:")
    print("   python -m googlechat_keycloak.cli --help")

if __name__ == "__main__":
    main()