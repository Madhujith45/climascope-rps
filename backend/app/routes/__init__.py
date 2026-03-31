"""
ClimaScope – Backend Routes Package Init
"""

from .data_routes import router as data_router
from .alert_routes import router as alert_router
from .prediction_routes import router as prediction_router
from .device_routes import router as device_router

__all__ = ["data_router", "alert_router", "prediction_router", "device_router"]

