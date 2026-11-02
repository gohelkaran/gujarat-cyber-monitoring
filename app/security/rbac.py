"""
Role-Based Access Control (RBAC) & Clearance Engine
Gujarat Cyber Crime Social Media Intelligence & Early Warning System
"""

from typing import List, Callable
from fastapi import Depends
from app.core.constants import UserRole, DataClassification
from app.core.exceptions import AuthorizationException
from app.schemas.user import UserRead


# Role hierarchy score: higher number = greater privilege
ROLE_HIERARCHY = {
    UserRole.CYBER_ANALYST: 1,
    UserRole.LEAD_INVESTIGATOR: 2,
    UserRole.AUDITOR: 2,  # Specialized compliance role
    UserRole.NODAL_OFFICER: 3,
    UserRole.SUPER_ADMIN: 4,
}

# Data classification hierarchy score
CLASSIFICATION_LEVELS = {
    DataClassification.UNCLASSIFIED: 0,
    DataClassification.RESTRICTED: 1,
    DataClassification.CONFIDENTIAL: 2,
    DataClassification.SECRET: 3,
}

# Minimum role required to access each classification tier
CLASSIFICATION_CLEARANCE_MAP = {
    DataClassification.UNCLASSIFIED: UserRole.CYBER_ANALYST,
    DataClassification.RESTRICTED: UserRole.CYBER_ANALYST,
    DataClassification.CONFIDENTIAL: UserRole.LEAD_INVESTIGATOR,
    DataClassification.SECRET: UserRole.NODAL_OFFICER,
}


def has_sufficient_role(user_role: UserRole, required_role: UserRole) -> bool:
    """Verifies if the given user role meets or exceeds required authority."""
    return ROLE_HIERARCHY.get(user_role, 0) >= ROLE_HIERARCHY.get(required_role, 0)


def require_role(required_role: UserRole) -> Callable:
    """
    FastAPI dependency factory enforcing a minimum role level.
    Usage:
        @router.get("/admin", dependencies=[Depends(require_role(UserRole.SUPER_ADMIN))])
    """
    def role_checker(current_user: UserRead = None):
        # When auth is implemented, current_user will be resolved via OAuth2/JWT dependency
        if current_user is None:
            # During foundation prototype without active session, verify or allow development passthrough
            return True

        if not has_sufficient_role(current_user.role, required_role):
            raise AuthorizationException(
                f"Action requires minimum role of '{required_role.value}'. Current role: '{current_user.role.value}'."
            )
        return True

    return role_checker


def require_clearance(target_classification: DataClassification) -> Callable:
    """FastAPI dependency factory ensuring user meets minimum data classification clearance."""
    def clearance_checker(current_user: UserRead = None):
        if current_user is None:
            return True

        required_min_role = CLASSIFICATION_CLEARANCE_MAP[target_classification]
        if not has_sufficient_role(current_user.role, required_min_role):
            raise AuthorizationException(
                f"Access denied. Data classification level '{target_classification.value}' requires clearance level of '{required_min_role.value}'."
            )
        return True

    return clearance_checker
