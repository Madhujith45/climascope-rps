"""
ClimaScope – DHT22 Temperature & Humidity Sensor Driver
Reads temperature and humidity from a DHT22 sensor wired to a GPIO pin.
Falls back to simulated values when the hardware library is unavailable
(useful for off-device development / testing).
"""

import time
import logging

logger = logging.getLogger(__name__)

# Try to import the real hardware library; gracefully degrade on non-Pi systems.
try:
    import adafruit_dht  # type: ignore
    import board  # type: ignore
    _HARDWARE_AVAILABLE = True
    # Initialize sensor on BCM pin 4 (board.D4)
    _SENSOR = adafruit_dht.DHT22(board.D4)
except (ImportError, RuntimeError, AttributeError):
    _HARDWARE_AVAILABLE = False
    logger.warning("adafruit_dht or board not found – DHT22 will return SIMULATED data.")
    _SENSOR = None  # type: ignore

# GPIO pin number (BCM numbering) where the DHT22 data line is connected.
DHT22_GPIO_PIN: int = 4

# Maximum consecutive read failures before raising an exception.
MAX_RETRIES: int = 3
RETRY_DELAY_S: float = 2.0


def read_dht22() -> dict:
    """
    Read temperature (°C) and relative humidity (%) from the DHT22 sensor.

    Returns
    -------
    dict with keys:
        temperature : float  – degrees Celsius
        humidity    : float  – percent relative humidity

    Raises
    ------
    RuntimeError if the sensor cannot be read after MAX_RETRIES attempts.
    """
    if not _HARDWARE_AVAILABLE:
        return _simulated_reading()

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            temperature = _SENSOR.temperature
            humidity = _SENSOR.humidity
            if temperature is not None and humidity is not None:
                # Sanity-clamp to physically plausible ranges.
                temperature = max(-40.0, min(80.0, float(temperature)))
                humidity = max(0.0, min(100.0, float(humidity)))
                logger.debug(
                    "DHT22 reading: temp=%.2f°C  hum=%.2f%%", temperature, humidity
                )
                return {"temperature": temperature, "humidity": humidity}
        except (RuntimeError, OSError) as e:
            # CircuitPython DHT raises RuntimeError or OSError on read failure
            logger.warning("DHT22 read failure (attempt %d/%d): %s", attempt, MAX_RETRIES, e)
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY_S)
            continue

    raise RuntimeError(
        f"DHT22 unreadable after {MAX_RETRIES} attempts on GPIO {DHT22_GPIO_PIN}"
    )


def _simulated_reading() -> dict:
    """Return plausible simulated DHT22 values for off-hardware development."""
    import random, math

    t = round(22.0 + 5.0 * math.sin(time.time() / 300) + random.gauss(0, 0.3), 2)
    h = round(55.0 + 10.0 * math.sin(time.time() / 600) + random.gauss(0, 0.5), 2)
    return {"temperature": t, "humidity": h}
