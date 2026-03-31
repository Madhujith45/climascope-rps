"""
ClimaScope - Device Management Routes
Handles device registration, listing, and management for authenticated users.
Devices now include API key authentication for edge → backend data ingestion.
"""

from fastapi import APIRouter, HTTPException, Depends, status, Query
from pydantic import BaseModel, Field
from typing import List, Optional
import logging
from datetime import datetime
import uuid

from ..db.mongo import get_mongo_db
from ..db.models.device import DeviceCreate, DeviceResponse, DeviceUpdate
from ..auth.auth_routes import get_current_user
from ..utils.security import generate_api_key, hash_otp as hash_api_key

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/devices", tags=["devices"])

class DeviceListResponse(BaseModel):
    """Response model for device list"""
    devices: List[DeviceResponse] = Field(..., description="List of user devices")
    total: int = Field(..., description="Total number of devices")

@router.post("/add", response_model=DeviceResponse, status_code=status.HTTP_201_CREATED)
async def add_device(
    device_data: DeviceCreate,
    current_user: dict = Depends(get_current_user)
):
    """
    Add a new device for the authenticated user
    """
    try:
        db = get_mongo_db()
        user_id = str(current_user["_id"])
        
        # Generate unique device ID
        device_id = f"device_{uuid.uuid4().hex[:8]}"
        
        # Check if device_id already exists for this user
        existing_device = await db.devices.find_one({
            "user_id": user_id,
            "device_id": device_id
        })
        
        if existing_device:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Device ID already exists"
            )
        
        # Generate secure API key for device authentication
        raw_api_key = generate_api_key()
        hashed_key = hash_api_key(raw_api_key)

        # Prepare device document
        device_doc = {
            "user_id": user_id,
            "device_id": device_id,
            "device_name": device_data.device_name,
            "location": device_data.location,
            "description": device_data.description,
            "api_key_hash": hashed_key,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "is_active": True,
            "last_seen": None
        }
        
        # Insert into database
        result = await db.devices.insert_one(device_doc)
        
        # Prepare response – API key shown ONLY on creation
        response_device = {
            "id": str(result.inserted_id),
            "device_id": device_id,
            "device_name": device_data.device_name,
            "location": device_data.location,
            "description": device_data.description,
            "api_key": raw_api_key,
            "created_at": device_doc["created_at"],
            "last_seen": None,
            "is_active": True
        }
        
        logger.info(f"Device added: {device_id} for user {user_id} (api_key issued)")
        return response_device
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Add device error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add device"
        )

@router.get("/list", response_model=DeviceListResponse)
async def list_devices(
    limit: int = Query(50, ge=1, le=100, description="Number of devices to return"),
    offset: int = Query(0, ge=0, description="Number of devices to skip"),
    current_user: dict = Depends(get_current_user)
):
    """
    List all devices for the authenticated user
    """
    try:
        db = get_mongo_db()
        user_id = str(current_user["_id"])
        
        # Get total count
        total = await db.devices.count_documents({"user_id": user_id})
        
        # Get devices with pagination
        cursor = db.devices.find({"user_id": user_id}).sort("created_at", -1).skip(offset).limit(limit)
        devices = []
        
        async for device in cursor:
            device_response = {
                "id": str(device["_id"]),
                "device_id": device["device_id"],
                "device_name": device["device_name"],
                "location": device.get("location"),
                "description": device.get("description"),
                "created_at": device["created_at"],
                "last_seen": device.get("last_seen"),
                "is_active": device.get("is_active", True)
            }
            devices.append(device_response)
        
        return {
            "devices": devices,
            "total": total
        }
        
    except Exception as e:
        logger.error(f"List devices error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list devices"
        )

@router.get("/{device_id}", response_model=DeviceResponse)
async def get_device(
    device_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get specific device details
    """
    try:
        db = get_mongo_db()
        user_id = str(current_user["_id"])
        
        # Find device
        device = await db.devices.find_one({
            "user_id": user_id,
            "device_id": device_id
        })
        
        if not device:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Device not found"
            )
        
        return {
            "id": str(device["_id"]),
            "device_id": device["device_id"],
            "device_name": device["device_name"],
            "location": device.get("location"),
            "description": device.get("description"),
            "created_at": device["created_at"],
            "last_seen": device.get("last_seen"),
            "is_active": device.get("is_active", True)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get device error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get device"
        )

@router.put("/{device_id}", response_model=DeviceResponse)
async def update_device(
    device_id: str,
    device_update: DeviceUpdate,
    current_user: dict = Depends(get_current_user)
):
    """
    Update device information
    """
    try:
        db = get_mongo_db()
        user_id = str(current_user["_id"])
        
        # Check if device exists and belongs to user
        existing_device = await db.devices.find_one({
            "user_id": user_id,
            "device_id": device_id
        })
        
        if not existing_device:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Device not found"
            )
        
        # Prepare update data
        update_data = {
            "updated_at": datetime.utcnow()
        }
        
        if device_update.device_name is not None:
            update_data["device_name"] = device_update.device_name
        if device_update.location is not None:
            update_data["location"] = device_update.location
        if device_update.description is not None:
            update_data["description"] = device_update.description
        if device_update.is_active is not None:
            update_data["is_active"] = device_update.is_active
        
        # Update device
        await db.devices.update_one(
            {"user_id": user_id, "device_id": device_id},
            {"$set": update_data}
        )
        
        # Get updated device
        updated_device = await db.devices.find_one({
            "user_id": user_id,
            "device_id": device_id
        })
        
        return {
            "id": str(updated_device["_id"]),
            "device_id": updated_device["device_id"],
            "device_name": updated_device["device_name"],
            "location": updated_device.get("location"),
            "description": updated_device.get("description"),
            "created_at": updated_device["created_at"],
            "last_seen": updated_device.get("last_seen"),
            "is_active": updated_device.get("is_active", True)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update device error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update device"
        )

@router.delete("/{device_id}")
async def remove_device(
    device_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Remove a device
    """
    try:
        db = get_mongo_db()
        user_id = str(current_user["_id"])
        
        # Check if device exists and belongs to user
        existing_device = await db.devices.find_one({
            "user_id": user_id,
            "device_id": device_id
        })
        
        if not existing_device:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Device not found"
            )
        
        # Delete device
        result = await db.devices.delete_one({
            "user_id": user_id,
            "device_id": device_id
        })
        
        if result.deleted_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Device not found"
            )
        
        logger.info(f"Device removed: {device_id} for user {user_id}")
        return {"message": "Device removed successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Remove device error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to remove device"
        )

@router.post("/{device_id}/heartbeat")
async def device_heartbeat(
    device_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Update device last seen timestamp (for device health monitoring)
    """
    try:
        db = get_mongo_db()
        user_id = str(current_user["_id"])
        
        # Update last_seen timestamp
        result = await db.devices.update_one(
            {"user_id": user_id, "device_id": device_id},
            {"$set": {"last_seen": datetime.utcnow()}}
        )
        
        if result.modified_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Device not found"
            )
        
        return {"message": "Heartbeat updated"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Device heartbeat error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update heartbeat"
        )
