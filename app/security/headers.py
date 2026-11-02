"""
Security HTTP Headers Definitions
Gujarat Cyber Crime Social Media Intelligence & Early Warning System

Enforces OWASP recommended defense-in-depth headers:
- Content-Security-Policy (CSP)
- HTTP Strict Transport Security (HSTS)
- X-Frame-Options (DENY to prevent clickjacking)
- X-Content-Type-Options (nosniff)
- Referrer-Policy (strict-origin-when-cross-origin)
- Permissions-Policy (disabling geolocation, mic, camera)
"""

from typing import Dict
from app.config.settings import get_settings


def get_security_headers() -> Dict[str, str]:
    """Generates standard government security HTTP response headers."""
    settings = get_settings()

    # Content Security Policy (allowing bootstrap, leaflet, chart.js CDNs & self)
    csp_directives = [
        "default-src 'self'",
        "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://unpkg.com",
        "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://unpkg.com https://fonts.googleapis.com",
        "font-src 'self' https://fonts.gstatic.com https://cdn.jsdelivr.net",
        "img-src 'self' data: https://unpkg.com https://*.tile.openstreetmap.org",
        "connect-src 'self'",
        "frame-ancestors 'none'",
        "base-uri 'self'",
        "form-action 'self'",
    ]

    headers = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Permissions-Policy": "geolocation=(), microphone=(), camera=(), payment=(), usb=()",
        "Content-Security-Policy": "; ".join(csp_directives),
        "Server": "Gujarat-Cyber-Intel/0.1",  # Obscures backend server fingerprints
    }

    # Apply HSTS in production or when SSL enforcement is enabled
    if settings.ENFORCE_SSL or settings.is_production:
        hsts_val = f"max-age={settings.HSTS_MAX_AGE_SECONDS}"
        if settings.HSTS_INCLUDE_SUBDOMAINS:
            hsts_val += "; includeSubDomains"
        if settings.HSTS_PRELOAD:
            hsts_val += "; preload"
        headers["Strict-Transport-Security"] = hsts_val

    return headers
