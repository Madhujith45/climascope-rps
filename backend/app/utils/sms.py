import os
from twilio.rest import Client
import logging

logger = logging.getLogger(__name__)

def send_sms(to_number: str, message: str) -> None:
    """Send an SMS alert using Twilio and environment variables."""
    TWILIO_SID = os.getenv("TWILIO_SID")
    TWILIO_AUTH = os.getenv("TWILIO_AUTH")
    TWILIO_PHONE = os.getenv("TWILIO_PHONE")
    
    if not TWILIO_SID or not TWILIO_AUTH or not TWILIO_PHONE:
        logger.warning(f"Would send SMS to {to_number} but Twilio credentials missing. msg: {message}")
        return
        
    if not to_number:
        logger.warning("Cannot send SMS: No destination phone number provided.")
        return

    try:
        client = Client(TWILIO_SID, TWILIO_AUTH)
        msg = client.messages.create(
            body=message,
            from_=TWILIO_PHONE,
            to=to_number
        )
        logger.info(f"Alert SMS successfully sent to {to_number}. SID: {msg.sid}")
    except Exception as e:
        logger.error(f"Failed to send SMS to {to_number}: {str(e)}")
