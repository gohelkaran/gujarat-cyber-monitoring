"""
Time and Date Utilities
Gujarat Cyber Crime Social Media Intelligence & Early Warning System

Ensures all database records, log timestamps, and cryptographic tokens
use strict UTC internally, while providing localized formatting (e.g. IST).
"""

from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from typing import Optional
from app.config.settings import get_settings


def utc_now() -> datetime:
    """Returns current datetime with explicit UTC timezone."""
    return datetime.now(timezone.utc)


def format_timestamp_utc(dt: Optional[datetime] = None) -> str:
    """Formats datetime to ISO 8601 UTC string format."""
    target = dt or utc_now()
    if target.tzinfo is None:
        target = target.replace(tzinfo=timezone.utc)
    return target.astimezone(timezone.utc).isoformat()


def format_localized_time(dt: Optional[datetime] = None, tz_name: Optional[str] = None) -> str:
    """
    Formats a UTC datetime into the designated administrative timezone
    (default: Asia/Kolkata / Indian Standard Time).
    """
    settings = get_settings()
    zone_str = tz_name or settings.DEFAULT_TIMEZONE
    try:
        zone = ZoneInfo(zone_str)
    except Exception:
        zone = timezone.utc

    target = dt or utc_now()
    if target.tzinfo is None:
        target = target.replace(tzinfo=timezone.utc)

    localized = target.astimezone(zone)
    return localized.strftime("%Y-%m-%d %H:%M:%S %Z")
