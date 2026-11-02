"""
Request ID and Correlation ID Middleware
Gujarat Cyber Crime Social Media Intelligence & Early Warning System

Ensures every incoming HTTP request receives an audit-ready correlation ID.
Propagates the ID across logs, downstream calls, and outgoing response headers.
"""

import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from app.core.logging_config import correlation_id_ctx


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """
    Middleware that captures or generates correlation identifiers.
    Header keys supported: 'X-Request-ID', 'X-Correlation-ID'.
    """
    async def dispatch(self, request: Request, call_next) -> Response:
        # Check incoming headers for existing distributed tracing ID
        incoming_id = request.headers.get("X-Request-ID") or request.headers.get("X-Correlation-ID")
        correlation_id = incoming_id if incoming_id else str(uuid.uuid4())

        # Set in context variable for logging and service layers
        token = correlation_id_ctx.set(correlation_id)

        try:
            response: Response = await call_next(request)
            # Attach correlation ID to response headers
            response.headers["X-Request-ID"] = correlation_id
            response.headers["X-Correlation-ID"] = correlation_id
            return response
        finally:
            correlation_id_ctx.reset(token)
