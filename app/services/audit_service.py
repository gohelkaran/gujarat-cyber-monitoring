"""
Audit Service Layer
Gujarat Cyber Crime Social Media Intelligence & Early Warning System
"""

import json
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from app.services.base import BaseService
from app.repositories.audit_repository import AuditRepository
from app.schemas.audit import AuditEventCreate, AuditEventRead
from app.core.constants import AuditAction, DataClassification
from app.core.logging_config import correlation_id_ctx
from app.config.settings import get_settings


class AuditService(BaseService):
    """Business service for recording forensic events and managing compliance logs."""
    def __init__(self, db: Session):
        super().__init__(db)
        self.repo = AuditRepository(db)
        self.settings = get_settings()

    def log_event(
        self,
        action: AuditAction,
        actor_id: Optional[str] = None,
        actor_role: Optional[str] = None,
        actor_ip: Optional[str] = None,
        actor_user_agent: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        classification_level: DataClassification = DataClassification.RESTRICTED,
    ) -> AuditEventRead:
        """
        Creates an audit record in the database and also mirrors it to the tamper-evident
        disk audit log file.
        """
        correlation_id = correlation_id_ctx.get()

        event_create = AuditEventCreate(
            actor_id=actor_id,
            actor_role=actor_role,
            actor_ip=actor_ip,
            actor_user_agent=actor_user_agent,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            correlation_id=correlation_id,
            classification_level=classification_level,
        )

        # 1. Database persistence
        record = self.repo.record_event(event_create)

        # 2. Append-only flat-file mirror for forensic redundancy
        try:
            with open(self.settings.AUDIT_LOG_FILE_PATH, "a", encoding="utf-8") as f:
                f.write(json.dumps({
                    "id": record.id,
                    "timestamp": record.timestamp.isoformat(),
                    "action": record.action.value,
                    "actor_id": record.actor_id,
                    "actor_role": record.actor_role,
                    "actor_ip": record.actor_ip,
                    "correlation_id": record.correlation_id,
                    "classification_level": record.classification_level.value,
                }) + "\n")
        except Exception as e:
            self.logger.error(f"Failed to write to file audit log: {e}")

        return AuditEventRead.model_validate(record)

    def log_security_event(
        self,
        action: AuditAction,
        actor_id: Optional[str] = None,
        actor_role: Optional[str] = None,
        actor_ip: Optional[str] = None,
        actor_user_agent: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        status: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        classification_level: DataClassification = DataClassification.RESTRICTED,
    ) -> AuditEventRead:
        """Helper for logging operational security events with status."""
        det = dict(details or {})
        if status:
            det["status"] = status
        return self.log_event(
            action=action,
            actor_id=actor_id,
            actor_role=actor_role,
            actor_ip=actor_ip,
            actor_user_agent=actor_user_agent,
            resource_type=resource_type,
            resource_id=resource_id,
            details=det,
            classification_level=classification_level,
        )

    def get_recent_audits(self, limit: int = 50, actor_id: Optional[str] = None) -> List[AuditEventRead]:
        """Returns recent audit events for compliance inspections."""
        records = self.repo.list_recent(limit=limit, actor_id=actor_id)
        return [AuditEventRead.model_validate(r) for r in records]
