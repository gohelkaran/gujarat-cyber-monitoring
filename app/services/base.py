"""
Base Service Layer
Gujarat Cyber Crime Social Media Intelligence & Early Warning System
"""

from typing import Optional
from sqlalchemy.orm import Session
from app.core.logging_config import get_logger


class BaseService:
    """Base class providing shared logging and DB session context to domain services."""
    def __init__(self, db: Optional[Session] = None):
        self.db = db
        self.logger = get_logger(self.__class__.__name__)
