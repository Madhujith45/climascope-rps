"""
ClimaScope – Edge AI Processing Engine  (hardened v2)
======================================================
Implements the complete risk scoring pipeline that runs entirely on the
Raspberry Pi (no cloud dependency):

  1. Ingest raw sensor readings into an in-memory rolling window (size = 10).
  2. Compute rolling mean and rolling standard deviation per metric.
     → std is clamped to a minimum epsilon so Z-scores never blow up.
  3. Compute Z-score for the latest reading of each metric.
     → |z| is capped at Z_SCORE_CAP (5.0) before any normalisation.
  4. Compute rate-of-change (delta from the previous reading).
  5. Normalise each feature independently to [0, 1] using its own physical-
     maximum constant (MAX_GAS_SPIKE, MAX_PRESSURE_GRAD, MAX_TEMP_ROC,
     MAX_HUMIDITY_ROC).
  6. Apply a verified, assertion-checked weight vector (must sum to 1.0).
  7. Smooth the raw score with an EMA:
       risk_smoothed = 0.7 * previous_risk + 0.3 * new_risk
  8. Clamp the smoothed score to [0, 100] and round to integer.
  9. Classify as SAFE / MODERATE / HIGH using explicit boundary comparisons.
 10. Generate a human-readable risk explanation list.
 11. Emit structured DEBUG log lines covering every intermediate quantity.

Risk weight matrix
------------------
  Gas spike magnitude         30 %
  Pressure gradient           25 %
  Temperature rate-of-change  20 %
  Humidity rate-of-change     15 %
  Anomaly flag                10 %
  ─────────────────────────────────
  TOTAL                      100 %
"""

from __future__ import annotations

import logging
import math
from collections import deque
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Module-level DEBUG helper
# Structured debug logging is enabled automatically when the logger's effective
# level is DEBUG.  No separate flag needed – callers simply set:
#   logging.getLogger("climascope.processing").setLevel(logging.DEBUG)
# or set CLIMASCOPE_LOG_LEVEL=DEBUG in the environment.
# ─────────────────────────────────────────────────────────────────────────────

def _dbg(msg: str, *args) -> None:
    """Emit a debug log line only when DEBUG is active (zero-cost otherwise)."""
    if logger.isEnabledFor(logging.DEBUG):
        logger.debug(msg, *args)


# ─────────────────────────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────────────────────────

WINDOW_SIZE: int = 10          # rolling-window length (samples)

# ── Numerical stability ───────────────────────────────────────────────────────
# Minimum standard deviation clamped inside _RollingBuffer.std().
# Prevents Z-score blow-up when readings are perfectly or near-perfectly constant.
STD_EPSILON: float = 1e-4

# Maximum absolute Z-score accepted by the pipeline.
# Any |z| > Z_SCORE_CAP is saturated to ±Z_SCORE_CAP before further processing.
Z_SCORE_CAP: float = 5.0

# ── Anomaly detection ─────────────────────────────────────────────────────────
# Reading is flagged as an anomaly when |z| exceeds this threshold for any metric.
Z_SCORE_THRESHOLD: float = 2.5

# ── Classification boundaries ─────────────────────────────────────────────────
# Explicit, inclusive upper bounds so logic is unambiguous:
#   0  <= score <= SAFE_MAX       → SAFE
#   SAFE_MAX < score <= MOD_MAX   → MODERATE
#   MOD_MAX  < score <= 100       → HIGH
SAFE_MAX: int = 30
MOD_MAX:  int = 65

# ── Normalisation maximum ranges (feature-specific) ──────────────────────────
# Per-feature saturation points: values at or above these map to norm = 1.0.
# Tune these to your deployment environment; they do not affect weight ratios.
MAX_GAS_SPIKE:      float = 40.0   # gas index units above rolling mean
MAX_PRESSURE_GRAD:  float = 5.0    # hPa per sample
MAX_TEMP_ROC:       float = 3.0    # °C  per sample
MAX_HUMIDITY_ROC:   float = 10.0   # %RH per sample
MAX_GAS_ACCEL:      float = 10.0   # gas index units per sample squared
MAX_PRESSURE_ACCEL: float = 2.0    # hPa per sample squared

# ── Risk weights ──────────────────────────────────────────────────────────────
# Must sum to exactly 1.0 – verified at import time by the assertion below.
WEIGHTS: dict[str, float] = {
    "gas_spike":         0.25,
    "pressure_gradient": 0.20,
    "temp_roc":          0.15,
    "humidity_roc":      0.10,
    "acceleration":      0.20,
    "anomaly_flag":      0.10,
}
# Hardening fix 4: assert weight sum at module load so misconfiguration is
# caught immediately rather than silently producing wrong scores.
assert abs(sum(WEIGHTS.values()) - 1.0) < 1e-9, (
    f"WEIGHTS must sum to 1.0; got {sum(WEIGHTS.values()):.10f}"
)

# ── EMA smoothing coefficients ────────────────────────────────────────────────
# risk_smoothed = EMA_PREV * previous_risk + EMA_NEW * new_risk
EMA_PREV: float = 0.7
EMA_NEW:  float = 0.3
assert abs(EMA_PREV + EMA_NEW - 1.0) < 1e-9, "EMA coefficients must sum to 1.0"


# ─────────────────────────────────────────────────────────────────────────────
# Internal rolling-buffer
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class _RollingBuffer:
    """Fixed-length deque with stable statistics helpers."""

    maxlen: int
    _buf: deque = field(default_factory=deque)

    def __post_init__(self) -> None:
        self._buf = deque(maxlen=self.maxlen)

    def push(self, value: float) -> None:
        self._buf.append(value)

    def mean(self) -> Optional[float]:
        if not self._buf:
            return None
        return sum(self._buf) / len(self._buf)

    def std(self) -> Optional[float]:
        """
        Sample standard deviation (Bessel-corrected, n-1 denominator).

        Returns None when fewer than 2 samples are present.
        Otherwise the result is clamped to STD_EPSILON so callers never
        receive zero, eliminating any risk of division-by-zero or
        extreme Z-score amplification (hardening fix 1).
        """
        n = len(self._buf)
        if n < 2:
            return None
        m = self.mean()
        variance = sum((x - m) ** 2 for x in self._buf) / (n - 1)
        raw_std = math.sqrt(variance)
        # Hardening fix 1: floor to STD_EPSILON – prevents ÷0 and Z-score
        # explosion when a sensor is stuck at a constant value.
        return max(raw_std, STD_EPSILON)

    def latest(self) -> Optional[float]:
        return self._buf[-1] if self._buf else None

    def previous(self) -> Optional[float]:
        return self._buf[-2] if len(self._buf) >= 2 else None

    def acceleration(self) -> float:
        """
        Compute the second derivative: (x_t - x_{t-1}) - (x_{t-1} - x_{t-2}).
        Formula: x_t - 2*x_{t-1} + x_{t-2}.
        Returns 0.0 if fewer than 3 samples.
        """
        if len(self._buf) < 3:
            return 0.0
        # self._buf[-1] is latest (t)
        # self._buf[-2] is previous (t-1)
        # self._buf[-3] is previous-previous (t-2)
        return self._buf[-1] - 2 * self._buf[-2] + self._buf[-3]


# ─────────────────────────────────────────────────────────────────────────────
# Processing engine
# ─────────────────────────────────────────────────────────────────────────────

class ProcessingEngine:
    """
    Stateful processing engine.

    A single instance is kept alive for the lifetime of the edge process so
    the rolling windows and the EMA risk state persist across samples.
    """

    def __init__(self, window: int = WINDOW_SIZE) -> None:
        self._temp     = _RollingBuffer(window)
        self._humidity = _RollingBuffer(window)
        self._pressure = _RollingBuffer(window)
        self._gas      = _RollingBuffer(window)

        # Hardening fix 5: EMA state – start at 0 (no prior risk assumed).
        # Stored as float so arithmetic stays in floating-point until the
        # final int(round(...)) conversion.
        self._prev_risk_score: float = 0.0

    # ── Public API ────────────────────────────────────────────────────────────

    def process(self, raw: dict) -> dict:
        """
        Ingest one dict of raw sensor readings and return a fully enriched
        payload ready for storage and transmission.

        Parameters
        ----------
        raw : dict
            Must contain: temperature, humidity, pressure, gas_index

        Returns
        -------
        dict with all raw fields plus:
            temp_mean / temp_std / humidity_mean / humidity_std /
            pressure_mean / pressure_std / gas_mean / gas_std
            temp_roc / humidity_roc / pressure_roc / gas_roc
            z_temp / z_humidity / z_pressure / z_gas
            anomaly_flag
            risk_score      (EMA-smoothed, clamped to [0, 100])
            risk_level      (SAFE | MODERATE | HIGH)
            risk_reason     (semicolon-delimited explanation string)
        """
        temp     = float(raw["temperature"])
        humidity = float(raw["humidity"])
        pressure = float(raw["pressure"])
        gas      = float(raw["gas_index"])

        # 1. Push into rolling windows
        self._temp.push(temp)
        self._humidity.push(humidity)
        self._pressure.push(pressure)
        self._gas.push(gas)

        # 2. Rolling statistics
        stats = self._compute_stats()

        # 3. Rate-of-change
        roc = self._compute_roc()

        # 4. Acceleration (instability)
        accel = self._compute_accel()

        # 5. Z-scores (capped) and anomaly flag
        z_scores = self._compute_z_scores(temp, humidity, pressure, gas, stats)
        anomaly_flag = any(abs(z) > Z_SCORE_THRESHOLD for z in z_scores.values())

        # 6–7. Risk scoring (returns pre-smoothing integer)
        raw_risk, _, risk_reason = self._compute_risk(
            gas_current  = gas,
            gas_mean     = stats["gas_mean"],
            pressure_roc = roc["pressure_roc"],
            temp_roc     = roc["temp_roc"],
            humidity_roc = roc["humidity_roc"],
            gas_accel    = accel["gas_accel"],
            pressure_accel = accel["pressure_accel"],
            anomaly_flag = anomaly_flag,
        )

        # Hardening fix 5: EMA smoothing
        #   risk_smoothed = 0.7 * previous_risk + 0.3 * new_risk
        smoothed = EMA_PREV * self._prev_risk_score + EMA_NEW * float(raw_risk)

        # Hardening fix 6: clamp smoothed result to [0, 100] before rounding
        risk_score = int(round(max(0.0, min(100.0, smoothed))))

        # Update EMA state for the next sample
        self._prev_risk_score = float(risk_score)

        # Hardening fix 7: re-classify using the smoothed score so the
        # displayed level always matches the displayed number exactly.
        risk_level = _classify(risk_score)

        _dbg(
            "EMA smoothing: raw=%d  prev=%.2f  smoothed=%.4f  "
            "final=%d  level=%s",
            raw_risk, self._prev_risk_score, smoothed, risk_score, risk_level,
        )

        return {
            # ── raw readings ──────────────────────────────────────────────
            "temperature": round(temp, 2),
            "humidity":    round(humidity, 2),
            "pressure":    round(pressure, 2),
            "gas":         round(gas, 2),
            # ── rolling statistics ────────────────────────────────────────
            **{k: (round(v, 4) if v is not None else None) for k, v in stats.items()},
            # ── rate of change ────────────────────────────────────────────
            **{k: (round(v, 4) if v is not None else None) for k, v in roc.items()},
            # ── acceleration (instability) ────────────────────────────────
            **{k: (round(v, 4) if v is not None else None) for k, v in accel.items()},
            # ── z-scores (post-cap) ───────────────────────────────────────
            **{k: (round(v, 4) if v is not None else None) for k, v in z_scores.items()},
            # ── risk output ───────────────────────────────────────────────
            "anomaly_flag": anomaly_flag,
            "risk_score":   risk_score,
            "risk_level":   risk_level,
            "risk_reason":  risk_reason,
        }

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _compute_stats(self) -> dict:
        stats = {
            "temp_mean":     self._temp.mean(),
            "temp_std":      self._temp.std(),
            "humidity_mean": self._humidity.mean(),
            "humidity_std":  self._humidity.std(),
            "pressure_mean": self._pressure.mean(),
            "pressure_std":  self._pressure.std(),
            "gas_mean":      self._gas.mean(),
            "gas_std":       self._gas.std(),
        }
        # Hardening fix 8: structured debug for rolling statistics
        _dbg(
            "Rolling stats: "
            "T_mean=%.3f T_std=%s | "
            "H_mean=%.3f H_std=%s | "
            "P_mean=%.3f P_std=%s | "
            "G_mean=%.3f G_std=%s",
            stats["temp_mean"]     or 0, _fmt(stats["temp_std"]),
            stats["humidity_mean"] or 0, _fmt(stats["humidity_std"]),
            stats["pressure_mean"] or 0, _fmt(stats["pressure_std"]),
            stats["gas_mean"]      or 0, _fmt(stats["gas_std"]),
        )
        return stats

    def _compute_roc(self) -> dict:
        def delta(buf: _RollingBuffer) -> float:
            if buf.previous() is None:
                return 0.0
            return buf.latest() - buf.previous()  # type: ignore[operator]

        roc = {
            "temp_roc":     delta(self._temp),
            "humidity_roc": delta(self._humidity),
            "pressure_roc": delta(self._pressure),
            "gas_roc":      delta(self._gas),
        }
        # Hardening fix 8: structured debug for rate-of-change
        _dbg(
            "ROC: T=%+.4f  H=%+.4f  P=%+.4f  G=%+.4f",
            roc["temp_roc"], roc["humidity_roc"],
            roc["pressure_roc"], roc["gas_roc"],
        )
        return roc

    def _compute_accel(self) -> dict:
        """
        Compute second derivative (acceleration) for Gas and Pressure.
        Used to detect rapid instability even before absolute thresholds are crossed.
        """
        accel = {
            "gas_accel":      self._gas.acceleration(),
            "pressure_accel": self._pressure.acceleration(),
        }
        # Hardening fix 9: structured debug for acceleration
        _dbg(
            "ACCEL: G=%+.4f  P=%+.4f",
            accel["gas_accel"], accel["pressure_accel"],
        )
        return accel

    def _compute_z_scores(
        self,
        temp: float,
        humidity: float,
        pressure: float,
        gas: float,
        stats: dict,
    ) -> dict:
        def zscore(x: float, mean: Optional[float], std: Optional[float]) -> float:
            """
            Compute Z-score with two hardening layers applied in order:
              1. std is already floored to STD_EPSILON by _RollingBuffer.std(),
                 so division by zero cannot occur here.
              2. The result is capped to ±Z_SCORE_CAP (hardening fix 2) so a
                 single outlier reading cannot dominate the weighted risk sum.
            """
            if mean is None or std is None:
                return 0.0
            # Defensive guard: std == 0 cannot be reached given fix 1, but
            # kept for correctness under any future refactor.
            if std == 0:
                return 0.0
            raw_z = (x - mean) / std
            # Hardening fix 2: saturate to ±Z_SCORE_CAP
            return max(-Z_SCORE_CAP, min(Z_SCORE_CAP, raw_z))

        z = {
            "z_temp":     zscore(temp,     stats["temp_mean"],     stats["temp_std"]),
            "z_humidity": zscore(humidity, stats["humidity_mean"], stats["humidity_std"]),
            "z_pressure": zscore(pressure, stats["pressure_mean"], stats["pressure_std"]),
            "z_gas":      zscore(gas,      stats["gas_mean"],      stats["gas_std"]),
        }
        # Hardening fix 8: structured debug for Z-scores
        _dbg(
            "Z-scores (capped ±%.1f): T=%.4f  H=%.4f  P=%.4f  G=%.4f",
            Z_SCORE_CAP,
            z["z_temp"], z["z_humidity"], z["z_pressure"], z["z_gas"],
        )
        return z

    def _compute_risk(
        self,
        gas_current: float,
        gas_mean: Optional[float],
        pressure_roc: Optional[float],
        temp_roc: Optional[float],
        humidity_roc: Optional[float],
        gas_accel: float,
        pressure_accel: float,
        anomaly_flag: bool,
    ) -> Tuple[int, str, str]:
        """
        Compute the weighted risk score and produce a classification + reason list.

        Each component is normalised using its own dedicated maximum constant
        (hardening fix 3) so adjusting the range of one axis does not silently
        change the effective weight of another.

        Returns
        -------
        Tuple[int, str, str]
            (raw_risk_score_pre_smoothing, risk_level, risk_reason)
            Smoothing is applied by the caller (process()) so this method
            remains pure and unit-testable independently.
        """
        reasons: List[str] = []

        # ── Component 1: Gas spike magnitude ──────────────────────────────
        # Hardening fix 3: independent normalisation via MAX_GAS_SPIKE.
        gas_spike = max(0.0, gas_current - (gas_mean if gas_mean is not None else gas_current))
        norm_gas = _clamp01(gas_spike / MAX_GAS_SPIKE)
        if norm_gas > 0.3:
            reasons.append(
                f"Gas spike: +{gas_spike:.1f} units above rolling mean "
                f"({gas_current:.1f} vs mean {gas_mean:.1f})"
            )

        # ── Component 2: Pressure gradient ────────────────────────────────
        # Hardening fix 3: independent normalisation via MAX_PRESSURE_GRAD.
        abs_pressure_roc = abs(pressure_roc or 0.0)
        norm_pressure = _clamp01(abs_pressure_roc / MAX_PRESSURE_GRAD)
        if norm_pressure > 0.3:
            reasons.append(
                f"Pressure change: {pressure_roc:+.2f} hPa/sample "
                f"({'rising' if (pressure_roc or 0) > 0 else 'falling'})"
            )

        # ── Component 3: Temperature rate-of-change ───────────────────────
        # Hardening fix 3: independent normalisation via MAX_TEMP_ROC.
        abs_temp_roc = abs(temp_roc or 0.0)
        norm_temp_roc = _clamp01(abs_temp_roc / MAX_TEMP_ROC)
        if norm_temp_roc > 0.3:
            reasons.append(
                f"Temperature change: {temp_roc:+.2f} °C/sample"
            )

        # ── Component 4: Humidity rate-of-change ──────────────────────────
        # Hardening fix 3: independent normalisation via MAX_HUMIDITY_ROC.
        abs_humidity_roc = abs(humidity_roc or 0.0)
        norm_humidity_roc = _clamp01(abs_humidity_roc / MAX_HUMIDITY_ROC)
        if norm_humidity_roc > 0.3:
            reasons.append(
                f"Humidity change: {humidity_roc:+.2f} %RH/sample"
            )

        # ── Component 5: Acceleration instability (New v3 feature) ────────
        # Composite score: 60% gas acceleration + 40% pressure acceleration
        abs_gas_accel = abs(gas_accel)
        abs_pressure_accel = abs(pressure_accel)
        
        norm_gas_accel = _clamp01(abs_gas_accel / MAX_GAS_ACCEL)
        norm_pressure_accel = _clamp01(abs_pressure_accel / MAX_PRESSURE_ACCEL)

        norm_acceleration = (0.6 * norm_gas_accel) + (0.4 * norm_pressure_accel)

        if norm_acceleration > 0.3:
            reasons.append(
                f"Rapid instability detected (accel: G={gas_accel:+.2f}, P={pressure_accel:+.2f})"
            )

        # ── Component 6: Anomaly flag ──────────────────────────────────────
        norm_anomaly = 1.0 if anomaly_flag else 0.0
        if anomaly_flag:
            reasons.append("Statistical anomaly detected (Z-score threshold exceeded)")

        # Hardening fix 8: structured debug for normalised feature vector
        _dbg(
            "Normalised features: gas=%.4f  pressure=%.4f  "
            "temp_roc=%.4f  hum_roc=%.4f  accel=%.4f  anomaly=%.1f",
            norm_gas, norm_pressure, norm_temp_roc, norm_humidity_roc, norm_acceleration, norm_anomaly,
        )

        # ── Weighted sum ──────────────────────────────────────────────────
        # Hardening fix 4: WEIGHTS assertion fires at import time, not here,
        # so no runtime overhead in the hot path.
        raw_weighted = (
            WEIGHTS["gas_spike"]         * norm_gas
            + WEIGHTS["pressure_gradient"] * norm_pressure
            + WEIGHTS["temp_roc"]          * norm_temp_roc
            + WEIGHTS["humidity_roc"]      * norm_humidity_roc
            + WEIGHTS["acceleration"]      * norm_acceleration
            + WEIGHTS["anomaly_flag"]      * norm_anomaly
        )
        # Hardening fix 8: log raw weighted score before scaling
        _dbg("Raw weighted score (0–1): %.6f", raw_weighted)

        # Convert to integer 0–100 (pre-EMA-smoothing)
        raw_risk = int(round(_clamp01(raw_weighted) * 100))

        # ── Classification (hardening fix 7) ──────────────────────────────
        # Uses the dedicated _classify() helper with explicit boundary checks.
        risk_level = _classify(raw_risk)

        if not reasons:
            reasons.append(_default_reason(risk_level))

        risk_reason = "; ".join(reasons)

        logger.info(
            "Risk (pre-smooth): score=%d  level=%s  anomaly=%s  reasons=%d",
            raw_risk, risk_level, anomaly_flag, len(reasons),
        )
        return raw_risk, risk_level, risk_reason


# ─────────────────────────────────────────────────────────────────────────────
# Module-level singleton (imported by main.py – public interface unchanged)
# ─────────────────────────────────────────────────────────────────────────────

engine = ProcessingEngine()


def process_reading(raw: dict) -> dict:
    """Convenience wrapper around the module-level ProcessingEngine singleton."""
    return engine.process(raw)


# ─────────────────────────────────────────────────────────────────────────────
# Utility functions
# ─────────────────────────────────────────────────────────────────────────────

def _clamp01(value: float) -> float:
    """Clamp a float to [0.0, 1.0]."""
    return max(0.0, min(1.0, value))


def _classify(score: int) -> str:
    """
    Classify an integer risk score into a level string.

    Hardening fix 7: uses explicit, inclusive boundary comparisons so the
    classification bands are unambiguous and cannot creep with floating-point
    rounding elsewhere in the pipeline.

      0  ≤ score ≤  30  →  SAFE
     31  ≤ score ≤  65  →  MODERATE
     66  ≤ score ≤ 100  →  HIGH
    """
    if 0 <= score <= SAFE_MAX:
        return "SAFE"
    if SAFE_MAX < score <= MOD_MAX:
        return "MODERATE"
    return "HIGH"


def _default_reason(risk_level: str) -> str:
    """Return a fallback reason string when no specific trigger fired."""
    if risk_level == "SAFE":
        return "All parameters within normal operating range"
    if risk_level == "MODERATE":
        return "Minor deviations detected – monitor closely"
    return "Multiple metrics exceed safe thresholds"


def _fmt(value: Optional[float]) -> str:
    """Format an optional float for debug log lines."""
    return f"{value:.4f}" if value is not None else "n/a"
