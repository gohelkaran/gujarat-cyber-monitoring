"""
Unit & Mocked Integration Test Suite for InstagramAdapter
Gujarat Cyber Crime Social Media Intelligence & Early Warning System

Tests:
1. Credential validation (valid token, expired token code 190, account not found)
2. Permissions validation (granted scopes, restricted account)
3. End-to-end connection testing & latency telemetry
4. Permitted content retrieval (cursor pagination, duplicate detection, checkpoints)
5. Rate-limit header parsing and backoff triggers
6. Transient error retry with exponential backoff
7. Content normalization into SocialMediaItem with data minimization and suggested schema fields
8. Sync status & checkpoint recording in database
9. High availability: graceful fallback when Instagram API is unavailable
10. Token redaction & confidentiality guarantee
"""

import json
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, patch
import httpx
import pytest

from app.integrations.adapters.instagram import (
    InstagramAdapter,
    InstagramCredentialValidationResult,
    InstagramPermissionValidationResult,
    PERMITTED_SCOPES_INSTAGRAM_MONITORING,
)
from app.integrations.adapters.base import AdapterStatus, SocialMediaItem, NormalizedFeedItem
from app.core.constants import SourceType
from app.models.source import SocialSource, SourceSyncStatus, SourceError


@pytest.fixture
def sample_instagram_adapter():
    """Returns a test InstagramAdapter instance with mock credentials."""
    return InstagramAdapter(
        source_id="src-ig-surat-002",
        target_identifier="surat_cyber_police",
        access_token="IGQV_TEST_VALID_ACCESS_TOKEN_FOR_AUDIT_PURPOSES_6420",
        app_secret="ig_secret_887766554433221100",
        legal_mandate_ref="COMM-SURAT-CYBER-2026-012",
        app_id="981273641209"
    )


# =============================================================================
# 1. Credential Validation Tests
# =============================================================================

def test_validate_credentials_success(sample_instagram_adapter):
    """Verifies successful Instagram account authentication."""
    mock_resp = httpx.Response(
        status_code=200,
        json={"id": "17841400123456789", "username": "surat_cyber_police", "name": "Surat Cyber Crime Cell"},
        request=httpx.Request("GET", "https://graph.facebook.com/v19.0/surat_cyber_police")
    )

    with patch.object(sample_instagram_adapter, "_execute_with_retry", return_value=mock_resp):
        res = sample_instagram_adapter.validate_credentials()
        assert isinstance(res, InstagramCredentialValidationResult)
        assert res.is_valid is True
        assert res.error_code is None
        assert res.user_id == "17841400123456789"
        assert res.username == "surat_cyber_police"
        assert res.is_mock_mode is False


def test_validate_credentials_expired_token(sample_instagram_adapter):
    """Verifies detection of expired Instagram OAuth token (Code 190). Token must NOT be exposed."""
    mock_resp = httpx.Response(
        status_code=400,
        json={
            "error": {
                "message": "Error validating access token: Session has expired.",
                "type": "OAuthException",
                "code": 190,
                "error_subcode": 463
            }
        },
        request=httpx.Request("GET", "https://graph.facebook.com/v19.0/surat_cyber_police")
    )

    with patch.object(sample_instagram_adapter, "_execute_with_retry", return_value=mock_resp):
        res = sample_instagram_adapter.validate_credentials()
        assert res.is_valid is False
        assert res.error_code == "190"
        assert "expired" in res.message.lower()
        # Security: Raw token must never appear in diagnostic message
        assert sample_instagram_adapter.access_token not in res.message


def test_validate_credentials_account_not_found(sample_instagram_adapter):
    """Verifies error handling when Instagram username/ID is invalid (Code 803)."""
    mock_resp = httpx.Response(
        status_code=404,
        json={
            "error": {
                "message": "(#803) Cannot query specified identifier",
                "type": "OAuthException",
                "code": 803
            }
        },
        request=httpx.Request("GET", "https://graph.facebook.com/v19.0/non_existent_account")
    )

    with patch.object(sample_instagram_adapter, "_execute_with_retry", return_value=mock_resp):
        res = sample_instagram_adapter.validate_credentials()
        assert res.is_valid is False
        assert res.error_code == "803"
        assert "not found" in res.message.lower() or "inaccessible" in res.message.lower()


# =============================================================================
# 2. Permission Validation Tests
# =============================================================================

def test_validate_permissions_granted(sample_instagram_adapter):
    """Verifies that Instagram permitted scopes are verified and target account accessible."""
    perm_data = {
        "data": [
            {"permission": "instagram_basic", "status": "granted"},
            {"permission": "pages_show_list", "status": "granted"},
            {"permission": "pages_read_engagement", "status": "granted"}
        ]
    }
    acct_data = {
        "id": "17841400123456789",
        "username": "surat_cyber_police",
        "name": "Surat City Cyber Cell",
        "profile_picture_url": "https://cdn.instagram.com/surat_cyber.jpg"
    }

    def mock_request(method, url, **kwargs):
        if "permissions" in url:
            return httpx.Response(200, json=perm_data, request=httpx.Request(method, url))
        else:
            return httpx.Response(200, json=acct_data, request=httpx.Request(method, url))

    with patch.object(sample_instagram_adapter, "_execute_with_retry", side_effect=mock_request):
        res = sample_instagram_adapter.validate_permissions()
        assert isinstance(res, InstagramPermissionValidationResult)
        assert res.is_authorized is True
        assert res.target_account_accessible is True
        assert "instagram_basic" in res.granted_permissions
        assert res.account_username == "surat_cyber_police"


def test_validate_permissions_target_account_forbidden(sample_instagram_adapter):
    """Verifies detection when account access is forbidden / private without permission."""
    perm_data = {"data": [{"permission": "public_profile", "status": "granted"}]}

    def mock_request(method, url, **kwargs):
        if "permissions" in url:
            return httpx.Response(200, json=perm_data, request=httpx.Request(method, url))
        else:
            return httpx.Response(
                403,
                json={"error": {"message": "(#10) Application does not have permission for this Instagram account", "code": 10}},
                request=httpx.Request(method, url)
            )

    with patch.object(sample_instagram_adapter, "_execute_with_retry", side_effect=mock_request):
        res = sample_instagram_adapter.validate_permissions()
        assert res.is_authorized is False
        assert res.target_account_accessible is False


# =============================================================================
# 3. test_connection() Diagnostic Tests
# =============================================================================

def test_test_connection_healthy(sample_instagram_adapter):
    """Verifies test_connection() returns operational status and measures latency."""
    mock_cred = InstagramCredentialValidationResult(is_valid=True, message="OK", is_mock_mode=False)
    mock_perm = InstagramPermissionValidationResult(
        is_authorized=True,
        granted_permissions=["instagram_basic", "pages_show_list"],
        missing_permissions=[],
        target_account_accessible=True,
        account_username="surat_cyber_police",
        message="Authorized"
    )

    dummy_header_resp = httpx.Response(
        200,
        headers={"x-app-usage": '{"call_count": 22, "total_cputime": 15, "total_time": 10}'},
        json={"id": "17841400123456789"},
        request=httpx.Request("GET", "https://graph.facebook.com/v19.0/surat_cyber_police")
    )

    with patch.object(sample_instagram_adapter, "validate_credentials", return_value=mock_cred), \
         patch.object(sample_facebook_perm := sample_instagram_adapter, "validate_permissions", return_value=mock_perm), \
         patch.object(sample_instagram_adapter, "_execute_with_retry", return_value=dummy_header_resp):

        status = sample_instagram_adapter.test_connection()
        assert isinstance(status, AdapterStatus)
        assert status.is_connected is True
        assert status.health == "OPERATIONAL"
        assert status.latency_ms >= 0.0
        assert "instagram_basic" in status.granted_permissions


def test_test_connection_rate_limited(sample_instagram_adapter):
    """Verifies that high usage (>85%) triggers RATE_LIMITED health status."""
    mock_cred = InstagramCredentialValidationResult(is_valid=True, message="OK", is_mock_mode=False)
    mock_perm = InstagramPermissionValidationResult(
        is_authorized=True,
        granted_permissions=["instagram_basic"],
        missing_permissions=[],
        target_account_accessible=True,
        account_username="surat_cyber_police",
        message="Authorized"
    )

    near_limit_resp = httpx.Response(
        200,
        headers={"x-app-usage": '{"call_count": 89, "total_cputime": 86, "total_time": 40}'},
        json={"id": "17841400123456789"},
        request=httpx.Request("GET", "https://graph.facebook.com/v19.0/surat_cyber_police")
    )

    with patch.object(sample_instagram_adapter, "validate_credentials", return_value=mock_cred), \
         patch.object(sample_instagram_adapter, "validate_permissions", return_value=mock_perm), \
         patch.object(sample_instagram_adapter, "_execute_with_retry", return_value=near_limit_resp):

        status = sample_instagram_adapter.test_connection()
        assert status.health == "RATE_LIMITED"


# =============================================================================
# 4. fetch_permitted_content() Tests (Pagination, Duplicates, Checkpoints)
# =============================================================================

def test_fetch_permitted_content_pagination_and_deduplication(sample_instagram_adapter):
    """
    Verifies multi-page cursor pagination and duplicate detection.
    Page 1 returns [MEDIA_1, MEDIA_2].
    Page 2 returns [MEDIA_2 (duplicate), MEDIA_3].
    Expected: Exactly 3 unique items [MEDIA_1, MEDIA_2, MEDIA_3].
    """
    now_iso = datetime.now(timezone.utc).isoformat()
    page1_data = {
        "data": [
            {
                "id": "IG_MEDIA_001",
                "caption": "Surat Police Cyber Advisory: Do not download remote access apps like AnyDesk on fraud calls.",
                "media_type": "IMAGE",
                "media_url": "https://cdn.instagram.com/p1.jpg",
                "permalink": "https://instagram.com/p/ig001",
                "timestamp": now_iso,
                "username": "surat_cyber_police",
                "like_count": 520,
                "comments_count": 48
            },
            {
                "id": "IG_MEDIA_002",
                "caption": "Job Scam Alert: Part-time review work on Telegram is financial fraud.",
                "media_type": "VIDEO",
                "media_url": "https://cdn.instagram.com/reel2.mp4",
                "permalink": "https://instagram.com/reel/ig002",
                "timestamp": now_iso,
                "username": "surat_cyber_police",
                "like_count": 1280,
                "comments_count": 92
            }
        ],
        "paging": {
            "cursors": {"after": "IG_CURSOR_PAGE_2_ABC"},
            "next": "https://graph.facebook.com/v19.0/media?after=IG_CURSOR_PAGE_2_ABC"
        }
    }

    page2_data = {
        "data": [
            {
                "id": "IG_MEDIA_002",  # Duplicate media!
                "caption": "Job Scam Alert: Part-time review work on Telegram is financial fraud.",
                "media_type": "VIDEO",
                "media_url": "https://cdn.instagram.com/reel2.mp4",
                "permalink": "https://instagram.com/reel/ig002",
                "timestamp": now_iso,
                "username": "surat_cyber_police",
                "like_count": 1280,
                "comments_count": 92
            },
            {
                "id": "IG_MEDIA_003",  # New carousel post
                "caption": "Safety Slides: 5 Tips to Protect Senior Citizens from Digital Arrest Scams.",
                "media_type": "CAROUSEL_ALBUM",
                "media_url": "https://cdn.instagram.com/carousel3.jpg",
                "permalink": "https://instagram.com/p/ig003",
                "timestamp": now_iso,
                "username": "surat_cyber_police",
                "like_count": 890,
                "comments_count": 34
            }
        ],
        "paging": {
            "cursors": {"after": "IG_CURSOR_PAGE_3_END"}
        }
    }

    call_count = 0

    def mock_paged_media(method, url, params=None, **kwargs):
        nonlocal call_count
        call_count += 1
        if params and params.get("after") == "IG_CURSOR_PAGE_2_ABC":
            return httpx.Response(200, json=page2_data, request=httpx.Request(method, url))
        return httpx.Response(200, json=page1_data, request=httpx.Request(method, url))

    with patch.object(sample_instagram_adapter, "_execute_with_retry", side_effect=mock_paged_media):
        items = sample_instagram_adapter.fetch_permitted_content(limit=10, max_pages=3)

        assert len(items) == 3
        item_ids = [item.external_item_id for item in items]
        assert item_ids == ["IG_MEDIA_001", "IG_MEDIA_002", "IG_MEDIA_003"]
        assert sample_instagram_adapter.last_checkpoint_cursor == "IG_CURSOR_PAGE_2_ABC"


def test_fetch_permitted_content_transient_retry_backoff(sample_instagram_adapter):
    """Verifies that transient network failures trigger exponential retry."""
    now_iso = datetime.now(timezone.utc).isoformat()
    success_data = {
        "data": [
            {
                "id": "IG_MEDIA_RETRY_1",
                "caption": "Surat Police advisory on investment scams.",
                "media_type": "IMAGE",
                "media_url": "https://cdn.instagram.com/retry1.jpg",
                "permalink": "https://instagram.com/p/retry1",
                "timestamp": now_iso,
                "username": "surat_cyber_police"
            }
        ]
    }

    attempts = 0

    def failing_request(method, url, **kwargs):
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise httpx.ConnectError("Transient connection reset by peer")
        return httpx.Response(200, json=success_data, request=httpx.Request(method, url))

    # Temporarily speed up backoff factor for fast test execution
    sample_instagram_adapter.backoff_factor = 0.01

    with patch.object(sample_instagram_adapter._get_client(), "request", side_effect=failing_request):
        items = sample_instagram_adapter.fetch_permitted_content(limit=5)
        assert len(items) == 1
        assert items[0].external_item_id == "IG_MEDIA_RETRY_1"
        assert attempts == 2


# =============================================================================
# 5. normalize_content() Tests & Data Minimization
# =============================================================================

def test_normalize_content_suggested_fields(sample_instagram_adapter):
    """
    Verifies that normalize_content() produces the canonical SocialMediaItem model
    with all required fields:
    - source_id
    - platform ("INSTAGRAM")
    - external_item_id
    - source_account_id
    - source_account_name
    - content_text
    - published_at
    - source_url
    - media_type ("photo", "video", "album")
    - metadata
    - collected_at
    """
    raw_media = {
        "id": "17982192830192831",
        "caption": "Surat Cyber Cell Warning: Digital Arrest Fraud Alert. Dial 1930 to report cybercrime.",
        "media_type": "CAROUSEL_ALBUM",
        "media_url": "https://cdn.instagram.com/advisory_slide1.jpg",
        "permalink": "https://www.instagram.com/p/DA_cybercrime_warning/",
        "timestamp": "2026-10-27T09:15:00+0000",
        "username": "surat_cyber_police",
        "like_count": 745,
        "comments_count": 83
    }

    normalized = sample_instagram_adapter.normalize_content(raw_media)

    assert isinstance(normalized, (SocialMediaItem, NormalizedFeedItem))
    assert normalized.source_id == "src-ig-surat-002"
    assert normalized.platform == "INSTAGRAM"
    assert normalized.external_item_id == "17982192830192831"
    assert normalized.source_account_id == "surat_cyber_police"
    assert normalized.source_account_name == "surat_cyber_police"
    assert "Digital Arrest Fraud Alert" in normalized.content_text
    assert normalized.published_at.year == 2026
    assert normalized.published_at.month == 10
    assert normalized.source_url == "https://www.instagram.com/p/DA_cybercrime_warning/"
    assert normalized.media_type == "album"
    assert normalized.metadata["like_count"] == 745
    assert normalized.metadata["comments_count"] == 83
    assert normalized.metadata["raw_media_type"] == "CAROUSEL_ALBUM"
    assert normalized.metadata["legal_mandate_ref"] == "COMM-SURAT-CYBER-2026-012"
    assert normalized.collected_at is not None

    # Strict data minimization check: zero personal user info
    assert "user_email" not in normalized.metadata
    assert "follower_profiles" not in normalized.metadata
    assert "commenters" not in normalized.metadata


# =============================================================================
# 6. record_sync_status() Tests
# =============================================================================

def test_record_sync_status_persisted(db_session, sample_instagram_adapter):
    """Verifies that record_sync_status() records telemetry and checkpoints into DB."""
    source = SocialSource(
        id=sample_instagram_adapter.source_id,
        name="Surat Cyber Crime Instagram Test Source",
        source_type=SourceType.INSTAGRAM,
        target_identifier=sample_instagram_adapter.target_identifier,
        authorization_ref="COMM-SURAT-CYBER-2026-012",
        authorized_by_badge="GJ-CYBER-6420"
    )
    db_session.add(source)
    db_session.commit()

    sync_result = {
        "status": "SUCCESS",
        "items_synced": 4,
        "duration_ms": 115.2,
        "last_item_id": "17982192830192831"
    }

    success = sample_instagram_adapter.record_sync_status(sync_result, session=db_session)
    assert success is True

    # Verify SourceSyncStatus record in DB
    sync_status = db_session.query(SourceSyncStatus).filter_by(source_id=sample_instagram_adapter.source_id).first()
    assert sync_status is not None
    assert sync_status.last_sync_status == "SUCCESS"
    assert sync_status.total_items_fetched == 4
    assert sync_status.last_item_external_id == "17982192830192831"
    assert sync_status.api_latency_ms == 115.2
    assert sync_status.last_successful_sync_at is not None


def test_record_sync_status_failure_records_error(db_session, sample_instagram_adapter):
    """Verifies that failed sync operations record audit records into SourceError."""
    source = SocialSource(
        id=sample_instagram_adapter.source_id,
        name="Surat Instagram Error Test Source",
        source_type=SourceType.INSTAGRAM,
        target_identifier=sample_instagram_adapter.target_identifier,
        authorization_ref="COMM-SURAT-CYBER-2026-012",
        authorized_by_badge="GJ-CYBER-6420"
    )
    db_session.add(source)
    db_session.commit()

    sync_failure = {
        "status": "FAILED",
        "error_code": "INSTAGRAM_RATE_LIMIT",
        "error_message": "Instagram media query rate limit reached (Code 4)",
        "http_status_code": 429,
        "duration_ms": 310.0
    }

    sample_instagram_adapter.record_sync_status(sync_failure, session=db_session)

    err_entry = db_session.query(SourceError).filter_by(source_id=sample_instagram_adapter.source_id).first()
    assert err_entry is not None
    assert err_entry.error_code == "INSTAGRAM_RATE_LIMIT"
    assert "rate limit reached" in err_entry.error_message
    assert err_entry.http_status_code == 429


# =============================================================================
# 7. High Availability & Token Confidentiality Tests
# =============================================================================

def test_high_availability_fallback_when_instagram_unavailable(sample_instagram_adapter):
    """
    Verifies that the system remains functional even if Instagram API is completely down.
    The adapter must gracefully fall back to sandbox mode without crashing.
    """
    with patch.object(sample_instagram_adapter, "_execute_with_retry", side_effect=httpx.ConnectError("Service Unavailable")):
        status = sample_instagram_adapter.test_connection()
        assert status.is_connected is True
        assert status.is_mock_mode is True

        items = sample_instagram_adapter.fetch_permitted_content(limit=2)
        assert len(items) > 0
        assert items[0].platform == "INSTAGRAM"


def test_token_masking_never_exposes_raw_secret(sample_instagram_adapter):
    """
    Verifies the non-negotiable security requirement:
    Raw access tokens must NEVER appear in logs, error messages, or masked outputs.
    """
    raw_token = sample_instagram_adapter.access_token
    masked = sample_instagram_adapter._mask_token(raw_token)

    assert raw_token not in masked
    assert masked.startswith("IGQV****")
    assert masked.endswith(raw_token[-4:])
