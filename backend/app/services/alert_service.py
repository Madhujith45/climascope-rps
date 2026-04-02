import datetime
import uuid
import logging
from app.db.mongo import get_mongo_db
from app.utils.email import send_email
from app.utils.sms import send_sms

logger = logging.getLogger(__name__)

# Global state for throttling (in-memory)
_last_alert_time = None

async def trigger_alert(risk_score: float, level: str, reason: str):
    """
    1. Create alert message
    2. Store in DB
    3. Throttling (within 5 minutes)
    4. Fetch users with enabled alerts
    5. Send email/SMS based on preferences
    """
    db = get_mongo_db()
    global _last_alert_time
    now = datetime.datetime.utcnow()

    # Throttling check
    if _last_alert_time is not None:
        if (now - _last_alert_time).total_seconds() < 300:
            logger.info("Alert throttled (sent within last 5 minutes)")
            return

    timestamp = now.isoformat()
    _last_alert_time = now
    
    # 1. Create message
    alert_id = str(uuid.uuid4())
    alert_doc = {
        "id": alert_id,
        "created_at": timestamp,
        "risk_score": risk_score,
        "severity": level.lower() if level.upper() != "HIGH" else "danger",     
        "message": reason,
        "is_read": False,
        "is_resolved": False,
        "device_name": "Edge Device"
    }

    # 2. Store in DB
    try:
        await db.alerts.insert_one(alert_doc.copy())
    except Exception as e:
        logger.error(f"Failed to store alert in DB: {e}")

    subject = "🚨 ClimaScope Alert - High Risk Detected"
    body = f"Risk Level: {level}\nRisk Score: {risk_score}\nReason: {reason}\nTime: {timestamp}"

    # 3. Fetch users with alerts configured optimally
    try:
        # User needs to have alerts enabled (or doesn't have the field yet -> default to true)
        users = await db.users.find(
            { "$or": [
                {"alerts_enabled": True}, 
                {"alerts_enabled": {"$exists": False}}
            ]}, 
            {"email": 1, "phone": 1, "alert_mode": 1, "_id": 0}
        ).to_list(length=1000)
    except Exception as e:
        logger.error(f"Failed to fetch users: {e}")
        users = []

    # 4. Send alerts based on user preferences
    for user in users:
        email = user.get("email")
        phone = user.get("phone")
        mode = user.get("alert_mode", "email")

        # Send Email
        if mode in ["email", "both"] and email:
            send_email(email, subject, body)

        # Send SMS
        if mode in ["sms", "both"] and phone:
            send_sms(phone, body)
