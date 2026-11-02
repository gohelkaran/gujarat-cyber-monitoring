"""
User and Security Identity ORM Model
Gujarat Cyber Crime Social Media Intelligence & Early Warning System
"""

from sqlalchemy import Column, String, Boolean, Integer, DateTime, Enum as SQLEnum
from app.core.database import Base
from app.core.constants import UserRole
from app.models.base import AuditMixin
from app.utils.time_utils import utc_now


class User(Base, AuditMixin):
    """
    Law Enforcement System User Account.
    Enforces RBAC, account lockout, and password rotation tracking.
    """
    __tablename__ = "users"

    badge_number = Column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
        doc="Official police badge number or service credential ID"
    )

    full_name = Column(
        String(150),
        nullable=False,
        doc="Full official name of the officer"
    )

    email = Column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
        doc="Official government email address"
    )

    hashed_password = Column(
        String(255),
        nullable=False,
        doc="Bcrypt/Argon2 one-way salted password hash"
    )

    role = Column(
        SQLEnum(UserRole),
        default=UserRole.CYBER_ANALYST,
        nullable=False,
        index=True,
        doc="Role-based access level"
    )

    department = Column(
        String(150),
        default="Gujarat State Cyber Crime Cell, CID Crime, Gandhinagar",
        nullable=False,
        doc="Designated police station, cyber lab, or unit"
    )

    designation = Column(
        String(100),
        default="Cyber Crime Officer",
        nullable=False,
        doc="Police rank or technical designation"
    )

    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
        doc="Account activation state"
    )

    is_locked = Column(
        Boolean,
        default=False,
        nullable=False,
        doc="Security lockout flag triggered by excessive failed attempts"
    )

    failed_login_attempts = Column(
        Integer,
        default=0,
        nullable=False,
        doc="Failed login attempt counter"
    )

    last_login_at = Column(
        DateTime(timezone=True),
        nullable=True,
        doc="Timestamp of most recent successful login in UTC"
    )

    password_changed_at = Column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
        doc="Timestamp of last password rotation"
    )
