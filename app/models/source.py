"""
Social Media Source Management ORM Models
Gujarat Cyber Crime Social Media Intelligence & Early Warning System

Models:
- social_sources
- source_credentials_metadata
- source_sync_status
- source_errors

Security Guarantee:
- API access tokens and secrets are stored in encrypted format only.
- Raw secrets are never exposed directly via ORM columns.
"""

from sqlalchemy import (
    Column,
    String,
    Boolean,
    Integer,
    Float,
    DateTime,
    Text,
    Enum as SQLEnum,
    ForeignKey,
    JSON,
)
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.core.constants import SourceType, SourceStatus, SourceHealth
from app.models.base import AuditMixin, generate_uuid
from app.utils.time_utils import utc_now


class SocialSource(Base, AuditMixin):
    """
    Legally authorized social-media monitoring stream.
    Requires strict government authorization reference and officer badge attribution.
    """
    __tablename__ = "social_sources"

    name = Column(
        String(150),
        nullable=False,
        doc="Human-readable title of the monitored source (e.g. Official Page Monitor)"
    )

    source_type = Column(
        SQLEnum(SourceType),
        nullable=False,
        index=True,
        doc="Source platform classification (FACEBOOK, INSTAGRAM, OTHER_AUTHORIZED_SOURCE)"
    )

    status = Column(
        SQLEnum(SourceStatus),
        default=SourceStatus.ACTIVE,
        nullable=False,
        index=True,
        doc="Operational source state"
    )

    is_enabled = Column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
        doc="Active monitoring toggle switch"
    )

    target_identifier = Column(
        String(255),
        nullable=False,
        doc="Public Page ID, Instagram Business Account ID, or authorized handle"
    )

    authorization_ref = Column(
        String(100),
        nullable=False,
        doc="Legal mandate, Court Order, or Police Department authorization reference"
    )

    authorized_by_badge = Column(
        String(50),
        nullable=False,
        doc="Police officer badge number who authorized ingestion"
    )

    description = Column(
        Text,
        nullable=True,
        doc="Operational description of intelligence scope"
    )

    health_status = Column(
        SQLEnum(SourceHealth),
        default=SourceHealth.OPERATIONAL,
        nullable=False,
        doc="Current API connection health"
    )

    # Relationships
    credentials = relationship(
        "SourceCredentialMetadata",
        back_populates="source",
        uselist=False,
        cascade="all, delete-orphan"
    )

    sync_status = relationship(
        "SourceSyncStatus",
        back_populates="source",
        uselist=False,
        cascade="all, delete-orphan"
    )

    errors = relationship(
        "SourceError",
        back_populates="source",
        cascade="all, delete-orphan",
        order_by="desc(SourceError.timestamp)"
    )


class SourceCredentialMetadata(Base, AuditMixin):
    """
    Encrypted credentials vault record for an authorized source.
    Plaintext secrets are NEVER stored in this table.
    """
    __tablename__ = "source_credentials_metadata"

    source_id = Column(
        String(36),
        ForeignKey("social_sources.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
        doc="Foreign key to social_sources"
    )

    encrypted_access_token = Column(
        Text,
        nullable=False,
        doc="Fernet-authenticated encrypted access token"
    )

    encrypted_app_secret = Column(
        Text,
        nullable=True,
        doc="Fernet-authenticated encrypted client secret"
    )

    app_id_masked = Column(
        String(50),
        nullable=True,
        doc="Masked App / Client ID (e.g. 9812****01)"
    )

    token_masked = Column(
        String(50),
        nullable=False,
        doc="Masked token preview for admin verification (e.g. EAAG****4a12)"
    )

    token_scope = Column(
        JSON,
        nullable=True,
        doc="List of authorized API permission scopes"
    )

    token_expires_at = Column(
        DateTime(timezone=True),
        nullable=True,
        doc="Token expiration timestamp in UTC"
    )

    key_version = Column(
        String(20),
        default="v1",
        nullable=False,
        doc="Encryption key version identifier for rotation audits"
    )

    # Relationship
    source = relationship("SocialSource", back_populates="credentials")


class SourceSyncStatus(Base, AuditMixin):
    """
    Tracks periodic synchronization progress, API rate limits, and latency metrics.
    """
    __tablename__ = "source_sync_status"

    source_id = Column(
        String(36),
        ForeignKey("social_sources.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
        doc="Foreign key to social_sources"
    )

    last_sync_at = Column(
        DateTime(timezone=True),
        nullable=True,
        doc="Timestamp of last attempted synchronization in UTC"
    )

    last_successful_sync_at = Column(
        DateTime(timezone=True),
        nullable=True,
        doc="Timestamp of last successful item fetch in UTC"
    )

    last_sync_status = Column(
        String(50),
        default="NEVER_RUN",
        nullable=False,
        doc="Status of the last sync run (SUCCESS, FAILED, RATE_LIMITED)"
    )

    total_items_fetched = Column(
        Integer,
        default=0,
        nullable=False,
        doc="Total cumulative feed items ingested"
    )

    last_item_external_id = Column(
        String(100),
        nullable=True,
        doc="ID of the most recently fetched social media post"
    )

    api_quota_used = Column(
        Integer,
        default=0,
        nullable=False,
        doc="Estimated hourly API calls made"
    )

    api_quota_limit = Column(
        Integer,
        default=200,
        nullable=False,
        doc="Hourly rate limit ceiling imposed by platform"
    )

    api_latency_ms = Column(
        Float,
        default=0.0,
        nullable=False,
        doc="Round-trip API response latency in milliseconds"
    )

    # Relationship
    source = relationship("SocialSource", back_populates="sync_status")


class SourceError(Base):
    """
    Forensic error log capturing API rejections, rate limits, and token revocations.
    """
    __tablename__ = "source_errors"

    id = Column(
        String(36),
        primary_key=True,
        default=generate_uuid,
        doc="Unique error record identifier"
    )

    source_id = Column(
        String(36),
        ForeignKey("social_sources.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Foreign key to social_sources"
    )

    timestamp = Column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
        index=True,
        doc="Timestamp when error occurred in UTC"
    )

    error_code = Column(
        String(100),
        nullable=False,
        doc="Machine-readable error category (e.g. OAUTH_EXPIRED, RATE_LIMIT)"
    )

    error_message = Column(
        Text,
        nullable=False,
        doc="Sanitized error description scrubbed of tokens"
    )

    http_status_code = Column(
        Integer,
        nullable=True,
        doc="HTTP status code returned by platform"
    )

    correlation_id = Column(
        String(64),
        nullable=True,
        index=True,
        doc="Distributed correlation ID of request that triggered error"
    )

    is_resolved = Column(
        Boolean,
        default=False,
        nullable=False,
        doc="Whether administrative resolution has occurred"
    )

    resolved_at = Column(
        DateTime(timezone=True),
        nullable=True,
        doc="Timestamp of error resolution in UTC"
    )

    resolved_by = Column(
        String(100),
        nullable=True,
        doc="Badge number of officer who marked error resolved"
    )

    # Relationship
    source = relationship("SocialSource", back_populates="errors")
