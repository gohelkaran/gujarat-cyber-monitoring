"""
Health Check and Diagnostics Tests
Gujarat Cyber Crime Social Media Intelligence & Early Warning System
"""

import pytest
from fastapi import status


def test_health_endpoint_success(client):
    """Verifies that the comprehensive health endpoint returns HTTP 200 with standard envelope."""
    response = client.get("/api/v1/health")
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert "success" in data
    assert "correlation_id" in data
    assert "timestamp" in data
    assert "data" in data

    health_data = data["data"]
    assert health_data["status"] in ["HEALTHY", "DEGRADED"]
    assert "uptime_seconds" in health_data
    assert "components" in health_data
    assert "database" in health_data["components"]


def test_liveness_probe(client):
    """Verifies container liveness endpoint returns UP status."""
    response = client.get("/api/v1/health/live")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "UP"
    assert "correlation_id" in data


def test_readiness_probe(client):
    """Verifies container readiness endpoint succeeds when DB is accessible."""
    response = client.get("/api/v1/health/ready")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "READY"
