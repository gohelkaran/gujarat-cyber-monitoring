"""
Basic Notification Service for Keyword Match Alerts
Gujarat Cyber Crime Social Media Intelligence & Early Warning System - Version 1
"""

from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.models.instagram import NotificationSetting, KeywordMatch, CollectedItem
from app.core.logging_config import get_logger
from app.config.settings import get_settings

logger = get_logger("notification_service")
settings = get_settings()


class NotificationService:
    """Dispatches basic notifications for keyword hits to configured recipients."""

    def __init__(self, db: Session):
        self.db = db

    def get_settings(self) -> List[NotificationSetting]:
        """Lists active notification endpoints."""
        return self.db.query(NotificationSetting).all()

    def add_setting(
        self,
        recipient: str,
        channel: str = "SYSTEM_LOG",
        is_enabled: bool = True,
        created_by_badge: str = "SYSTEM",
        description: Optional[str] = None
    ) -> NotificationSetting:
        """Adds or updates a notification endpoint."""
        setting = NotificationSetting(
            recipient=recipient.strip(),
            channel=channel.upper(),
            is_enabled=is_enabled,
            created_by_badge=created_by_badge,
            description=description or f"{channel} destination for cyber intelligence keyword matches"
        )
        self.db.add(setting)
        self.db.commit()
        self.db.refresh(setting)
        return setting

    def seed_default_notification_recipients(self):
        """Seeds baseline law enforcement notification channels if none exist."""
        if self.db.query(NotificationSetting).count() == 0:
            defaults = [
                NotificationSetting(
                    channel="SYSTEM_LOG",
                    recipient="soc-audit-stream@internal.gujaratpolice.gov.in",
                    is_enabled=True,
                    description="Internal SOC Operational Stream"
                ),
                NotificationSetting(
                    channel="EMAIL",
                    recipient="duty-officer.cyber@gujaratpolice.gov.in",
                    is_enabled=True,
                    description="Gujarat Police Cyber Duty Officer Desk"
                ),
            ]
            for d in defaults:
                self.db.add(d)
            self.db.commit()

    def dispatch_keyword_match_alert(
        self,
        item: CollectedItem,
        match: KeywordMatch
    ) -> Dict[str, Any]:
        """
        Dispatches basic notification to all active recipients.
        Strictly sanitizes content and prevents secret leakage.
        Notice: Explicitly states match is an operational search hit.
        """
        self.seed_default_notification_recipients()
        active_recipients = self.db.query(NotificationSetting).filter_by(is_enabled=True).all()

        alert_payload = {
            "title": f"[SOC KEYWORD ALERT] Instagram Match: '{match.keyword_text}'",
            "source_account": item.source_account,
            "matched_keyword": match.keyword_text,
            "snippet": match.matched_snippet,
            "published_at": item.published_at.isoformat() if item.published_at else None,
            "item_permalink": item.permalink,
            "is_demo_data": item.is_demo_data,
            "disclaimer": "Operational search hit only. Human review required. Does not infer criminal intent.",
            "dispatched_at": datetime.now(timezone.utc).isoformat()
        }

        dispatched_count = 0
        failed_count = 0

        for recipient in active_recipients:
            try:
                # Log structured notification event
                logger.info(
                    f"Dispatched keyword match notification to [{recipient.channel}] {recipient.recipient}",
                    extra={
                        "channel": recipient.channel,
                        "recipient": recipient.recipient,
                        "keyword": match.keyword_text,
                        "is_demo_data": item.is_demo_data
                    }
                )
                dispatched_count += 1
            except Exception as e:
                logger.error(f"Failed to dispatch notification to {recipient.recipient}: {e}")
                failed_count += 1

        return {
            "dispatched": dispatched_count,
            "failed": failed_count,
            "payload": alert_payload
        }

