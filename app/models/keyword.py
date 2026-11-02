"""
Monitored Keywords and Threat Intelligence Database Models
Gujarat Cyber Crime Social Media Intelligence & Early Warning System

Tracks statutory keywords, categories (Financial Fraud, Phishing, Account Compromise,
Identity Abuse, Extortion, Manual Entries), severity levels, and detection hits.
"""

import uuid
from sqlalchemy import Column, String, Boolean, DateTime, Integer, Float, Text, Enum as SQLEnum, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.base import AuditMixin
from app.core.constants import AlertSeverity, KeywordCategory, KeywordMatchType
from app.utils.time_utils import utc_now


class MonitoredKeyword(Base, AuditMixin):
    """
    Registry of legally authorized monitored cybercrime keywords and phrases.
    Enforces statutory tracking under Gujarat Police Cyber Crime guidelines.
    """
    __tablename__ = "monitored_keywords"

    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        doc="Unique identifier for the monitored keyword rule"
    )

    keyword = Column(
        String(150),
        nullable=False,
        index=True,
        doc="Monitored keyword, phrase, or regex pattern (e.g. 'UPI fraud', 'KYC', 'sextortion')"
    )

    category = Column(
        String(60),
        nullable=False,
        index=True,
        default=KeywordCategory.FINANCIAL_FRAUD.value,
        doc="Threat taxonomy (Financial Fraud, Phishing, Account Compromise, Identity Abuse, Extortion, Other)"
    )

    severity = Column(
        SQLEnum(AlertSeverity, native_enum=False),
        nullable=False,
        default=AlertSeverity.HIGH,
        index=True,
        doc="Severity weight applied to detections matching this keyword"
    )

    match_type = Column(
        String(20),
        nullable=False,
        default=KeywordMatchType.PHRASE.value,
        doc="Matching mode: PHRASE (word boundary/substring), EXACT (full string), REGEX (regular expression)"
    )

    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
        doc="Whether monitoring engine actively scans for this keyword"
    )

    language = Column(
        String(20),
        default="en",
        nullable=False,
        doc="Target language code: 'en' (English), 'gu' (Gujarati), 'hi' (Hindi), 'all'"
    )

    description = Column(
        Text,
        nullable=True,
        doc="Investigative context, operational purpose, or scam MO briefing"
    )

    authorization_ref = Column(
        String(100),
        nullable=False,
        doc="Statutory legal mandate or case sanction reference (e.g. 'DGP-CYBER-KEYWORD-2026-001')"
    )

    created_by_badge = Column(
        String(50),
        nullable=False,
        doc="Authorizing officer badge number"
    )

    hits_count = Column(
        Integer,
        default=0,
        nullable=False,
        doc="Cumulative number of social media items flagged by this keyword"
    )

    last_detected_at = Column(
        DateTime(timezone=True),
        nullable=True,
        doc="Timestamp of most recent detection event in UTC"
    )

    # Relationships
    detections = relationship("KeywordDetectionLog", back_populates="keyword_ref", cascade="all, delete-orphan")


class KeywordDetectionLog(Base):
    """
    Forensic record of a keyword match on an ingested social media item.
    """
    __tablename__ = "keyword_detection_logs"

    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    keyword_id = Column(
        String(36),
        ForeignKey("monitored_keywords.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    source_id = Column(
        String(36),
        nullable=True,
        index=True,
        doc="Originating SocialSource internal ID"
    )

    platform = Column(
        String(50),
        nullable=False,
        doc="Platform where flag occurred (FACEBOOK, INSTAGRAM, OTHER)"
    )

    external_item_id = Column(
        String(100),
        nullable=True,
        index=True,
        doc="Platform post / media external ID"
    )

    confidence_score = Column(
        Float,
        default=1.0,
        nullable=False,
        doc="Algorithm confidence score (0.0 to 1.0)"
    )

    matched_text_snippet = Column(
        Text,
        nullable=True,
        doc="Sanitized textual snippet containing the keyword hit"
    )

    detected_at = Column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
        index=True
    )

    # Relationship
    keyword_ref = relationship("MonitoredKeyword", back_populates="detections")
