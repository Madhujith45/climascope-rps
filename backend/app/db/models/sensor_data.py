"""
ClimaScope - Sensor Data Model
Defines sensor data structures and validation
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class SensorDataBase(BaseModel):
    """Base sensor data model with common fields"""
    temperature: float = Field(..., description="Temperature reading (°C)")
    humidity: float = Field(..., description="Humidity reading (%)")
    pressure: float = Field(..., description="Pressure reading (hPa)")
    gas_voltage: float = Field(..., description="Gas sensor voltage (V)")
    gas_ppm: float = Field(..., description="Gas concentration (PPM)")

class SensorDataCreate(SensorDataBase):
    """Sensor data model for creation"""
    device_id: str = Field(..., description="Device identifier")
    prediction: Optional[float] = Field(None, description="ML prediction")
    health_score: Optional[int] = Field(None, description="System health score (0-100)")
    status: Optional[str] = Field(None, description="System status")
    anomaly: Optional[bool] = Field(None, description="Anomaly detected")
    anomaly_score: Optional[float] = Field(None, description="Anomaly severity score")

class SensorDataInDB(SensorDataBase):
    """Sensor data model as stored in database"""
    id: str = Field(..., description="Data record ID")
    device_id: str = Field(..., description="Device identifier")
    user_id: str = Field(..., description="Owner user ID")
    prediction: Optional[float] = Field(None, description="ML prediction")
    health_score: Optional[int] = Field(None, description="System health score (0-100)")
    status: Optional[str] = Field(None, description="System status")
    anomaly: Optional[bool] = Field(None, description="Anomaly detected")
    anomaly_score: Optional[float] = Field(None, description="Anomaly severity score")
    timestamp: datetime = Field(..., description="Reading timestamp")

class SensorDataResponse(BaseModel):
    """Sensor data model for API responses"""
    id: str = Field(..., description="Data record ID")
    device_id: str = Field(..., description="Device identifier")
    temperature: float = Field(..., description="Temperature reading (°C)")
    humidity: float = Field(..., description="Humidity reading (%)")
    pressure: float = Field(..., description="Pressure reading (hPa)")
    gas_voltage: float = Field(..., description="Gas sensor voltage (V)")
    gas_ppm: float = Field(..., description="Gas concentration (PPM)")
    prediction: Optional[float] = Field(None, description="ML prediction")
    health_score: Optional[int] = Field(None, description="System health score (0-100)")
    status: Optional[str] = Field(None, description="System status")
    anomaly: Optional[bool] = Field(None, description="Anomaly detected")
    anomaly_score: Optional[float] = Field(None, description="Anomaly severity score")
    timestamp: datetime = Field(..., description="Reading timestamp")
