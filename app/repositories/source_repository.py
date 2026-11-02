"""
Social Source Repository Layer
Gujarat Cyber Crime Social Media Intelligence & Early Warning System

Handles parameterized database queries, encryption/decryption of access tokens,
and sync/error telemetry tracking.
"""

from datetime import datetime, timezone
from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select, update, desc

from app.models.source import SocialSource, SourceCredentialMetadata, SourceSyncStatus, SourceError
from app.repositories.base import BaseRepository
from app.schemas.source import SourceCreate, SourceUpdate
from app.core.constants import SourceType, SourceStatus, SourceHealth
from app.security.encryption import encrypt_secret, decrypt_secret, mask_token, mask_identifier
from app.utils.time_utils import utc_now


class SourceRepository(BaseRepository[SocialSource]):
    """Data access abstraction for authorized social media streams."""
    def __init__(self, db: Session):
        super().__init__(SocialSource, db)

    def create_source(self, data: SourceCreate, created_by: str) -> SocialSource:
        """
        Creates and stores an authorized SocialSource and immediately encrypts credentials.
        Plaintext access tokens and app secrets are never stored at rest.
        """
        source = SocialSource(
            name=data.name,
            source_type=data.source_type,
            status=SourceStatus.ACTIVE,
            is_enabled=True,
            target_identifier=data.target_identifier,
            authorization_ref=data.authorization_ref,
            authorized_by_badge=data.authorized_by_badge,
            description=data.description,
            health_status=SourceHealth.OPERATIONAL,
            created_by=created_by,
            classification_level=data.classification_level,
            source_provenance={
                "authorized_by": data.authorized_by_badge,
                "mandate_ref": data.authorization_ref,
                "created_via": "ADMIN_SOURCE_MANAGEMENT_CONSOLE"
            }
        )
        self.db.add(source)
        self.db.flush()

        # Encrypt access token and secrets
        enc_token = encrypt_secret(data.access_token) if data.access_token else ""
        enc_secret = encrypt_secret(data.app_secret) if data.app_secret else None
        masked_tok = mask_token(data.access_token) if data.access_token else "NOT_CONFIGURED"
        masked_app = mask_identifier(data.app_id) if data.app_id else None

        cred_metadata = SourceCredentialMetadata(
            source_id=source.id,
            encrypted_access_token=enc_token,
            encrypted_app_secret=enc_secret,
            app_id_masked=masked_app,
            token_masked=masked_tok,
            token_scope=data.token_scope or [],
            key_version="v1",
            created_by=created_by,
            classification_level=data.classification_level
        )
        self.db.add(cred_metadata)

        # Initialize sync status
        sync_status = SourceSyncStatus(
            source_id=source.id,
            last_sync_status="NEVER_RUN",
            created_by=created_by,
            classification_level=data.classification_level
        )
        self.db.add(sync_status)

        self.db.commit()
        self.db.refresh(source)
        return source

    def get_source_with_relations(self, source_id: str, include_deleted: bool = False) -> Optional[SocialSource]:
        """Fetches a source with eagerly loaded credentials, sync status, and error logs."""
        stmt = (
            select(SocialSource)
            .options(
                joinedload(SocialSource.credentials),
                joinedload(SocialSource.sync_status),
                joinedload(SocialSource.errors),
            )
            .where(SocialSource.id == source_id)
        )
        if not include_deleted:
            stmt = stmt.where(SocialSource.is_deleted.is_(False))
        return self.db.execute(stmt).unique().scalar_one_or_none()

    def list_sources(
        self,
        source_type: Optional[SourceType] = None,
        is_enabled: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[SocialSource]:
        """Lists sources with relations and optional filters."""
        stmt = (
            select(SocialSource)
            .options(
                joinedload(SocialSource.credentials),
                joinedload(SocialSource.sync_status),
            )
            .where(SocialSource.is_deleted.is_(False))
            .order_by(desc(SocialSource.created_at))
        )
        if source_type:
            stmt = stmt.where(SocialSource.source_type == source_type)
        if is_enabled is not None:
            stmt = stmt.where(SocialSource.is_enabled.is_(is_enabled))

        stmt = stmt.offset(skip).limit(min(limit, 200))
        return list(self.db.execute(stmt).unique().scalars().all())

    def update_source(self, source_id: str, data: SourceUpdate, updated_by: str) -> Optional[SocialSource]:
        """Updates source parameters and handles credential rotation if new token provided."""
        source = self.get_source_with_relations(source_id)
        if not source:
            return None

        # Update core attributes
        if data.name is not None:
            source.name = data.name
        if data.target_identifier is not None:
            source.target_identifier = data.target_identifier
        if data.authorization_ref is not None:
            source.authorization_ref = data.authorization_ref
        if data.description is not None:
            source.description = data.description
        if data.is_enabled is not None:
            source.is_enabled = data.is_enabled
            source.status = SourceStatus.ACTIVE if data.is_enabled else SourceStatus.DISABLED

        source.updated_at = utc_now()
        source.updated_by = updated_by

        # Handle credential rotation if new secret is passed
        if data.access_token is not None:
            if not source.credentials:
                source.credentials = SourceCredentialMetadata(
                    source_id=source.id,
                    encrypted_access_token="",
                    token_masked="",
                    created_by=updated_by
                )
            source.credentials.encrypted_access_token = encrypt_secret(data.access_token)
            source.credentials.token_masked = mask_token(data.access_token)
            source.credentials.updated_at = utc_now()
            source.credentials.updated_by = updated_by

        if data.app_id is not None and source.credentials:
            source.credentials.app_id_masked = mask_identifier(data.app_id)
        if data.app_secret is not None and source.credentials:
            source.credentials.encrypted_app_secret = encrypt_secret(data.app_secret)
        if data.token_scope is not None and source.credentials:
            source.credentials.token_scope = data.token_scope

        self.db.commit()
        self.db.refresh(source)
        return source

    def get_decrypted_credentials(self, source_id: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Internal-only method: Decrypts access token and app secret strictly for adapter invocation.
        Never expose the returned strings in APIs or logs.
        """
        source = self.get_source_with_relations(source_id)
        if not source or not source.credentials:
            return None, None

        raw_token = decrypt_secret(source.credentials.encrypted_access_token) if source.credentials.encrypted_access_token else None
        raw_secret = decrypt_secret(source.credentials.encrypted_app_secret) if source.credentials.encrypted_app_secret else None
        return raw_token, raw_secret

    def record_sync_success(
        self,
        source_id: str,
        items_count: int,
        last_item_id: Optional[str] = None,
        quota_used: int = 1,
        latency_ms: float = 0.0
    ) -> None:
        """Records successful synchronization telemetry."""
        now = utc_now()
        stmt = (
            update(SourceSyncStatus)
            .where(SourceSyncStatus.source_id == source_id)
            .values(
                last_sync_at=now,
                last_successful_sync_at=now,
                last_sync_status="SUCCESS",
                total_items_fetched=SourceSyncStatus.total_items_fetched + items_count,
                last_item_external_id=last_item_id,
                api_quota_used=SourceSyncStatus.api_quota_used + quota_used,
                api_latency_ms=latency_ms,
                updated_at=now
            )
        )
        self.db.execute(stmt)

        # Update source health status
        self.db.execute(
            update(SocialSource)
            .where(SocialSource.id == source_id)
            .values(health_status=SourceHealth.OPERATIONAL, updated_at=now)
        )
        self.db.commit()

    def record_sync_failure(
        self,
        source_id: str,
        error_code: str,
        error_message: str,
        http_status: Optional[int] = None,
        correlation_id: Optional[str] = None
    ) -> SourceError:
        """Records API error and updates source health to DEGRADED/ERROR."""
        now = utc_now()
        err = SourceError(
            source_id=source_id,
            timestamp=now,
            error_code=error_code,
            error_message=error_message,
            http_status_code=http_status,
            correlation_id=correlation_id
        )
        self.db.add(err)

        # Update sync status
        self.db.execute(
            update(SourceSyncStatus)
            .where(SourceSyncStatus.source_id == source_id)
            .values(
                last_sync_at=now,
                last_sync_status="FAILED",
                updated_at=now
            )
        )

        # Update source health
        health = SourceHealth.RATE_LIMITED if "RATE" in error_code.upper() else SourceHealth.DEGRADED
        self.db.execute(
            update(SocialSource)
            .where(SocialSource.id == source_id)
            .values(health_status=health, updated_at=now)
        )
        self.db.commit()
        return err

    def list_errors(self, source_id: str, limit: int = 50) -> List[SourceError]:
        """Lists recent error logs for a source."""
        stmt = (
            select(SourceError)
            .where(SourceError.source_id == source_id)
            .order_by(desc(SourceError.timestamp))
            .limit(min(limit, 100))
        )
        return list(self.db.execute(stmt).scalars().all())
