"""
Monitored Keyword and Threat Intelligence Service
Gujarat Cyber Crime Social Media Intelligence & Early Warning System

Provides:
- Statutory cybercrime keyword rule lifecycle (Create, Read, Update, Delete, Toggle)
- High-performance text scanning engine with regex word boundaries and snippet extraction
- Automated threat scoring and multi-tier severity categorization
- Default statutory taxonomy seeding (Financial Fraud, Phishing, Account Compromise, Identity Abuse, Extortion)
- Full statutory audit logging under Section 69 Indian IT Act / 91 CrPC
"""

import re
import time
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session

from app.services.base import BaseService
from app.services.audit_service import AuditService
from app.repositories.keyword_repository import KeywordRepository
from app.models.keyword import MonitoredKeyword, KeywordDetectionLog
from app.schemas.keyword import (
    KeywordCreate,
    KeywordUpdate,
    KeywordRead,
    KeywordCategorySummary,
    KeywordScanRequest,
    KeywordScanHit,
    KeywordScanResult,
)
from app.core.constants import (
    AlertSeverity,
    KeywordCategory,
    KeywordMatchType,
    UserRole,
    AuditAction,
    DataClassification,
)
from app.core.exceptions import (
    AuthorizationException,
    EntityNotFoundException,
    ValidationException,
)
from app.utils.time_utils import utc_now, format_localized_time


DEFAULT_STATUTORY_KEYWORDS = [
    # 1. Financial Fraud
    {
        "keyword": "UPI fraud",
        "category": KeywordCategory.FINANCIAL_FRAUD.value,
        "severity": AlertSeverity.CRITICAL,
        "match_type": KeywordMatchType.PHRASE,
        "description": "Unauthorized UPI transaction fraud, fake payment confirmations, and reverse pay scams",
        "authorization_ref": "GJ-CYBER-MANDATE-FIN-2026-001"
    },
    {
        "keyword": "OTP",
        "category": KeywordCategory.FINANCIAL_FRAUD.value,
        "severity": AlertSeverity.HIGH,
        "match_type": KeywordMatchType.PHRASE,
        "description": "One-Time Password phishing, social engineering, and unauthorized banking verification sharing",
        "authorization_ref": "GJ-CYBER-MANDATE-FIN-2026-002"
    },
    {
        "keyword": "KYC",
        "category": KeywordCategory.FINANCIAL_FRAUD.value,
        "severity": AlertSeverity.HIGH,
        "match_type": KeywordMatchType.PHRASE,
        "description": "Fraudulent KYC suspension SMS/calls, deceptive banking document update links",
        "authorization_ref": "GJ-CYBER-MANDATE-FIN-2026-003"
    },
    {
        "keyword": "bank fraud",
        "category": KeywordCategory.FINANCIAL_FRAUD.value,
        "severity": AlertSeverity.CRITICAL,
        "match_type": KeywordMatchType.PHRASE,
        "description": "General banking spoofing, unauthorized debit/credit card siphoning, and fake bank support",
        "authorization_ref": "GJ-CYBER-MANDATE-FIN-2026-004"
    },
    {
        "keyword": "investment scam",
        "category": KeywordCategory.FINANCIAL_FRAUD.value,
        "severity": AlertSeverity.CRITICAL,
        "match_type": KeywordMatchType.PHRASE,
        "description": "Deceptive high-yield investment schemes, fake stock trading groups, and Ponzi solicitations",
        "authorization_ref": "GJ-CYBER-MANDATE-FIN-2026-005"
    },

    # 2. Phishing
    {
        "keyword": "phishing",
        "category": KeywordCategory.PHISHING.value,
        "severity": AlertSeverity.HIGH,
        "match_type": KeywordMatchType.PHRASE,
        "description": "Credential harvesting links, lookalike portal redirects, and spoofed security advisories",
        "authorization_ref": "GJ-CYBER-MANDATE-PHISH-2026-001"
    },
    {
        "keyword": "malicious link",
        "category": KeywordCategory.PHISHING.value,
        "severity": AlertSeverity.HIGH,
        "match_type": KeywordMatchType.PHRASE,
        "description": "Distribution of malware payloads, deceptive shorteners, or weaponized download URLs",
        "authorization_ref": "GJ-CYBER-MANDATE-PHISH-2026-002"
    },
    {
        "keyword": "fake login",
        "category": KeywordCategory.PHISHING.value,
        "severity": AlertSeverity.CRITICAL,
        "match_type": KeywordMatchType.PHRASE,
        "description": "Cloned social media or corporate portal authentication pages designed to capture officer/citizen credentials",
        "authorization_ref": "GJ-CYBER-MANDATE-PHISH-2026-003"
    },

    # 3. Account Compromise
    {
        "keyword": "hacked account",
        "category": KeywordCategory.ACCOUNT_COMPROMISE.value,
        "severity": AlertSeverity.HIGH,
        "match_type": KeywordMatchType.PHRASE,
        "description": "Reporting or illicit sale of hijacked digital accounts, SIM swap fallout, or compromised credentials",
        "authorization_ref": "GJ-CYBER-MANDATE-ACC-2026-001"
    },
    {
        "keyword": "account takeover",
        "category": KeywordCategory.ACCOUNT_COMPROMISE.value,
        "severity": AlertSeverity.CRITICAL,
        "match_type": KeywordMatchType.PHRASE,
        "description": "Unauthorized elevation of privileges, automated brute force takeovers, and credentials stuffing",
        "authorization_ref": "GJ-CYBER-MANDATE-ACC-2026-002"
    },
    {
        "keyword": "Instagram hacked",
        "category": KeywordCategory.ACCOUNT_COMPROMISE.value,
        "severity": AlertSeverity.HIGH,
        "match_type": KeywordMatchType.PHRASE,
        "description": "Compromised Meta/Instagram handles used for crypto scams or impersonating victims",
        "authorization_ref": "GJ-CYBER-MANDATE-ACC-2026-003"
    },

    # 4. Identity Abuse
    {
        "keyword": "fake profile",
        "category": KeywordCategory.IDENTITY_ABUSE.value,
        "severity": AlertSeverity.MEDIUM,
        "match_type": KeywordMatchType.PHRASE,
        "description": "Synthetic profiles mimicking real individuals, fraudulent officer accounts, or fake agencies",
        "authorization_ref": "GJ-CYBER-MANDATE-ID-2026-001"
    },
    {
        "keyword": "impersonation",
        "category": KeywordCategory.IDENTITY_ABUSE.value,
        "severity": AlertSeverity.HIGH,
        "match_type": KeywordMatchType.PHRASE,
        "description": "Pretending to be Gujarat Police officers, government officials, or judicial authorities",
        "authorization_ref": "GJ-CYBER-MANDATE-ID-2026-002"
    },
    {
        "keyword": "identity theft",
        "category": KeywordCategory.IDENTITY_ABUSE.value,
        "severity": AlertSeverity.CRITICAL,
        "match_type": KeywordMatchType.PHRASE,
        "description": "Theft of Aadhaar, PAN, voter ID, or biometric identity assets for fraudulent activations",
        "authorization_ref": "GJ-CYBER-MANDATE-ID-2026-003"
    },

    # 5. Extortion
    {
        "keyword": "sextortion",
        "category": KeywordCategory.EXTORTION.value,
        "severity": AlertSeverity.CRITICAL,
        "match_type": KeywordMatchType.PHRASE,
        "description": "Video call entrapment, intimate imagery blackmail, and predatory financial extortion syndicates",
        "authorization_ref": "GJ-CYBER-MANDATE-EXT-2026-001"
    },
    {
        "keyword": "blackmail",
        "category": KeywordCategory.EXTORTION.value,
        "severity": AlertSeverity.HIGH,
        "match_type": KeywordMatchType.PHRASE,
        "description": "Coercive digital demands, threat of reputational damage or data release",
        "authorization_ref": "GJ-CYBER-MANDATE-EXT-2026-002"
    },
    {
        "keyword": "threatening images",
        "category": KeywordCategory.EXTORTION.value,
        "severity": AlertSeverity.CRITICAL,
        "match_type": KeywordMatchType.PHRASE,
        "description": "Weaponized morphed photos, deepfakes, or threatening visual media sent for extortion",
        "authorization_ref": "GJ-CYBER-MANDATE-EXT-2026-003"
    }
]


SEVERITY_WEIGHTS = {
    AlertSeverity.LOW: 0.25,
    AlertSeverity.MEDIUM: 0.50,
    AlertSeverity.HIGH: 0.75,
    AlertSeverity.CRITICAL: 1.00
}


class KeywordService(BaseService):
    """Business service orchestrating cybercrime keyword rules and threat scanning."""

    def __init__(self, db: Session):
        super().__init__(db)
        self.repo = KeywordRepository(db)
        self.audit_service = AuditService(db)

    def _verify_officer_clearance(self, officer_role: str, action_name: str) -> None:
        """Enforces that keyword modifications are performed only by authorized personnel."""
        allowed_roles = [
            UserRole.SUPER_ADMIN.value,
            UserRole.NODAL_OFFICER.value,
            UserRole.LEAD_INVESTIGATOR.value,
            "SUPER_ADMIN",
            "NODAL_OFFICER",
            "LEAD_INVESTIGATOR"
        ]
        if officer_role not in allowed_roles:
            raise AuthorizationException(
                f"Statutory Access Denied: Action '{action_name}' requires minimum clearance of LEAD_INVESTIGATOR or SUPER_ADMIN."
            )

    def ensure_seeded(self) -> None:
        """Ensures default statutory keywords are present."""
        if self.db.query(MonitoredKeyword).count() == 0:
            self.seed_default_keywords()

    def seed_default_keywords(self, force: bool = False) -> int:
        """
        Seeds standard statutory threat taxonomy keywords if not already present.
        Returns count of newly registered keywords.
        """
        created_count = 0
        default_officer_badge = "GJ-CYBER-CHIEF-01"
        system_user_id = "SYSTEM_INITIALIZER"

        for kw_data in DEFAULT_STATUTORY_KEYWORDS:
            existing = self.repo.get_by_keyword_text(kw_data["keyword"])
            if existing and not force:
                continue

            if not existing:
                create_dto = KeywordCreate(
                    keyword=kw_data["keyword"],
                    category=kw_data["category"],
                    severity=kw_data["severity"],
                    match_type=kw_data["match_type"],
                    language="en",
                    description=kw_data["description"],
                    authorization_ref=kw_data["authorization_ref"],
                    authorizing_officer_badge=default_officer_badge
                )
                self.repo.create_keyword(create_dto, created_by=system_user_id)
                created_count += 1

        return created_count

    def list_keywords(
        self,
        category: Optional[str] = None,
        severity: Optional[AlertSeverity] = None,
        is_active: Optional[bool] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[KeywordRead], int]:
        """List keywords with filtering and pagination."""
        self.ensure_seeded()
        items, total = self.repo.list_keywords(
            category=category,
            severity=severity,
            is_active=is_active,
            search=search,
            skip=skip,
            limit=limit
        )
        read_items = [KeywordRead.model_validate(item) for item in items]
        return read_items, total

    def get_keyword(self, keyword_id: str) -> KeywordRead:
        """Fetch single keyword by ID or raise EntityNotFoundException."""
        item = self.repo.get_by_id(keyword_id)
        if not item:
            raise EntityNotFoundException("MonitoredKeyword", keyword_id)
        return KeywordRead.model_validate(item)

    def create_keyword(
        self,
        data: KeywordCreate,
        current_user_id: str,
        current_user_role: str,
        current_user_badge: Optional[str] = None
    ) -> KeywordRead:
        """
        Registers a new custom or manual keyword.
        Enforces unique keyword check and statutory audit trail.
        """
        self.ensure_seeded()
        self._verify_officer_clearance(current_user_role, "CREATE_KEYWORD")

        # Validate legal mandate
        if not data.authorization_ref or len(data.authorization_ref.strip()) < 3:
            raise ValidationException("Statutory authorization mandate reference is mandatory.")

        # Validate unique
        existing = self.repo.get_by_keyword_text(data.keyword)
        if existing:
            raise ValidationException(f"Keyword or phrase '{data.keyword}' is already registered in category '{existing.category}'.")

        badge = current_user_badge or data.authorizing_officer_badge
        data.authorizing_officer_badge = badge

        keyword_obj = self.repo.create_keyword(data, created_by=current_user_id)

        # Audit trail
        self.audit_service.log_event(
            action=AuditAction.KEYWORD_CREATE,
            actor_id=badge,
            actor_role=current_user_role,
            resource_type="MONITORED_KEYWORD",
            resource_id=keyword_obj.id,
            details={
                "keyword": keyword_obj.keyword,
                "category": keyword_obj.category,
                "severity": keyword_obj.severity.value if hasattr(keyword_obj.severity, "value") else str(keyword_obj.severity),
                "match_type": keyword_obj.match_type,
                "authorization_ref": keyword_obj.authorization_ref
            },
            classification_level=DataClassification.CONFIDENTIAL
        )

        return KeywordRead.model_validate(keyword_obj)

    def update_keyword(
        self,
        keyword_id: str,
        data: KeywordUpdate,
        current_user_id: str,
        current_user_role: str,
        current_user_badge: Optional[str] = None
    ) -> KeywordRead:
        """Updates an existing monitored keyword."""
        self._verify_officer_clearance(current_user_role, "UPDATE_KEYWORD")

        existing = self.repo.get_by_id(keyword_id)
        if not existing:
            raise EntityNotFoundException("MonitoredKeyword", keyword_id)

        # Check duplicate if keyword text is being changed
        if data.keyword and data.keyword.strip().lower() != existing.keyword.lower():
            dup = self.repo.get_by_keyword_text(data.keyword)
            if dup and dup.id != keyword_id:
                raise ValidationException(f"Keyword '{data.keyword}' already exists in rule ID '{dup.id}'.")

        updated_obj = self.repo.update_keyword(keyword_id, data, updated_by=current_user_id)

        # Audit trail
        self.audit_service.log_event(
            action=AuditAction.KEYWORD_UPDATE,
            actor_id=current_user_badge or current_user_id,
            actor_role=current_user_role,
            resource_type="MONITORED_KEYWORD",
            resource_id=keyword_id,
            details={
                "keyword": updated_obj.keyword,
                "category": updated_obj.category,
                "severity": updated_obj.severity.value if hasattr(updated_obj.severity, "value") else str(updated_obj.severity),
                "is_active": updated_obj.is_active
            },
            classification_level=DataClassification.CONFIDENTIAL
        )

        return KeywordRead.model_validate(updated_obj)

    def toggle_keyword(
        self,
        keyword_id: str,
        is_active: bool,
        current_user_id: str,
        current_user_role: str,
        current_user_badge: Optional[str] = None
    ) -> KeywordRead:
        """Enables or disables scanning for a keyword."""
        self._verify_officer_clearance(current_user_role, "TOGGLE_KEYWORD")

        updated_obj = self.repo.toggle_active(keyword_id, is_active, updated_by=current_user_id)
        if not updated_obj:
            raise EntityNotFoundException("MonitoredKeyword", keyword_id)

        self.audit_service.log_event(
            action=AuditAction.KEYWORD_TOGGLE,
            actor_id=current_user_badge or current_user_id,
            actor_role=current_user_role,
            resource_type="MONITORED_KEYWORD",
            resource_id=keyword_id,
            details={"is_active": is_active, "keyword": updated_obj.keyword},
            classification_level=DataClassification.CONFIDENTIAL
        )

        return KeywordRead.model_validate(updated_obj)

    def delete_keyword(
        self,
        keyword_id: str,
        current_user_id: str,
        current_user_role: str,
        current_user_badge: Optional[str] = None
    ) -> bool:
        """Deletes a monitored keyword rule."""
        self._verify_officer_clearance(current_user_role, "DELETE_KEYWORD")

        existing = self.repo.get_by_id(keyword_id)
        if not existing:
            raise EntityNotFoundException("MonitoredKeyword", keyword_id)

        keyword_text = existing.keyword
        success = self.repo.delete_keyword(keyword_id)

        self.audit_service.log_event(
            action=AuditAction.KEYWORD_DELETE,
            actor_id=current_user_badge or current_user_id,
            actor_role=current_user_role,
            resource_type="MONITORED_KEYWORD",
            resource_id=keyword_id,
            details={"deleted_keyword": keyword_text},
            classification_level=DataClassification.CONFIDENTIAL
        )

        return success

    def get_category_summaries(self) -> List[KeywordCategorySummary]:
        """Statistical overview of threat categories."""
        self.ensure_seeded()
        summaries = self.repo.get_category_summaries()
        return [KeywordCategorySummary(**item) for item in summaries]

    def scan_text(
        self,
        payload: KeywordScanRequest,
        current_user_id: str,
        current_user_badge: Optional[str] = None,
        source_id: Optional[str] = None,
        record_detections: bool = False
    ) -> KeywordScanResult:
        """
        High-performance scanning engine.
        Tests arbitrary suspect content against all enabled keyword rules.
        Uses regex boundary matching to prevent false positives (e.g. 'HOTPOT' matching 'OTP').
        Calculates normalized threat scores and aggregates severities.
        """
        self.ensure_seeded()
        start_time = time.perf_counter()
        active_keywords = self.repo.get_all_active()
        text = payload.text
        matches: List[KeywordScanHit] = []
        categories_detected = set()
        matched_severities: List[AlertSeverity] = []

        for kw in active_keywords:
            pattern_str = kw.keyword.strip()
            match_type = kw.match_type

            matched_spans = []
            try:
                if match_type == KeywordMatchType.REGEX.value:
                    regex = re.compile(pattern_str, re.IGNORECASE)
                    for match in regex.finditer(text):
                        matched_spans.append((match.start(), match.end()))
                elif match_type == KeywordMatchType.EXACT.value:
                    if pattern_str.lower() == text.strip().lower():
                        matched_spans.append((0, len(text)))
                else:  # PHRASE (default with word boundary safety)
                    escaped = re.escape(pattern_str)
                    regex = re.compile(rf"\b{escaped}\b", re.IGNORECASE)
                    for match in regex.finditer(text):
                        matched_spans.append((match.start(), match.end()))
            except re.error:
                if pattern_str.lower() in text.lower():
                    idx = text.lower().find(pattern_str.lower())
                    matched_spans.append((idx, idx + len(pattern_str)))

            if matched_spans:
                categories_detected.add(kw.category)
                matched_severities.append(kw.severity)

                first_start, first_end = matched_spans[0]
                snippet_start = max(0, first_start - 35)
                snippet_end = min(len(text), first_end + 35)
                prefix = "..." if snippet_start > 0 else ""
                suffix = "..." if snippet_end < len(text) else ""
                snippet = f"{prefix}{text[snippet_start:snippet_end].strip()}{suffix}"

                matches.append(
                    KeywordScanHit(
                        keyword_id=kw.id,
                        keyword=kw.keyword,
                        category=kw.category,
                        severity=kw.severity,
                        match_type=kw.match_type,
                        matched_snippet=snippet
                    )
                )

                if record_detections:
                    self.repo.record_hit(
                        keyword_id=kw.id,
                        source_id=source_id,
                        platform=payload.platform or "MANUAL_SCAN",
                        external_item_id=payload.target_identifier,
                        matched_text_snippet=snippet,
                        confidence_score=1.0
                    )

        # Threat calculation
        if not matched_severities:
            threat_severity = AlertSeverity.LOW
            threat_score = 0.0
        else:
            severity_order = [
                AlertSeverity.CRITICAL,
                AlertSeverity.HIGH,
                AlertSeverity.MEDIUM,
                AlertSeverity.LOW
            ]
            threat_severity = AlertSeverity.LOW
            for s in severity_order:
                if s in matched_severities:
                    threat_severity = s
                    break

            max_weight = SEVERITY_WEIGHTS.get(threat_severity, 0.25)
            bonus = min(0.35, (len(matches) - 1) * 0.08) if len(matches) > 1 else 0.0
            threat_score = round(min(1.0, (max_weight * 0.65) + bonus + 0.15), 2)

        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)

        # Audit scan execution
        self.audit_service.log_event(
            action=AuditAction.KEYWORD_SCAN,
            actor_id=current_user_badge or current_user_id,
            actor_role="INVESTIGATOR",
            resource_type="THREAT_INTELLIGENCE",
            resource_id="KEYWORD_SCAN",
            details={
                "platform": payload.platform,
                "matches_count": len(matches),
                "threat_score": threat_score,
                "threat_severity": threat_severity.value,
                "latency_ms": elapsed_ms
            },
            classification_level=DataClassification.RESTRICTED
        )

        return KeywordScanResult(
            total_matches=len(matches),
            threat_severity=threat_severity,
            threat_score=threat_score,
            categories_detected=sorted(list(categories_detected)),
            matches=matches,
            scan_latency_ms=elapsed_ms,
            timestamp=utc_now().isoformat()
        )
