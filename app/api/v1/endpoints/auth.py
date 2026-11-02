"""
Authentication and Authorization Endpoints
Gujarat Cyber Crime Social Media Intelligence & Early Warning System
"""

from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.constants import AuditAction, UserRole
from app.core.exceptions import AuthenticationException, AuthorizationException
from app.models.user import User
from app.models.audit_log import AuditEvent
from app.schemas.user import LoginRequest, TokenResponse, UserRead
from app.schemas.common import ApiResponse
from app.security.hashing import verify_password, hash_password
from app.security.jwt import create_access_token, get_current_user
from app.services.audit_service import AuditService
from app.config.settings import get_settings

router = APIRouter(prefix="/auth", tags=["Authentication"])
settings = get_settings()

MAX_FAILED_ATTEMPTS = 5


def seed_default_users_if_empty(db: Session):
    """Ensures baseline authorized officer accounts exist for prototype operation."""
    if db.query(User).count() == 0:
        default_officers = [
            {
                "badge_number": "GJ-CYBER-8921",
                "full_name": "Insp. R. K. Vala",
                "email": "rk.vala@gujaratpolice.gov.in",
                "password": "Password@12345",
                "role": UserRole.LEAD_INVESTIGATOR,
                "department": "Gujarat State Cyber Crime Cell, CID Crime, Gandhinagar",
                "designation": "Police Inspector & Cyber Intelligence Lead",
            },
            {
                "badge_number": "GJ-CYBER-7410",
                "full_name": "Analyst P. M. Dave",
                "email": "pm.dave@gujaratpolice.gov.in",
                "password": "Password@12345",
                "role": UserRole.CYBER_ANALYST,
                "department": "Gujarat State Cyber Crime Cell, Ahmedabad",
                "designation": "Cyber Intelligence Analyst",
            },
            {
                "badge_number": "GJ-CYBER-0012",
                "full_name": "SP Cyber CID",
                "email": "sp.cyber@gujaratpolice.gov.in",
                "password": "Password@12345",
                "role": UserRole.NODAL_OFFICER,
                "department": "CID Crime Headquarters, Gandhinagar",
                "designation": "Superintendent of Police",
            },
            {
                "badge_number": "GJ-AUDIT-004",
                "full_name": "Auditor V. G. Patel",
                "email": "vg.patel@gujaratpolice.gov.in",
                "password": "Password@12345",
                "role": UserRole.AUDITOR,
                "department": "Home Department Oversight & Cyber Compliance",
                "designation": "State Cyber Compliance Auditor",
            },
        ]
        for officer_data in default_officers:
            pwd = officer_data.pop("password")
            user = User(
                **officer_data,
                hashed_password=hash_password(pwd),
                is_active=True,
                is_locked=False,
                failed_login_attempts=0
            )
            db.add(user)
        db.commit()


@router.post("/login", response_model=ApiResponse[TokenResponse])
def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
):
    """
    Authenticates authorized law enforcement officer.
    Enforces account lockout policy and forensic audit logging.
    """
    seed_default_users_if_empty(db)
    audit = AuditService(db)

    identifier = payload.username_or_badge.strip()
    client_ip = request.client.host if request.client else "127.0.0.1"
    user_agent = request.headers.get("user-agent", "Unknown")

    user = db.query(User).filter(
        (User.badge_number == identifier) | (User.email == identifier)
    ).first()

    if not user:
        audit.log_security_event(
            actor_id=identifier,
            actor_role="UNKNOWN",
            actor_ip=client_ip,
            actor_user_agent=user_agent,
            action=AuditAction.AUTH_LOGIN_FAILURE,
            resource_type="auth",
            resource_id=identifier,
            status="REJECTED",
            details={"reason": "User not found"}
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid service credentials or badge number."
        )

    if user.is_locked:
        audit.log_security_event(
            actor_id=user.badge_number,
            actor_role=user.role.value,
            actor_ip=client_ip,
            actor_user_agent=user_agent,
            action=AuditAction.SECURITY_VIOLATION,
            resource_type="auth",
            resource_id=user.id,
            status="LOCKED",
            details={"reason": "Attempt on locked account"}
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is locked due to security policy. Please contact CID Cyber Administrator."
        )

    if not verify_password(payload.password, user.hashed_password):
        user.failed_login_attempts += 1
        if user.failed_login_attempts >= MAX_FAILED_ATTEMPTS:
            user.is_locked = True
            db.commit()
            audit.log_security_event(
                actor_id=user.badge_number,
                actor_role=user.role.value,
                actor_ip=client_ip,
                actor_user_agent=user_agent,
                action=AuditAction.SECURITY_VIOLATION,
                resource_type="auth",
                resource_id=user.id,
                status="ACCOUNT_LOCKED",
                details={"failed_attempts": user.failed_login_attempts}
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Too many failed login attempts. Account has been securely locked."
            )

        db.commit()
        audit.log_security_event(
            actor_id=user.badge_number,
            actor_role=user.role.value,
            actor_ip=client_ip,
            actor_user_agent=user_agent,
            action=AuditAction.AUTH_LOGIN_FAILURE,
            resource_type="auth",
            resource_id=user.id,
            status="FAILED_PASSWORD",
            details={"attempt": user.failed_login_attempts}
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid service credentials or password."
        )

    # Reset failed attempts and record successful login
    user.failed_login_attempts = 0
    user.last_login_at = datetime.now(timezone.utc)
    db.commit()

    # Create signed token
    access_token = create_access_token({
        "sub": user.id,
        "badge": user.badge_number,
        "role": user.role.value,
        "email": user.email,
        "name": user.full_name
    })

    # Set secure cookie
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        samesite="lax",
        secure=settings.ENFORCE_SSL
    )

    audit.log_security_event(
        actor_id=user.badge_number,
        actor_role=user.role.value,
        actor_ip=client_ip,
        actor_user_agent=user_agent,
        action=AuditAction.AUTH_LOGIN_SUCCESS,
        resource_type="auth",
        resource_id=user.id,
        status="SUCCESS",
        details={"department": user.department}
    )

    return ApiResponse.success_response(
        data=TokenResponse(
            access_token=access_token,
            expires_in_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
            user=UserRead.model_validate(user)
        ),
        message=f"Officer {user.full_name} authenticated successfully."
    )


@router.get("/me", response_model=ApiResponse[UserRead])
def get_me(current_user: User = Depends(get_current_user)):
    """Retrieves profile of the currently authenticated officer."""
    return ApiResponse.success_response(
        data=UserRead.model_validate(current_user),
        message="Active profile session verified."
    )


@router.post("/logout", response_model=ApiResponse[dict])
def logout(
    request: Request,
    response: Response,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Terminates session and records logout audit log."""
    response.delete_cookie("access_token")
    audit = AuditService(db)
    audit.log_security_event(
        actor_id=current_user.badge_number,
        actor_role=current_user.role.value,
        actor_ip=request.client.host if request.client else "127.0.0.1",
        actor_user_agent=request.headers.get("user-agent", "Unknown"),
        action=AuditAction.AUTH_LOGOUT,
        resource_type="auth",
        resource_id=current_user.id,
        status="SUCCESS",
        details={"message": "Logged out successfully"}
    )
    return ApiResponse.success_response(
        data={"logged_out": True},
        message="Session revoked successfully."
    )

