"""
Mock / Sandbox Social Source Adapter
Gujarat Cyber Crime Social Media Intelligence & Early Warning System

Provides safe, deterministic test feeds for development and compliance audits
when official Meta enterprise credentials are not provisioned.
"""

import time
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Dict, Any
from app.integrations.adapters.base import SocialSourceAdapter, NormalizedFeedItem, AdapterStatus
from app.core.constants import SourceType


class MockSocialSourceAdapter(SocialSourceAdapter):
    """
    Simulated Law Enforcement Test Adapter.
    Generates realistic, normalized public posts for testing without external API calls.
    """
    def __init__(
        self,
        source_id: str,
        target_identifier: str,
        source_type: SourceType = SourceType.FACEBOOK,
        access_token: Optional[str] = None,
        app_secret: Optional[str] = None,
        legal_mandate_ref: Optional[str] = None,
    ):
        super().__init__(source_id, target_identifier, access_token, app_secret, legal_mandate_ref)
        self.source_type = source_type
        self._connected = True
        self._quota_remaining = 195
        self._latency = 34.5

    def connect(self) -> bool:
        self._connected = True
        return True

    def validate_access(self) -> AdapterStatus:
        start = time.perf_counter()
        time.sleep(0.04)  # Simulate network hop
        latency = round((time.perf_counter() - start) * 1000, 2)

        return AdapterStatus(
            is_connected=True,
            health="OPERATIONAL",
            message=f"Mock adapter connected successfully for target '{self.target_identifier}'. Sandboxed compliance mode active.",
            rate_limit_remaining=self._quota_remaining,
            rate_limit_limit=200,
            latency_ms=latency,
            granted_permissions=["public_profile", "pages_read_engagement", "pages_show_list"],
            is_mock_mode=True
        )

    def fetch_items(self, since: Optional[datetime] = None, limit: int = 50) -> List[NormalizedFeedItem]:
        now = datetime.now(timezone.utc)
        items = []

        sample_posts = [
            {
                "id": f"mock_{self.target_identifier}_post_101",
                "message": "Warning: Fraudulent messages claiming digital arrest by Gujarat Police are circulating. Do not transfer funds.",
                "created_time": (now - timedelta(minutes=15)).isoformat(),
                "permalink_url": f"https://instagram.com/p/C3x918a101",
                "author": {"id": self.target_identifier, "name": f"Gujarat Police Alert Channel ({self.target_identifier})"},
                "media": []
            },
            {
                "id": f"mock_{self.target_identifier}_post_102",
                "message": "Advisory on Telegram Part-time job recruitment schemes promising daily returns of Rs. 3,500.",
                "created_time": (now - timedelta(minutes=45)).isoformat(),
                "permalink_url": f"https://instagram.com/p/C3x918a102",
                "author": {"id": self.target_identifier, "name": f"Gujarat Cyber Crime Advisory ({self.target_identifier})"},
                "media": ["https://images.example.com/advisory.png"]
            }
        ]

        for raw in sample_posts[:limit]:
            items.append(self.normalize_item(raw))

        self._quota_remaining = max(0, self._quota_remaining - len(items))
        return items

    def normalize_item(self, raw_item: Dict[str, Any]) -> NormalizedFeedItem:
        published_dt = datetime.fromisoformat(raw_item["created_time"].replace("Z", "+00:00"))
        if published_dt.tzinfo is None:
            published_dt = published_dt.replace(tzinfo=timezone.utc)

        return NormalizedFeedItem(
            source_id=self.source_id,
            source_type=self.source_type,
            external_id=raw_item["id"],
            author_id=raw_item.get("author", {}).get("id", self.target_identifier),
            author_name=raw_item.get("author", {}).get("name", "Public Account"),
            content_text=raw_item.get("message", ""),
            permalink_url=raw_item.get("permalink_url"),
            media_urls=raw_item.get("media", []),
            published_at=published_dt,
            raw_payload=raw_item,
            legal_provenance={
                "adapter": "MockSocialSourceAdapter",
                "authorization_ref": self.legal_mandate_ref,
                "target_identifier": self.target_identifier,
                "sanction_mode": "SANDBOX_VERIFIED"
            }
        )

    def get_status(self) -> AdapterStatus:
        return self.validate_access()

    def disconnect(self) -> None:
        self._connected = False
