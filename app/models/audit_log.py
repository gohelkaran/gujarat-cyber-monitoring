"""
Forensic Audit Log ORM Model
Gujarat Cyber Crime Social Media Intelligence & Early Warning System

Maintains an immutable, append-only log of all security-sensitive actions,
data access queries, administrative actions, and configuration modifications.
"""

from sqlalchemy import Column, String, DateTime, Enum as SQLEnum, JSON, Text
from app.core.database import Base
from app.core.constants import AuditAction, DataClassification
from app.models.base import generate_uuid
from app.utils.time_utils import utc_now


class AuditEvent(Base):
    """
    Forensic Audit Record.
    Must never be modified or deleted directly by normal users.
    """
    __tablename__ = "audit_events"

    id = Column(
        String(36),
        primary_key=True,
        default=generate_uuid,
        doc="Unique audit record identifier"
    )

    timestamp = Column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
        index=True,
        doc="Timestamp in UTC when the event occurred"
    )

    actor_id = Column(
        String(100),
        nullable=True,
        index=True,
        doc="Identifier or badge number of the initiating actor/system"
    )

    actor_role = Column(
        String(50),
        nullable=True,
        doc="RBAC role of the actor at the time of execution"
    )

    actor_ip = Column(
        String(45),  # Fits IPv4 and IPv6
        nullable=True,
        doc="Source IP address of the client"
    )

    actor_user_agent = Column(
        String(255),
        nullable=True,
        doc="Client user-agent string"
    )

    action = Column(
        SQLEnum(AuditAction),
        nullable=False,
        index=True,
        doc="Classified audit action category"
    )

    resource_type = Column(
        String(100),
        nullable=True,
        index=True,
        doc="Domain entity or system area acted upon"
    )

    resource_id = Column(
        String(100),
        nullable=True,
        index=True,
        doc="Unique ID of the entity acted upon"
    )

    details = Column(
        JSON,
        nullable=True,
        doc="Structured details of the action (sanitized of secrets)"
    )

    correlation_id = Column(
        String(64),
        nullable=True,
        index=True,
        doc="Request correlation ID linking related logs"
    )

    classification_level = Column(
        SQLEnum(DataClassification),
        default=DataClassification.RESTRICTED,
        nullable=False,
        doc="Security classification of the logged action"
    )

    tamper_hash = Column(
        String(64),
        nullable=True,
        doc="Cryptographic digest (SHA-256) computed over previous log hash and record body"
    )
