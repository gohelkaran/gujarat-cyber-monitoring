"""
Forensic Audit Repository
Gujarat Cyber Crime Social Media Intelligence & Early Warning System
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, desc
from app.models.audit_log import AuditEvent
from app.schemas.audit import AuditEventCreate
from app.repositories.base import BaseRepository
from app.utils.sanitizer import redact_sensitive_dict


class AuditRepository(BaseRepository[AuditEvent]):
    """Specialized repository for immutable forensic audit trail records."""
    def __init__(self, db: Session):
        super().__init__(AuditEvent, db)

    def record_event(self, event_data: AuditEventCreate) -> AuditEvent:
        """
        Creates an immutable audit log entry.
        Sanitizes payload details before persistence.
        """
        clean_details = redact_sensitive_dict(event_data.details or {})
        
        event = AuditEvent(
            actor_id=event_data.actor_id,
            actor_role=event_data.actor_role,
            actor_ip=event_data.actor_ip,
            actor_user_agent=event_data.actor_user_agent,
            action=event_data.action,
            resource_type=event_data.resource_type,
            resource_id=event_data.resource_id,
            details=clean_details,
            correlation_id=event_data.correlation_id,
            classification_level=event_data.classification_level,
        )
        return self.create(event)

    def list_recent(self, limit: int = 50, actor_id: Optional[str] = None) -> List[AuditEvent]:
        """Queries recent audit logs chronologically."""
        stmt = select(AuditEvent).order_by(desc(AuditEvent.timestamp))
        if actor_id:
            stmt = stmt.where(AuditEvent.actor_id == actor_id)
        stmt = stmt.limit(min(limit, 200))
        return list(self.db.execute(stmt).scalars().all())
