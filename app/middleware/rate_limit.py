"""
Rate Limiting Middleware
Gujarat Cyber Crime Social Media Intelligence & Early Warning System

Implements sliding window token-bucket rate limiting per client IP.
Designed with a modular backend adapter pattern for easy migration to Redis.
"""

import time
from collections import defaultdict
from threading import Lock
from typing import Dict, List
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette import status
from app.config.settings import get_settings
from app.core.logging_config import get_logger, correlation_id_ctx

logger = get_logger("rate_limit")


class InMemoryRateLimitStore:
    """Thread-safe in-memory sliding window rate tracker."""
    def __init__(self):
        self._history: Dict[str, List[float]] = defaultdict(list)
        self._lock = Lock()

    def record_and_check(self, key: str, max_requests: int, window_seconds: int = 60) -> tuple[bool, int, int]:
        """
        Returns (is_allowed, remaining, reset_seconds).
        Cleans expired entries and checks against current count.
        """
        now = time.time()
        cutoff = now - window_seconds

        with self._lock:
            # Clean expired timestamps
            timestamps = [ts for ts in self._history[key] if ts > cutoff]
            current_count = len(timestamps)

            if current_count >= max_requests:
                earliest = min(timestamps) if timestamps else now
                reset_in = max(1, int(window_seconds - (now - earliest)))
                self._history[key] = timestamps
                return False, 0, reset_in

            timestamps.append(now)
            self._history[key] = timestamps
            remaining = max(0, max_requests - len(timestamps))
            return True, remaining, window_seconds


# Global store instance
_rate_limit_store = InMemoryRateLimitStore()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware applying rate limits per IP address.
    Static files and docs are exempted to prevent UI prototype breakage.
    """
    EXEMPT_PREFIXES = ("/static", "/favicon.ico", "/docs", "/redoc", "/openapi.json", "/api/v1/instagram/webhook")

    async def dispatch(self, request: Request, call_next) -> Response:
        settings = get_settings()

        # Exempt static assets and API spec
        if request.url.path.startswith(self.EXEMPT_PREFIXES):
            return await call_next(request)

        # Determine client identifier (respecting forward headers if configured)
        client_ip = request.client.host if request.client else "127.0.0.1"
        limit = settings.RATE_LIMIT_PER_MINUTE
        window = 60

        is_allowed, remaining, reset_in = _rate_limit_store.record_and_check(
            key=client_ip,
            max_requests=limit,
            window_seconds=window
        )

        if not is_allowed:
            logger.warning(f"Rate limit exceeded for client: {client_ip} on path {request.url.path}")
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "success": False,
                    "error": {
                        "code": "RATE_LIMIT_EXCEEDED",
                        "message": f"Rate limit threshold of {limit} requests per minute exceeded. Please retry after {reset_in} seconds.",
                    },
                    "correlation_id": correlation_id_ctx.get(),
                },
                headers={
                    "Retry-After": str(reset_in),
                    "X-RateLimit-Limit": str(limit),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(reset_in),
                }
            )

        response: Response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(reset_in)
        return response
