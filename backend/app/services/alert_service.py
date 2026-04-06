import asyncio
import datetime
import uuid
import logging
from app.db.mongo import get_mongo_db
from app.utils.email import send_email
from app.utils.sms import send_sms

logger = logging.getLogger(__name__)

# Global state for throttling (in-memory)
_last_alert_time = None


async def _dispatch_notifications(users: list[dict], subject: str, body: str) -> None:
    """Send notifications without blocking API request handling."""
    for user in users:
        email = user.get("email")
        phone = user.get("phone")
        mode = user.get("alert_mode", "email")

        try:
            if mode in ["email", "both"] and email:
                await asyncio.wait_for(
                    asyncio.to_thread(send_email, email, subject, body),
                    timeout=8,
                )
        except Exception as e:
            logger.warning(f"Email dispatch skipped for {email}: {e}")

        try:
            if mode in ["sms", "both"] and phone:
                await asyncio.wait_for(
                    asyncio.to_thread(send_sms, phone, body),
                    timeout=8,
                )
        except Exception as e:
            logger.warning(f"SMS dispatch skipped for {phone}: {e}")

async def trigger_alert(
    risk_score: float,
    level: str,
    reason: str,
    device_id: str | None = None,
    user_id: str | None = None,
):
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

    timestamp = now
    _last_alert_time = now

    normalized_level = (level or "").upper()
    severity = "danger" if normalized_level == "HIGH" else "warning"

    target_devices = []
    try:
        query = {}
        if user_id:
            query["user_id"] = user_id
        if device_id:
            query["device_id"] = device_id
        if query:
            target_devices = await db.devices.find(query, {"user_id": 1, "device_id": 1}).to_list(length=100)
    except Exception as e:
        logger.error(f"Failed to resolve target device(s): {e}")

    # 2. Store in DB (user/device scoped where possible)
    try:
        if target_devices:
            docs = []
            for dev in target_devices:
                docs.append(
                    {
                        "id": str(uuid.uuid4()),
                        "user_id": str(dev.get("user_id")),
                        "device_id": dev.get("device_id"),
                        "created_at": timestamp,
                        "risk_score": risk_score,
                        "severity": severity,
                        "message": reason,
                        "alert_type": "device",
                        "is_read": False,
                        "is_resolved": False,
                    }
                )
            if docs:
                await db.alerts.insert_many(docs)
        else:
            fallback_doc = {
                "id": str(uuid.uuid4()),
                "created_at": timestamp,
                "risk_score": risk_score,
                "severity": severity,
                "message": reason,
                "alert_type": "device",
                "is_read": False,
                "is_resolved": False,
                "device_name": "Edge Device",
            }
            if user_id:
                fallback_doc["user_id"] = user_id
            if device_id:
                fallback_doc["device_id"] = device_id
            await db.alerts.insert_one(fallback_doc)
    except Exception as e:
        logger.error(f"Failed to store alert in DB: {e}")

    subject = "🚨 ClimaScope Alert - High Risk Detected"
    body = f"Risk Level: {level}\nRisk Score: {risk_score}\nReason: {reason}\nTime: {timestamp.isoformat()}"

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

    # 4. Dispatch notifications in a detached async task so this background
    # task returns quickly and does not block request handling.
    if users:
        asyncio.create_task(_dispatch_notifications(users, subject, body))
