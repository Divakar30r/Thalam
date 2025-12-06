"""
API router initialization
"""

from .users import router as users_router
from .roles import router as roles_router
from .terminals import router as terminals_router
from .role_details import router as role_details_router

__all__ = [
    "users_router",
    "roles_router",
    "terminals_router",
    "role_details_router"
]