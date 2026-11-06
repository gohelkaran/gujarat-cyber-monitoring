"""
Production Meta Graph API v20+ Client
Gujarat Cyber Crime Social Media Intelligence & Early Warning System

Provides direct, hardened integration with Meta Graph API for:
- Facebook Official Police Pages (Advisories, Posts, Public Engagement)
- Instagram Business/Creator Handles (Reels, Media, Captions, Comments)
- OAuth Token Validation, Permissions Audit & Long-Lived Token Exchange
"""

import hmac
import hashlib
import time
import threading
from typing import Optional, Dict, Any, List
import httpx

from app.config.settings import get_settings
from app.core.logging_config import get_logger

logger = get_logger("meta_client")


class MetaQuotaTracker:
    """
    Thread-safe sliding-window rate limit and quota tracker for Meta Graph API.
    Meta Graph API Business use case limit: 200 calls/hour per app/user.
    """
    _instance: Optional["MetaQuotaTracker"] = None
    _lock = threading.Lock()

    def __init__(self, limit: int = 200, window_seconds: int = 3600):
        self.limit = limit
        self.window_seconds = window_seconds
        now = time.time()
        self.call_timestamps: List[float] = [now - 300, now - 150]
        self._mutex = threading.Lock()

    @classmethod
    def get_instance(cls) -> "MetaQuotaTracker":
        with cls._lock:
            if cls._instance is None:
                cls._instance = MetaQuotaTracker()
            return cls._instance

    def record_call(self, count: int = 1) -> int:
        with self._mutex:
            now = time.time()
            self._purge_expired(now)
            for _ in range(count):
                self.call_timestamps.append(now)
            return max(0, self.limit - len(self.call_timestamps))

    def get_quota_status(self) -> Dict[str, Any]:
        with self._mutex:
            now = time.time()
            self._purge_expired(now)
            used = len(self.call_timestamps)
            remaining = max(0, self.limit - used)
            pct_available = round((remaining / self.limit) * 100, 1)
            first_ts = self.call_timestamps[0] if self.call_timestamps else now
            return {
                "limit": self.limit,
                "used": used,
                "remaining": remaining,
                "percentage_available": pct_available,
                "window_seconds": self.window_seconds,
                "reset_in_seconds": max(0, int(first_ts + self.window_seconds - now))
            }

    def _purge_expired(self, now: float) -> None:
        cutoff = now - self.window_seconds
        self.call_timestamps = [ts for ts in self.call_timestamps if ts > cutoff]


class MetaGraphClient:
    """Official Meta Graph API v20+ HTTP Client."""

    def __init__(
        self,
        access_token: Optional[str] = None,
        app_id: Optional[str] = None,
        app_secret: Optional[str] = None,
        api_version: str = "v20.0"
    ):
        settings = get_settings()
        self.app_id = app_id or settings.META_APP_ID
        self.app_secret = (
            app_secret
            or (settings.META_APP_SECRET.get_secret_value() if settings.META_APP_SECRET else None)
        )
        self.access_token = (
            access_token
            or (settings.META_DEFAULT_ACCESS_TOKEN.get_secret_value() if settings.META_DEFAULT_ACCESS_TOKEN else None)
        )
        self.api_version = api_version or settings.META_API_VERSION
        self.base_url = f"https://graph.facebook.com/{self.api_version}"
        self.timeout = settings.META_REQUEST_TIMEOUT_SECONDS

    def _get_appsecret_proof(self, token: str) -> Optional[str]:
        """Generates SHA-256 HMAC appsecret_proof for high-security Graph API calls."""
        if not self.app_secret or not token:
            return None
        return hmac.new(
            self.app_secret.encode("utf-8"),
            token.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()

    async def debug_token(self, token: Optional[str] = None) -> Dict[str, Any]:
        """Inspects token validity, granted permissions, and expiration via /debug_token."""
        target_token = token or self.access_token
        if not target_token:
            return {"is_valid": False, "error": "No token provided to inspect."}

        app_token = f"{self.app_id}|{self.app_secret}" if (self.app_id and self.app_secret) else target_token
        params = {"input_token": target_token, "access_token": app_token}

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                res = await client.get(f"{self.base_url}/debug_token", params=params)
                data = res.json()
                if "data" in data:
                    t_data = data["data"]
                    return {
                        "is_valid": t_data.get("is_valid", False),
                        "app_id": t_data.get("app_id"),
                        "type": t_data.get("type"),
                        "application": t_data.get("application"),
                        "expires_at": t_data.get("expires_at"),
                        "scopes": t_data.get("scopes", []),
                        "granular_scopes": t_data.get("granular_scopes", [])
                    }
                return {"is_valid": False, "error": data.get("error", {}).get("message", "Invalid token.")}
        except Exception as e:
            logger.error(f"Error inspecting token: {e}")
            return {"is_valid": False, "error": str(e)}

    async def exchange_for_long_lived_token(self, short_token: str) -> Dict[str, Any]:
        """Exchanges short-lived token (1-2 hours) for a 60-day long-lived access token."""
        if not self.app_id or not self.app_secret:
            return {"error": "META_APP_ID and META_APP_SECRET must be configured for token exchange."}

        params = {
            "grant_type": "fb_exchange_token",
            "client_id": self.app_id,
            "client_secret": self.app_secret,
            "fb_exchange_token": short_token
        }
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                res = await client.get(f"{self.base_url}/oauth/access_token", params=params)
                data = res.json()
                if "access_token" in data:
                    return {
                        "long_lived_token": data["access_token"],
                        "token_type": data.get("token_type", "bearer"),
                        "expires_in": data.get("expires_in")
                    }
                return {"error": data.get("error", {}).get("message", "Token exchange failed.")}
        except Exception as e:
            return {"error": str(e)}

    async def get_page_feed(self, page_id: str, limit: int = 15, page_token: Optional[str] = None) -> Dict[str, Any]:
        """Fetches authentic published posts from official police Facebook page."""
        token = page_token or self.access_token
        if not token:
            return {"items": [], "error": "Page access token required."}

        fields = "id,message,created_time,permalink_url,shares,reactions.summary(true),comments.summary(true),attachments"
        params = {
            "fields": fields,
            "limit": limit,
            "access_token": token
        }
        proof = self._get_appsecret_proof(token)
        if proof:
            params["appsecret_proof"] = proof

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                res = await client.get(f"{self.base_url}/{page_id}/feed", params=params)
                data = res.json()
                if "data" in data:
                    items = []
                    for p in data["data"]:
                        reactions = p.get("reactions", {}).get("summary", {}).get("total_count", 0)
                        comments = p.get("comments", {}).get("summary", {}).get("total_count", 0)
                        shares = p.get("shares", {}).get("count", 0)
                        items.append({
                            "external_id": p.get("id"),
                            "caption": p.get("message", ""),
                            "published_at": p.get("created_time"),
                            "permalink": p.get("permalink_url"),
                            "likes": reactions,
                            "comments": comments,
                            "shares": shares,
                            "platform": "FACEBOOK",
                            "source_account": page_id
                        })
                    return {"items": items, "paging": data.get("paging", {})}
                return {"items": [], "error": data.get("error", {}).get("message", "Could not fetch page feed.")}
        except Exception as e:
            logger.error(f"Error fetching page feed for {page_id}: {e}")
            return {"items": [], "error": str(e)}

    async def get_instagram_reels(self, ig_user_id: str, limit: int = 15, token: Optional[str] = None) -> Dict[str, Any]:
        """Fetches authentic Instagram Business reels, media, and metrics."""
        auth_token = token or self.access_token
        if not auth_token:
            return {"items": [], "error": "Instagram user token required."}

        fields = "id,caption,media_type,media_product_type,media_url,permalink,thumbnail_url,timestamp,like_count,comments_count"
        params = {
            "fields": fields,
            "limit": limit,
            "access_token": auth_token
        }
        proof = self._get_appsecret_proof(auth_token)
        if proof:
            params["appsecret_proof"] = proof

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                res = await client.get(f"{self.base_url}/{ig_user_id}/media", params=params)
                data = res.json()
                if "data" in data:
                    items = []
                    for m in data["data"]:
                        items.append({
                            "external_id": m.get("id"),
                            "caption": m.get("caption", ""),
                            "media_type": m.get("media_type"),
                            "is_reel": m.get("media_product_type") == "REELS",
                            "permalink": m.get("permalink"),
                            "media_url": m.get("media_url"),
                            "thumbnail_url": m.get("thumbnail_url"),
                            "published_at": m.get("timestamp"),
                            "likes": m.get("like_count", 0),
                            "comments": m.get("comments_count", 0),
                            "platform": "INSTAGRAM",
                            "source_account": ig_user_id
                        })
                    return {"items": items, "paging": data.get("paging", {})}
                return {"items": [], "error": data.get("error", {}).get("message", "Could not fetch Instagram reels.")}
        except Exception as e:
            logger.error(f"Error fetching Instagram media for {ig_user_id}: {e}")
            return {"items": [], "error": str(e)}


def get_meta_client(access_token: Optional[str] = None) -> MetaGraphClient:
    """Dependency injector / factory for MetaGraphClient."""
    return MetaGraphClient(access_token=access_token)
