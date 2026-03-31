"""
ClimaScope – Runtime Anomaly Detector
======================================

Loads the pre-trained Isolation Forest model (anomaly_model.pkl) once at
import time and exposes a single function:

    detect(temperature, pressure, gas_ppm, mq2_voltage)
        → (anomaly_flag: bool, risk_reason: str | None)

If the model file does not exist yet (i.e. the trainer has not been run),
detection falls back gracefully to rule-based thresholds so the API still
works without a trained model.

Rule-based thresholds (fallback + reason generation):
    gas_ppm      > 250   → "Gas spike detected"
    temperature  > 42    → "Temperature spike detected"
    pressure drop        → detected via IsolationForest score only
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

_THIS_DIR  = Path(__file__).parent.resolve()
MODEL_PATH = _THIS_DIR / "anomaly_model.pkl"

# ── Rule-based thresholds (always applied for human-readable reasons) ─────────
_GAS_SPIKE_PPM    = 250.0
_TEMP_SPIKE_C     = 42.0
_PRESSURE_LOW_HPA = 970.0   # anything below this is suspicious

# ── Model singleton ────────────────────────────────────────────────────────────
_model_bundle: Optional[dict] = None
_model_load_attempted = False


def _load_model() -> Optional[dict]:
    """Load the model bundle from disk exactly once."""
    global _model_bundle, _model_load_attempted
    if _model_load_attempted:
        return _model_bundle

    _model_load_attempted = True
    if not MODEL_PATH.exists():
        logger.warning(
            "Anomaly model not found at %s. "
            "Run train_anomaly_model.py to train it. "
            "Falling back to rule-based detection.",
            MODEL_PATH,
        )
        _model_bundle = None
        return None

    try:
        import joblib
        bundle = joblib.load(str(MODEL_PATH))
        _model_bundle = bundle
        logger.info(
            "Anomaly model loaded from %s  (contamination=%.0f%%)",
            MODEL_PATH,
            bundle.get("contamination", 0) * 100,
        )
        return _model_bundle
    except Exception as exc:
        logger.error("Failed to load anomaly model: %s", exc)
        _model_bundle = None
        return None


def _rule_based_reasons(
    temperature: float,
    pressure: float,
    gas_ppm: float,
    mq2_voltage: float,
) -> list[str]:
    """Return a list of human-readable anomaly reasons based on thresholds."""
    reasons: list[str] = []
    if gas_ppm > _GAS_SPIKE_PPM:
        reasons.append(f"Gas spike detected: {gas_ppm:.1f} ppm (>{_GAS_SPIKE_PPM:.0f})")
    if temperature > _TEMP_SPIKE_C:
        reasons.append(f"Temperature spike: {temperature:.1f} °C (>{_TEMP_SPIKE_C:.0f})")
    if pressure < _PRESSURE_LOW_HPA:
        reasons.append(f"Pressure anomaly: {pressure:.1f} hPa (<{_PRESSURE_LOW_HPA:.0f})")
    return reasons


def detect(
    temperature: float,
    pressure: float,
    gas_ppm: float,
    mq2_voltage: float,
) -> Tuple[bool, Optional[str]]:
    """
    Classify one sensor reading.

    Parameters
    ----------
    temperature  : °C
    pressure     : hPa
    gas_ppm      : ppm
    mq2_voltage  : V

    Returns
    -------
    (anomaly_flag, risk_reason)
        anomaly_flag  – True if the reading is anomalous
        risk_reason   – Human-readable explanation, or None if normal
    """
    bundle = _load_model()

    # ── Rule-based reasons (always computed) ──────────────────────────────────
    rule_reasons = _rule_based_reasons(temperature, pressure, gas_ppm, mq2_voltage)

    is_anomaly = False

    if bundle is not None:
        # ── Model-based detection ─────────────────────────────────────────────
        try:
            import numpy as np
            X = np.array([[temperature, pressure, gas_ppm, mq2_voltage]], dtype=float)
            pipeline = bundle["pipeline"]

            prediction = pipeline.predict(X)[0]   # 1 = normal, -1 = anomaly
            score      = float(pipeline.decision_function(X)[0])

            is_anomaly = (prediction == -1)

            if is_anomaly and not rule_reasons:
                # Model caught something the rules didn't — add a generic reason
                rule_reasons.append(
                    f"Statistical anomaly detected (score={score:.4f})"
                )

            logger.debug(
                "detect T=%.2f P=%.2f gas=%.2f mq2=%.3f → %s  score=%.4f",
                temperature, pressure, gas_ppm, mq2_voltage,
                "ANOMALY" if is_anomaly else "normal",
                score,
            )
        except Exception as exc:
            logger.error("Model inference error: %s – falling back to rules", exc)
            # Fall through to rule-based below

    else:
        # ── Fallback: rule-based only ──────────────────────────────────────────
        is_anomaly = len(rule_reasons) > 0

    risk_reason = "; ".join(rule_reasons) if rule_reasons else None
    return is_anomaly, risk_reason


def reload_model() -> None:
    """Force re-load the model from disk (call after re-training)."""
    global _model_bundle, _model_load_attempted
    _model_bundle = None
    _model_load_attempted = False
    _load_model()
