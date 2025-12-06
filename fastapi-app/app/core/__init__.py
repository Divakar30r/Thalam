"""
Core module initialization
"""

from .config import settings, get_settings
from .database import database, connect_to_database, disconnect_from_database
from .exceptions import (
    BaseAPIException,
    ValidationError,
    NotFoundError,
    ConflictError,
    ReferentialIntegrityError,
    DatabaseError,
    MongoSchemaValidatorError
)
from .logging import setup_logging, get_logger
from .dependencies import (
    get_current_settings,
    get_database_dependency,
    verify_database_connection,
    get_pagination_params,
    get_location_params
)
from .health import health_check, get_api_info
from .exception_handlers import register_exception_handlers

__all__ = [
    "settings",
    "get_settings",
    "database",
    "connect_to_database",
    "disconnect_from_database",
    "BaseAPIException",
    "ValidationError",
    "NotFoundError",
    "ConflictError",
    "ReferentialIntegrityError",
    "DatabaseError",
    "MongoSchemaValidatorError",
    "setup_logging",
    "get_logger",
    "get_current_settings",
    "get_database_dependency",
    "verify_database_connection",
    "get_pagination_params",
    "get_location_params",
    "health_check",
    "get_api_info",
    "register_exception_handlers"
]