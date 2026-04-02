from fastapi import APIRouter, BackgroundTasks, Request
from app.services.alert_service import trigger_alert
import app.services.alert_service as alert_service 
import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["development"])

@router.get("/test-alert")
async def test_alert(request: Request, background_tasks: BackgroundTasks):
    risk = int(request.query_params.get("risk", 85))
    
    # 3. LOGGING (No sensitive user info included)
    logger.info("Test alert triggered")
    
    # Bypass the 5-minute throttling exclusively for this test run
    alert_service._last_alert_time = None
    
    test_data = {
        "temperature": 50.0,
        "humidity": 90.0,
        "gas": 500.0,
        "pressure": 900.0,
        "risk_score": float(risk),
        "anomaly": True
    }
    
    reason = "TEST ALERT: Simulated high risk environmental conditions."
    
    logger.info("Sending SMS")
    logger.info("Sending Email")
    
    # Call the existing alert_service in background
    background_tasks.add_task(trigger_alert, float(risk), "HIGH", reason)
    
    return {
        "message": "Test alert triggered successfully",
        "risk": risk,
        "status": "Check terminal for logs"
    }
