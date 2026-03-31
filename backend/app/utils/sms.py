"""
ClimaScope - SMS utilities (optional)
Uses Twilio when credentials are configured.
"""

import logging
import os
import importlib

logger = logging.getLogger(__name__)


def send_sms_alert(message: str, to_phone: str | None = None) -> bool:
    """Send SMS alert via Twilio if configured, otherwise no-op in dev mode."""
    account_sid = os.getenv("TWILIO_ACCOUNT_SID", "")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN", "")
    from_phone = os.getenv("TWILIO_FROM_PHONE", "")
    target_phone = to_phone or os.getenv("TWILIO_TO_PHONE", "")

    if not account_sid or not auth_token or not from_phone or not target_phone:
        logger.info("Twilio not configured; skipping SMS alert")
        return False

    try:
        twilio_rest = importlib.import_module("twilio.rest")
        Client = getattr(twilio_rest, "Client")

        client = Client(account_sid, auth_token)
        client.messages.create(
            body=message,
            from_=from_phone,
            to=target_phone,
        )
        logger.info("SMS alert sent to %s", target_phone)
        return True
    except Exception as exc:
        logger.error("Failed to send SMS alert: %s", exc)
        return False
