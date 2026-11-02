"""
Password Hashing and Cryptographic Key Derivation
Gujarat Cyber Crime Social Media Intelligence & Early Warning System
"""

import hashlib
import secrets
import bcrypt


def hash_password(password: str) -> str:
    """Hashes a password with secure bcrypt salt."""
    pwd_bytes = password.encode("utf-8")[:72]
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain password against the stored bcrypt hash."""
    pwd_bytes = plain_password.encode("utf-8")[:72]
    hash_bytes = hashed_password.encode("utf-8")
    try:
        return bcrypt.checkpw(pwd_bytes, hash_bytes)
    except Exception:
        return False


def generate_secure_token(nbytes: int = 32) -> str:
    """Generates a cryptographically strong pseudo-random URL-safe token."""
    return secrets.token_urlsafe(nbytes)


def compute_sha256(data: str) -> str:
    """Calculates SHA-256 digest for audit log chaining and evidence sealing."""
    return hashlib.sha256(data.encode("utf-8")).hexdigest()
