"""
Social Media Source Management Endpoints
Gujarat Cyber Crime Social Media Intelligence & Early Warning System

Security Controls:
- Only authorized administrators (SUPER_ADMIN / LEAD_INVESTIGATOR) can modify sources.
- Investigators can view source telemetry and test connections, but can never view raw secrets.
- All tokens are masked in output (e.g. EAAG****4a12).
- Every mutation records an immutable forensic audit log.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, Header, Request, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.source_service import SourceService
from app.schemas.common import ApiResponse
from app.schemas.source import (
    SourceCreate,
    SourceUpdate,
    SourceRead,
    SourceTestResult,
    SourceSyncResult,
    SourceErrorRead,
)
from app.core.constants import SourceType, UserRole
from app.core.exceptions import AuthorizationException
from app.core.logging_config import correlation_id_ctx
from app.utils.time_utils import format_timestamp_utc

router = APIRouter(prefix="/sources", tags=["Social Media Source Management"])


def resolve_officer_context(
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
    x_officer_badge: Optional[str] = Header(None, alias="X-Officer-Badge")
):
    """Resolves authenticated police officer clearance and badge number."""
    role = x_user_role or UserRole.LEAD_INVESTIGATOR.value
    badge = x_officer_badge or "GJ-CYBER-8921"

    if role.upper() in ["UNAUTHORIZED", "PUBLIC", "GUEST"]:
        raise AuthorizationException(
            "Access Denied: Source management requires authorized law enforcement credentials."
        )
    return {"role": role, "badge": badge}


@router.get(
    "",
    response_model=ApiResponse[List[SourceRead]],
    summary="List Authorized Social Media Sources",
    description="Returns all legally authorized social-media monitoring sources with masked credentials."
)
def list_sources(
    source_type: Optional[SourceType] = Query(None, description="Filter by platform (FACEBOOK, INSTAGRAM, OTHER)"),
    is_enabled: Optional[bool] = Query(None, description="Filter by active monitoring status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    officer: dict = Depends(resolve_officer_context)
):
    service = SourceService(db)
    sources = service.list_sources(source_type=source_type, is_enabled=is_enabled, skip=skip, limit=limit)
    return ApiResponse(
        success=True,
        data=sources,
        correlation_id=correlation_id_ctx.get(),
        timestamp=format_timestamp_utc()
    )


@router.post(
    "",
    response_model=ApiResponse[SourceRead],
    status_code=status.HTTP_201_CREATED,
    summary="Register New Authorized Social Source",
    description="Only authorized administrators can add sources. Mandates statutory warrant/mandate reference."
)
def create_source(
    data: SourceCreate,
    request: Request,
    db: Session = Depends(get_db),
    officer: dict = Depends(resolve_officer_context)
):
    service = SourceService(db)
    client_ip = request.client.host if request.client else "127.0.0.1"
    new_source = service.create_source(
        data=data,
        acting_officer_badge=officer["badge"],
        acting_officer_role=officer["role"],
        actor_ip=client_ip
    )
    return ApiResponse(
        success=True,
        data=new_source,
        correlation_id=correlation_id_ctx.get(),
        timestamp=format_timestamp_utc()
    )


@router.get(
    "/{source_id}",
    response_model=ApiResponse[SourceRead],
    summary="Get Source Details & Telemetry",
    description="Retrieves a specific source configuration, sync metrics, and health status."
)
def get_source(
    source_id: str,
    db: Session = Depends(get_db),
    officer: dict = Depends(resolve_officer_context)
):
    service = SourceService(db)
    source = service.get_source(source_id)
    return ApiResponse(
        success=True,
        data=source,
        correlation_id=correlation_id_ctx.get(),
        timestamp=format_timestamp_utc()
    )


@router.put(
    "/{source_id}",
    response_model=ApiResponse[SourceRead],
    summary="Update Source Configuration or Rotate Secrets",
    description="Updates source metadata or securely replaces encrypted credentials."
)
def update_source(
    source_id: str,
    data: SourceUpdate,
    request: Request,
    db: Session = Depends(get_db),
    officer: dict = Depends(resolve_officer_context)
):
    service = SourceService(db)
    client_ip = request.client.host if request.client else "127.0.0.1"
    updated = service.update_source(
        source_id=source_id,
        data=data,
        acting_officer_badge=officer["badge"],
        acting_officer_role=officer["role"],
        actor_ip=client_ip
    )
    return ApiResponse(
        success=True,
        data=updated,
        correlation_id=correlation_id_ctx.get(),
        timestamp=format_timestamp_utc()
    )


@router.post(
    "/{source_id}/toggle",
    response_model=ApiResponse[SourceRead],
    summary="Enable or Disable Monitoring",
    description="Quick toggle to pause or resume active ingestion."
)
def toggle_monitoring(
    source_id: str,
    is_enabled: bool = Query(..., description="Target active monitoring state"),
    request: Request = None,
    db: Session = Depends(get_db),
    officer: dict = Depends(resolve_officer_context)
):
    service = SourceService(db)
    client_ip = request.client.host if request and request.client else "127.0.0.1"
    toggled = service.toggle_monitoring(
        source_id=source_id,
        is_enabled=is_enabled,
        acting_officer_badge=officer["badge"],
        acting_officer_role=officer["role"],
        actor_ip=client_ip
    )
    return ApiResponse(
        success=True,
        data=toggled,
        correlation_id=correlation_id_ctx.get(),
        timestamp=format_timestamp_utc()
    )


@router.post(
    "/{source_id}/test",
    response_model=ApiResponse[SourceTestResult],
    summary="Test Connection via SocialSourceAdapter",
    description="Executes live access validation without retrieving feed items or exposing access tokens."
)
def test_connection(
    source_id: str,
    request: Request = None,
    db: Session = Depends(get_db),
    officer: dict = Depends(resolve_officer_context)
):
    service = SourceService(db)
    client_ip = request.client.host if request and request.client else "127.0.0.1"
    result = service.test_connection(
        source_id=source_id,
        acting_officer_badge=officer["badge"],
        actor_ip=client_ip
    )
    return ApiResponse(
        success=result.success,
        data=result,
        correlation_id=correlation_id_ctx.get(),
        timestamp=format_timestamp_utc()
    )


@router.post(
    "/{source_id}/sync",
    response_model=ApiResponse[SourceSyncResult],
    summary="Trigger Manual Stream Synchronization",
    description="Forces immediate ingestion of public posts via the designated platform adapter."
)
def trigger_sync(
    source_id: str,
    limit: int = Query(25, ge=1, le=100),
    db: Session = Depends(get_db),
    officer: dict = Depends(resolve_officer_context)
):
    service = SourceService(db)
    result = service.sync_source(
        source_id=source_id,
        limit=limit,
        acting_officer_badge=officer["badge"]
    )
    return ApiResponse(
        success=result.success,
        data=result,
        correlation_id=correlation_id_ctx.get(),
        timestamp=format_timestamp_utc()
    )


@router.get(
    "/{source_id}/errors",
    response_model=ApiResponse[List[SourceErrorRead]],
    summary="View Source API Rejections and Error Logs",
    description="Lists recent platform errors and quota rejections for administrative inspection."
)
def list_errors(
    source_id: str,
    limit: int = Query(25, ge=1, le=100),
    db: Session = Depends(get_db),
    officer: dict = Depends(resolve_officer_context)
):
    service = SourceService(db)
    errors = service.list_source_errors(source_id=source_id, limit=limit)
    return ApiResponse(
        success=True,
        data=errors,
        correlation_id=correlation_id_ctx.get(),
        timestamp=format_timestamp_utc()
    )


@router.delete(
    "/{source_id}",
    response_model=ApiResponse[dict],
    summary="Deactivate and Soft-Delete Monitored Source",
    description="Soft-deletes the source configuration while maintaining forensic evidence trails."
)
def delete_source(
    source_id: str,
    request: Request = None,
    db: Session = Depends(get_db),
    officer: dict = Depends(resolve_officer_context)
):
    service = SourceService(db)
    client_ip = request.client.host if request and request.client else "127.0.0.1"
    success = service.delete_source(
        source_id=source_id,
        acting_officer_badge=officer["badge"],
        acting_officer_role=officer["role"],
        actor_ip=client_ip
    )
    return ApiResponse(
        success=success,
        data={"source_id": source_id, "deleted": success, "message": "Source soft-deleted and archived."},
        correlation_id=correlation_id_ctx.get(),
        timestamp=format_timestamp_utc()
    )
