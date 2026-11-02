"""
Schemas Package
Instagram Monitoring System - Version 1
Gujarat Cyber Crime Social Media Intelligence & Early Warning System
"""

from app.schemas.common import ApiResponse, ErrorDetail, HealthResponse, ComponentHealth
from app.schemas.audit import AuditEventCreate, AuditEventRead
from app.schemas.user import UserBase, UserCreate, UserRead, LoginRequest, TokenResponse
from app.schemas.source import (
    SourceBase,
    SourceCreate,
    SourceUpdate,
    SourceRead,
    SourceCredentialRead,
    SourceSyncRead,
    SourceErrorRead,
    SourceTestResult,
    SourceSyncResult,
)
from app.schemas.keyword import (
    KeywordBase,
    KeywordCreate,
    KeywordUpdate,
    KeywordRead,
)

__all__ = [
    "ApiResponse",
    "ErrorDetail",
    "HealthResponse",
    "ComponentHealth",
    "AuditEventCreate",
    "AuditEventRead",
    "UserBase",
    "UserCreate",
    "UserRead",
    "LoginRequest",
    "TokenResponse",
    "SourceBase",
    "SourceCreate",
    "SourceUpdate",
    "SourceRead",
    "SourceCredentialRead",
    "SourceSyncRead",
    "SourceErrorRead",
    "SourceTestResult",
    "SourceSyncResult",
    "KeywordBase",
    "KeywordCreate",
    "KeywordUpdate",
    "KeywordRead",
]
