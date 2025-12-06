"""
Middleware for Keycloak authentication
"""

from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth import login
from .authentication import KeycloakAuthenticationBackend
from .session_auth import session_token_extractor
import logging

logger = logging.getLogger(__name__)

class KeycloakAuthenticationMiddleware(MiddlewareMixin):
    """
    Middleware to handle Keycloak authentication for regular Django views
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.backend = KeycloakAuthenticationBackend()
    
    def process_request(self, request):
        """
        Process the request and authenticate user if token is present
        Supports both Bearer tokens and session cookies
        """
        # Skip authentication for certain paths
        skip_paths = ['/admin/', '/static/', '/media/']
        if any(request.path.startswith(path) for path in skip_paths):
            return None

        try:
            # Extract token from request (supports Bearer token and session cookies)
            token = session_token_extractor.extract_token_from_request(request)
            if not token:
                return None

            # Authenticate user
            user = self.backend.authenticate(request, token=token)
            if user:
                # Set user in request
                request.user = user
                logger.debug(f"Authenticated user {user.username} via middleware")

        except Exception as e:
            logger.error(f"Middleware authentication failed: {e}")

        return None