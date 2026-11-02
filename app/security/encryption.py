"""
Cryptographic Secret Management & Credential Vault
Gujarat Cyber Crime Social Media Intelligence & Early Warning System

Provides authenticated symmetric encryption (Fernet) for social media API secrets,
OAuth tokens, and webhook secrets, preventing plaintext exposure in databases or logs.
"""

import base64
import hashlib
from typing import Optional
from cryptography.fernet import Fernet
from app.config.settings import get_settings


def _derive_fernet_key(master_secret: str) -> bytes:
    """Derives a standard 32-byte URL-safe base64 Fernet key from master secret."""
    digest = hashlib.sha256(master_secret.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest)


def get_fernet_cipher() -> Fernet:
    """Instantiates a Fernet cryptographic engine using the application master secret."""
    settings = get_settings()
    raw_secret = settings.SECRET_KEY.get_secret_value()
    key = _derive_fernet_key(raw_secret)
    return Fernet(key)


def encrypt_secret(plaintext: str) -> str:
    """
    Encrypts sensitive credentials (access tokens, app secrets, webhooks).
    Returns ASCII ciphertext safe for database storage.
    """
    if not plaintext:
        return ""
    cipher = get_fernet_cipher()
    encrypted_bytes = cipher.encrypt(plaintext.encode("utf-8"))
    return encrypted_bytes.decode("utf-8")


def decrypt_secret(ciphertext: str) -> str:
    """
    Decrypts stored encrypted credentials for adapter invocation.
    Never pass decrypted plaintext to frontend or log streams!
    """
    if not ciphertext:
        return ""
    cipher = get_fernet_cipher()
    decrypted_bytes = cipher.decrypt(ciphertext.encode("utf-8"))
    return decrypted_bytes.decode("utf-8")


def mask_token(token: Optional[str], visible_start: int = 4, visible_end: int = 4) -> str:
    """
    Masks access tokens for display in law enforcement UI.
    Example: 'EAAG9182...4a89' -> 'EAAG****4a89'
    """
    if not token:
        return "NOT_CONFIGURED"
    token = token.strip()
    if len(token) <= (visible_start + visible_end):
        return "********"
    return f"{token[:visible_start]}****{token[-visible_end:]}"


def mask_identifier(val: Optional[str]) -> str:
    """Masks sensitive external client or App IDs."""
    if not val:
        return "--"
    val = str(val).strip()
    if len(val) <= 6:
        return f"{val[:2]}****"
    return f"{val[:4]}****{val[-2:]}"
