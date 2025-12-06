"""
Django authentication backend for Keycloak integration
"""

from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.models import User, AnonymousUser
from django.contrib.auth import get_user_model
from .service import keycloak_service
import logging

logger = logging.getLogger(__name__)

User = get_user_model()

class KeycloakAuthenticationBackend(BaseBackend):
    """
    Custom authentication backend for Keycloak OAuth2 integration
    """
    
    def authenticate(self, request, token=None, **kwargs):
        """
        Authenticate user using Keycloak token
        """
        if not token:
            return None
            
        # Validate token with Keycloak
        user_info = keycloak_service.get_user_info_with_roles(token)
        if not user_info:
            return None
        
        # Return KeycloakUser (no DB storage)
        return KeycloakUser(user_info, user_info.get('app_roles', []))
    
    def get_user(self, user_internal_id):
        """
        Get user by ID
        """
        try:
            return User.objects.get(pk=user_internal_id)
        except User.DoesNotExist:
            return None

class KeycloakUser:
    """
    Custom user class that represents a Keycloak authenticated user
    """
    
    def __init__(self, user_info: dict, roles: list = None):
        self.user_info = user_info
        self.roles = roles or []
        self.is_authenticated = True
        self.is_active = True
        self.is_anonymous = False
    
    @property
    def id(self):
        return self.user_info.get('sub')
    
    @property
    def username(self):
        return self.user_info.get('preferred_username')
    
    @property
    def email(self):
        return self.user_info.get('email', '')
    
    def has_role(self, role_name: str) -> bool:
        """Check if user has specific role"""
        return role_name in self.roles
    
    def has_any_role(self, role_names: list) -> bool:
        """Check if user has any of the specified roles"""
        return any(role in self.roles for role in role_names)
    
    def get_roles(self) -> list:
        """Get user roles"""
        return self.roles.copy()
    
    def __str__(self):
        return self.username or self.email or str(self.id)