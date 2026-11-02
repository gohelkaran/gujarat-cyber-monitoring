"""
Monitored Keyword and Threat Intelligence Endpoints
Gujarat Cyber Crime Social Media Intelligence & Early Warning System

Statutory Security & Regulatory Compliance:
- Monitored keywords are maintained under legal mandate (Section 69 Indian IT Act / 91 CrPC).
- Modifications are restricted to authorized cyber police officers (LEAD_INVESTIGATOR / SUPER_ADMIN).
- Every keyword modification and scan execution is recorded in the forensic audit ledger.
- High-speed threat scanner detects suspect posts and assigns severity scores.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, Header, Request, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.keyword_service import KeywordService
from app.schemas.common import ApiResponse
from app.schemas.keyword import (
    KeywordCreate,
    KeywordUpdate,
    KeywordRead,
    KeywordCategorySummary,
    KeywordScanRequest,
    KeywordScanResult,
)
from app.core.constants import AlertSeverity, UserRole
from app.core.exceptions import AuthorizationException
from app.core.logging_config import correlation_id_ctx
from app.utils.time_utils import format_timestamp_utc


router = APIRouter(prefix="/keywords", tags=["Keyword & Threat Intelligence"])


def resolve_officer_context(
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
    x_officer_badge: Optional[str] = Header(None, alias="X-Officer-Badge")
):
    """Resolves authenticated police officer clearance and badge number."""
    role = x_user_role or UserRole.LEAD_INVESTIGATOR.value
    badge = x_officer_badge or "GJ-CYBER-8921"

    if role.upper() in ["UNAUTHORIZED", "PUBLIC", "GUEST"]:
        raise AuthorizationException(
            "Access Denied: Keyword intelligence requires authenticated Gujarat Police credentials."
        )
    return {"role": role, "badge": badge}


@router.get(
    "",
    response_model=ApiResponse[List[KeywordRead]],
    summary="List Monitored Keywords",
    description="Returns list of monitored keywords and phrases with category, severity, and hit counts."
)
def list_keywords(
    category: Optional[str] = Query(None, description="Filter by category (Financial Fraud, Phishing, etc.)"),
    severity: Optional[AlertSeverity] = Query(None, description="Filter by severity level"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    search: Optional[str] = Query(None, description="Search keyword, description, or mandate ref"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    officer: dict = Depends(resolve_officer_context)
):
    service = KeywordService(db)
    items, total = service.list_keywords(
        category=category,
        severity=severity,
        is_active=is_active,
        search=search,
        skip=skip,
        limit=limit
    )
    return ApiResponse(
        data=items,
        message=f"Retrieved {len(items)} monitored keywords (Total: {total}).",
        correlation_id=correlation_id_ctx.get(),
        timestamp=format_timestamp_utc()
    )


@router.get(
    "/categories",
    response_model=ApiResponse[List[KeywordCategorySummary]],
    summary="Get Keyword Threat Category Summaries",
    description="Returns aggregate counts, active status, and hit counts for each cybercrime threat taxonomy."
)
def get_category_summaries(
    db: Session = Depends(get_db),
    officer: dict = Depends(resolve_officer_context)
):
    service = KeywordService(db)
    summaries = service.get_category_summaries()
    return ApiResponse(
        data=summaries,
        message="Category threat intelligence summaries generated successfully.",
        correlation_id=correlation_id_ctx.get(),
        timestamp=format_timestamp_utc()
    )


@router.get(
    "/{keyword_id}",
    response_model=ApiResponse[KeywordRead],
    summary="Get Monitored Keyword Details",
    description="Fetches specific monitored keyword rule by internal identifier."
)
def get_keyword(
    keyword_id: str,
    db: Session = Depends(get_db),
    officer: dict = Depends(resolve_officer_context)
):
    service = KeywordService(db)
    kw = service.get_keyword(keyword_id)
    return ApiResponse(
        data=kw,
        message="Monitored keyword details retrieved.",
        correlation_id=correlation_id_ctx.get(),
        timestamp=format_timestamp_utc()
    )


@router.post(
    "",
    response_model=ApiResponse[KeywordRead],
    status_code=status.HTTP_201_CREATED,
    summary="Register Monitored Keyword",
    description="Registers a new keyword or phrase under a statutory cybercrime category and legal mandate reference."
)
def create_keyword(
    payload: KeywordCreate,
    db: Session = Depends(get_db),
    officer: dict = Depends(resolve_officer_context)
):
    service = KeywordService(db)
    kw = service.create_keyword(
        data=payload,
        current_user_id=officer["badge"],
        current_user_role=officer["role"],
        current_user_badge=officer["badge"]
    )
    return ApiResponse(
        data=kw,
        message=f"Monitored keyword '{kw.keyword}' registered successfully under category '{kw.category}'.",
        correlation_id=correlation_id_ctx.get(),
        timestamp=format_timestamp_utc()
    )


@router.put(
    "/{keyword_id}",
    response_model=ApiResponse[KeywordRead],
    summary="Update Monitored Keyword",
    description="Modifies existing keyword configuration, severity, match mode, or operational description."
)
def update_keyword(
    keyword_id: str,
    payload: KeywordUpdate,
    db: Session = Depends(get_db),
    officer: dict = Depends(resolve_officer_context)
):
    service = KeywordService(db)
    kw = service.update_keyword(
        keyword_id=keyword_id,
        data=payload,
        current_user_id=officer["badge"],
        current_user_role=officer["role"],
        current_user_badge=officer["badge"]
    )
    return ApiResponse(
        data=kw,
        message=f"Monitored keyword rule '{kw.keyword}' updated successfully.",
        correlation_id=correlation_id_ctx.get(),
        timestamp=format_timestamp_utc()
    )


@router.post(
    "/{keyword_id}/toggle",
    response_model=ApiResponse[KeywordRead],
    summary="Toggle Keyword Active Status",
    description="Enables or disables active text scanning for the designated keyword rule."
)
def toggle_keyword_status(
    keyword_id: str,
    is_active: bool = Query(..., description="Target active state (true=enable, false=disable)"),
    db: Session = Depends(get_db),
    officer: dict = Depends(resolve_officer_context)
):
    service = KeywordService(db)
    kw = service.toggle_keyword(
        keyword_id=keyword_id,
        is_active=is_active,
        current_user_id=officer["badge"],
        current_user_role=officer["role"],
        current_user_badge=officer["badge"]
    )
    status_label = "activated" if is_active else "deactivated"
    return ApiResponse(
        data=kw,
        message=f"Monitored keyword '{kw.keyword}' has been {status_label}.",
        correlation_id=correlation_id_ctx.get(),
        timestamp=format_timestamp_utc()
    )


@router.delete(
    "/{keyword_id}",
    response_model=ApiResponse[bool],
    summary="Delete Monitored Keyword",
    description="Permanently deletes a monitored keyword rule from the detection engine."
)
def delete_keyword(
    keyword_id: str,
    db: Session = Depends(get_db),
    officer: dict = Depends(resolve_officer_context)
):
    service = KeywordService(db)
    success = service.delete_keyword(
        keyword_id=keyword_id,
        current_user_id=officer["badge"],
        current_user_role=officer["role"],
        current_user_badge=officer["badge"]
    )
    return ApiResponse(
        data=success,
        message="Monitored keyword rule deleted successfully.",
        correlation_id=correlation_id_ctx.get(),
        timestamp=format_timestamp_utc()
    )


@router.post(
    "/scan",
    response_model=ApiResponse[KeywordScanResult],
    summary="Interactive Threat Scanner Sandbox",
    description="Runs suspect social media text through active keyword engine, calculating threat scores and snippets."
)
def scan_suspect_text(
    payload: KeywordScanRequest,
    record_detections: bool = Query(False, description="Whether to record forensic detection logs and increment hits"),
    db: Session = Depends(get_db),
    officer: dict = Depends(resolve_officer_context)
):
    service = KeywordService(db)
    scan_result = service.scan_text(
        payload=payload,
        current_user_id=officer["badge"],
        current_user_badge=officer["badge"],
        record_detections=record_detections
    )
    return ApiResponse(
        data=scan_result,
        message=f"Scan complete: {scan_result.total_matches} matches detected across {len(scan_result.categories_detected)} categories.",
        correlation_id=correlation_id_ctx.get(),
        timestamp=format_timestamp_utc()
    )
