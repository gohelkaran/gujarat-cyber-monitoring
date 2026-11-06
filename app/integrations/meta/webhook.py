"""
Meta Webhook Event Processor & Verification Handshake
Gujarat Cyber Crime Social Media Intelligence & Early Warning System
"""

import hmac
import hashlib
from typing import Optional, Dict, Any, Tuple
from app.config.settings import get_settings
from app.core.logging_config import get_logger

logger = get_logger("meta_webhook")


class MetaWebhookHandler:
    """Handles verification challenge handshake and HMAC-SHA256 signature verification for Meta Webhooks."""

    def __init__(self, verify_token: Optional[str] = None, app_secret: Optional[str] = None):
        settings = get_settings()
        self.verify_token = verify_token or settings.META_WEBHOOK_VERIFY_TOKEN
        self.app_secret = (
            app_secret
            or (settings.META_APP_SECRET.get_secret_value() if settings.META_APP_SECRET else "")
        )

    def verify_handshake(self, mode: Optional[str], token: Optional[str], challenge: Optional[str]) -> Tuple[bool, Optional[str]]:
        """
        Validates Meta's GET webhook challenge.
        Meta sends: hub.mode=subscribe&hub.challenge=1158201444&hub.verify_token=me_token
        """
        if mode == "subscribe" and token == self.verify_token and challenge:
            logger.info("Meta webhook handshake challenge accepted successfully.")
            return True, challenge
        logger.warning(f"Meta webhook handshake rejected: mode={mode}, token_matches={token == self.verify_token}")
        return False, None

    def verify_signature(self, payload_bytes: bytes, signature_header: Optional[str]) -> bool:
        """
        Verifies X-Hub-Signature-256 header using SHA-256 HMAC against META_APP_SECRET.
        """
        if not self.app_secret:
            # If app secret not set in dev, accept with warning
            logger.warning("META_APP_SECRET not set; skipping webhook signature verification.")
            return True

        if not signature_header or not signature_header.startswith("sha256="):
            logger.warning("Missing or malformed X-Hub-Signature-256 header.")
            return False

        expected_hash = signature_header.split("sha256=")[1].strip()
        computed_hash = hmac.new(
            self.app_secret.encode("utf-8"),
            payload_bytes,
            hashlib.sha256
        ).hexdigest()

        is_valid = hmac.compare_digest(expected_hash, computed_hash)
        if not is_valid:
            logger.error("Meta webhook HMAC signature mismatch.")
        return is_valid

