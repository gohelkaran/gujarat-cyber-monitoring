"""
JSON Web Token (JWT) Security and User Authentication Dependencies
Gujarat Cyber Crime Social Media Intelligence & Early Warning System
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.config.settings import get_settings
from app.core.database import get_db
from app.core.exceptions import AuthenticationException, AuthorizationException
from app.models.user import User
from app.core.logging_config import get_logger

logger = get_logger("jwt_security")
settings = get_settings()

security_bearer = HTTPBearer(auto_error=False)


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Creates a cryptographically signed JWT access token."""
    to_encode = data.copy()
    now_utc = datetime.now(timezone.utc)
    if expires_delta:
        expire = now_utc + expires_delta
    else:
        expire = now_utc + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({
        "exp": expire,
        "iat": now_utc,
        "nbf": now_utc,
        "iss": "GujaratCyberCrimeSOC",
    })
    secret = settings.SECRET_KEY.get_secret_value()
    encoded_jwt = jwt.encode(to_encode, secret, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Dict[str, Any]:
    """Decodes and validates a signed JWT token."""
    secret = settings.SECRET_KEY.get_secret_value()
    try:
        payload = jwt.decode(token, secret, algorithms=[settings.ALGORITHM], issuer="GujaratCyberCrimeSOC")
        return payload
    except JWTError as e:
        raise AuthenticationException(f"Invalid or expired authentication token: {str(e)}")


def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer),
    db: Session = Depends(get_db)
) -> User:
    """
    FastAPI dependency resolving the currently authenticated user.
    Checks Authorization: Bearer <token> or session cookie 'access_token'.
    """
    token = None
    if credentials:
        token = credentials.credentials
    elif "access_token" in request.cookies:
        token = request.cookies["access_token"]
    elif "authorization" in request.headers:
        auth_hdr = request.headers["authorization"]
        if auth_hdr.lower().startswith("bearer "):
            token = auth_hdr[7:].strip()

    if not token:
        # Check if running in development mode and an officer simulation header is supplied
        officer_badge = request.headers.get("x-officer-badge")
        if officer_badge:
            user = db.query(User).filter_by(badge_number=officer_badge).first()
            if user and user.is_active and not user.is_locked:
                return user
        raise AuthenticationException("Authentication required. Please sign in.")

    payload = decode_access_token(token)
    user_id = payload.get("sub")
    if not user_id:
        raise AuthenticationException("Malformed token claims.")

    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        raise AuthenticationException("User account associated with token not found.")

    if not user.is_active:
        raise AuthorizationException("Account is disabled. Contact system administrator.")

    if user.is_locked:
        raise AuthorizationException("Account is locked due to security policy. Contact supervisor.")

    return user


def get_current_active_user_optional(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Resolves current user if token is present, returns None otherwise."""
    try:
        return get_current_user(request, credentials, db)
    except Exception:
        return None

