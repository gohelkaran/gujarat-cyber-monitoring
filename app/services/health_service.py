"""
System Health and Diagnostics Service
Gujarat Cyber Crime Social Media Intelligence & Early Warning System
"""

import time
import os
from typing import Dict, Any
from sqlalchemy.orm import Session
from app.config.settings import get_settings
from app.core.database import check_database_connection
from app.schemas.common import HealthResponse, ComponentHealth
from app.utils.time_utils import format_timestamp_utc, format_localized_time
from app.services.base import BaseService

# Application start time tracker
START_TIME = time.time()


class HealthService(BaseService):
    """Provides consolidated diagnostics across databases, storage, and runtime."""
    def __init__(self, db: Session = None):
        super().__init__(db)
        self.settings = get_settings()

    def get_system_health(self) -> HealthResponse:
        """Inspects all critical dependencies and returns health status."""
        uptime = round(time.time() - START_TIME, 2)
        components: Dict[str, ComponentHealth] = {}

        # 1. Database Check
        db_check = check_database_connection()
        components["database"] = ComponentHealth(
            status=db_check.get("status", "UNKNOWN"),
            message=db_check.get("message", "Database check completed"),
            details={"dialect": db_check.get("dialect", "unknown")}
        )

        # 2. Filesystem / Audit Logs Check
        audit_log_path = self.settings.AUDIT_LOG_FILE_PATH
        log_dir = os.path.dirname(audit_log_path) or "."
        log_dir_writable = os.access(log_dir, os.W_OK)
        components["audit_storage"] = ComponentHealth(
            status="UP" if log_dir_writable else "DEGRADED",
            message="Audit log storage accessible and writable" if log_dir_writable else "Audit log storage directory not writable",
            details={"path": audit_log_path}
        )

        # 3. Overall status aggregation
        all_up = all(c.status == "UP" for c in components.values())
        overall_status = "HEALTHY" if all_up else "DEGRADED"

        return HealthResponse(
            status=overall_status,
            environment=self.settings.APP_ENV,
            version=self.settings.APP_VERSION,
            timestamp_utc=format_timestamp_utc(),
            timestamp_localized=format_localized_time(),
            uptime_seconds=uptime,
            components=components,
        )
