"""
ClimaScope - Isolation Forest Anomaly Model Trainer
====================================================

Loads all environmental sensor readings from the SQLite database, trains
an Isolation Forest model on the four core features:

    temperature, pressure, gas_ppm, mq2_voltage

...and saves the fitted model + scaler to:

    backend/app/ai/anomaly_model.pkl

USAGE (run from the project root or the backend/ folder):
---------------------------------------------------------
  python -m app.ai.train_anomaly_model
  # or
  python backend/app/ai/train_anomaly_model.py
"""

from __future__ import annotations

import os
import sqlite3
import sys
import time
from pathlib import Path

# ── Resolve paths regardless of working directory ────────────────────────────
_THIS_DIR   = Path(__file__).parent.resolve()
_BACKEND    = _THIS_DIR.parent.parent          # backend/
_DB_FILE    = _BACKEND / "climascope_backend.db"
MODEL_PATH  = _THIS_DIR / "anomaly_model.pkl"

FEATURES = ["temperature", "pressure", "gas_ppm", "mq2_voltage"]

# Contamination ≈ expected fraction of anomalies in the training set.
# Simulator injects ~8 % anomalies (4 % gas + 2 % pressure + 2 % temp).
CONTAMINATION = 0.08


def load_data() -> list[list[float]]:
    """Read sensor readings from SQLite and return a list of feature vectors."""
    if not _DB_FILE.exists():
        print(f"[ERROR] Database not found: {_DB_FILE}", file=sys.stderr)
        print("        Run the edge simulator first to populate the database.", file=sys.stderr)
        sys.exit(1)

    conn = sqlite3.connect(str(_DB_FILE))
    try:
        cur = conn.execute(
            "SELECT temperature, pressure, gas_ppm, mq2_voltage "
            "FROM environmental_data "
            "WHERE temperature IS NOT NULL "
            "  AND pressure IS NOT NULL "
            "  AND gas_ppm IS NOT NULL "
            "  AND mq2_voltage IS NOT NULL"
        )
        rows = cur.fetchall()
    finally:
        conn.close()

    print(f"[INFO] Loaded {len(rows)} rows from {_DB_FILE.name}")
    if len(rows) < 50:
        print(
            f"[WARN] Only {len(rows)} rows - model accuracy will be limited.\n"
            "       Run the simulator with --count 5000 --interval 0 for a better dataset.",
            file=sys.stderr,
        )
    return [list(r) for r in rows]


def train(data: list[list[float]]) -> None:
    """Train Isolation Forest + StandardScaler and save to MODEL_PATH."""
    try:
        import joblib
        import numpy as np
        from sklearn.ensemble import IsolationForest
        from sklearn.preprocessing import StandardScaler
        from sklearn.pipeline import Pipeline
    except ImportError as exc:
        print(f"[ERROR] Missing dependency: {exc}", file=sys.stderr)
        print("        pip install scikit-learn joblib", file=sys.stderr)
        sys.exit(1)

    X = np.array(data, dtype=float)
    n_samples, n_features = X.shape
    print(f"[INFO] Training on {n_samples} samples × {n_features} features: {FEATURES}")

    pipeline = Pipeline([
        ("scaler", StandardScaler()),
        ("iforest", IsolationForest(
            n_estimators=200,
            contamination=CONTAMINATION,
            max_features=n_features,
            bootstrap=False,
            random_state=42,
            n_jobs=-1,
        )),
    ])

    t0 = time.perf_counter()
    pipeline.fit(X)
    elapsed = time.perf_counter() - t0
    print(f"[INFO] Training complete in {elapsed:.2f}s")

    # Sanity-check: fraction labelled anomalous on training data
    preds = pipeline.predict(X)
    n_anomaly = int((preds == -1).sum())
    frac = n_anomaly / n_samples * 100
    print(f"[INFO] Model flagged {n_anomaly}/{n_samples} training samples as anomalies ({frac:.1f}%)")

    # Show score distribution
    scores = pipeline.decision_function(X)
    print(f"[INFO] Anomaly score  min={scores.min():.4f}  max={scores.max():.4f}  mean={scores.mean():.4f}")

    joblib.dump(
        {"pipeline": pipeline, "features": FEATURES, "contamination": CONTAMINATION},
        str(MODEL_PATH),
    )
    print(f"[INFO] Model saved -> {MODEL_PATH}")


def run() -> None:
    print("=" * 60)
    print("  ClimaScope - Anomaly Model Trainer")
    print("=" * 60)
    data = load_data()
    train(data)
    print("=" * 60)
    print("  Training complete. Run the backend to activate detection.")
    print("=" * 60)


if __name__ == "__main__":
    run()
