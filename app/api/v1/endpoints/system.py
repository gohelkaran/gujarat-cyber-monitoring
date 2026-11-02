"""
System Status & Security Configuration Metadata Endpoints
Gujarat Cyber Crime Social Media Intelligence & Early Warning System
"""

from typing import List, Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.config.settings import get_settings
from app.schemas.common import ApiResponse
from app.schemas.audit import AuditEventRead
from app.services.audit_service import AuditService
from app.core.constants import UserRole, DataClassification
from app.core.logging_config import correlation_id_ctx
from app.utils.time_utils import format_timestamp_utc, format_localized_time

router = APIRouter(prefix="/system", tags=["System & Security Governance"])


@router.get(
    "/info",
    response_model=ApiResponse[Dict[str, Any]],
    summary="System Security & Posture Metadata",
    description="Returns public-safe governance metadata, legal mandate tags, and security levels."
)
def get_system_info():
    settings = get_settings()
    info = {
        "platform_name": settings.APP_NAME,
        "agency": "Gujarat Cyber Crime Police / State Cyber Crime Cell, CID Crime",
        "state": "Gujarat, India",
        "environment": settings.APP_ENV,
        "version": settings.APP_VERSION,
        "security_policy": {
            "default_data_classification": settings.DEFAULT_DATA_CLASSIFICATION,
            "statutory_retention_days": settings.AUDIT_LOG_RETENTION_DAYS,
            "rate_limit_per_minute": settings.RATE_LIMIT_PER_MINUTE,
            "max_upload_size_mb": settings.MAX_CONTENT_LENGTH_BYTES // (1024 * 1024),
            "enforce_ssl": settings.ENFORCE_SSL or settings.is_production,
        },
        "system_time": {
            "utc": format_timestamp_utc(),
            "localized": format_localized_time(),
            "designated_timezone": settings.DEFAULT_TIMEZONE
        },
        "compliance": {
            "framework": "Government of Gujarat IT Security & Digital Evidence Guidelines",
            "offensive_tools_enabled": False,
            "unauthorized_scraping_enabled": False,
            "mode": "AUTHORIZED_INTELLIGENCE_MONITORING_ONLY"
        }
    }
    return ApiResponse(
        success=True,
        data=info,
        correlation_id=correlation_id_ctx.get(),
        timestamp=format_timestamp_utc()
    )


@router.get(
    "/audit-logs",
    response_model=ApiResponse[List[AuditEventRead]],
    summary="Retrieve Recent Forensic Audit Events",
    description="Accessible by compliance auditors and nodal officers to inspect immutable trail."
)
def get_recent_audit_logs(limit: int = 20, db: Session = Depends(get_db)):
    service = AuditService(db)
    logs = service.get_recent_audits(limit=limit)
    return ApiResponse(
        success=True,
        data=logs,
        correlation_id=correlation_id_ctx.get(),
        timestamp=format_timestamp_utc()
    )
