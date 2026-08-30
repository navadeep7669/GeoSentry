from __future__ import annotations
"""
Thin inference wrapper — prefer using app.services.ml_service.ml_service singleton.
This module exists for standalone script / notebook usage.
"""
import joblib
import numpy as np
from app.models.report import RiskLevel


def load_model(path: str = "app/ml/model.pkl"):
    return joblib.load(path)


def predict_risk(
    model,
    rainfall_mm: float,
    humidity_pct: float,
    slope_deg: float,
    elevation_m: float,
    soil_saturation: float,
    ndvi: float = 0.3,
    distance_to_water: float = 1.0,
    prev_events_30d: int = 0,
) -> tuple[float, RiskLevel]:
    """Return (score 0-100, RiskLevel)."""
    features = np.array([[
        rainfall_mm, humidity_pct, slope_deg, elevation_m,
        soil_saturation, ndvi, distance_to_water, prev_events_30d,
    ]], dtype=np.float32)
    raw = float(model.predict(features)[0])
    score = float(np.clip(raw * 100, 0, 100))

    if score < 25:
        level = RiskLevel.low
    elif score < 50:
        level = RiskLevel.moderate
    elif score < 75:
        level = RiskLevel.high
    else:
        level = RiskLevel.critical

    return round(score, 2), level
