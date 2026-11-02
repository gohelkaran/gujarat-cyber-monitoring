"""
Monitored Keyword and Threat Intelligence Schemas
Gujarat Cyber Crime Social Media Intelligence & Early Warning System
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from app.core.constants import AlertSeverity, KeywordCategory, KeywordMatchType


class KeywordBase(BaseModel):
    keyword: str = Field(..., min_length=2, max_length=150, description="Keyword or phrase pattern")
    category: str = Field(default=KeywordCategory.FINANCIAL_FRAUD.value, max_length=60, description="Threat taxonomy category")
    severity: AlertSeverity = Field(default=AlertSeverity.HIGH, description="Threat severity weighting")
    match_type: KeywordMatchType = Field(default=KeywordMatchType.PHRASE, description="Matching mode")
    language: str = Field(default="en", max_length=20, description="Language code")
    description: Optional[str] = Field(None, description="Investigative context or scam MO briefing")
    authorization_ref: str = Field(..., max_length=100, description="Statutory legal mandate or case sanction reference")


class KeywordCreate(KeywordBase):
    """Payload for registering a new monitored keyword."""
    authorizing_officer_badge: str = Field(..., max_length=50, description="Authorizing officer badge")


class KeywordUpdate(BaseModel):
    """Payload for updating an existing monitored keyword."""
    keyword: Optional[str] = Field(None, min_length=2, max_length=150)
    category: Optional[str] = Field(None, max_length=60)
    severity: Optional[AlertSeverity] = None
    match_type: Optional[KeywordMatchType] = None
    is_active: Optional[bool] = None
    language: Optional[str] = None
    description: Optional[str] = None
    authorization_ref: Optional[str] = None


class KeywordRead(KeywordBase):
    """Read model for monitored keyword."""
    id: str
    is_active: bool
    created_by_badge: str
    hits_count: int = 0
    last_detected_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class KeywordCategorySummary(BaseModel):
    """Statistical summary of cybercrime categories."""
    category: str
    total_keywords: int
    active_keywords: int
    total_hits: int
    sample_keywords: List[str]


class KeywordScanRequest(BaseModel):
    """Input payload for testing suspect text against keyword engine."""
    text: str = Field(..., min_length=1, max_length=10000, description="Suspect social media post, comment, or message text")
    platform: Optional[str] = Field(default="MANUAL_SCAN", description="Source platform context")
    target_identifier: Optional[str] = None


class KeywordScanHit(BaseModel):
    """Detail of an individual keyword match."""
    keyword_id: str
    keyword: str
    category: str
    severity: AlertSeverity
    match_type: str
    matched_snippet: str


class KeywordScanResult(BaseModel):
    """Aggregated threat detection output from keyword scanning engine."""
    total_matches: int
    threat_severity: AlertSeverity
    threat_score: float = Field(..., description="Calculated threat probability (0.0 to 1.0)")
    categories_detected: List[str]
    matches: List[KeywordScanHit]
    scan_latency_ms: float
    timestamp: str
