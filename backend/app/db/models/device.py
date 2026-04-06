"""
ClimaScope - Device Model
Defines device data structures and validation
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class DeviceBase(BaseModel):
    """Base device model with common fields"""
    device_name: str = Field(..., description="Device name")
    location: Optional[str] = Field(None, description="Device location")
    description: Optional[str] = Field(None, description="Device description")

class DeviceCreate(DeviceBase):
    """Device model for creation"""
    pass

class DeviceInDB(DeviceBase):
    """Device model as stored in database"""
    id: str = Field(..., description="Device ID")
    user_id: str = Field(..., description="Owner user ID")
    device_id: str = Field(..., description="Unique device identifier")
    api_key: Optional[str] = Field(None, description="Device API key (hashed in DB)")
    created_at: datetime = Field(..., description="Device creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    is_active: bool = Field(True, description="Device status")
    last_seen: Optional[datetime] = Field(None, description="Last data received timestamp")

class DeviceResponse(BaseModel):
    """Device model for API responses"""
    id: str = Field(..., description="Device ID")
    device_id: str = Field(..., description="Unique device identifier")
    device_name: str = Field(..., description="Device name")
    location: Optional[str] = Field(None, description="Device location")
    description: Optional[str] = Field(None, description="Device description")
    api_key: Optional[str] = Field(None, description="Device API key (shown only on creation)")
    created_at: datetime = Field(..., description="Device creation timestamp")
    last_seen: Optional[datetime] = Field(None, description="Last data received timestamp")
    is_active: bool = Field(True, description="Device status")
    status: Optional[str] = Field(None, description="Device connection status (online/offline/slow)")

class DeviceUpdate(BaseModel):
    """Device model for updates"""
    device_name: Optional[str] = Field(None, description="Device name")
    location: Optional[str] = Field(None, description="Device location")
    description: Optional[str] = Field(None, description="Device description")
    is_active: Optional[bool] = Field(None, description="Device status")

