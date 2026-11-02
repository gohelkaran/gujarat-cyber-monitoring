"""
Health and Liveness Check Endpoints
Gujarat Cyber Crime Social Media Intelligence & Early Warning System
"""

from fastapi import APIRouter, Depends, status, Response
from sqlalchemy.orm import Session
from app.core.database import get_db, check_database_connection
from app.services.health_service import HealthService
from app.schemas.common import ApiResponse, HealthResponse
from app.core.logging_config import correlation_id_ctx
from app.utils.time_utils import format_timestamp_utc

router = APIRouter(prefix="/health", tags=["Health & Diagnostics"])


@router.get(
    "",
    response_model=ApiResponse[HealthResponse],
    summary="Comprehensive Subsystem Health Status",
    description="Inspects database pooling, storage availability, and operational metrics."
)
def get_full_health(db: Session = Depends(get_db)):
    service = HealthService(db)
    health = service.get_system_health()
    return ApiResponse(
        success=(health.status == "HEALTHY"),
        data=health,
        correlation_id=correlation_id_ctx.get(),
        timestamp=format_timestamp_utc(),
    )


@router.get(
    "/live",
    summary="Liveness Probe",
    description="Low-overhead probe for orchestrator container liveness checks."
)
def liveness_probe():
    return {
        "status": "UP",
        "correlation_id": correlation_id_ctx.get(),
        "timestamp": format_timestamp_utc()
    }


@router.get(
    "/ready",
    summary="Readiness Probe",
    description="Verifies database responsiveness before traffic routing."
)
def readiness_probe(response: Response):
    db_check = check_database_connection()
    if db_check.get("status") != "UP":
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {
            "status": "NOT_READY",
            "reason": db_check.get("message"),
            "correlation_id": correlation_id_ctx.get()
        }
    return {
        "status": "READY",
        "correlation_id": correlation_id_ctx.get(),
        "timestamp": format_timestamp_utc()
    }
