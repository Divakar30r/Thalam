"""
Django REST Framework authentication class for Keycloak
"""

from keycloak_auth.authentication import KeycloakUser
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from django.contrib.auth import get_user_model
from .service import keycloak_service
import logging

logger = logging.getLogger(__name__)

User = get_user_model()

class KeycloakAuthentication(BaseAuthentication):
    """
    REST Framework authentication class for Keycloak tokens
    """
    
    def authenticate(self, request):
        """
        Authenticate the request using Keycloak token
        Returns a two-tuple of (user, token) if authentication succeeds,
        or None if authentication is not attempted.
        """
        # Get token from Authorization header
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        if not auth_header:
            return None
        
        try:
            # Extract token from "Bearer <token>" format
            auth_parts = auth_header.split(' ')
            if len(auth_parts) != 2 or auth_parts[0].lower() != 'bearer':
                return None
            
            token = auth_parts[1]
            
            # Prefer local verification (JWKS) if configured
            verified = keycloak_service.verify_token(token)
            if not verified:
                logger.warning("Token verification failed or not accepted")
                raise AuthenticationFailed('Invalid or expired token')

            # Verification succeeded; fetch richer user info from Keycloak
            user_info = keycloak_service.get_user_info_with_roles(token)
            if not user_info:
                logger.warning("Token verified but failed to retrieve user info from Keycloak")
                raise AuthenticationFailed('Failed to retrieve user details')

            return (KeycloakUser(user_info, user_info.get('app_roles', [])), token)
            """ 
            # Validate token with Keycloak
            user_info = keycloak_service.get_user_info(token)
            if not user_info:
                raise AuthenticationFailed('Invalid or expired token')
            
            # Get user roles
            user_internal_id = user_info.get('sub')
            if user_internal_id:
                roles = keycloak_service.get_user_roles_via_admin(user_internal_id)
            else:
                roles = []
            
            # Create Keycloak user object
            from .authentication import KeycloakUser
            user = KeycloakUser(user_info, roles)
            
            logger.info(f"Successfully authenticated user: {user.username}")
            return (user, token)
             """
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            raise AuthenticationFailed('Authentication failed')
    
    def authenticate_header(self, request):
        """
        Return a string to be used as the value of the `WWW-Authenticate`
        header in a `401 Unauthenticated` response.
        """
        return 'Bearer realm="keycloak"'