"""
Rate Limiting Verification Tests
Gujarat Cyber Crime Social Media Intelligence & Early Warning System
"""

import pytest
from fastapi import status


def test_rate_limit_headers_injected(client):
    """Verifies that rate limit headers are included in response."""
    response = client.get("/api/v1/health")
    assert "X-RateLimit-Limit" in response.headers
    assert "X-RateLimit-Remaining" in response.headers
    assert "X-RateLimit-Reset" in response.headers


def test_payload_size_limit_rejection(client):
    """Verifies that oversized payloads are rejected with HTTP 413."""
    # Simulate a request declaring a payload size larger than 10MB
    oversized_bytes = 15 * 1024 * 1024
    response = client.post(
        "/api/v1/health",
        headers={"Content-Length": str(oversized_bytes)},
        content=b"test"
    )
    assert response.status_code == status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
    data = response.json()
    assert data["error"]["code"] == "PAYLOAD_TOO_LARGE"
