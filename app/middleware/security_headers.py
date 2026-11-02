"""
Security Headers Middleware
Gujarat Cyber Crime Social Media Intelligence & Early Warning System
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from app.security.headers import get_security_headers


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Injects hardened security response headers onto all outgoing HTTP responses."""
    async def dispatch(self, request: Request, call_next) -> Response:
        response: Response = await call_next(request)
        for header_name, header_value in get_security_headers().items():
            response.headers[header_name] = header_value
        return response
