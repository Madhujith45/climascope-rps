"""
ClimaScope – Security Utilities
Handles password hashing, API key generation, and reset token creation.
"""

import secrets
import hashlib
from typing import Optional


def generate_api_key(prefix: str = "csk") -> str:
    """Generate a secure random API key for device authentication.

    Format: csk_<40-char-hex>
    Example: csk_a1b2c3d4e5f6...
    """
    random_bytes = secrets.token_hex(20)  # 40 hex chars
    return f"{prefix}_{random_bytes}"


def hash_otp(otp: str) -> str:
    """Hash an OTP using SHA-256 for storage.

    OTPs are short-lived but we still hash them so a DB leak
    doesn't expose valid reset codes.
    """
    return hashlib.sha256(otp.encode("utf-8")).hexdigest()


def verify_otp_hash(otp: str, hashed: str) -> bool:
    """Verify an OTP against its SHA-256 hash."""
    return hash_otp(otp) == hashed


def generate_reset_token() -> str:
    """Generate a secure temporary token for password reset confirmation."""
    return secrets.token_urlsafe(32)
