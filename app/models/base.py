"""
Base Declarative Models & Government Audit Mixins
Gujarat Cyber Crime Social Media Intelligence & Early Warning System

Provides standard fields for:
- UUID primary keys
- Strict UTC timestamps
- Data classification levels
- Source provenance tracking
- Soft-deletion architecture for forensic evidence preservation
"""

import uuid
from datetime import datetime
from typing import Any, Dict, Optional
from sqlalchemy import Column, String, DateTime, Boolean, Enum as SQLEnum, JSON
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from app.core.database import Base
from app.core.constants import DataClassification
from app.utils.time_utils import utc_now


def generate_uuid() -> str:
    """Generates a UUID4 string representation."""
    return str(uuid.uuid4())


class AuditMixin:
    """
    Standard mixin applied to all domain models in the Gujarat Cyber Crime system.
    Guarantees forensic traceability, data classification, and provenance.
    """
    id = Column(
        String(36),
        primary_key=True,
        default=generate_uuid,
        index=True,
        doc="Universally unique identifier for the record"
    )

    created_at = Column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
        index=True,
        doc="Record creation timestamp in UTC"
    )

    updated_at = Column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
        doc="Record modification timestamp in UTC"
    )

    created_by = Column(
        String(100),
        nullable=True,
        doc="Identifier or badge number of the initiating user or service account"
    )

    updated_by = Column(
        String(100),
        nullable=True,
        doc="Identifier or badge number of the last modifying user"
    )

    classification_level = Column(
        SQLEnum(DataClassification),
        default=DataClassification.RESTRICTED,
        nullable=False,
        index=True,
        doc="Government security classification (UNCLASSIFIED, RESTRICTED, CONFIDENTIAL, SECRET)"
    )

    source_provenance = Column(
        JSON,
        nullable=True,
        doc="Legally authorized origin tracking metadata (e.g., API source, legal reference)"
    )

    is_deleted = Column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
        doc="Soft-deletion indicator to maintain forensic integrity and audit trails"
    )

    deleted_at = Column(
        DateTime(timezone=True),
        nullable=True,
        doc="Timestamp of soft-deletion in UTC"
    )

    deleted_by = Column(
        String(100),
        nullable=True,
        doc="Officer who authorized the soft-deletion"
    )
