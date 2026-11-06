"""Official Meta Graph API v20+ Client & Webhook Integration."""
from app.integrations.meta.client import MetaGraphClient, get_meta_client
from app.integrations.meta.webhook import MetaWebhookHandler

__all__ = ["MetaGraphClient", "get_meta_client", "MetaWebhookHandler"]
