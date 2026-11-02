"""
Social Source Adapter Factory
Instagram Monitoring System - Version 1
Gujarat Cyber Crime Social Media Intelligence & Early Warning System
"""

from typing import Optional
from app.integrations.adapters.base import SocialSourceAdapter
from app.integrations.adapters.instagram import InstagramAdapter
from app.integrations.adapters.mock import MockSocialSourceAdapter
from app.core.constants import SourceType
from app.models.source import SocialSource


class AdapterFactory:
    """Factory responsible for instantiating the appropriate SocialSourceAdapter."""

    @staticmethod
    def get_adapter(
        source: SocialSource,
        decrypted_access_token: Optional[str] = None,
        decrypted_app_secret: Optional[str] = None,
    ) -> SocialSourceAdapter:
        """Instantiates the correct adapter configured with the target identifier and credentials."""
        target = source.target_identifier
        mandate = source.authorization_ref
        source_id = source.id

        if source.source_type == SourceType.INSTAGRAM:
            return InstagramAdapter(
                source_id=source_id,
                target_identifier=target,
                access_token=decrypted_access_token,
                app_secret=decrypted_app_secret,
                legal_mandate_ref=mandate
            )
        else:
            return MockSocialSourceAdapter(
                source_id=source_id,
                target_identifier=target,
                source_type=source.source_type,
                legal_mandate_ref=mandate
            )
