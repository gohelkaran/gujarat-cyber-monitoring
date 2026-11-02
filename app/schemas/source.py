"""
Social Source Management Pydantic Schemas
Gujarat Cyber Crime Social Media Intelligence & Early Warning System

Security Guarantee:
- Access tokens and client secrets are write-only inputs.
- Read schemas strictly expose masked tokens (e.g. EAAG****4a12) and masked App IDs.
- Raw decrypted secrets are never transmitted over API responses.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from app.core.constants import SourceType, SourceStatus, SourceHealth, DataClassification
from app.integrations.adapters.base import AdapterStatus


class SourceBase(BaseModel):
    name: str = Field(..., max_length=150, example="Ahmedabad City Police Public Facebook Monitor")
    source_type: SourceType = Field(..., example=SourceType.FACEBOOK)
    target_identifier: str = Field(..., max_length=255, example="AhmedabadCityPoliceOfficial", description="Public Page ID, Instagram Handle, or Channel ID")
    authorization_ref: str = Field(..., max_length=100, example="DGP-CYBER-MANDATE-2026-081", description="Statutory legal warrant, FIR, or administrative sanction reference")
    authorized_by_badge: str = Field(..., max_length=50, example="GJ-CYBER-8921", description="Badge number of senior authorizing officer")
    description: Optional[str] = Field(None, example="Authorized monitoring of public police advisory page and public complaints comments stream.")


class SourceCreate(SourceBase):
    """Write-only input payload for registering an authorized source."""
    access_token: Optional[str] = Field(None, description="API Access token (immediately encrypted at rest)")
    app_id: Optional[str] = Field(None, description="Platform App / Client ID")
    app_secret: Optional[str] = Field(None, description="Platform App Secret (immediately encrypted at rest)")
    token_scope: Optional[List[str]] = Field(default_factory=list, example=["pages_read_engagement", "public_profile"])
    classification_level: DataClassification = DataClassification.RESTRICTED


class SourceUpdate(BaseModel):
    """Update payload for modifying source parameters or rotating credentials."""
    name: Optional[str] = Field(None, max_length=150)
    target_identifier: Optional[str] = Field(None, max_length=255)
    authorization_ref: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    is_enabled: Optional[bool] = None
    access_token: Optional[str] = Field(None, description="Optional new token to rotate")
    app_id: Optional[str] = None
    app_secret: Optional[str] = None
    token_scope: Optional[List[str]] = None


class SourceCredentialRead(BaseModel):
    """Safe, masked credential metadata returned to authorized administrators."""
    app_id_masked: Optional[str] = None
    token_masked: str = Field(..., example="EAAG****4a12")
    token_scope: Optional[List[str]] = None
    token_expires_at: Optional[datetime] = None
    key_version: str = "v1"

    model_config = {"from_attributes": True}


class SourceSyncRead(BaseModel):
    """Last synchronization metrics."""
    last_sync_at: Optional[datetime] = None
    last_successful_sync_at: Optional[datetime] = None
    last_sync_status: str = "NEVER_RUN"
    total_items_fetched: int = 0
    api_quota_used: int = 0
    api_quota_limit: int = 200
    api_latency_ms: float = 0.0

    model_config = {"from_attributes": True}


class SourceErrorRead(BaseModel):
    """Error event record."""
    id: str
    timestamp: datetime
    error_code: str
    error_message: str
    http_status_code: Optional[int] = None
    is_resolved: bool = False

    model_config = {"from_attributes": True}


class SourceRead(SourceBase):
    """Full safe read model for an authorized source."""
    id: str
    status: SourceStatus
    is_enabled: bool
    health_status: SourceHealth
    credentials: Optional[SourceCredentialRead] = None
    sync_status: Optional[SourceSyncRead] = None
    recent_errors_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SourceTestResult(BaseModel):
    """Result of an on-demand API connection verification."""
    source_id: str
    source_name: str
    success: bool
    adapter_status: AdapterStatus
    timestamp: str


class SourceSyncResult(BaseModel):
    """Result of an on-demand feed synchronization."""
    source_id: str
    source_name: str
    success: bool
    items_synced: int
    duration_ms: float
    last_status: str
    timestamp: str
