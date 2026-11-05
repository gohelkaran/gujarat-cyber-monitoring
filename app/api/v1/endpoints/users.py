"""
User & Officer Management API Endpoints
Gujarat Cyber Crime Social Media Intelligence & Early Warning System
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Header, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.core.constants import UserRole, AuditAction
from app.models.user import User
from app.schemas.common import ApiResponse
from app.services.audit_service import AuditService
from app.core.logging_config import get_logger

logger = get_logger("user_endpoints")
router = APIRouter(prefix="/users", tags=["Officer & User Management"])


class OfficerCreatePayload(BaseModel):
    badge_number: str = Field(..., description="Official badge number e.g. GJ-CYBER-1024")
    full_name: str = Field(..., description="Full officer name e.g. PI M. B. Jadeja")
    email: str = Field(..., description="Official government email")
    role: UserRole = Field(default=UserRole.CYBER_ANALYST, description="Assigned role")
    password: str = Field(default="GujaratPolice@2026", description="Initial temp password")


class OfficerUpdateStatusPayload(BaseModel):
    is_active: bool = Field(..., description="Account active status")


@router.get("", response_model=ApiResponse[List[Dict[str, Any]]])
def list_officers(
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
    db: Session = Depends(get_db)
):
    """
    Lists all registered police officers, analysts, and administrators.
    Used by Administrators to maintain officer accounts.
    """
    users = db.query(User).filter_by(is_deleted=False).order_by(User.id.asc()).all()
    out = []
    for u in users:
        role_str = u.role.value if hasattr(u.role, "value") else str(u.role)
        out.append({
            "id": u.id,
            "badge_number": u.badge_number,
            "full_name": u.full_name,
            "email": u.email,
            "role": role_str,
            "is_active": u.is_active,
            "last_login_at": u.last_login_at.isoformat() if u.last_login_at else None,
            "created_at": u.created_at.isoformat() if u.created_at else None
        })
    return ApiResponse.success_response(data=out, message=f"Retrieved {len(out)} officer accounts.")


@router.post("", response_model=ApiResponse[Dict[str, Any]])
def create_officer(
    payload: OfficerCreatePayload,
    request: Request,
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
    db: Session = Depends(get_db)
):
    """
    Registers a new police officer or cyber analyst account.
    Restricted to Administrator role.
    """
    existing = db.query(User).filter(
        (User.badge_number == payload.badge_number) | (User.email == payload.email)
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Officer with this badge number or email already exists."
        )

    from app.security.hashing import hash_password
    hashed = hash_password(payload.password)

    new_user = User(
        badge_number=payload.badge_number.strip().upper(),
        full_name=payload.full_name.strip(),
        email=payload.email.strip().lower(),
        hashed_password=hashed,
        role=payload.role,
        is_active=True
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    actor_ip = request.client.host if request and hasattr(request, "client") and request.client else "127.0.0.1"
    AuditService(db).log_event(
        action=AuditAction.USER_CREATE,
        actor_id=x_user_role or "SUPER_ADMIN",
        actor_role=UserRole.SUPER_ADMIN.value,
        actor_ip=actor_ip,
        resource_type="USER",
        resource_id=new_user.badge_number,
        details={"badge": new_user.badge_number, "role": new_user.role.value if hasattr(new_user.role, 'value') else str(new_user.role)}
    )

    return ApiResponse.success_response(
        data={"badge_number": new_user.badge_number, "full_name": new_user.full_name, "role": str(new_user.role)},
        message=f"Officer account {new_user.badge_number} created successfully."
    )


@router.patch("/{badge_number}/status", response_model=ApiResponse[Dict[str, Any]])
def toggle_officer_status(
    badge_number: str,
    payload: OfficerUpdateStatusPayload,
    request: Request,
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
    db: Session = Depends(get_db)
):
    """
    Activates or deactivates an officer account.
    """
    user = db.query(User).filter(User.badge_number == badge_number.strip().upper()).first()
    if not user:
        raise HTTPException(status_code=404, detail="Officer not found.")

    user.is_active = payload.is_active
    db.commit()

    actor_ip = request.client.host if request and hasattr(request, "client") and request.client else "127.0.0.1"
    AuditService(db).log_event(
        action=AuditAction.USER_UPDATE,
        actor_id=x_user_role or "SUPER_ADMIN",
        actor_role=UserRole.SUPER_ADMIN.value,
        actor_ip=actor_ip,
        resource_type="USER",
        resource_id=user.badge_number,
        details={"status_updated": user.is_active}
    )

    return ApiResponse.success_response(
        data={"badge_number": user.badge_number, "is_active": user.is_active},
        message=f"Officer {user.badge_number} status updated to {'Active' if user.is_active else 'Deactivated'}."
    )
