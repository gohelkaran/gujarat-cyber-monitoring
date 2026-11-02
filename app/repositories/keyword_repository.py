"""
Monitored Keywords and Threat Intelligence Repository
Gujarat Cyber Crime Social Media Intelligence & Early Warning System

Provides data access operations for statutory cybercrime keyword tracking,
filtering, updates, hit statistics, and forensic detection logs.
"""

from datetime import datetime
from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select, func, desc

from app.models.keyword import MonitoredKeyword, KeywordDetectionLog
from app.repositories.base import BaseRepository
from app.schemas.keyword import KeywordCreate, KeywordUpdate
from app.core.constants import AlertSeverity, KeywordCategory
from app.utils.time_utils import utc_now


class KeywordRepository(BaseRepository[MonitoredKeyword]):
    """Data access repository for monitored keywords and detection logs."""

    def __init__(self, db: Session):
        super().__init__(MonitoredKeyword, db)

    def get_by_id(self, keyword_id: str) -> Optional[MonitoredKeyword]:
        """Fetch a single monitored keyword by unique identifier."""
        return self.db.query(MonitoredKeyword).filter(MonitoredKeyword.id == keyword_id).first()

    def get_by_keyword_text(self, keyword_text: str) -> Optional[MonitoredKeyword]:
        """Fetch keyword by exact text match (case-insensitive)."""
        return self.db.query(MonitoredKeyword).filter(
            func.lower(MonitoredKeyword.keyword) == func.lower(keyword_text.strip())
        ).first()

    def list_keywords(
        self,
        category: Optional[str] = None,
        severity: Optional[AlertSeverity] = None,
        is_active: Optional[bool] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[MonitoredKeyword], int]:
        """
        Query keywords with optional filtering across category, severity,
        active state, and search query on keyword/description/mandate.
        """
        query = self.db.query(MonitoredKeyword)

        if category:
            query = query.filter(MonitoredKeyword.category == category)
        if severity:
            query = query.filter(MonitoredKeyword.severity == severity)
        if is_active is not None:
            query = query.filter(MonitoredKeyword.is_active == is_active)
        if search:
            search_term = f"%{search.strip().lower()}%"
            query = query.filter(
                (func.lower(MonitoredKeyword.keyword).like(search_term)) |
                (func.lower(MonitoredKeyword.description).like(search_term)) |
                (func.lower(MonitoredKeyword.authorization_ref).like(search_term))
            )

        total = query.count()
        keywords = query.order_by(desc(MonitoredKeyword.created_at)).offset(skip).limit(limit).all()
        return keywords, total

    def get_all_active(self) -> List[MonitoredKeyword]:
        """Return all enabled keywords for real-time text matching engines."""
        return self.db.query(MonitoredKeyword).filter(MonitoredKeyword.is_active == True).all()

    def create_keyword(self, data: KeywordCreate, created_by: str) -> MonitoredKeyword:
        """Create and persist a new monitored keyword with statutory mandate."""
        keyword_obj = MonitoredKeyword(
            keyword=data.keyword.strip(),
            category=data.category,
            severity=data.severity,
            match_type=data.match_type.value if hasattr(data.match_type, "value") else str(data.match_type),
            language=data.language,
            description=data.description,
            authorization_ref=data.authorization_ref.strip(),
            created_by_badge=data.authorizing_officer_badge.strip(),
            created_by=created_by,
            is_active=True,
            hits_count=0
        )
        self.db.add(keyword_obj)
        self.db.commit()
        self.db.refresh(keyword_obj)
        return keyword_obj

    def update_keyword(self, keyword_id: str, data: KeywordUpdate, updated_by: str) -> Optional[MonitoredKeyword]:
        """Update mutable fields on an existing keyword rule."""
        keyword_obj = self.get_by_id(keyword_id)
        if not keyword_obj:
            return None

        if data.keyword is not None:
            keyword_obj.keyword = data.keyword.strip()
        if data.category is not None:
            keyword_obj.category = data.category
        if data.severity is not None:
            keyword_obj.severity = data.severity
        if data.match_type is not None:
            keyword_obj.match_type = data.match_type.value if hasattr(data.match_type, "value") else str(data.match_type)
        if data.is_active is not None:
            keyword_obj.is_active = data.is_active
        if data.language is not None:
            keyword_obj.language = data.language
        if data.description is not None:
            keyword_obj.description = data.description
        if data.authorization_ref is not None:
            keyword_obj.authorization_ref = data.authorization_ref.strip()

        keyword_obj.updated_by = updated_by
        self.db.commit()
        self.db.refresh(keyword_obj)
        return keyword_obj

    def toggle_active(self, keyword_id: str, is_active: bool, updated_by: str) -> Optional[MonitoredKeyword]:
        """Enable or disable active scanning for a keyword."""
        keyword_obj = self.get_by_id(keyword_id)
        if not keyword_obj:
            return None

        keyword_obj.is_active = is_active
        keyword_obj.updated_by = updated_by
        self.db.commit()
        self.db.refresh(keyword_obj)
        return keyword_obj

    def delete_keyword(self, keyword_id: str) -> bool:
        """Permanently remove a monitored keyword and related detection logs."""
        keyword_obj = self.get_by_id(keyword_id)
        if not keyword_obj:
            return False

        self.db.delete(keyword_obj)
        self.db.commit()
        return True

    def record_hit(
        self,
        keyword_id: str,
        source_id: Optional[str],
        platform: str,
        external_item_id: Optional[str],
        matched_text_snippet: str,
        confidence_score: float = 1.0
    ) -> Optional[KeywordDetectionLog]:
        """
        Record a detection log entry and atomically increment keyword hit statistics.
        """
        keyword_obj = self.get_by_id(keyword_id)
        if not keyword_obj:
            return None

        now = utc_now()
        keyword_obj.hits_count += 1
        keyword_obj.last_detected_at = now

        log = KeywordDetectionLog(
            keyword_id=keyword_id,
            source_id=source_id,
            platform=platform,
            external_item_id=external_item_id,
            confidence_score=confidence_score,
            matched_text_snippet=matched_text_snippet[:1000] if matched_text_snippet else None,
            detected_at=now
        )
        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)
        return log

    def get_category_summaries(self) -> List[Dict[str, Any]]:
        """
        Generate aggregate metrics per cybercrime category.
        """
        all_keywords = self.db.query(MonitoredKeyword).all()
        categories_map: Dict[str, Dict[str, Any]] = {}

        # Initialize defaults for standard categories
        for cat in [
            KeywordCategory.FINANCIAL_FRAUD.value,
            KeywordCategory.PHISHING.value,
            KeywordCategory.ACCOUNT_COMPROMISE.value,
            KeywordCategory.IDENTITY_ABUSE.value,
            KeywordCategory.EXTORTION.value,
            KeywordCategory.OTHER.value
        ]:
            categories_map[cat] = {
                "category": cat,
                "total_keywords": 0,
                "active_keywords": 0,
                "total_hits": 0,
                "sample_keywords": []
            }

        for kw in all_keywords:
            cat = kw.category or KeywordCategory.OTHER.value
            if cat not in categories_map:
                categories_map[cat] = {
                    "category": cat,
                    "total_keywords": 0,
                    "active_keywords": 0,
                    "total_hits": 0,
                    "sample_keywords": []
                }
            entry = categories_map[cat]
            entry["total_keywords"] += 1
            if kw.is_active:
                entry["active_keywords"] += 1
            entry["total_hits"] += (kw.hits_count or 0)
            if len(entry["sample_keywords"]) < 5:
                entry["sample_keywords"].append(kw.keyword)

        return list(categories_map.values())
