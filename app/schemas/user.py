"""
User Identity Pydantic Schemas
Gujarat Cyber Crime Social Media Intelligence & Early Warning System
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from app.core.constants import UserRole, DataClassification


class UserBase(BaseModel):
    badge_number: str = Field(..., max_length=50, example="GJ-CYBER-8921")
    full_name: str = Field(..., max_length=150, example="K. V. Jadeja")
    email: str = Field(..., max_length=255, pattern=r"^[\w\.-]+@[\w\.-]+\.\w+$", example="kv.jadeja@gujaratpolice.gov.in")
    role: UserRole = Field(default=UserRole.CYBER_ANALYST)
    department: str = Field(default="Gujarat State Cyber Crime Cell, CID Crime, Gandhinagar")
    designation: str = Field(default="Cyber Crime Officer")


class UserCreate(UserBase):
    password: str = Field(..., min_length=12, description="Strong password adhering to police IT policy")
    classification_level: DataClassification = DataClassification.RESTRICTED


class UserRead(UserBase):
    id: str
    is_active: bool
    is_locked: bool
    last_login_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class LoginRequest(BaseModel):
    username_or_badge: str = Field(..., description="Badge number or official email address")
    password: str = Field(..., description="User password")


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in_minutes: int
    user: UserRead

