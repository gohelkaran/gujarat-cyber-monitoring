"""
Data Sanitization and Redaction Utilities
Gujarat Cyber Crime Social Media Intelligence & Early Warning System

Ensures sensitive values (tokens, passwords, PII, auth headers) are never
exposed in application logs or standard error traces.
"""

import re
from typing import Any, Dict

# Regex patterns for sensitive key names in dictionaries/json
SENSITIVE_KEY_PATTERNS = re.compile(
    r"(password|secret|token|authorization|bearer|api_key|private_key|credit_card|ssn|aadhaar)",
    re.IGNORECASE
)

REDACTED_PLACEHOLDER = "[REDACTED_BY_SECURITY_POLICY]"


def redact_sensitive_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively redacts sensitive keys from a dictionary before logging."""
    if not isinstance(data, dict):
        return data

    cleaned = {}
    for key, value in data.items():
        if SENSITIVE_KEY_PATTERNS.search(str(key)):
            cleaned[key] = REDACTED_PLACEHOLDER
        elif isinstance(value, dict):
            cleaned[key] = redact_sensitive_dict(value)
        elif isinstance(value, list):
            cleaned[key] = [
                redact_sensitive_dict(item) if isinstance(item, dict) else item
                for item in value
            ]
        else:
            cleaned[key] = value
    return cleaned


def mask_string(val: str, visible_start: int = 2, visible_end: int = 2) -> str:
    """Masks middle characters of an identifier or token."""
    if not val:
        return ""
    if len(val) <= (visible_start + visible_end):
        return "***"
    return f"{val[:visible_start]}{'*' * (len(val) - (visible_start + visible_end))}{val[-visible_end:]}"
