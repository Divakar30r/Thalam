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
from .config import KEYCLOAK_CONFIG, GOOGLE_CLOUD_CONFIG, GOOGLE_CHAT_CONFIG, WIF_CONFIG


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
        Get ID token from Keycloak using client credentials flow
        """
        token_data = {
            'grant_type': 'client_credentials',
            'client_id': KEYCLOAK_CONFIG['client_id'],
            'client_secret': KEYCLOAK_CONFIG['client_secret'],
            'scope': 'openid'  # Request openid scope to get ID token
        }
        
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        try:
            # Check SSL verification setting
            verify_ssl = KEYCLOAK_CONFIG.get('verify_ssl', True)
            if not verify_ssl:
                import urllib3
                urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
                print("⚠️  SSL verification disabled for Keycloak connection")
            
            response = requests.post(
                KEYCLOAK_CONFIG['token_endpoint'],
                data=token_data,
                headers=headers,
                verify=verify_ssl
            )
            response.raise_for_status()
            
            token_response = response.json()
            # Try to get ID token first, fall back to access token
            self.keycloak_token = token_response.get('id_token') or token_response.get('access_token')
            
            if not self.keycloak_token:
                raise Exception(f"No ID token or access token in response: {token_response}")
            
            token_type = "ID token" if token_response.get('id_token') else "access token"
            print(f"Successfully obtained Keycloak {token_type}")
            
            # Debug: Decode and print the token payload to see the subject
            if token_response.get('id_token'):
                self._debug_token_payload(self.keycloak_token)
            
            return self.keycloak_token
            
        except requests.exceptions.RequestException as e:
            print(f"Error getting Keycloak token: {e}")
            raise
    
    def _debug_token_payload(self, token):
        """
        Debug method to decode and print JWT token payload
        """
        try:
            import base64
            import json
            
            # JWT tokens have 3 parts separated by dots: header.payload.signature
            parts = token.split('.')
            if len(parts) != 3:
                print("Invalid JWT token format")
                return
            
            # Decode the payload (second part)
            payload = parts[1]
            # Add padding if needed
            payload += '=' * (4 - len(payload) % 4)
            decoded_bytes = base64.urlsafe_b64decode(payload)
            decoded_payload = json.loads(decoded_bytes.decode('utf-8'))
            
            print("🔍 ID Token Payload:")
            print(json.dumps(decoded_payload, indent=2))
            
            # Specifically highlight the subject
            if 'sub' in decoded_payload:
                print(f"📋 Subject (sub): {decoded_payload['sub']}")
            
            if 'email' in decoded_payload:
                print(f"📧 Email: {decoded_payload['email']}")
                
        except Exception as e:
            print(f"Error decoding token: {e}")
    
    
    def setup_wif_credentials(self):
        """
        Set up Google credentials using Workload Identity Federation with service account impersonation
        Keycloak Token → STS Exchange → Federated Token → Service Account Impersonation → Google Chat Token
        """
        try:
            # Get Keycloak token first
            keycloak_token = self.get_keycloak_token()
            if not keycloak_token:
                raise Exception("Failed to get Keycloak token for WIF")
            
            print(f"Got Keycloak token: {keycloak_token[:10]}...")
            
            # Step 1: Exchange Keycloak token for federated access token via STS
            federated_token = self._exchange_token_via_sts(keycloak_token)
            if not federated_token:
                raise Exception("Failed to exchange token via STS")
            
            print("Successfully obtained federated token")
            
            # Step 2: Use federated token to impersonate service account
            service_account_token = self._impersonate_service_account(federated_token)
            if not service_account_token:
                raise Exception("Failed to impersonate service account")
            
            # Create Google credentials with the service account access token
            from google.oauth2 import credentials as oauth2_credentials
            
            self.google_credentials = oauth2_credentials.Credentials(
                token=service_account_token,
                scopes=GOOGLE_CHAT_CONFIG['scopes']
            )
            
            print("Successfully set up WIF credentials with service account impersonation")
            return self.google_credentials
            
        except Exception as e:
            print(f"Error setting up WIF credentials: {e}")
            raise
    
    def _exchange_token_via_sts(self, keycloak_token):
        """
        Exchange Keycloak token for federated access token via Security Token Service
        """
        sts_url = "https://sts.googleapis.com/v1/token"
        
        # Prepare the STS token exchange request
        sts_data = {
            'audience': WIF_CONFIG['audience'],
            'grant_type': 'urn:ietf:params:oauth:grant-type:token-exchange',
            'requested_token_type': 'urn:ietf:params:oauth:token-type:access_token',
            'scope': 'https://www.googleapis.com/auth/cloud-platform',
            'subject_token': keycloak_token,
            'subject_token_type': WIF_CONFIG['subject_token_type']  # Use config value (id_token)
        }
        
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        try:
            print("Exchanging Keycloak token via STS...")
            response = requests.post(sts_url, data=sts_data, headers=headers)
            
            print(f"STS Response Status: {response.status_code}")
            if response.status_code != 200:
                print(f"STS Error Response: {response.text}")
            
            response.raise_for_status()
            
            sts_response = response.json()
            access_token = sts_response.get('access_token')
            
            if not access_token:
                raise Exception(f"No access token in STS response: {sts_response}")
            
            print("Successfully exchanged token via STS")
            
            # Debug: Decode the federated token to see what principal Google sees
            print("🔍 Debugging federated token principal...")
            self._debug_token_payload(access_token)
            
            return access_token
            
        except requests.exceptions.RequestException as e:
            print(f"Error in STS token exchange: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"STS Response: {e.response.text}")
            raise
    
    def _impersonate_service_account(self, federated_token):
        """
        Use the federated token to impersonate the service account and get Chat API access token
        """
        impersonation_url = f"https://iamcredentials.googleapis.com/v1/projects/-/serviceAccounts/{GOOGLE_CLOUD_CONFIG['service_account_email']}:generateAccessToken"
        
        headers = {
            'Authorization': f'Bearer {federated_token}',
            'Content-Type': 'application/json'
        }
        
        impersonation_data = {
            'scope': GOOGLE_CHAT_CONFIG['scopes']
        }
        
        try:
            print(f"Impersonating service account: {GOOGLE_CLOUD_CONFIG['service_account_email']}")
            print(f"Using federated token: {federated_token[:20]}...")
            
            response = requests.post(impersonation_url, json=impersonation_data, headers=headers)
            
            print(f"Impersonation Response Status: {response.status_code}")
            if response.status_code != 200:
                print(f"Impersonation Error Response: {response.text}")
                # Try to get more detailed error information
                try:
                    error_details = response.json()
                    if 'error' in error_details and 'message' in error_details['error']:
                        print(f"📋 Detailed error: {error_details['error']['message']}")
                except:
                    pass
            
            response.raise_for_status()
            
            impersonation_response = response.json()
            access_token = impersonation_response.get('accessToken')
            
            if not access_token:
                raise Exception(f"No access token in impersonation response: {impersonation_response}")
            
            print("Successfully impersonated service account")
            return access_token
            
        except requests.exceptions.RequestException as e:
            print(f"Error in service account impersonation: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Impersonation Response: {e.response.text}")
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
        
        # Step 1: Get Keycloak token and exchange it for Google access token
        credentials = self.setup_wif_credentials()
        if not credentials:
            raise Exception("Failed to set up WIF credentials")
        
        # Step 2: Get Google access token
        access_token = self.get_google_access_token()
        if not access_token:
            raise Exception("Failed to get Google access token")
        
        print("Authentication completed successfully")
        return access_token
    
    def verify_authentication(self):
        """
        Verify that authentication is working by making a test API call
        """
        print("Attempting to obtain Google access token for verification")
        try:
            access_token = self.get_google_access_token()
            if not access_token:
                print("Failed to obtain Google access token for verification")
                return False
            
            # Test with a simple API call to verify token works
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            print("Making test API call to verify authentication...")
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