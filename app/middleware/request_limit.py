"""
Request Payload Size Limiting Middleware
Gujarat Cyber Crime Social Media Intelligence & Early Warning System

Protects the server from memory exhaustion and Denial-of-Service attacks
caused by oversized payloads.
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette import status
from app.config.settings import get_settings
from app.core.logging_config import get_logger, correlation_id_ctx

logger = get_logger("request_limit")


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """Rejects incoming HTTP requests exceeding MAX_CONTENT_LENGTH_BYTES."""
    async def dispatch(self, request: Request, call_next) -> Response:
        settings = get_settings()
        content_length = request.headers.get("content-length")

        if content_length:
            try:
                length_int = int(content_length)
                if length_int > settings.MAX_CONTENT_LENGTH_BYTES:
                    logger.warning(
                        f"Request payload too large: {length_int} bytes (limit: {settings.MAX_CONTENT_LENGTH_BYTES})",
                        extra={"ip": request.client.host if request.client else "unknown"}
                    )
                    return JSONResponse(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        content={
                            "success": False,
                            "error": {
                                "code": "PAYLOAD_TOO_LARGE",
                                "message": f"Request body exceeds maximum allowed size of {settings.MAX_CONTENT_LENGTH_BYTES // (1024 * 1024)} MB.",
                            },
                            "correlation_id": correlation_id_ctx.get(),
                        }
                    )
            except ValueError:
                pass

        return await call_next(request)
