"""
Authentication module for Google Chat API using Keycloak Workload Identity Federation
"""

import requests
import json
import os
from google.auth import external_account
from google.auth.transport.requests import Request
from google.oauth2 import service_account
import google.auth
from config import KEYCLOAK_CONFIG, GOOGLE_CLOUD_CONFIG, GOOGLE_CHAT_CONFIG


class KeycloakWIFAuth:
    """
    Handles authentication using Keycloak as Workload Identity Federation provider
    """
    
    def __init__(self):
        self.keycloak_token = None
        self.google_credentials = None
        self.wif_config_file = "wif-config.json"
    
    def get_keycloak_token(self):
        """
        Get access token from Keycloak using client credentials flow
        """
        token_data = {
            'grant_type': 'client_credentials',
            'client_id': KEYCLOAK_CONFIG['client_id'],
            'client_secret': KEYCLOAK_CONFIG['client_secret']
        }
        
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        try:
            response = requests.post(
                KEYCLOAK_CONFIG['token_endpoint'],
                data=token_data,
                headers=headers
            )
            response.raise_for_status()
            
            token_response = response.json()
            self.keycloak_token = token_response.get('access_token')
            
            print("Successfully obtained Keycloak token")
            return self.keycloak_token
            
        except requests.exceptions.RequestException as e:
            print(f"Error getting Keycloak token: {e}")
            raise
    
    def setup_wif_credentials(self):
        """
        Set up Google credentials using Workload Identity Federation
        """
        if not os.path.exists(self.wif_config_file):
            print(f"WIF config file {self.wif_config_file} not found. Run wif_setup.py first.")
            return None
        
        try:
            # Set environment variable for Google Application Credentials
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = self.wif_config_file
            
            # Load credentials from WIF config
            credentials = external_account.Credentials.from_file(
                self.wif_config_file,
                scopes=GOOGLE_CHAT_CONFIG['scopes']
            )
            
            # Refresh credentials to get access token
            request = Request()
            credentials.refresh(request)
            
            self.google_credentials = credentials
            print("Successfully set up WIF credentials")
            return credentials
            
        except Exception as e:
            print(f"Error setting up WIF credentials: {e}")
            raise
    
    def get_google_access_token(self):
        """
        Get Google access token using WIF
        """
        if not self.google_credentials:
            self.setup_wif_credentials()
        
        if self.google_credentials:
            # Refresh token if needed
            if not self.google_credentials.valid:
                request = Request()
                self.google_credentials.refresh(request)
            
            return self.google_credentials.token
        
        return None
    
    def authenticate(self):
        """
        Complete authentication flow
        """
        print("Starting authentication flow...")
        
        # Step 1: Get Keycloak token
        keycloak_token = self.get_keycloak_token()
        if not keycloak_token:
            raise Exception("Failed to get Keycloak token")
        
        # Step 2: Set up WIF credentials
        credentials = self.setup_wif_credentials()
        if not credentials:
            raise Exception("Failed to set up WIF credentials")
        
        # Step 3: Get Google access token
        access_token = self.get_google_access_token()
        if not access_token:
            raise Exception("Failed to get Google access token")
        
        print("Authentication completed successfully")
        return access_token
    
    def verify_authentication(self):
        """
        Verify that authentication is working by making a test API call
        """
        try:
            access_token = self.get_google_access_token()
            if not access_token:
                return False
            
            # Test with a simple API call to verify token works
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            # Make a test call to list spaces (this will require appropriate permissions)
            test_url = f"{GOOGLE_CHAT_CONFIG['api_endpoint']}/spaces"
            response = requests.get(test_url, headers=headers)
            
            if response.status_code == 200:
                print("Authentication verification successful")
                return True
            else:
                print(f"Authentication verification failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"Error verifying authentication: {e}")
            return False


def get_authenticated_headers():
    """
    Convenience function to get authenticated headers for API calls
    """
    auth = KeycloakWIFAuth()
    access_token = auth.authenticate()
    
    return {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }


if __name__ == "__main__":
    # Test authentication
    auth = KeycloakWIFAuth()
    try:
        token = auth.authenticate()
        print(f"Access token obtained: {token[:50]}...")
        
        # Verify authentication
        if auth.verify_authentication():
            print("Authentication setup is working correctly!")
        else:
            print("Authentication verification failed.")
            
    except Exception as e:
        print(f"Authentication failed: {e}")
        print("\nMake sure to:")
        print("1. Update config.py with correct values")
        print("2. Run wif_setup.py to generate WIF config")
        print("3. Set up Workload Identity Federation in Google Cloud Console")