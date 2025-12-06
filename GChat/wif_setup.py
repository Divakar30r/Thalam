"""
Workload Identity Federation Configuration Generator
This module creates the WIF configuration file needed for authentication
"""

import json
import os
from config import KEYCLOAK_CONFIG, GOOGLE_CLOUD_CONFIG, WIF_CONFIG, GOOGLE_CHAT_CONFIG


def generate_wif_config():
    """
    Generate the Workload Identity Federation configuration file
    """
    wif_config = {
        "type": "external_account",
        "audience": WIF_CONFIG["audience"],
        "subject_token_type": WIF_CONFIG["subject_token_type"],
        "token_url": WIF_CONFIG["token_url"],
        "credential_source": {
            "url": KEYCLOAK_CONFIG["token_endpoint"],
            "headers": {
                "Content-Type": "application/x-www-form-urlencoded"
            },
            "format": {
                "type": "json",
                "subject_token_field_name": "access_token"
            },
            "request": {
                "url": KEYCLOAK_CONFIG["token_endpoint"],
                "method": "POST",
                "headers": {
                    "Content-Type": "application/x-www-form-urlencoded"
                },
                "data": f"grant_type=client_credentials&client_id={KEYCLOAK_CONFIG['client_id']}&client_secret={KEYCLOAK_CONFIG['client_secret']}"
            }
        },
        "service_account_impersonation_url": f"https://iamcredentials.googleapis.com/v1/projects/-/serviceAccounts/{GOOGLE_CLOUD_CONFIG['service_account_email']}:generateAccessToken"
    }
    
    return wif_config


def save_wif_config(filename="wif-config.json"):
    """
    Save the WIF configuration to a JSON file
    """
    config = generate_wif_config()
    
    with open(filename, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"WIF configuration saved to {filename}")
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
    
    print("Environment file (.env) created")


if __name__ == "__main__":
    # Generate WIF configuration
    save_wif_config()
    
    # Create environment file
    create_environment_file()
    
    print("\nSetup complete! Make sure to:")
    print("1. Update the placeholders in config.py with your actual values")
    print("2. Set up the Workload Identity Federation in Google Cloud Console")
    print("3. Configure the Keycloak client with appropriate settings")