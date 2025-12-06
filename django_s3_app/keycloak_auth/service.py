"""
Keycloak authentication service using OAuth2 client credentials flow
Retrieves user authentication, roles and permissions from Keycloak
"""
from typing import Optional, Dict, List
import logging
import requests
import jwt
from jwt import PyJWKClient, PyJWTError
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)


class KeycloakAuthService:
    """Service wrapper for Keycloak interactions (token, userinfo, admin)."""

    def __init__(self):
        # Build commonly used Keycloak endpoint URLs from settings if not explicitly set
        server = getattr(settings, 'KEYCLOAK_SERVER_URL', '').rstrip('/')
        realm = getattr(settings, 'KEYCLOAK_REALM', '')

        self.jwks_uri = getattr(settings, 'KEYCLOAK_JWKS_URI', None) or (f"{server}/realms/{realm}/protocol/openid-connect/certs" if server and realm else None)
        self.userinfo_url = getattr(settings, 'KEYCLOAK_USERINFO_URL', None) or (f"{server}/realms/{realm}/protocol/openid-connect/userinfo" if server and realm else None)
        self.admin_url = getattr(settings, 'KEYCLOAK_ADMIN_URL', None) or (f"{server}/admin/realms/{realm}" if server and realm else None)
        self.token_url = getattr(settings, 'KEYCLOAK_TOKEN_URL', None) or (f"{server}/realms/{realm}/protocol/openid-connect/token" if server and realm else None)


    def get_admin_client_access_token(self) -> Optional[str]:
        """Obtain a client credentials access token for Keycloak admin API and cache it.

        This is the recovered/rewritten implementation of the original helper.
        Returns the access token string or None on failure.
        """
        cache_key = 'keycloak_admin_client_token'
        token = cache.get(cache_key)
        if token:
            return token

        # Allow explicit override of token URL, otherwise build from server+realm
        token_url = getattr(settings, 'KEYCLOAK_TOKEN_URL', None)
        if not token_url:
            server = getattr(settings, 'KEYCLOAK_SERVER_URL', '')
            realm = getattr(settings, 'KEYCLOAK_REALM', '')
            if not server or not realm:
                logger.error('KEYCLOAK_SERVER_URL or KEYCLOAK_REALM not configured; cannot request admin token')
                return None
            token_url = f"{server.rstrip('/')}/realms/{realm}/protocol/openid-connect/token"

        client_id = getattr(settings, 'KEYCLOAK_CLIENT_ID', None)
        client_secret = getattr(settings, 'KEYCLOAK_CLIENT_SECRET', None)
        if not client_id or not client_secret:
            logger.error('Keycloak admin client credentials are not configured')
            return None

        payload = {
            'grant_type': 'client_credentials',
            'client_id': client_id,
            'client_secret': client_secret,
        }

        try:
            resp = requests.post(token_url, data=payload, headers={'Content-Type': 'application/x-www-form-urlencoded'}, timeout=getattr(settings, 'KEYCLOAK_REQUEST_TIMEOUT', 10))
            if resp.status_code != 200:
                logger.error('Failed to get client token: %s - %s', resp.status_code, resp.text)
                return None

            data = resp.json()
            access_token = data.get('access_token')
            expires_in = data.get('expires_in', 3600)
            if not access_token:
                logger.error('Token response did not include access_token')
                return None

            # Cache token for slightly less than expiry to avoid edge cases
            cache_timeout = min(max(expires_in - 60, 30), getattr(settings, 'KEYCLOAK_TOKEN_CACHE_TIMEOUT', 3600))
            cache.set(cache_key, access_token, cache_timeout)
            logger.info('Successfully obtained client access token')
            return access_token
        except requests.RequestException as e:
            logger.error('Request failed while getting client token: %s', e)
            return None

    

    def get_user_info(self, token: str) -> Optional[Dict]:
        """
        [DEPRECATED] Use get_user_info_with_roles() instead for better performance
        Validate user token and return user information using admin API
        """
        try:
            # First get user info from userinfo endpoint to get email
            headers = {'Authorization': f'Bearer {token}'}
            keycloakresp_userinfo = requests.get(
                self.userinfo_url,
                headers=headers,
                timeout=settings.KEYCLOAK_REQUEST_TIMEOUT
            )
            
            if keycloakresp_userinfo.status_code != 200:
                logger.warning(f"Token validation failed: {keycloakresp_userinfo.status_code}")
                return None
            
            keycloakresp_user_info = keycloakresp_userinfo.json()
            user_email = keycloakresp_user_info.get('email')
            
            if not user_email:
                logger.warning("No email found in user token")
                return None
            
            # Get client token for admin API
            client_token = self.get_admin_client_access_token()
            if not client_token:
                logger.error("Failed to get client access token")
                return None
            
            # Get user details by email using admin API
            admin_headers = {'Authorization': f'Bearer {client_token}'}
            users_url = f"{self.admin_url}/users?email={user_email}"
            
            keycloakresp_users = requests.get(
                users_url,
                headers=admin_headers,
                timeout=settings.KEYCLOAK_REQUEST_TIMEOUT
            )
            
            if keycloakresp_users.status_code == 200:
                keycloakresp_users_data = keycloakresp_users.json()
                if keycloakresp_users_data and len(keycloakresp_users_data) > 0:
                    # Get the first user (should be unique by email)
                    keycloakresp_user_detail = keycloakresp_users_data[0]
                    # Add internal user ID to the user info
                    keycloakresp_user_info['internal_user_id'] = keycloakresp_user_detail.get('id')
                    logger.info(f"Token validated for user: {keycloakresp_user_info.get('preferred_username')}")
                    return keycloakresp_user_info
                else:
                    logger.warning(f"No user found with email: {user_email}")
                    return None
            else:
                logger.error(f"Failed to get user by email: {keycloakresp_users.status_code} - {keycloakresp_users.text}")
                return None
                
        except requests.RequestException as e:
            logger.error(f"Request failed while validating token: {e}")
            return None
        
    def get_user_roles_via_admin(self, user_internal_id: str) -> List[str]:
        
        admin_client_token = self.get_admin_client_access_token()
        if not admin_client_token:
            return []
            
        try:
            headers = {'Authorization': f'Bearer {admin_client_token}'}
            
            # Get role mappings using internal user ID
            role_mappings_url = f"{self.admin_url}/users/{user_internal_id}/role-mappings"
            keycloakresp_roles = requests.get(role_mappings_url, headers=headers, timeout=settings.KEYCLOAK_REQUEST_TIMEOUT)
            
            app_roles = []
            if keycloakresp_roles.status_code == 200:
                keycloakresp_role_data = keycloakresp_roles.json()
                
                # Extract client roles from clientMappings
                keycloakresp_client_mappings = keycloakresp_role_data.get('clientMappings', {})
                
                # Look for the app client (could be configurable client name)
                for client_name, keycloakresp_client_info in keycloakresp_client_mappings.items():
                    if client_name == 'ORDMGMT':
                        keycloakresp_mappings = keycloakresp_client_info.get('mappings', [])
                        for keycloakresp_mapping in keycloakresp_mappings:
                            role_name = keycloakresp_mapping.get('name')
                            if role_name:
                                app_roles.append(role_name)
                
                logger.info(f"Retrieved {len(app_roles)} client roles for user {user_internal_id}: {app_roles}")
            else:
                logger.warning(f"Failed to get user roles: {keycloakresp_roles.status_code} - {keycloakresp_roles.text}")
            
            return app_roles
            
        except requests.RequestException as e:
            logger.error(f"Request failed while getting user roles: {e}")
            return []

    def _decode_jwt_unverified(self, token: str) -> dict:
        """Decode JWT without signature verification, return claims or empty dict on failure."""
        if not token:
            return {}
        try:
            return jwt.decode(token, options={"verify_signature": False})
        except PyJWTError as e:
            logger.warning("Failed to decode JWT token: %s", e)
            return {}

    def verify_token(self, token: str) -> bool:
        """Verify token signature, issuer and audience using JWKS. Returns payload or None on failure.

        This verification is performed only if KEYCLOAK_JWKS_URI and KEYCLOAK_ISSUER are configured.
        """
        jwks_uri = settings.KEYCLOAK_JWKS_URI
        issuer = settings.KEYCLOAK_ISSUER
        audience = settings.KEYCLOAK_AUDIENCE or None
        if not jwks_uri or not issuer:
            # verification not configured -> treat as unverified and return False (or True if you want permissive)
            return False

        jwk_client = PyJWKClient(jwks_uri)
        try:
            # Determine algorithm from token header (fallback to RS256) without logging token details
            try:
                header = jwt.get_unverified_header(token)
                alg = header.get('alg', 'RS256')
            except Exception:
                alg = 'RS256'

            signing_key = jwk_client.get_signing_key_from_jwt(token)
            jwt.decode(
                token,
                key=signing_key.key,
                algorithms=[alg],
                audience=audience,
                issuer=issuer,
            )
            return True
        except requests.RequestException:
            logger.warning("Token verification failed: unable to fetch JWKS from configured JWKS URI")
            return False
        except jwt.ExpiredSignatureError:
            logger.warning("Token verification failed: token is expired")
            return False
        except jwt.InvalidAudienceError:
            logger.warning("Token verification failed: invalid audience")
            return False
        except jwt.InvalidIssuerError:
            logger.warning("Token verification failed: invalid issuer")
            return False
        except jwt.PyJWTError:
            logger.warning("Token verification failed: signature or token format invalid")
            return False
        except Exception:
            # Generic catch-all to avoid leaking token details in logs
            logger.warning("Token verification failed: unexpected error during verification")
            return False

    def get_user_info_with_roles(self, token: str) -> Optional[Dict]:
        """
        Get complete user information including roles in a single efficient call
        Gets user info from userinfo endpoint and extracts roles from JWT token
        
        Args:
            token: JWT token string
            
        Returns:
            dict: User info with app_roles added, or None if validation fails
        """
        try:
            # Step 1: Get user info from userinfo endpoint
            headers = {'Authorization': f'Bearer {token}'}
            keycloakresp_userinfo = requests.get(
                self.userinfo_url,
                headers=headers,
                timeout=settings.KEYCLOAK_REQUEST_TIMEOUT
            )
            
            if keycloakresp_userinfo.status_code != 200:
                logger.warning(f"Token validation failed: {keycloakresp_userinfo.status_code}")
                return None
            
            keycloakresp_user_info = keycloakresp_userinfo.json()
            service_account_email = getattr(settings, 'KEYCLOAK_SERVICE_ACCOUNT_EMAIL', 'sb.docadmin@drworkplace.microsoft.com')
            if (keycloakresp_user_info.get('email') == service_account_email):
                keycloakresp_user_info['app_roles'] = ['ADM']  # Service account gets admin privileges
                keycloakresp_user_info['roles'] = ['ADM']  # Standard roles attribute
                return keycloakresp_user_info

            # Step 2: Extract roles from JWT token
            # Decode JWT token without verification (just to extract claims)
            decoded_token = self._decode_jwt_unverified(token)
            # Extract roles from JWT token structure - resource_access.ORDMGMT.roles
            resource_access = decoded_token.get('resource_access', {})
            app_roles = resource_access.get('ORDMGMT', {}).get('roles', [])
        
            # Step 3: Add roles to user info
            keycloakresp_user_info['app_roles'] = app_roles
            
            logger.info(f"Successfully retrieved user info with {len(app_roles)} roles for: {keycloakresp_user_info.get('preferred_username')}")
            return keycloakresp_user_info
        
        except requests.RequestException as e:
            logger.error(f"Request failed while getting user info with roles: {e}")
            return None
    
     
    def get_user_info_with_roles_admin(self, user_email: str) -> Optional[Dict]:
        """
        Get complete user information including roles in a single efficient call
        Combines user validation, admin API lookup, and role retrieval
        Args:
            user_email: User email address
        """
    
        try:
            # Step 1: Get basic user info from userinfo endpoint
            
            if not user_email:
                logger.warning("No email found in user token")
                return None
            
            # Step 2: Get client token for admin API
            admin_client_token = self.get_admin_client_access_token()
            if not admin_client_token:
                logger.error("Failed to get client access token")
                return None
            
            # Step 3: Get internal user ID by email
            admin_headers = {'Authorization': f'Bearer {admin_client_token}'}
            users_url = f"{self.admin_url}/users?email={user_email}"
            
            keycloakresp_users = requests.get(
                users_url,
                headers=admin_headers,
                timeout=settings.KEYCLOAK_REQUEST_TIMEOUT
            )
            
            if keycloakresp_users.status_code != 200:
                logger.error(f"Failed to get user by email: {keycloakresp_users.status_code} - {keycloakresp_users.text}")
                return None
                
            keycloakresp_users_data = keycloakresp_users.json()
            logger.info(f"Keycloak response for user info: {keycloakresp_users_data}")
            if not keycloakresp_users_data or len(keycloakresp_users_data) == 0:
                logger.warning(f"No user found with email: {user_email}")
                return None
            
            # Get internal user ID
            keycloakresp_user_detail = keycloakresp_users_data[0]
            user_internal_id = keycloakresp_user_detail.get('id')
            
            if not user_internal_id:
                logger.error("No internal user ID found")
                return None
            
            # Step 4: Get user roles using internal ID
            role_mappings_url = f"{self.admin_url}/users/{user_internal_id}/role-mappings"
            keycloakresp_roles = requests.get(
                role_mappings_url, 
                headers=admin_headers, 
                timeout=settings.KEYCLOAK_REQUEST_TIMEOUT
            )
            
            app_roles = []
            if keycloakresp_roles.status_code == 200:
                 
                keycloakresp_role_data = keycloakresp_roles.json()
                keycloakresp_client_mappings = keycloakresp_role_data.get('clientMappings', {})
                
                # Extract client roles
                for client_name, keycloakresp_client_info in keycloakresp_client_mappings.items():
                    if client_name == 'ORDMGMT':
                        keycloakresp_mappings = keycloakresp_client_info.get('mappings', [])
                        for keycloakresp_mapping in keycloakresp_mappings:
                            role_name = keycloakresp_mapping.get('name')
                            if role_name:
                                #print role_name
                                logger.info(f"Extracted role name: {role_name}")
                                app_roles.append(role_name)
            else:
                logger.warning(f"Failed to get user roles: {keycloakresp_roles.status_code} - {keycloakresp_roles.text}")
            
            # Step 5: Combine all information with standard frontend user structure
            keycloakresp_user_info = {
                'email': user_email,
                'preferred_username': keycloakresp_user_detail.get('username', user_email),
                'sub': user_internal_id,
                'internal_user_id': user_internal_id,
                'roles': app_roles,  # Standard roles attribute for frontend compatibility
                'given_name': keycloakresp_user_detail.get('firstName', ''),
                'family_name': keycloakresp_user_detail.get('lastName', ''),
                'name': f"{keycloakresp_user_detail.get('firstName', '')} {keycloakresp_user_detail.get('lastName', '')}".strip(),
                # Add resource_access structure for JWT compatibility
                'resource_access': {
                    'ORDMGMT': {
                        'roles': app_roles
                    }
                }
            }
            
            logger.info(f"Successfully retrieved user info with {len(app_roles)} roles for: {keycloakresp_user_info.get('preferred_username')}")
            return keycloakresp_user_info
            
        except requests.RequestException as e:
            logger.error(f"Request failed while getting user info with roles: {e}")
            return None
  
 
 ## PERMISSION related methods ##
    def check_user_list_permission(self, request, requested_user_email):
        """
        Utility function to check if user can list documents for another user
        
        Args:
            request: Django request object
            requested_user_email: User email being requested in the query
            
        Returns:
            bool: True if access allowed
        """
        if not hasattr(request, 'user') or not request.user.is_authenticated:
            return False
            
        current_user_email = self.get_user_email_from_request(request)
        user_roles = self.get_user_roles_from_request(request)
        
        # User can access their own documents
        if requested_user_email == current_user_email:
            return True
            
            
        return False
    
    def get_user_id_from_request(self, request):
        """
        Extract user ID from Keycloak JWT token
        
        Args:
            request: Django request object
            
        Returns:
            str: User ID from JWT 'sub' claim or None
        """
        if hasattr(request, 'user') and request.user.is_authenticated:
            # Try to get from user object first
            user_internal_id = getattr(request.user, 'id', None)
            user_id = getattr(request.user, 'email', None)
            if user_id:
                return user_id
                
            # Fallback to JWT token attributes
            if hasattr(request.user, 'get'):
                return request.user.get('sub')
                
        return None
    
    def get_user_email_from_request(self, request):
        """
        Extract user email from Keycloak JWT token
        
        Args:
            request: Django request object
            
        Returns:
            str: User email from JWT 'email' claim or None
        """
        if hasattr(request, 'user') and request.user.is_authenticated:
            # Try to get email from user object
            user_email = getattr(request.user, 'email', None)
            if user_email:
                return user_email
                
            # Fallback to JWT token attributes
            if hasattr(request.user, 'get'):
                return request.user.get('email')
                
        return None
    
    def get_user_roles_from_request(self, request):
        """
        Extract user roles from Keycloak JWT token
        
        Args:
            request: Django request object
            
        Returns:
            list: List of role names from resource_access.ORDMGMT.roles or empty list
        """
        if hasattr(request, 'user') and request.user.is_authenticated:
            # Extract from JWT token structure - resource_access.ORDMGMT.roles
            if hasattr(request.user, 'get'):
                resource_access = request.user.get('resource_access', {})
                roles = resource_access.get('ORDMGMT', {}).get('roles', [])
                return roles
                
            # Fallback to user object roles attribute if JWT structure not available
            roles = getattr(request.user, 'roles', None)
            if roles is not None:
                return roles
                
        return []

# Global service instance
keycloak_service = KeycloakAuthService()