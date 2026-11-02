"""
Abstract Generic Social Source Adapter Interface
Gujarat Cyber Crime Social Media Intelligence & Early Warning System

Enforces consistent abstraction for all social media ingestion streams.
The core application interacts exclusively with this interface and never directly with Meta APIs.
"""

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, model_validator
from app.core.constants import SourceType


class NormalizedFeedItem(BaseModel):
    """
    Canonical, normalized social media post / announcement / comment.
    Enforces strict data minimization: collects only legally accessible content
    without personal private data.
    """
    source_id: str = Field(..., description="Internal UUID of the monitored SocialSource")
    platform: str = Field(default="FACEBOOK", description="Platform identifier (FACEBOOK, INSTAGRAM, OTHER)")
    external_item_id: str = Field(..., description="Platform post / media ID")
    source_account_id: str = Field(..., description="Public profile ID or public page ID")
    source_account_name: Optional[str] = Field(None, description="Public page / profile display name")
    content_text: str = Field(..., description="Text content of the public post or announcement")
    published_at: datetime = Field(..., description="Post publication timestamp in UTC")
    source_url: Optional[str] = Field(None, description="Direct URL to public post")
    media_type: Optional[str] = Field(default="status", description="Type of media (status, photo, video, album, link)")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Permitted non-PII metrics (shares, reactions count, media count)")
    collected_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Ingestion timestamp in UTC")

    # Canonical aliases for backward compatibility across modules
    source_type: SourceType = SourceType.FACEBOOK
    external_id: Optional[str] = None
    author_id: Optional[str] = None
    author_name: Optional[str] = None
    permalink_url: Optional[str] = None
    media_urls: List[str] = Field(default_factory=list, description="Public media attachments URLs")
    ingested_at: Optional[datetime] = None
    raw_payload: Dict[str, Any] = Field(default_factory=dict, description="Platform raw response payload")
    legal_provenance: Dict[str, Any] = Field(default_factory=dict, description="Statutory audit reference & warrant tracking")

    @model_validator(mode="before")
    @classmethod
    def sync_aliases(cls, data: Any) -> Any:
        if isinstance(data, dict):
            # external_item_id <-> external_id
            if "external_id" in data and "external_item_id" not in data:
                data["external_item_id"] = data["external_id"]
            elif "external_item_id" in data and "external_id" not in data:
                data["external_id"] = data["external_item_id"]

            # platform <-> source_type
            if "source_type" in data:
                st = data["source_type"]
                val = st.value if hasattr(st, "value") else str(st)
                data.setdefault("platform", val)
            elif "platform" in data:
                p = data["platform"]
                try:
                    data.setdefault("source_type", SourceType(p))
                except Exception:
                    data.setdefault("source_type", SourceType.OTHER_AUTHORIZED_SOURCE)

            # source_account_id <-> author_id
            if "author_id" in data and "source_account_id" not in data:
                data["source_account_id"] = data["author_id"]
            elif "source_account_id" in data and "author_id" not in data:
                data["author_id"] = data["source_account_id"]

            # source_account_name <-> author_name
            if "author_name" in data and "source_account_name" not in data:
                data["source_account_name"] = data["author_name"]
            elif "source_account_name" in data and "author_name" not in data:
                data["author_name"] = data["source_account_name"]

            # source_url <-> permalink_url
            if "permalink_url" in data and "source_url" not in data:
                data["source_url"] = data["permalink_url"]
            elif "source_url" in data and "permalink_url" not in data:
                data["permalink_url"] = data["source_url"]

            # collected_at <-> ingested_at
            if "ingested_at" in data and "collected_at" not in data:
                data["collected_at"] = data["ingested_at"]
            elif "collected_at" in data and "ingested_at" not in data:
                data["ingested_at"] = data["collected_at"]

            # media_type inference if absent
            if "media_type" not in data and "media_urls" in data and data["media_urls"]:
                data["media_type"] = "photo"

        return data


# Canonical Alias for common SocialMediaItem model
SocialMediaItem = NormalizedFeedItem


class AdapterStatus(BaseModel):
    """Real-time connectivity and rate-limit diagnostics for a source adapter."""
    is_connected: bool = Field(..., description="Whether API connection test succeeded")
    health: str = Field(default="OPERATIONAL", description="OPERATIONAL, DEGRADED, RATE_LIMITED, OFFLINE")
    message: str = Field(..., description="Status summary or diagnostic message")
    rate_limit_remaining: int = Field(default=200, description="Available API calls in current window")
    rate_limit_limit: int = Field(default=200, description="Platform rate limit ceiling")
    latency_ms: float = Field(default=0.0, description="API round-trip duration in milliseconds")
    granted_permissions: List[str] = Field(default_factory=list, description="Verified OAuth permission scopes")
    is_mock_mode: bool = Field(default=False, description="True if operating in safe simulated sandbox")
    error_code: Optional[str] = None


class SocialSourceAdapter(ABC):
    """
    Universal Law Enforcement Adapter Contract.
    Must be implemented by all social platform connectors.
    """
    def __init__(
        self,
        source_id: str,
        target_identifier: str,
        access_token: Optional[str] = None,
        app_secret: Optional[str] = None,
        legal_mandate_ref: Optional[str] = None,
    ):
        self.source_id = source_id
        self.target_identifier = target_identifier
        self.access_token = access_token
        self.app_secret = app_secret
        self.legal_mandate_ref = legal_mandate_ref or "STATE-CYBER-MANDATE-PENDING"

    @abstractmethod
    def connect(self) -> bool:
        """Establishes authenticated session with platform API."""
        pass

    @abstractmethod
    def validate_access(self) -> AdapterStatus:
        """Verifies API credentials, permissions, and quota health without fetching feed data."""
        pass

    @abstractmethod
    def fetch_items(self, since: Optional[datetime] = None, limit: int = 50) -> List[NormalizedFeedItem]:
        """Fetches recent public items published after 'since' up to 'limit'."""
        pass

    @abstractmethod
    def normalize_item(self, raw_item: Dict[str, Any]) -> NormalizedFeedItem:
        """Converts raw platform JSON into a canonical NormalizedFeedItem."""
        pass

    @abstractmethod
    def get_status(self) -> AdapterStatus:
        """Returns current operational status and rate-limit diagnostics."""
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """Gracefully closes active sessions and releases connection sockets."""
        pass
