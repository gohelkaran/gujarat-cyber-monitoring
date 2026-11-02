"""
Audit Log Pydantic Schemas
Gujarat Cyber Crime Social Media Intelligence & Early Warning System
"""

from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from app.core.constants import AuditAction, DataClassification


class AuditEventCreate(BaseModel):
    """Schema for recording a new forensic audit event."""
    actor_id: Optional[str] = Field(None, max_length=100)
    actor_role: Optional[str] = Field(None, max_length=50)
    actor_ip: Optional[str] = Field(None, max_length=45)
    actor_user_agent: Optional[str] = Field(None, max_length=255)
    action: AuditAction
    resource_type: Optional[str] = Field(None, max_length=100)
    resource_id: Optional[str] = Field(None, max_length=100)
    details: Optional[Dict[str, Any]] = None
    correlation_id: Optional[str] = Field(None, max_length=64)
    classification_level: DataClassification = DataClassification.RESTRICTED


class AuditEventRead(BaseModel):
    """Schema for reading audit event records."""
    id: str
    timestamp: datetime
    actor_id: Optional[str]
    actor_role: Optional[str]
    actor_ip: Optional[str]
    action: AuditAction
    resource_type: Optional[str]
    resource_id: Optional[str]
    details: Optional[Dict[str, Any]]
    correlation_id: Optional[str]
    classification_level: DataClassification

    model_config = {"from_attributes": True}
