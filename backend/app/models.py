"""
ClimaScope – Backend SQLAlchemy Models
"""

from sqlalchemy import Boolean, Column, Integer, Float, String, Text
from .database import Base


class EnvironmentalData(Base):
    """Stores sensor readings forwarded from edge devices.

    Core fields (always present):
        device_id, timestamp, temperature, pressure, mq2_voltage, gas_ppm

    Legacy / extended fields (nullable – populated when the full risk
    pipeline runs on the edge):
        humidity, gas, risk_score, risk_level, anomaly_flag, risk_reason
    """

    __tablename__ = "environmental_data"

    id           = Column(Integer,     primary_key=True, index=True, autoincrement=True)
    device_id    = Column(String(64),  nullable=True,  index=True)
    timestamp    = Column(String(32),  nullable=False, index=True)
    temperature  = Column(Float,       nullable=False)
    pressure     = Column(Float,       nullable=False)
    mq2_voltage  = Column(Float,       nullable=True)
    gas_ppm      = Column(Float,       nullable=True)
    # Legacy / extended columns kept for backward compatibility
    humidity     = Column(Float,       nullable=True)
    gas          = Column(Float,       nullable=True)
    risk_score   = Column(Integer,     nullable=True)
    risk_level   = Column(String(16),  nullable=True)
    anomaly_flag = Column(Boolean,     nullable=False, default=False)
    risk_reason  = Column(Text,        nullable=True)
