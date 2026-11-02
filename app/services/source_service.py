"""
Social Source Management Business Service
Gujarat Cyber Crime Social Media Intelligence & Early Warning System

Enforces:
- Mandatory legal warrant / mandate reference validation
- RBAC authorization check (Admin clearance required for credential changes)
- Audit trail logging on every configuration mutation
- Interaction exclusively via SocialSourceAdapter interface
"""

import time
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from app.services.base import BaseService
from app.services.audit_service import AuditService
from app.models.source import SocialSource
from app.repositories.source_repository import SourceRepository
from app.integrations.adapters.factory import AdapterFactory
from app.schemas.source import (
    SourceCreate,
    SourceUpdate,
    SourceRead,
    SourceCredentialRead,
    SourceSyncRead,
    SourceErrorRead,
    SourceTestResult,
    SourceSyncResult,
)
from app.core.constants import (
    SourceType,
    SourceStatus,
    SourceHealth,
    UserRole,
    AuditAction,
    DataClassification,
)
from app.core.exceptions import (
    AuthorizationException,
    EntityNotFoundException,
    BaseAppException,
)
from app.utils.time_utils import format_localized_time, utc_now


class SourceService(BaseService):
    """Orchestrates source lifecycle, credential encryption, adapter calls, and audit trails."""
    def __init__(self, db: Session):
        super().__init__(db)
        self.repo = SourceRepository(db)
        self.audit_service = AuditService(db)

    def _verify_admin_clearance(self, officer_role: str, action_name: str) -> None:
        """Enforces that only authorized administrators or nodal officers manage sources."""
        if officer_role not in [UserRole.SUPER_ADMIN.value, UserRole.NODAL_OFFICER.value, "SUPER_ADMIN", "NODAL_OFFICER", "LEAD_INVESTIGATOR"]:
            raise AuthorizationException(
                f"Access Denied: Action '{action_name}' requires minimum clearance of LEAD_INVESTIGATOR or SUPER_ADMIN."
            )

    def create_source(
        self,
        data: SourceCreate,
        acting_officer_badge: str,
        acting_officer_role: str,
        actor_ip: Optional[str] = None
    ) -> SourceRead:
        """
        Registers an authorized social media monitoring stream.
        Validates authorization mandate and records forensic audit event.
        """
        self._verify_admin_clearance(acting_officer_role, "CREATE_SOURCE")

        # Validate legal authorization reference
        if not data.authorization_ref or len(data.authorization_ref.strip()) < 5:
            raise BaseAppException(
                message="Valid legal authorization mandate reference is required by Gujarat Police statutory guidelines.",
                status_code=400,
                code="INVALID_AUTHORIZATION_MANDATE"
            )

        source = self.repo.create_source(data, created_by=acting_officer_badge)

        # Audit event
        self.audit_service.log_event(
            action=AuditAction.SOURCE_CREATE,
            actor_id=acting_officer_badge,
            actor_role=acting_officer_role,
            actor_ip=actor_ip,
            resource_type="SOCIAL_SOURCE",
            resource_id=source.id,
            details={
                "source_name": source.name,
                "source_type": source.source_type.value,
                "target_identifier": source.target_identifier,
                "authorization_ref": source.authorization_ref,
                "authorized_by_badge": source.authorized_by_badge,
                "token_configured": bool(data.access_token)
            },
            classification_level=DataClassification.CONFIDENTIAL
        )

        return self._to_read_dto(source)

    def update_source(
        self,
        source_id: str,
        data: SourceUpdate,
        acting_officer_badge: str,
        acting_officer_role: str,
        actor_ip: Optional[str] = None
    ) -> SourceRead:
        """Updates source settings or rotates credentials with audit logging."""
        self._verify_admin_clearance(acting_officer_role, "UPDATE_SOURCE")

        existing = self.repo.get_source_with_relations(source_id)
        if not existing:
            raise EntityNotFoundException("SocialSource", source_id)

        updated = self.repo.update_source(source_id, data, updated_by=acting_officer_badge)

        self.audit_service.log_event(
            action=AuditAction.SOURCE_UPDATE,
            actor_id=acting_officer_badge,
            actor_role=acting_officer_role,
            actor_ip=actor_ip,
            resource_type="SOCIAL_SOURCE",
            resource_id=source_id,
            details={
                "updated_fields": [k for k, v in data.model_dump(exclude_unset=True).items() if k != "access_token"],
                "credentials_rotated": bool(data.access_token)
            },
            classification_level=DataClassification.CONFIDENTIAL
        )

        return self._to_read_dto(updated)

    def toggle_monitoring(
        self,
        source_id: str,
        is_enabled: bool,
        acting_officer_badge: str,
        acting_officer_role: str,
        actor_ip: Optional[str] = None
    ) -> SourceRead:
        """Enables or disables active stream monitoring."""
        self._verify_admin_clearance(acting_officer_role, "TOGGLE_SOURCE")

        update_dto = SourceUpdate(is_enabled=is_enabled)
        updated = self.repo.update_source(source_id, update_dto, updated_by=acting_officer_badge)
        if not updated:
            raise EntityNotFoundException("SocialSource", source_id)

        self.audit_service.log_event(
            action=AuditAction.SOURCE_TOGGLE,
            actor_id=acting_officer_badge,
            actor_role=acting_officer_role,
            actor_ip=actor_ip,
            resource_type="SOCIAL_SOURCE",
            resource_id=source_id,
            details={"is_enabled": is_enabled, "status": updated.status.value},
            classification_level=DataClassification.RESTRICTED
        )

        return self._to_read_dto(updated)

    def test_connection(
        self,
        source_id: str,
        acting_officer_badge: str,
        actor_ip: Optional[str] = None
    ) -> SourceTestResult:
        """
        Executes on-demand connection verification via SocialSourceAdapter.
        Decrypts access token internally for adapter handshake without exposing it.
        """
        source = self.repo.get_source_with_relations(source_id)
        if not source:
            raise EntityNotFoundException("SocialSource", source_id)

        raw_token, raw_secret = self.repo.get_decrypted_credentials(source_id)

        # Instantiate adapter via factory
        adapter = AdapterFactory.get_adapter(
            source=source,
            decrypted_access_token=raw_token,
            decrypted_app_secret=raw_secret
        )

        try:
            adapter.connect()
            status = adapter.validate_access()
        finally:
            adapter.disconnect()

        # If test failed, record diagnostic error
        if not status.is_connected and status.error_code:
            self.repo.record_sync_failure(
                source_id=source_id,
                error_code=status.error_code,
                error_message=status.message
            )

        # Audit event
        self.audit_service.log_event(
            action=AuditAction.SOURCE_TEST_CONNECTION,
            actor_id=acting_officer_badge,
            actor_role="OFFICER",
            actor_ip=actor_ip,
            resource_type="SOCIAL_SOURCE",
            resource_id=source_id,
            details={
                "is_connected": status.is_connected,
                "latency_ms": status.latency_ms,
                "is_mock_mode": status.is_mock_mode
            },
            classification_level=DataClassification.RESTRICTED
        )

        return SourceTestResult(
            source_id=source.id,
            source_name=source.name,
            success=status.is_connected,
            adapter_status=status,
            timestamp=format_localized_time()
        )

    def sync_source(
        self,
        source_id: str,
        limit: int = 50,
        acting_officer_badge: str = "SYSTEM_SCHEDULER"
    ) -> SourceSyncResult:
        """
        Triggers feed ingestion via the adapter interface.
        Updates sync telemetry and records audit trail.
        """
        source = self.repo.get_source_with_relations(source_id)
        if not source:
            raise EntityNotFoundException("SocialSource", source_id)

        if not source.is_enabled:
            raise BaseAppException(
                message=f"Cannot synchronize disabled source '{source.name}'. Enable monitoring first.",
                status_code=400,
                code="SOURCE_DISABLED"
            )

        raw_token, raw_secret = self.repo.get_decrypted_credentials(source_id)
        adapter = AdapterFactory.get_adapter(source, raw_token, raw_secret)

        start = time.perf_counter()
        try:
            adapter.connect()
            since_time = source.sync_status.last_successful_sync_at if source.sync_status else None
            items = adapter.fetch_items(since=since_time, limit=limit)
            duration = round((time.perf_counter() - start) * 1000, 2)

            last_id = items[0].external_id if items else None
            self.repo.record_sync_success(
                source_id=source_id,
                items_count=len(items),
                last_item_id=last_id,
                quota_used=1,
                latency_ms=duration
            )

            # Audit event
            self.audit_service.log_event(
                action=AuditAction.SOURCE_SYNC,
                actor_id=acting_officer_badge,
                actor_role="SYSTEM_WORKER",
                resource_type="SOCIAL_SOURCE",
                resource_id=source_id,
                details={
                    "items_ingested": len(items),
                    "duration_ms": duration,
                    "status": "SUCCESS"
                },
                classification_level=DataClassification.RESTRICTED
            )

            return SourceSyncResult(
                source_id=source.id,
                source_name=source.name,
                success=True,
                items_synced=len(items),
                duration_ms=duration,
                last_status="SUCCESS",
                timestamp=format_localized_time()
            )
        except Exception as e:
            duration = round((time.perf_counter() - start) * 1000, 2)
            self.repo.record_sync_failure(
                source_id=source_id,
                error_code="SYNC_EXCEPTION",
                error_message=str(e)
            )
            return SourceSyncResult(
                source_id=source.id,
                source_name=source.name,
                success=False,
                items_synced=0,
                duration_ms=duration,
                last_status="FAILED",
                timestamp=format_localized_time()
            )
        finally:
            adapter.disconnect()

    def get_source(self, source_id: str) -> SourceRead:
        """Retrieves a single source with masked credentials."""
        source = self.repo.get_source_with_relations(source_id)
        if not source:
            raise EntityNotFoundException("SocialSource", source_id)
        return self._to_read_dto(source)

    def list_sources(
        self,
        source_type: Optional[SourceType] = None,
        is_enabled: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[SourceRead]:
        """Lists active and configured sources."""
        sources = self.repo.list_sources(source_type=source_type, is_enabled=is_enabled, skip=skip, limit=limit)
        return [self._to_read_dto(s) for s in sources]

    def delete_source(
        self,
        source_id: str,
        acting_officer_badge: str,
        acting_officer_role: str,
        actor_ip: Optional[str] = None
    ) -> bool:
        """Soft-deletes a source to preserve evidentiary provenance and statutory audit trail."""
        self._verify_admin_clearance(acting_officer_role, "DELETE_SOURCE")

        existing = self.repo.get_source_with_relations(source_id)
        if not existing:
            raise EntityNotFoundException("SocialSource", source_id)

        success = self.repo.soft_delete(source_id, deleted_by=acting_officer_badge)

        self.audit_service.log_event(
            action=AuditAction.SOURCE_DELETE,
            actor_id=acting_officer_badge,
            actor_role=acting_officer_role,
            actor_ip=actor_ip,
            resource_type="SOCIAL_SOURCE",
            resource_id=source_id,
            details={"source_name": existing.name, "soft_deleted": True},
            classification_level=DataClassification.CONFIDENTIAL
        )

        return success

    def list_source_errors(self, source_id: str, limit: int = 50) -> List[SourceErrorRead]:
        """Lists recent error logs for the specified source."""
        errors = self.repo.list_errors(source_id, limit=limit)
        return [SourceErrorRead.model_validate(err) for err in errors]

    def _to_read_dto(self, source: SocialSource) -> SourceRead:
        """Converts ORM entity to safe DTO with masked secrets."""
        cred_dto = None
        if source.credentials:
            cred_dto = SourceCredentialRead(
                app_id_masked=source.credentials.app_id_masked,
                token_masked=source.credentials.token_masked,
                token_scope=source.credentials.token_scope,
                token_expires_at=source.credentials.token_expires_at,
                key_version=source.credentials.key_version
            )

        sync_dto = None
        if source.sync_status:
            sync_dto = SourceSyncRead(
                last_sync_at=source.sync_status.last_sync_at,
                last_successful_sync_at=source.sync_status.last_successful_sync_at,
                last_sync_status=source.sync_status.last_sync_status,
                total_items_fetched=source.sync_status.total_items_fetched,
                api_quota_used=source.sync_status.api_quota_used,
                api_quota_limit=source.sync_status.api_quota_limit,
                api_latency_ms=source.sync_status.api_latency_ms
            )

        errors_count = len(source.errors) if source.errors else 0

        return SourceRead(
            id=source.id,
            name=source.name,
            source_type=source.source_type,
            status=source.status,
            is_enabled=source.is_enabled,
            target_identifier=source.target_identifier,
            authorization_ref=source.authorization_ref,
            authorized_by_badge=source.authorized_by_badge,
            description=source.description,
            health_status=source.health_status,
            credentials=cred_dto,
            sync_status=sync_dto,
            recent_errors_count=errors_count,
            created_at=source.created_at,
            updated_at=source.updated_at
        )
