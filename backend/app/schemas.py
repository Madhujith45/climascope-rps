"""
ClimaScope – Backend Pydantic Schemas
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class SensorDataIn(BaseModel):
    """Payload received from an edge device via POST /api/data.

    Required core fields match the raw sensor output:
        device_id, timestamp, temperature, pressure, mq2_voltage, gas_ppm

    Optional extended fields are populated when the full risk pipeline
    runs on the edge device:
        humidity, risk_score, risk_level, anomaly_flag, risk_reason
    """

    device_id:    str   = Field(..., description="Unique edge device identifier, e.g. 'climascope_001'")
    timestamp:    str   = Field(..., description="ISO-8601 timestamp, e.g. '2026-02-28T14:09:31'")
    temperature:  float = Field(..., ge=-40,  le=80,   description="Ambient temperature in °C")
    pressure:     float = Field(..., ge=800,  le=1200, description="Atmospheric pressure in hPa")
    mq2_voltage:  float = Field(..., ge=0,    le=5,    description="MQ2 sensor raw voltage (V)")
    gas_ppm:      float = Field(..., ge=0,              description="Gas concentration in PPM")
    # Device authentication
    api_key:      Optional[str] = Field(None, description="Device API key for authentication")
    # Optional legacy / extended fields
    humidity:     Optional[float] = Field(None, ge=0, le=100, description="Relative humidity % RH")
    risk_score:   Optional[int]   = Field(None, ge=0, le=100, description="Computed risk score 0–100")
    risk_level:   Optional[str]   = Field(None, pattern="^(SAFE|MODERATE|HIGH)$")
    anomaly_flag: bool             = False
    risk_reason:  Optional[str]   = None
    risk_local:   Optional[str]   = Field(None, pattern="^(SAFE|MODERATE|HIGH)$")

    @field_validator("timestamp")
    @classmethod
    def validate_timestamp(cls, v: str) -> str:
        """Accept ISO-8601 strings; raises if the format is unrecognisable."""
        try:
            datetime.fromisoformat(v)
        except ValueError as exc:
            raise ValueError(
                f"timestamp must be ISO-8601, e.g. '2026-02-28T14:09:31'. Got: {v!r}"
            ) from exc
        return v

    @field_validator("risk_level", mode="before")
    @classmethod
    def risk_level_upper(cls, v: Optional[str]) -> Optional[str]:
        return v.upper() if v else v


class SensorDataOut(BaseModel):
    """Full record returned to API clients."""

    id:           str
    device_id:    Optional[str]
    timestamp:    str
    temperature:  float
    pressure:     float
    mq2_voltage:  Optional[float]
    gas_ppm:      Optional[float]
    # Legacy / extended fields
    humidity:     Optional[float]
    gas:          Optional[float]
    risk_score:   Optional[int]
    risk_level:   Optional[str]
    risk_local:   Optional[str]
    anomaly_flag: bool
    risk_reason:  Optional[str]

    model_config = {"from_attributes": True}


class AlertOut(BaseModel):
    """Simplified alert record for the /alerts endpoint."""

    id:          int
    timestamp:   str
    risk_score:  int
    risk_level:  str
    risk_reason: Optional[str]
    anomaly_flag: bool

    model_config = {"from_attributes": True}


class HistoryResponse(BaseModel):
    total:   int
    records: List[SensorDataOut]


class StatusResponse(BaseModel):
    status:  str
    message: str
