"""
Session-based authentication handler for Keycloak
Converts AUTH_SESSION cookie to Bearer token format
"""

import logging
import requests
from django.conf import settings
from typing import Optional

logger = logging.getLogger(__name__)


class SessionTokenExtractor:
    """
    Extracts and converts Keycloak session cookies to access tokens
    Supports both frontend (AUTH_SESSION cookie) and backend (Bearer token) authentication
    """

    def __init__(self):
        self.keycloak_server_url = getattr(settings, 'KEYCLOAK_SERVER_URL', '')
        self.keycloak_realm = getattr(settings, 'KEYCLOAK_REALM', '')
        self.keycloak_client_id = getattr(settings, 'KEYCLOAK_CLIENT_ID', '')
        self.keycloak_client_secret = getattr(settings, 'KEYCLOAK_CLIENT_SECRET', '')

    def extract_token_from_request(self, request) -> Optional[str]:
        """
        Extract access token from request
        Supports both Bearer token (backend) and session cookies (frontend)

        Args:
            request: Django/DRF request object

        Returns:
            Access token string or None
        """
        # Priority 1: Check Authorization header (backend/server-to-server)
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        if auth_header:
            token = self._extract_bearer_token(auth_header)
            if token:
                logger.debug("Token extracted from Authorization header")
                return token

        # Priority 2: Check for access_token in cookies (frontend)
        access_token = request.COOKIES.get('access_token')
        if access_token:
            logger.debug("Token extracted from access_token cookie")
            return access_token

        # Priority 3: Try to extract from AUTH_SESSION cookie (Keycloak session)
        auth_session = request.COOKIES.get('AUTH_SESSION_ID')
        if auth_session:
            logger.debug("Found AUTH_SESSION_ID cookie, attempting token exchange")
            return self._exchange_session_for_token(auth_session, request)

        # Priority 4: Check for KEYCLOAK_SESSION cookie
        keycloak_session = request.COOKIES.get('KEYCLOAK_SESSION')
        if keycloak_session:
            logger.debug("Found KEYCLOAK_SESSION cookie, attempting token exchange")
            return self._exchange_session_for_token(keycloak_session, request)

        logger.debug("No authentication token or session found in request")
        return None

    def _extract_bearer_token(self, auth_header: str) -> Optional[str]:
        """
        Extract token from Bearer authorization header

        Args:
            auth_header: Authorization header value

        Returns:
            Token string or None
        """
        try:
            auth_parts = auth_header.split(' ')
            if len(auth_parts) == 2 and auth_parts[0].lower() == 'bearer':
                return auth_parts[1]
        except Exception as e:
            logger.error(f"Failed to extract bearer token: {e}")
        return None

    def _exchange_session_for_token(self, session_id: str, request) -> Optional[str]:
        """
        Exchange Keycloak session cookie for access token

        Note: This is a placeholder implementation. The actual implementation
        depends on your Keycloak setup and whether you're using:
        1. Direct Keycloak session introspection
        2. A custom backend endpoint that has the session token
        3. Token refresh flow

        Args:
            session_id: Keycloak session ID
            request: Django request object (may contain other cookies)

        Returns:
            Access token string or None
        """
        logger.warning(
            "Session-to-token exchange not fully implemented. "
            "AUTH_SESSION_ID found but cannot be directly converted to access token. "
            "Consider storing access token in a separate cookie or using refresh token flow."
        )

        # Implementation options:
        # Option 1: If you have refresh token in a separate cookie
        refresh_token = request.COOKIES.get('refresh_token')
        if refresh_token:
            return self._refresh_access_token(refresh_token)

        # Option 2: Call a backend endpoint that has access to the session
        # return self._call_backend_session_endpoint(session_id)

        # Option 3: Return None and require frontend to send access_token explicitly
        return None

    def _refresh_access_token(self, refresh_token: str) -> Optional[str]:
        """
        Use refresh token to get new access token

        Args:
            refresh_token: Keycloak refresh token

        Returns:
            New access token or None
        """
        if not all([self.keycloak_server_url, self.keycloak_realm, self.keycloak_client_id]):
            logger.error("Keycloak configuration incomplete for token refresh")
            return None

        try:
            token_url = f"{self.keycloak_server_url.rstrip('/')}/realms/{self.keycloak_realm}/protocol/openid-connect/token"

            data = {
                'grant_type': 'refresh_token',
                'refresh_token': refresh_token,
                'client_id': self.keycloak_client_id,
            }

            # Add client secret if configured
            if self.keycloak_client_secret:
                data['client_secret'] = self.keycloak_client_secret

            response = requests.post(token_url, data=data, timeout=10)

            if response.status_code == 200:
                token_data = response.json()
                access_token = token_data.get('access_token')
                if access_token:
                    logger.info("Successfully refreshed access token")
                    return access_token
            else:
                logger.error(f"Token refresh failed: {response.status_code} - {response.text}")

        except Exception as e:
            logger.error(f"Error refreshing access token: {e}")

        return None


# Global instance
session_token_extractor = SessionTokenExtractor()
