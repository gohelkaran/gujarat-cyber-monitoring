"""
Source Management & Adapter Test Suite
Gujarat Cyber Crime Social Media Intelligence & Early Warning System
"""

import pytest
from fastapi import status


def _create_sample_facebook_source(client, name="Gujarat Police State CID Public Announcements"):
    payload = {
        "name": name,
        "source_type": "FACEBOOK",
        "target_identifier": "GujaratPoliceOfficialPage",
        "authorization_ref": "DGP-CYBER-MANDATE-2026-081",
        "authorized_by_badge": "GJ-CYBER-8921",
        "description": "Authorized public page advisory monitoring",
        "access_token": "EAAG91829102930491823940192348a12",
        "app_id": "981273641209",
        "token_scope": ["pages_read_engagement", "public_profile"]
    }
    response = client.post("/api/v1/sources", json=payload)
    assert response.status_code == status.HTTP_201_CREATED
    return response.json()["data"]


def test_create_authorized_source_facebook(client):
    """Verifies creating an authorized Facebook source with encrypted credential storage."""
    data = _create_sample_facebook_source(client)
    assert data["source_type"] == "FACEBOOK"
    assert data["target_identifier"] == "GujaratPoliceOfficialPage"
    assert data["is_enabled"] is True

    # Plaintext token must NEVER be returned
    assert "access_token" not in data
    assert "EAAG****" in data["credentials"]["token_masked"]


def test_create_authorized_source_instagram(client):
    """Verifies creating an authorized Instagram source."""
    payload = {
        "name": "Surat Cyber Cell Public Awareness Instagram",
        "source_type": "INSTAGRAM",
        "target_identifier": "surat_cyber_police",
        "authorization_ref": "COMM-SURAT-CYBER-2026-012",
        "authorized_by_badge": "GJ-CYBER-6420",
        "description": "Public advisory stream for cyber fraud awareness in Surat range",
        "access_token": "IGQV98129301928301928301293810239",
        "token_scope": ["instagram_basic"]
    }
    response = client.post("/api/v1/sources", json=payload)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()["data"]
    assert data["source_type"] == "INSTAGRAM"
    assert "IGQV****" in data["credentials"]["token_masked"]


def test_reject_source_missing_legal_mandate(client):
    """Verifies that creating a source without valid legal authorization is rejected."""
    payload = {
        "name": "Unauthorized Rogue Stream",
        "source_type": "FACEBOOK",
        "target_identifier": "random_page",
        "authorization_ref": "",  # Missing legal mandate!
        "authorized_by_badge": "GJ-CYBER-8921"
    }
    response = client.post("/api/v1/sources", json=payload)
    assert response.status_code in [status.HTTP_422_UNPROCESSABLE_ENTITY, status.HTTP_400_BAD_REQUEST]


def test_list_sources_and_get_details(client):
    """Verifies listing sources with masked identifiers."""
    created = _create_sample_facebook_source(client, name="List Source Test")
    response = client.get("/api/v1/sources")
    assert response.status_code == status.HTTP_200_OK

    sources = response.json()["data"]
    assert len(sources) >= 1
    found = any(s["id"] == created["id"] for s in sources)
    assert found is True

    detail_resp = client.get(f"/api/v1/sources/{created['id']}")
    assert detail_resp.status_code == status.HTTP_200_OK
    detail = detail_resp.json()["data"]
    assert detail["id"] == created["id"]
    assert "access_token" not in detail


def test_toggle_source_monitoring(client):
    """Verifies enabling and disabling monitoring for a source."""
    source = _create_sample_facebook_source(client, name="Toggle Test Source")
    source_id = source["id"]

    # Disable
    res_off = client.post(f"/api/v1/sources/{source_id}/toggle?is_enabled=false")
    assert res_off.status_code == status.HTTP_200_OK
    assert res_off.json()["data"]["is_enabled"] is False

    # Enable
    res_on = client.post(f"/api/v1/sources/{source_id}/toggle?is_enabled=true")
    assert res_on.status_code == status.HTTP_200_OK
    assert res_on.json()["data"]["is_enabled"] is True


def test_test_source_connection_adapter(client):
    """Verifies on-demand connection test invoking the SocialSourceAdapter."""
    source = _create_sample_facebook_source(client, name="Connection Test Source")
    source_id = source["id"]

    response = client.post(f"/api/v1/sources/{source_id}/test")
    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert body["success"] is True

    test_data = body["data"]
    assert "adapter_status" in test_data
    assert test_data["adapter_status"]["is_connected"] is True
    assert "latency_ms" in test_data["adapter_status"]


def test_sync_source_adapter_feed(client):
    """Verifies stream synchronization via the adapter interface."""
    source = _create_sample_facebook_source(client, name="Sync Test Source")
    source_id = source["id"]

    response = client.post(f"/api/v1/sources/{source_id}/sync?limit=10")
    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert body["success"] is True
    assert body["data"]["items_synced"] > 0
    assert body["data"]["last_status"] == "SUCCESS"


def test_update_source_parameters(client):
    """Verifies updating source description and rotating token."""
    source = _create_sample_facebook_source(client, name="Update Test Source")
    source_id = source["id"]

    payload = {
        "description": "Updated police investigation description with expanded legal scope.",
        "access_token": "EAAG_ROTATED_TOKEN_123456789012345678"
    }
    response = client.put(f"/api/v1/sources/{source_id}", json=payload)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()["data"]
    assert data["description"] == payload["description"]
    assert "EAAG****5678" in data["credentials"]["token_masked"]


def test_soft_delete_source(client):
    """Verifies soft-deleting a source preserves forensic evidence records."""
    source = _create_sample_facebook_source(client, name="Delete Test Source")
    source_id = source["id"]

    del_resp = client.delete(f"/api/v1/sources/{source_id}")
    assert del_resp.status_code == status.HTTP_200_OK
    assert del_resp.json()["data"]["deleted"] is True

    # Confirm it is excluded from active listings
    remaining = client.get("/api/v1/sources").json()["data"]
    remaining_ids = [s["id"] for s in remaining]
    assert source_id not in remaining_ids


def test_unauthorized_role_rejected(client):
    """Verifies that non-police unauthorized users cannot manage sources."""
    response = client.get("/api/v1/sources", headers={"X-User-Role": "UNAUTHORIZED"})
    assert response.status_code == status.HTTP_403_FORBIDDEN
