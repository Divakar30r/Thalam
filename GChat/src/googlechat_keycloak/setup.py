"""
Setup utilities for Google Chat Keycloak Integration
"""

import json
import os
import sys
from pathlib import Path
from googlechat_keycloak.config import KEYCLOAK_CONFIG, GOOGLE_CLOUD_CONFIG, WIF_CONFIG, GOOGLE_CHAT_CONFIG


def generate_wif_config():
    """
    Generate a simple WIF configuration file for reference
    Note: This is now used for reference only, actual token exchange is handled in auth.py
    """
    wif_config = {
        "type": "external_account",
        "audience": WIF_CONFIG["audience"],
        "subject_token_type": WIF_CONFIG["subject_token_type"],
        "token_url": WIF_CONFIG["token_url"],
        "keycloak_endpoint": KEYCLOAK_CONFIG["token_endpoint"],
        "service_account_impersonation_url": f"https://iamcredentials.googleapis.com/v1/projects/-/serviceAccounts/{GOOGLE_CLOUD_CONFIG['service_account_email']}:generateAccessToken",
        "_note": "This config is for reference. Actual token exchange is handled programmatically in auth.py"
    }
    
    return wif_config


def save_wif_config(filename="wif-config.json"):
    """
    Save the WIF configuration to a JSON file
    """
    config = generate_wif_config()
    
    with open(filename, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"✓ WIF configuration saved to {filename}")
    return filename


def create_environment_file():
    """
    Create a .env file with environment variables
    """
    env_content = f"""# Google Application Credentials
GOOGLE_APPLICATION_CREDENTIALS=wif-config.json

# Keycloak Configuration
KEYCLOAK_SERVER_URL={KEYCLOAK_CONFIG['server_url']}
KEYCLOAK_REALM={KEYCLOAK_CONFIG['realm']}
KEYCLOAK_CLIENT_ID={KEYCLOAK_CONFIG['client_id']}
KEYCLOAK_CLIENT_SECRET={KEYCLOAK_CONFIG['client_secret']}

# Google Cloud Configuration
GOOGLE_PROJECT_NUMBER={GOOGLE_CLOUD_CONFIG['project_number']}
GOOGLE_PROJECT_ID={GOOGLE_CLOUD_CONFIG['project_id']}
GOOGLE_SERVICE_ACCOUNT_EMAIL={GOOGLE_CLOUD_CONFIG['service_account_email']}

# Google Chat Configuration
GOOGLE_CHAT_USER_EMAIL={GOOGLE_CHAT_CONFIG['user_email']}
"""
    
    with open('.env', 'w') as f:
        f.write(env_content)
    
    print("✓ Environment file (.env) created")


def verify_configuration():
    """
    Verify that all required configuration values are set
    """
    print("🔍 Verifying configuration...")
    
    issues = []
    
    # Check Keycloak config
    if not KEYCLOAK_CONFIG.get('server_url') or 'localhost:9090' in KEYCLOAK_CONFIG.get('server_url', ''):
        if 'localhost:9090' in KEYCLOAK_CONFIG.get('server_url', ''):
            print("⚠️  Using localhost Keycloak server - make sure it's running")
    
    if not KEYCLOAK_CONFIG.get('client_secret') or 'YOUR_' in KEYCLOAK_CONFIG.get('client_secret', ''):
        issues.append("Keycloak client secret not set")
    
    # Check Google Cloud config
    if not GOOGLE_CLOUD_CONFIG.get('project_number') or 'YOUR_' in str(GOOGLE_CLOUD_CONFIG.get('project_number', '')):
        issues.append("Google Cloud project number not set")
    
    if not GOOGLE_CLOUD_CONFIG.get('project_id') or 'YOUR_' in GOOGLE_CLOUD_CONFIG.get('project_id', ''):
        issues.append("Google Cloud project ID not set")
    
    if not GOOGLE_CLOUD_CONFIG.get('service_account_email') or 'YOUR_' in GOOGLE_CLOUD_CONFIG.get('service_account_email', ''):
        issues.append("Service account email not set")
    
    if issues:
        print("❌ Configuration issues found:")
        for issue in issues:
            print(f"   - {issue}")
        return False
    else:
        print("✓ Configuration looks good!")
        return True


def check_prerequisites():
    """
    Check that all prerequisites are met
    """
    print("🔍 Checking prerequisites...")
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ required")
        return False
    
    print(f"✓ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    
    # Check required modules
    required_modules = ['requests', 'google.auth', 'google.oauth2']
    missing_modules = []
    
    for module in required_modules:
        try:
            __import__(module)
            print(f"✓ {module} available")
        except ImportError:
            missing_modules.append(module)
            print(f"❌ {module} not available")
    
    if missing_modules:
        print("\n📦 Install missing dependencies:")
        print("   pip install -r requirements.txt")
        return False
    
    return True


def setup_main():
    """
    Main setup function
    """
    print("🚀 Google Chat Keycloak Integration Setup")
    print("=" * 50)
    
    # Check prerequisites
    if not check_prerequisites():
        print("\n❌ Prerequisites not met. Please install required dependencies.")
        return False
    
    # Verify configuration
    if not verify_configuration():
        print("\n❌ Configuration incomplete. Please update config.py")
        return False
    
    # Generate WIF configuration
    try:
        save_wif_config()
    except Exception as e:
        print(f"❌ Failed to generate WIF config: {e}")
        return False
    
    # Create environment file
    try:
        create_environment_file()
    except Exception as e:
        print(f"❌ Failed to create environment file: {e}")
        return False
    
    print("\n🎉 Setup completed successfully!")
    print("\n📋 Next steps:")
    print("1. Ensure Keycloak is running and accessible")
    print("2. Verify Google Cloud Workload Identity Federation is configured")
    print("3. Test authentication: python -m googlechat_keycloak.auth")
    print("4. Run example: python -m googlechat_keycloak.cli demo")
    
    return True


if __name__ == "__main__":
    setup_main()