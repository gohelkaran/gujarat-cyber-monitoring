"""
Comprehensive Test Suite for Instagram Monitoring System - Version 1
Gujarat Cyber Crime Social Media Intelligence & Early Warning System

Covers:
1. Login and authorization
2. OAuth callback validation and error handling
3. Missing or insufficient API permissions
4. Expired or revoked tokens
5. API rate limits and temporary failures
6. Duplicate collection prevention
7. Keyword matching and case-insensitive search
8. Empty and malformed API responses
9. Notification failures
10. Data retention and deletion
11. Secret leakage prevention
12. Clear separation of demo data and real API data
"""

import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch, MagicMock
import httpx

from app.models.user import User
from app.models.source import SocialSource, SourceCredentialMetadata
from app.models.keyword import MonitoredKeyword
from app.models.instagram import CollectedItem, KeywordMatch, NotificationSetting
from app.core.constants import UserRole, SourceType, SourceStatus
from app.security.hashing import hash_password
from app.security.jwt import create_access_token
from app.services.instagram_service import InstagramService
from app.integrations.adapters.instagram import InstagramAdapter


# =============================================================================
# Helper Fixture: Seed Test Officer
# =============================================================================
@pytest.fixture
def test_officer(db_session):
    user = User(
        badge_number="GJ-CYBER-9999",
        full_name="Insp. Test Officer",
        email="test.officer@gujaratpolice.gov.in",
        hashed_password=hash_password("PoliceTest@123"),
        role=UserRole.LEAD_INVESTIGATOR,
        is_active=True,
        is_locked=False,
        failed_login_attempts=0
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def auth_headers(test_officer):
    token = create_access_token({
        "sub": test_officer.id,
        "badge": test_officer.badge_number,
        "role": test_officer.role.value,
        "email": test_officer.email
    })
    return {"Authorization": f"Bearer {token}"}


# =============================================================================
# 1. Login and Authorization Tests
# =============================================================================
def test_auth_login_success(client, test_officer):
    resp = client.post("/api/v1/auth/login", json={
        "username_or_badge": "GJ-CYBER-9999",
        "password": "PoliceTest@123"
    })
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert "access_token" in data
    assert data["user"]["badge_number"] == "GJ-CYBER-9999"


def test_auth_login_invalid_password(client, test_officer, db_session):
    resp = client.post("/api/v1/auth/login", json={
        "username_or_badge": "GJ-CYBER-9999",
        "password": "WrongPassword!"
    })
    assert resp.status_code == 401
    db_session.refresh(test_officer)
    assert test_officer.failed_login_attempts == 1


def test_auth_account_lockout_after_max_attempts(client, test_officer, db_session):
    for i in range(5):
        resp = client.post("/api/v1/auth/login", json={
            "username_or_badge": "GJ-CYBER-9999",
            "password": "WrongPassword!"
        })
    assert resp.status_code == 403
    db_session.refresh(test_officer)
    assert test_officer.is_locked is True


def test_auth_me_protected_endpoint(client, auth_headers):
    resp = client.get("/api/v1/auth/me", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["data"]["badge_number"] == "GJ-CYBER-9999"


def test_auth_me_unauthorized(client):
    resp = client.get("/api/v1/auth/me")
    assert resp.status_code in (401, 403)


# =============================================================================
# 2. OAuth Callback Validation and Error Handling
# =============================================================================
def test_oauth_authorize_url_generation(client):
    resp = client.get("/api/v1/instagram/oauth/authorize")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert "oauth_url" in data
    assert "dialog/oauth" in data["oauth_url"]
    assert "instagram_basic" in data["oauth_url"]
    assert len(data["access_limitations"]) > 0


def test_oauth_callback_mock_exchange(client):
    resp = client.post("/api/v1/instagram/oauth/callback?code=MOCK_CODE_TEST_123")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["success"] is True
    assert data["is_mock_mode"] is True
    assert data["account_username"] == "surat_cyber_police"


# =============================================================================
# 3. Missing or Insufficient API Permissions
# =============================================================================
def test_connection_status_permission_validation(client):
    resp = client.get("/api/v1/instagram/connection-status")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert "is_connected" in data
    assert "granted_permissions" in data
    assert "access_limitations" in data
    assert any("private" in lim.lower() for lim in data["access_limitations"])


# =============================================================================
# 4. Expired or Revoked Tokens
# =============================================================================
def test_expired_token_handling():
    adapter = InstagramAdapter(
        source_id="test-source",
        target_identifier="test_account",
        access_token="INVALID_EXPIRED_LONG_TOKEN_STRING_12345"
    )

    mock_resp = MagicMock(spec=httpx.Response)
    mock_resp.status_code = 400
    mock_resp.json.return_value = {
        "error": {
            "message": "Error validating access token: Session has expired",
            "type": "OAuthException",
            "code": 190,
            "error_subcode": 463
        }
    }

    with patch.object(adapter, "_execute_with_retry", return_value=mock_resp):
        cred_res = adapter.validate_credentials()
        assert cred_res.is_valid is False
        assert cred_res.error_code == "190"
        assert "expired" in cred_res.message.lower()


# =============================================================================
# 5. API Rate Limits and Temporary Failures
# =============================================================================
def test_rate_limit_header_parsing():
    adapter = InstagramAdapter(
        source_id="test-source",
        target_identifier="test_account",
        access_token="MOCK_TEST_TOKEN"
    )

    mock_resp = MagicMock(spec=httpx.Response)
    mock_resp.headers = {"x-app-usage": '{"call_count": 92, "total_cputime": 40, "total_time": 60}'}
    usage = adapter._parse_rate_limit_headers(mock_resp)

    assert usage["app_call_count_pct"] == 92
    assert usage["is_near_limit"] is True


def test_retry_on_server_error_and_rate_limit():
    adapter = InstagramAdapter(
        source_id="test-source",
        target_identifier="test_account",
        access_token="VALID_ACCESS_TOKEN_FOR_TESTING_123"
    )
    adapter.max_retries = 2
    adapter.backoff_factor = 1.0

    mock_500 = MagicMock(spec=httpx.Response, status_code=500)
    mock_200 = MagicMock(spec=httpx.Response, status_code=200)

    mock_client = MagicMock()
    mock_client.request.side_effect = [mock_500, mock_200]

    with patch.object(adapter, "_get_client", return_value=mock_client), patch("time.sleep"):
        resp = adapter._execute_with_retry("GET", "https://graph.facebook.com/v19.0/me")
        assert resp.status_code == 200
        assert mock_client.request.call_count == 2


# =============================================================================
# 6. Duplicate Collection Prevention
# =============================================================================
def test_duplicate_collection_prevention(client, db_session):
    # First collection run
    resp1 = client.post("/api/v1/instagram/collect")
    assert resp1.status_code == 200
    res1_data = resp1.json()["data"]
    initial_saved = res1_data["new_items_saved"]
    assert initial_saved > 0

    # Second collection run (should skip duplicates)
    resp2 = client.post("/api/v1/instagram/collect")
    assert resp2.status_code == 200
    res2_data = resp2.json()["data"]
    assert res2_data["new_items_saved"] == 0
    assert res2_data["duplicates_prevented"] >= initial_saved


# =============================================================================
# 7. Keyword Matching and Case-Insensitive Search
# =============================================================================
def test_keyword_matching_case_insensitivity(db_session):
    service = InstagramService(db_session)

    # Seed monitored keyword
    kw = MonitoredKeyword(
        keyword="digital arrest",
        category="Financial Fraud",
        authorization_ref="DGP-KW-TEST-01",
        created_by_badge="GJ-CYBER-8921",
        is_active=True,
        match_type="PHRASE"
    )
    db_session.add(kw)
    db_session.commit()

    # Create collected item with uppercase keyword
    item = CollectedItem(
        source_id="test-source",
        external_id="ext-item-case-test-1",
        platform="INSTAGRAM",
        source_account="surat_cyber_police",
        caption="URGENT ADVISORY: Beware of scammers threatening DIGITAL ARREST over WhatsApp calls.",
        media_type="IMAGE",
        published_at=datetime.now(timezone.utc),
        is_demo_data=True
    )
    db_session.add(item)
    db_session.commit()

    matches = service._match_keywords_on_item(item)
    assert len(matches) == 1
    assert matches[0].keyword_text == "digital arrest"
    assert "DIGITAL ARREST" in matches[0].matched_snippet
    assert "Operational keyword match only" in matches[0].legal_disclaimer


# =============================================================================
# 8. Empty and Malformed API Responses
# =============================================================================
def test_empty_and_malformed_api_responses():
    adapter = InstagramAdapter(
        source_id="test-source",
        target_identifier="test_account",
        access_token="VALID_TOKEN_TEST_MOCK_12345"
    )

    # Malformed item missing fields
    malformed_raw = {"id": "18921921"}
    normalized = adapter.normalize_content(malformed_raw)
    assert normalized.content_text == ""
    assert normalized.external_item_id == "18921921"
    assert normalized.published_at is not None

    # Empty data response
    mock_resp = MagicMock(spec=httpx.Response)
    mock_resp.status_code = 200
    mock_resp.headers = {}
    mock_resp.json.return_value = {"data": []}

    with patch.object(adapter, "_execute_with_retry", return_value=mock_resp):
        items = adapter.fetch_permitted_content()
        assert len(items) == 0


# =============================================================================
# 9. Notification Failures Handled Gracefully
# =============================================================================
def test_notification_dispatch_failure_handling(db_session):
    from app.services.notification_service import NotificationService
    notifier = NotificationService(db_session)

    item = CollectedItem(
        source_id="src-1",
        external_id="ext-notif-1",
        source_account="test_account",
        caption="Fraudulent scheme alert",
        published_at=datetime.now(timezone.utc),
        is_demo_data=True
    )
    match = KeywordMatch(
        collected_item_id="item-1",
        keyword_text="fraud",
        matched_snippet="...fraud...",
        match_type="PHRASE"
    )

    res = notifier.dispatch_keyword_match_alert(item, match)
    assert "dispatched" in res
    assert "failed" in res
    assert res["dispatched"] >= 1


# =============================================================================
# 10. Data Retention and Deletion
# =============================================================================
def test_data_retention_purge(db_session):
    service = InstagramService(db_session)

    # Insert old item (100 days ago)
    old_date = datetime.now(timezone.utc) - timedelta(days=100)
    old_item = CollectedItem(
        source_id="src-old",
        external_id="ext-old-1",
        source_account="test_acct",
        caption="Old post caption",
        published_at=old_date,
        collected_at=old_date,
        is_demo_data=True
    )
    db_session.add(old_item)

    # Insert fresh item (1 day ago)
    fresh_date = datetime.now(timezone.utc) - timedelta(days=1)
    fresh_item = CollectedItem(
        source_id="src-fresh",
        external_id="ext-fresh-1",
        source_account="test_acct",
        caption="Fresh post caption",
        published_at=fresh_date,
        collected_at=fresh_date,
        is_demo_data=True
    )
    db_session.add(fresh_item)
    db_session.commit()

    # Purge older than 90 days
    purge_res = service.cleanup_expired_retention(retention_days=90)
    assert purge_res["purged_records_count"] >= 1

    # Verify old item deleted, fresh item kept
    assert db_session.query(CollectedItem).filter_by(id=old_item.id).first() is None
    assert db_session.query(CollectedItem).filter_by(id=fresh_item.id).first() is not None


# =============================================================================
# 11. Secret Leakage Prevention
# =============================================================================
def test_secret_leakage_prevention(client, db_session):
    # Ensure source has credentials
    service = InstagramService(db_session)
    source = service._ensure_or_update_source(
        target_identifier="secret_test_account",
        name="Secret Leakage Check Stream",
        access_token="SUPER_CONFIDENTIAL_META_ACCESS_TOKEN_VALUE_SECRET",
        mandate_ref="MANDATE-LEAK-TEST",
        officer_badge="GJ-CYBER-8921",
        scopes=["instagram_basic"]
    )

    # Query connection status
    resp = client.get("/api/v1/instagram/connection-status")
    resp_text = resp.text

    # Verify raw token is NOT in JSON response
    assert "SUPER_CONFIDENTIAL_META_ACCESS_TOKEN_VALUE_SECRET" not in resp_text


# =============================================================================
# 12. Clear Separation of Demo Data and Real API Data
# =============================================================================
def test_separation_of_demo_data_and_real_data(client, db_session):
    # Trigger collection in sandbox mode
    client.post("/api/v1/instagram/collect")

    resp = client.get("/api/v1/instagram/dashboard")
    assert resp.status_code == 200
    data = resp.json()["data"]

    # In sandbox test mode, items must be explicitly marked as demo data
    results = data["results"]
    assert len(results) > 0
    for r in results:
        assert r["is_demo_data"] is True


def test_connect_with_direct_token_mock(client):
    """Tests connecting via direct token in mock sandbox mode."""
    payload = {
        "target_identifier": "surat_cyber_police",
        "access_token": "MOCK_TOKEN_DIRECT_DEV",
        "mandate_ref": "COMM-DIRECT-MOCK-001"
    }
    resp = client.post("/api/v1/instagram/connect-token", json=payload)
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["success"] is True
    assert data["is_mock_mode"] is True


def test_connect_with_direct_token_invalid_handled(client):
    """Tests that invalid live token is rejected with safe diagnostic message."""
    payload = {
        "target_identifier": "invalid_acct_test",
        "access_token": "INVALID_TOKEN_TEST_NOT_MOCK_123456",
        "mandate_ref": "COMM-INVALID-TEST-002"
    }
    resp = client.post("/api/v1/instagram/connect-token", json=payload)
    # Rejection returns 400 with sanitized message
    assert resp.status_code == 400


