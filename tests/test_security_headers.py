"""
Security Headers and Hardening Verification Tests
Gujarat Cyber Crime Social Media Intelligence & Early Warning System
"""

import pytest


def test_security_headers_present(client):
    """Verifies that all OWASP defense-in-depth headers are injected on HTTP responses."""
    response = client.get("/api/v1/health")

    # Anti-sniffing
    assert response.headers.get("X-Content-Type-Options") == "nosniff"

    # Anti-clickjacking
    assert response.headers.get("X-Frame-Options") == "DENY"

    # Content Security Policy
    csp = response.headers.get("Content-Security-Policy")
    assert csp is not None
    assert "default-src 'self'" in csp
    assert "frame-ancestors 'none'" in csp

    # Referrer policy
    assert response.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"

    # Permissions policy
    assert "geolocation=()" in response.headers.get("Permissions-Policy", "")

    # Server fingerprint obfuscation
    assert "Gujarat-Cyber-Intel" in response.headers.get("Server", "")


def test_correlation_id_headers(client):
    """Verifies that correlation headers are captured and returned."""
    custom_cid = "POLICE-INVESTIGATION-REF-789012"
    response = client.get("/api/v1/health", headers={"X-Request-ID": custom_cid})

    assert response.headers.get("X-Request-ID") == custom_cid
    assert response.headers.get("X-Correlation-ID") == custom_cid

    # Verify standard envelope contains the same correlation ID
    data = response.json()
    assert data["correlation_id"] == custom_cid
