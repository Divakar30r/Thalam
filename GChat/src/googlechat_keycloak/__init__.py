"""
Google Chat API with Keycloak Workload Identity Federation
A Python package for integrating Google Chat API with Keycloak authentication
"""

__version__ = "1.0.0"
__author__ = "Your Name"
__email__ = "divakar30@drapps.dev"

from .auth import KeycloakWIFAuth
from .client import GoogleChatClient, GoogleChatBot
from .config import KEYCLOAK_CONFIG, GOOGLE_CLOUD_CONFIG, GOOGLE_CHAT_CONFIG

__all__ = [
    'KeycloakWIFAuth',
    'GoogleChatClient', 
    'GoogleChatBot',
    'KEYCLOAK_CONFIG',
    'GOOGLE_CLOUD_CONFIG', 
    'GOOGLE_CHAT_CONFIG'
]