"""
Exception handlers for the FastAPI application
"""

from fastapi import Request, status
from fastapi.responses import JSONResponse

from app.core.exceptions import (
    BaseAPIException,
    ValidationError,
    NotFoundError,
    ConflictError,
    ReferentialIntegrityError,
    DatabaseError
)
from app.core.logging import get_logger

logger = get_logger(__name__)


async def base_api_exception_handler(request: Request, exc: BaseAPIException):
    """Handle custom API exceptions"""
    logger.warning(f"API Exception: {exc.message} (Status: {exc.status_code})")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "message": exc.message,
            "details": exc.details,
            "path": str(request.url)
        }
    )


async def validation_exception_handler(request: Request, exc: ValidationError):
    """Handle validation errors"""
    logger.warning(f"Validation Error: {exc.message} (Field: {exc.field})")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "message": exc.message,
            "field": exc.field,
            "details": exc.details,
            "path": str(request.url)
        }
    )


async def not_found_exception_handler(request: Request, exc: NotFoundError):
    """Handle not found errors"""
    logger.info(f"Not Found: {exc.message}")
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={
            "message": exc.message,
            "resource": exc.resource,
            "identifier": exc.identifier,
            "path": str(request.url)
        }
    )


async def conflict_exception_handler(request: Request, exc: ConflictError):
    """Handle conflict errors"""
    logger.warning(f"Conflict Error: {exc.message}")
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={
            "message": exc.message,
            "conflicting_field": exc.conflicting_field,
            "path": str(request.url)
        }
    )


async def referential_integrity_exception_handler(request: Request, exc: ReferentialIntegrityError):
    """Handle referential integrity errors"""
    logger.warning(f"Referential Integrity Error: {exc.message}")
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "message": exc.message,
            "referenced_collection": exc.referenced_collection,
            "path": str(request.url)
        }
    )


async def database_exception_handler(request: Request, exc: DatabaseError):
    """Handle database errors"""
    logger.error(f"Database Error: {exc.message}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "message": "Internal server error",
            "path": str(request.url)
        }
    )


async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions"""
    logger.error(f"Unexpected error: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "message": "Internal server error",
            "path": str(request.url)
        }
    )


def register_exception_handlers(app):
    """Register all exception handlers with the FastAPI app"""
    app.add_exception_handler(BaseAPIException, base_api_exception_handler)
    app.add_exception_handler(ValidationError, validation_exception_handler)
    app.add_exception_handler(NotFoundError, not_found_exception_handler)
    app.add_exception_handler(ConflictError, conflict_exception_handler)
    app.add_exception_handler(ReferentialIntegrityError, referential_integrity_exception_handler)
    app.add_exception_handler(DatabaseError, database_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)