"""
Instagram Monitoring ORM Models
Gujarat Cyber Crime Social Media Intelligence & Early Warning System - Version 1

Models:
- CollectedItem: Permitted Instagram media items and non-PII metadata
- KeywordMatch: Operational search hits with human review status
- NotificationSetting: Basic notification recipients for keyword matches
"""

import uuid
from sqlalchemy import (
    Column,
    String,
    Boolean,
    Integer,
    DateTime,
    Text,
    ForeignKey,
    JSON,
    Index,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.base import AuditMixin, generate_uuid
from app.utils.time_utils import utc_now


class CollectedItem(Base, AuditMixin):
    """
    Permitted Instagram content and non-PII metadata.
    Strictly minimizes data: stores only public media caption, permalink, timestamps,
    and aggregate metrics. Zero follower lists, personal profile scraping, or commenter PII.
    """
    __tablename__ = "collected_items"

    source_id = Column(
        String(36),
        ForeignKey("social_sources.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        doc="Originating authorized source reference"
    )

    external_id = Column(
        String(100),
        nullable=False,
        index=True,
        doc="Meta/Instagram media ID (unique identifier from API)"
    )

    platform = Column(
        String(50),
        default="INSTAGRAM",
        nullable=False,
        index=True,
        doc="Originating platform (INSTAGRAM)"
    )

    source_account = Column(
        String(150),
        nullable=False,
        index=True,
        doc="Public username or Page ID"
    )

    city = Column(
        String(100),
        default="All Gujarat",
        nullable=True,
        index=True,
        doc="City or district jurisdiction (e.g. Veraval, Surat, Ahmedabad)"
    )

    caption = Column(
        Text,
        nullable=True,
        doc="Permitted media caption or textual content"
    )

    media_type = Column(
        String(50),
        default="IMAGE",
        nullable=False,
        doc="Permitted media type: IMAGE, VIDEO, or CAROUSEL_ALBUM"
    )

    permalink = Column(
        String(500),
        nullable=True,
        doc="Direct public URL (never visited or executed automatically)"
    )

    media_url = Column(
        Text,
        nullable=True,
        doc="Media thumbnail or public image link"
    )

    published_at = Column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
        doc="Original timestamp when post was published on Instagram"
    )

    collected_at = Column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
        index=True,
        doc="Timestamp when item was ingested into local storage"
    )

    like_count = Column(
        Integer,
        default=0,
        nullable=False,
        doc="Aggregate like count (non-PII)"
    )

    comments_count = Column(
        Integer,
        default=0,
        nullable=False,
        doc="Aggregate comments count (non-PII)"
    )

    is_demo_data = Column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
        doc="Distinguishes synthetic development mock items from real authorized API items"
    )

    raw_metadata = Column(
        JSON,
        nullable=True,
        doc="Non-PII technical response attributes and authorization provenance"
    )

    # Relationships
    matches = relationship(
        "KeywordMatch",
        back_populates="item",
        cascade="all, delete-orphan",
        order_by="desc(KeywordMatch.detected_at)"
    )

    __table_args__ = (
        UniqueConstraint("source_id", "external_id", name="uq_collected_items_source_external"),
        Index("idx_collected_items_search", "is_demo_data", "published_at"),
    )


class KeywordMatch(Base, AuditMixin):
    """
    Search hit recording an authorized keyword detected in permitted Instagram content.
    Legal Notice:
    A keyword match is solely an operational search hit. It does NOT infer criminality,
    guilt, intent, or precise location. Mandatory human officer review required.
    """
    __tablename__ = "keyword_matches"

    collected_item_id = Column(
        String(36),
        ForeignKey("collected_items.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Foreign key to the collected item"
    )

    keyword_id = Column(
        String(36),
        ForeignKey("monitored_keywords.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        doc="Foreign key to the monitored keyword definition"
    )

    keyword_text = Column(
        String(150),
        nullable=False,
        index=True,
        doc="Matched keyword phrase or token"
    )

    matched_snippet = Column(
        Text,
        nullable=False,
        doc="Sanitized excerpt around the keyword match"
    )

    match_type = Column(
        String(50),
        default="PHRASE",
        nullable=False,
        doc="Pattern type: PHRASE, EXACT, or REGEX"
    )

    detected_at = Column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
        index=True,
        doc="Timestamp of match detection in UTC"
    )

    review_status = Column(
        String(50),
        default="PENDING_REVIEW",
        nullable=False,
        index=True,
        doc="Human review status: PENDING_REVIEW, REVIEWED_RELEVANT, REVIEWED_BENIGN, DISMISSED"
    )

    reviewed_by_badge = Column(
        String(50),
        nullable=True,
        doc="Badge number of officer who conducted human review"
    )

    reviewed_at = Column(
        DateTime(timezone=True),
        nullable=True,
        doc="Timestamp of human review action"
    )

    review_notes = Column(
        Text,
        nullable=True,
        doc="Officer operational assessment remarks"
    )

    legal_disclaimer = Column(
        String(255),
        default="Operational keyword match only. Not proof of criminal intent.",
        nullable=False,
        doc="Statutory disclaimer"
    )

    # Relationships
    item = relationship("CollectedItem", back_populates="matches")
    keyword = relationship("MonitoredKeyword")


class NotificationSetting(Base, AuditMixin):
    """
    Recipient and channel configuration for keyword match notifications.
    """
    __tablename__ = "notification_settings"

    channel = Column(
        String(50),
        default="SYSTEM_LOG",
        nullable=False,
        doc="Channel type: EMAIL, WEBHOOK, SYSTEM_LOG"
    )

    recipient = Column(
        String(255),
        nullable=False,
        doc="Destination email address, webhook URL, or internal queue name"
    )

    is_enabled = Column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
        doc="Whether notification alerts are actively sent"
    )

    notify_on_all_matches = Column(
        Boolean,
        default=True,
        nullable=False,
        doc="Send alert on every new keyword detection"
    )

    created_by_badge = Column(
        String(50),
        default="SYSTEM",
        nullable=False,
        doc="Officer who configured notification endpoint"
    )

    description = Column(
        String(255),
        nullable=True,
        doc="Brief note on recipient role or purpose"
    )

