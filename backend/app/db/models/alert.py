"""
ClimaScope - Alert Model
Defines alert data structures and validation
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class AlertBase(BaseModel):
    """Base alert model with common fields"""
    message: str = Field(..., description="Alert message")
    severity: str = Field(..., description="Alert severity: warning/danger")

class AlertCreate(AlertBase):
    """Alert model for creation"""
    device_id: str = Field(..., description="Device identifier")
    alert_type: Optional[str] = Field(None, description="Alert type")

class AlertInDB(AlertBase):
    """Alert model as stored in database"""
    id: str = Field(..., description="Alert ID")
    user_id: str = Field(..., description="Owner user ID")
    device_id: str = Field(..., description="Device identifier")
    alert_type: Optional[str] = Field(None, description="Alert type")
    is_read: bool = Field(False, description="Alert read status")
    is_resolved: bool = Field(False, description="Alert resolution status")
    created_at: datetime = Field(..., description="Alert creation timestamp")
    resolved_at: Optional[datetime] = Field(None, description="Alert resolution timestamp")

class AlertResponse(BaseModel):
    """Alert model for API responses"""
    id: str = Field(..., description="Alert ID")
    device_id: str = Field(..., description="Device identifier")
    device_name: Optional[str] = Field(None, description="Device name")
    message: str = Field(..., description="Alert message")
    severity: str = Field(..., description="Alert severity: warning/danger")
    alert_type: Optional[str] = Field(None, description="Alert type")
    is_read: bool = Field(False, description="Alert read status")
    is_resolved: bool = Field(False, description="Alert resolution status")
    created_at: datetime = Field(..., description="Alert creation timestamp")
    resolved_at: Optional[datetime] = Field(None, description="Alert resolution timestamp")

class AlertUpdate(BaseModel):
    """Alert model for updates"""
    is_read: Optional[bool] = Field(None, description="Alert read status")
    is_resolved: Optional[bool] = Field(None, description="Alert resolution status")
