"""
Social Media Adapters Package
Instagram Monitoring System - Version 1
Gujarat Cyber Crime Social Media Intelligence & Early Warning System
"""

from app.integrations.adapters.base import SocialSourceAdapter, NormalizedFeedItem, SocialMediaItem, AdapterStatus
from app.integrations.adapters.instagram import InstagramAdapter
from app.integrations.adapters.mock import MockSocialSourceAdapter
from app.integrations.adapters.factory import AdapterFactory

__all__ = [
    "SocialSourceAdapter",
    "NormalizedFeedItem",
    "SocialMediaItem",
    "AdapterStatus",
    "InstagramAdapter",
    "MockSocialSourceAdapter",
    "AdapterFactory",
]
