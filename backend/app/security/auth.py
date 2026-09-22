from __future__ import annotations

import hashlib
import hmac
import os
import secrets
from datetime import datetime, timedelta, timezone

SECRET_KEY = os.getenv("SECRET_KEY", "netralink-insecure-dev-secret-key-change-in-prod")


def hash_password(password: str) -> str:
    """Hash password using salt + SHA-256 for basic security."""
    salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100000)
    return f"{salt}:{key.hex()}"


def verify_password(stored_password_hash: str, password_attempt: str) -> bool:
    """Verify password against stored salt:hash."""
    if ":" not in stored_password_hash:
        return False
    salt, key_hex = stored_password_hash.split(":", 1)
    test_key = hashlib.pbkdf2_hmac("sha256", password_attempt.encode(), salt.encode(), 100000)
    return hmac.compare_digest(test_key.hex(), key_hex)
