"""
ClimaScope - Alert System Routes
Handles intelligent alert generation, management, and notifications
"""

from fastapi import APIRouter, HTTPException, Depends, status, Query
from pydantic import BaseModel, Field
from typing import List, Optional
import logging
from datetime import datetime, timedelta
from bson import ObjectId

from ..db.mongo import get_mongo_db
from ..db.models.alert import AlertCreate, AlertResponse, AlertUpdate
from ..auth.auth_routes import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/alerts", tags=["alerts"])

class AlertListResponse(BaseModel):
    """Response model for alert list"""
    alerts: List[AlertResponse] = Field(..., description="List of user alerts")
    total: int = Field(..., description="Total number of alerts")
    unread_count: int = Field(..., description="Number of unread alerts")

@router.get("/", response_model=AlertListResponse)
async def list_alerts(
    limit: int = Query(50, ge=1, le=100, description="Number of alerts to return"),
    offset: int = Query(0, ge=0, description="Number of alerts to skip"),
    severity: Optional[str] = Query(None, description="Filter by severity: warning/danger"),
    unread_only: bool = Query(False, description="Show only unread alerts"),
    current_user: dict = Depends(get_current_user)
):
    """
    List all alerts for the authenticated user
    """
    try:
        db = get_mongo_db()
        user_id = str(current_user["_id"])
        
        # Build query
        query = {"user_id": user_id}
        
        if severity:
            query["severity"] = severity
        if unread_only:
            query["is_read"] = False
        
        # Get total count
        total = await db.alerts.count_documents(query)
        
        # Get unread count
        unread_query = {"user_id": user_id, "is_read": False}
        unread_count = await db.alerts.count_documents(unread_query)
        
        # Get alerts with pagination
        cursor = db.alerts.find(query).sort("created_at", -1).skip(offset).limit(limit)
        alerts = []
        
        async for alert in cursor:
            # Get device name for better context
            device_id = alert.get("device_id") or "unknown_device"
            device = await db.devices.find_one({
                "user_id": user_id,
                "device_id": device_id
            })
            
            alert_response = {
                "id": str(alert["_id"]),
                "device_id": device_id,
                "device_name": (
                    device["device_name"]
                    if device
                    else alert.get("device_name") or "Unknown Device"
                ),
                "message": alert["message"],
                "severity": alert["severity"],
                "alert_type": alert.get("alert_type"),
                "is_read": alert.get("is_read", False),
                "is_resolved": alert.get("is_resolved", False),
                "created_at": alert["created_at"],
                "resolved_at": alert.get("resolved_at")
            }
            alerts.append(alert_response)
        
        return {
            "alerts": alerts,
            "total": total,
            "unread_count": unread_count
        }
        
    except Exception as e:
        logger.error(f"List alerts error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list alerts"
        )

@router.post("/{alert_id}/read")
async def mark_alert_read(
    alert_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Mark an alert as read
    """
    try:
        db = get_mongo_db()
        user_id = str(current_user["_id"])
        
        # Update alert
        result = await db.alerts.update_one(
            {"_id": ObjectId(alert_id), "user_id": user_id},
            {"$set": {"is_read": True}}
        )
        
        if result.modified_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Alert not found"
            )
        
        return {"message": "Alert marked as read"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Mark alert read error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to mark alert as read"
        )

@router.post("/{alert_id}/resolve")
async def resolve_alert(
    alert_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Mark an alert as resolved
    """
    try:
        db = get_mongo_db()
        user_id = str(current_user["_id"])
        
        # Update alert
        result = await db.alerts.update_one(
            {"_id": ObjectId(alert_id), "user_id": user_id},
            {"$set": {"is_resolved": True, "resolved_at": datetime.utcnow()}}
        )
        
        if result.modified_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Alert not found"
            )
        
        return {"message": "Alert marked as resolved"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Resolve alert error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to resolve alert"
        )

@router.delete("/{alert_id}")
async def delete_alert(
    alert_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Delete an alert
    """
    try:
        db = get_mongo_db()
        user_id = str(current_user["_id"])
        
        # Delete alert
        result = await db.alerts.delete_one({
            "_id": ObjectId(alert_id),
            "user_id": user_id
        })
        
        if result.deleted_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Alert not found"
            )
        
        return {"message": "Alert deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete alert error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete alert"
        )

@router.post("/mark-all-read")
async def mark_all_alerts_read(current_user: dict = Depends(get_current_user)):
    """
    Mark all alerts as read for the user
    """
    try:
        db = get_mongo_db()
        user_id = str(current_user["_id"])
        
        # Update all unread alerts
        result = await db.alerts.update_many(
            {"user_id": user_id, "is_read": False},
            {"$set": {"is_read": True}}
        )
        
        return {
            "message": "All alerts marked as read",
            "count": result.modified_count
        }
        
    except Exception as e:
        logger.error(f"Mark all alerts read error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to mark all alerts as read"
        )

@router.get("/stats")
async def get_alert_stats(current_user: dict = Depends(get_current_user)):
    """
    Get alert statistics for the user
    """
    try:
        db = get_mongo_db()
        user_id = str(current_user["_id"])
        
        # Get counts by severity
        warning_count = await db.alerts.count_documents({
            "user_id": user_id,
            "severity": "warning"
        })
        
        danger_count = await db.alerts.count_documents({
            "user_id": user_id,
            "severity": "danger"
        })
        
        unread_count = await db.alerts.count_documents({
            "user_id": user_id,
            "is_read": False
        })
        
        resolved_count = await db.alerts.count_documents({
            "user_id": user_id,
            "is_resolved": True
        })
        
        # Get recent alerts (last 24 hours)
        yesterday = datetime.utcnow() - timedelta(days=1)
        recent_count = await db.alerts.count_documents({
            "user_id": user_id,
            "created_at": {"$gte": yesterday}
        })
        
        return {
            "total_warning": warning_count,
            "total_danger": danger_count,
            "unread_count": unread_count,
            "resolved_count": resolved_count,
            "recent_count": recent_count,
            "total": warning_count + danger_count
        }
        
    except Exception as e:
        logger.error(f"Get alert stats error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get alert statistics"
        )

# Alert generation function (to be called from prediction routes)
async def generate_alert(user_id: str, device_id: str, message: str, severity: str, alert_type: str = None):
    """
    Generate and store an alert automatically
    """
    try:
        db = get_mongo_db()
        
        # Create alert document
        alert_doc = {
            "user_id": user_id,
            "device_id": device_id,
            "message": message,
            "severity": severity,
            "alert_type": alert_type,
            "is_read": False,
            "is_resolved": False,
            "created_at": datetime.utcnow()
        }
        
        # Insert alert
        result = await db.alerts.insert_one(alert_doc)
        
        logger.info(f"Alert generated: {severity} - {message[:50]}...")
        return str(result.inserted_id)
        
    except Exception as e:
        logger.error(f"Generate alert error: {str(e)}")
        return None
