"""
Custom Application Exceptions and Handlers
Gujarat Cyber Crime Social Media Intelligence & Early Warning System
"""

from typing import Any, Dict, Optional
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from app.core.logging_config import get_logger, correlation_id_ctx
from app.config.settings import get_settings

logger = get_logger("exceptions")


class BaseAppException(Exception):
    """Base class for all business and security domain exceptions."""
    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        code: str = "INTERNAL_ERROR",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code
        self.details = details or {}


class AuthenticationException(BaseAppException):
    """Raised when authentication credentials are invalid or expired."""
    def __init__(self, message: str = "Invalid authentication credentials"):
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="AUTHENTICATION_FAILED"
        )


class AuthorizationException(BaseAppException):
    """Raised when user permissions or security clearance are insufficient."""
    def __init__(self, message: str = "Insufficient privileges or clearance"):
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            code="PERMISSION_DENIED"
        )


class EntityNotFoundException(BaseAppException):
    """Raised when an identified resource does not exist."""
    def __init__(self, entity_name: str, identifier: Optional[Any] = None):
        if identifier is not None:
            msg = f"{entity_name} with identifier '{identifier}' was not found."
            details = {"entity": entity_name, "identifier": str(identifier)}
        else:
            msg = entity_name
            details = {"entity": "Resource", "identifier": entity_name}
        super().__init__(
            message=msg,
            status_code=status.HTTP_404_NOT_FOUND,
            code="RESOURCE_NOT_FOUND",
            details=details
        )


class SecurityIntegrityException(BaseAppException):
    """Raised when cryptographic hashes or evidence seals fail verification."""
    def __init__(self, message: str = "Security integrity verification failed"):
        super().__init__(
            message=message,
            status_code=status.HTTP_409_CONFLICT,
            code="INTEGRITY_VIOLATION"
        )


class RateLimitExceededException(BaseAppException):
    """Raised when client exceeds designated API invocation thresholds."""
    def __init__(self, message: str = "Rate limit threshold exceeded"):
        super().__init__(
            message=message,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            code="RATE_LIMIT_EXCEEDED"
        )


class ValidationException(BaseAppException):
    """Raised when statutory or business rule validation fails."""
    def __init__(self, message: str = "Validation failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            code="VALIDATION_FAILED",
            details=details or {}
        )


# Global Exception Handlers for FastAPI
async def app_exception_handler(request: Request, exc: BaseAppException) -> JSONResponse:
    """Handles domain exceptions cleanly."""
    correlation_id = correlation_id_ctx.get()
    logger.warning(
        f"Domain Exception: [{exc.code}] {exc.message}",
        extra={"status_code": exc.status_code, "path": request.url.path, "details": exc.details}
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
            },
            "correlation_id": correlation_id,
        }
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handles Pydantic input validation errors without leaking internal code."""
    correlation_id = correlation_id_ctx.get()
    logger.warning(f"Request Validation Error at {request.url.path}: {exc.errors()}")
    
    # Clean validation errors for client
    cleaned_errors = []
    for err in exc.errors():
        loc = " -> ".join([str(x) for x in err.get("loc", []) if x != "body"])
        cleaned_errors.append({
            "field": loc or "payload",
            "message": err.get("msg", "Invalid field format")
        })

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Input validation failed on request payload or parameters.",
                "details": {"validation_errors": cleaned_errors},
            },
            "correlation_id": correlation_id,
        }
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Catch-all unhandled exception handler.
    Strictly prevents leaking stack traces, table names, or credentials to clients in production.
    """
    settings = get_settings()
    correlation_id = correlation_id_ctx.get()
    logger.error(
        f"Unhandled Server Error at {request.url.path}: {str(exc)}",
        exc_info=True,
        extra={"correlation_id": correlation_id}
    )

    # In production, show generic message; in dev, show message only if debug enabled
    message = (
        f"Internal server error: {str(exc)}"
        if settings.is_development and settings.DEBUG
        else "An internal server error occurred. This incident has been logged with correlation tracking."
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": message,
            },
            "correlation_id": correlation_id,
        }
    )
