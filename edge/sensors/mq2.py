"""
ClimaScope – MQ2 Gas Sensor Driver (via ADS1115 ADC over I2C)

The MQ2 is an analog sensor; the Raspberry Pi has no built-in ADC, so an
ADS1115 16-bit ADC is wired on the same I2C bus (default address 0x48).

The raw ADC value is converted to a normalised 0–100 gas index:
    gas_index = (adc_voltage / 3.3) * 100

Falls back to simulated values on non-Pi systems.
"""

import time
import logging

logger = logging.getLogger(__name__)

try:
    import board  # type: ignore
    import busio  # type: ignore
    import adafruit_ads1x15.ads1115 as ADS  # type: ignore
    from adafruit_ads1x15.analog_in import AnalogIn  # type: ignore
    _HARDWARE_AVAILABLE = True
except ImportError:
    _HARDWARE_AVAILABLE = False
    logger.warning(
        "adafruit_ads1x15 not found – MQ2/ADS1115 will return SIMULATED data."
    )

# ADS1115 I2C address (ADDR pin → GND = 0x48)
ADS1115_ADDRESS: int = 0x48

# The MQ2 analogue output is wired to ADS1115 channel A0.
ADS_CHANNEL = 0  # A0

# ADS1115 gain setting: GAIN_ONE → ±4.096 V full-scale
ADS_GAIN: int = 1

# Operating supply voltage of the MQ2 (determines maximum expected output)
MQ2_VCC: float = 3.3

_ads_device = None
_ads_channel_obj = None


def _init_ads1115():
    """Initialise ADS1115 and return (ads_device, channel_object)."""
    global _ads_device, _ads_channel_obj
    i2c = busio.I2C(board.SCL, board.SDA)
    _ads_device = ADS.ADS1115(i2c, address=ADS1115_ADDRESS)
    _ads_device.gain = ADS_GAIN
    _ads_channel_obj = AnalogIn(_ads_device, ADS_CHANNEL)


def read_mq2() -> dict:
    """
    Read the MQ2 gas sensor value via the ADS1115 ADC.

    Returns
    -------
    dict with keys:
        gas_raw     : int   – raw 16-bit ADC value (0–32767)
        gas_voltage : float – computed voltage (0–3.3 V)
        gas_index   : float – normalised gas concentration index (0–100)
    """
    if not _HARDWARE_AVAILABLE:
        return _simulated_reading()

    global _ads_device, _ads_channel_obj
    try:
        if _ads_device is None or _ads_channel_obj is None:
            _init_ads1115()

        raw = _ads_channel_obj.value           # 16-bit signed integer
        voltage = _ads_channel_obj.voltage     # float in volts

        # Clamp to positive range (ADS1115 can return small negatives at zero)
        raw = max(0, raw)
        voltage = max(0.0, min(MQ2_VCC, voltage))

        gas_index = round((voltage / MQ2_VCC) * 100.0, 2)

        logger.debug(
            "MQ2: raw=%d  voltage=%.4fV  gas_index=%.2f", raw, voltage, gas_index
        )
        return {"gas_raw": raw, "gas_voltage": voltage, "gas_index": gas_index}

    except Exception as exc:
        _ads_device = None
        _ads_channel_obj = None
        raise RuntimeError(f"MQ2/ADS1115 read failed: {exc}") from exc


def _simulated_reading() -> dict:
    """Return plausible simulated MQ2 values for off-hardware development."""
    import random, math

    # Occasional synthetic gas spike to exercise the anomaly detector.
    base = 15.0
    spike = 0.0
    if random.random() < 0.03:           # 3 % chance of a spike
        spike = random.uniform(30.0, 60.0)

    gas_index = round(
        base + spike + 5.0 * math.sin(time.time() / 120) + random.gauss(0, 1.0), 2
    )
    gas_index = max(0.0, min(100.0, gas_index))
    voltage = round((gas_index / 100.0) * MQ2_VCC, 4)
    raw = int((voltage / 4.096) * 32767)
    return {"gas_raw": raw, "gas_voltage": voltage, "gas_index": gas_index}
