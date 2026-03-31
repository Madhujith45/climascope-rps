"""
ClimaScope – OTP Utilities
Generate, store, and verify 6-digit one-time passwords for password reset.
"""

import random
import logging
from datetime import datetime, timedelta
from typing import Optional, Tuple

from ..db.mongo import get_mongo_db
from .security import hash_otp, verify_otp_hash, generate_reset_token

logger = logging.getLogger(__name__)

# Configuration
OTP_LENGTH = 6
OTP_EXPIRY_MINUTES = 10
MAX_OTP_ATTEMPTS = 5


def generate_otp() -> str:
    """Generate a cryptographically random 6-digit OTP."""
    return "".join([str(random.SystemRandom().randint(0, 9)) for _ in range(OTP_LENGTH)])


async def create_otp_record(email: str) -> str:
    """Create and store an OTP record in MongoDB.

    Returns the plain-text OTP (to be sent via email).
    The stored version is SHA-256 hashed.
    """
    db = get_mongo_db()
    otp = generate_otp()
    hashed = hash_otp(otp)

    # Delete any existing OTP for this email
    await db.otp_records.delete_many({"email": email})

    record = {
        "email": email,
        "otp_hash": hashed,
        "expires_at": datetime.utcnow() + timedelta(minutes=OTP_EXPIRY_MINUTES),
        "attempts": 0,
        "created_at": datetime.utcnow(),
        "used": False,
    }
    await db.otp_records.insert_one(record)

    logger.info("OTP created for email=%s (expires in %d min)", email, OTP_EXPIRY_MINUTES)
    return otp


async def verify_otp(email: str, otp: str) -> Tuple[bool, Optional[str], str]:
    """Verify an OTP for the given email.

    Returns:
        (success, reset_token_or_none, error_message)
    """
    db = get_mongo_db()
    record = await db.otp_records.find_one({"email": email, "used": False})

    if not record:
        return False, None, "No OTP request found for this email"

    # Check expiry
    if datetime.utcnow() > record["expires_at"]:
        await db.otp_records.delete_one({"_id": record["_id"]})
        return False, None, "OTP has expired. Please request a new one"

    # Check attempt limit
    if record["attempts"] >= MAX_OTP_ATTEMPTS:
        await db.otp_records.delete_one({"_id": record["_id"]})
        return False, None, "Too many failed attempts. Please request a new OTP"

    # Increment attempt counter
    await db.otp_records.update_one(
        {"_id": record["_id"]},
        {"$inc": {"attempts": 1}}
    )

    # Verify hash
    if not verify_otp_hash(otp, record["otp_hash"]):
        remaining = MAX_OTP_ATTEMPTS - record["attempts"] - 1
        return False, None, f"Invalid OTP. {remaining} attempt(s) remaining"

    # Generate reset token and mark OTP as used
    reset_token = generate_reset_token()
    await db.otp_records.update_one(
        {"_id": record["_id"]},
        {"$set": {"used": True, "reset_token": reset_token}}
    )

    logger.info("OTP verified successfully for email=%s", email)
    return True, reset_token, "OTP verified successfully"


async def verify_reset_token(email: str, reset_token: str) -> bool:
    """Verify that a reset token is valid for the given email."""
    db = get_mongo_db()
    record = await db.otp_records.find_one({
        "email": email,
        "reset_token": reset_token,
        "used": True,
    })
    if not record:
        return False

    # Check if the original OTP hasn't expired (extra safety window)
    expiry_window = record["expires_at"] + timedelta(minutes=5)
    if datetime.utcnow() > expiry_window:
        await db.otp_records.delete_one({"_id": record["_id"]})
        return False

    return True


async def consume_reset_token(email: str, reset_token: str) -> None:
    """Delete the OTP record after a successful password reset."""
    db = get_mongo_db()
    await db.otp_records.delete_many({"email": email, "reset_token": reset_token})
    logger.info("Reset token consumed for email=%s", email)
