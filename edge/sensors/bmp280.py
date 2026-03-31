"""
ClimaScope – BMP280 Pressure & Temperature Sensor Driver
Communicates over I2C (default address 0x76, or 0x77 when SDO pulled high).
Falls back to simulated values on non-Pi systems.
"""

import time
import logging

logger = logging.getLogger(__name__)

try:
    import board  # type: ignore
    import busio  # type: ignore
    import adafruit_bmp280  # type: ignore
    _HARDWARE_AVAILABLE = True
except ImportError:
    _HARDWARE_AVAILABLE = False
    logger.warning("adafruit_bmp280 not found – BMP280 will return SIMULATED data.")

# Sea-level reference pressure used for altitude calculation (hPa).
SEA_LEVEL_PRESSURE_HPA: float = 1013.25


def _init_bmp280():
    """Initialise and return an Adafruit BMP280 I2C device object."""
    i2c = busio.I2C(board.SCL, board.SDA)
    sensor = adafruit_bmp280.Adafruit_BMP280_I2C(i2c, address=0x76)
    sensor.sea_level_pressure = SEA_LEVEL_PRESSURE_HPA
    return sensor


# Module-level singleton so we don't re-open I2C on every reading.
_bmp280_device = None


def read_bmp280() -> dict:
    """
    Read barometric pressure (hPa) and temperature (°C) from the BMP280.

    Returns
    -------
    dict with keys:
        pressure    : float  – hectopascals (hPa)
        temperature : float  – degrees Celsius (secondary, for cross-check)
        altitude    : float  – estimated metres above sea level
    """
    if not _HARDWARE_AVAILABLE:
        return _simulated_reading()

    global _bmp280_device
    try:
        if _bmp280_device is None:
            _bmp280_device = _init_bmp280()

        pressure = float(_bmp280_device.pressure)
        temperature = float(_bmp280_device.temperature)
        altitude = float(_bmp280_device.altitude)

        # Sanity bounds
        pressure = max(800.0, min(1200.0, pressure))
        temperature = max(-40.0, min(85.0, temperature))

        logger.debug(
            "BMP280: pressure=%.2f hPa  temp=%.2f°C  alt=%.2f m",
            pressure, temperature, altitude,
        )
        return {"pressure": pressure, "temperature": temperature, "altitude": altitude}

    except Exception as exc:
        # On I2C errors reset the device object so it is re-initialised next call.
        _bmp280_device = None
        raise RuntimeError(f"BMP280 read failed: {exc}") from exc


def _simulated_reading() -> dict:
    """Return plausible simulated BMP280 values for off-hardware development."""
    import random, math

    base_pressure = 1013.25
    p = round(
        base_pressure + 3.0 * math.sin(time.time() / 1800) + random.gauss(0, 0.2), 2
    )
    t = round(23.0 + random.gauss(0, 0.4), 2)
    alt = round(44330.0 * (1.0 - (p / base_pressure) ** (1.0 / 5.255)), 2)
    return {"pressure": p, "temperature": t, "altitude": alt}
