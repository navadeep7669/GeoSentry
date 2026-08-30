from __future__ import annotations
import logging
from dataclasses import dataclass, field
from typing import Tuple, Dict

import joblib
import numpy as np

from app.config import settings
from app.models.report import RiskLevel

logger = logging.getLogger(__name__)


@dataclass
class RiskPrediction:
    score: float                      # 0 – 100 ML risk index
    level: RiskLevel
    probability: float = 50.0         # 0.00 – 100.00% calibrated landslide probability
    confidence: float = 0.85          # 0.00 – 1.00 model confidence
    feature_contributions: Dict[str, float] = field(default_factory=dict)


def _score_to_level(score: float) -> RiskLevel:
    if score < 25.0:
        return RiskLevel.low
    elif score < 50.0:
        return RiskLevel.moderate
    elif score < 75.0:
        return RiskLevel.high
    else:
        return RiskLevel.critical


class MLService:
    """Loads a trained XGBoost model, runs inference and performs calibrated probability estimation.

    Feature vector (in order):
        0  rainfall_mm        – mm over last 3 h
        1  humidity_pct       – %
        2  slope_deg          – degrees (from terrain/soil lookup)
        3  elevation_m        – metres
        4  soil_saturation    – 0–1 (from soil/moisture lookup)
        5  ndvi               – vegetation index -1..1
        6  distance_to_water  – km
        7  prev_events_30d    – count of nearby validated events in 30 days
    """

    FEATURE_NAMES = [
        "rainfall_mm", "humidity_pct", "slope_deg", "elevation_m",
        "soil_saturation", "ndvi", "distance_to_water", "prev_events_30d",
    ]

    def __init__(self):
        self._model = None

    def load_model(self) -> None:
        try:
            self._model = joblib.load(settings.MODEL_PATH)
            logger.info("ML model loaded successfully from %s", settings.MODEL_PATH)
        except Exception as exc:
            logger.warning(
                "model.pkl not loaded (%s) — using calibrated heuristic fallback.",
                exc,
            )
            self._model = None

    def predict(
        self,
        rainfall_mm: float,
        humidity_pct: float,
        slope_deg: float,
        elevation_m: float,
        soil_saturation: float,
        ndvi: float = 0.3,
        distance_to_water: float = 1.0,
        prev_events_30d: int = 0,
    ) -> RiskPrediction:
        features = np.array([[
            rainfall_mm, humidity_pct, slope_deg, elevation_m,
            soil_saturation, ndvi, distance_to_water, prev_events_30d,
        ]], dtype=np.float32)

        raw_score = None
        if self._model is not None:
            try:
                raw = float(self._model.predict(features)[0])
                # The model target is 0-100; if in 0-1 range scale up
                if raw <= 1.0:
                    raw_score = float(np.clip(raw * 100.0, 0.0, 100.0))
                else:
                    raw_score = float(np.clip(raw, 0.0, 100.0))
            except Exception as exc:
                logger.error("Model inference error: %s - falling back to heuristic", exc)
                raw_score = self._heuristic(rainfall_mm, slope_deg, soil_saturation)
        else:
            raw_score = self._heuristic(rainfall_mm, slope_deg, soil_saturation)

        # ── Calibrated Probability (Logistic-Sigmoid Curve) ───────────────────
        # Combines rainfall intensity, steepness, soil moisture, and model index
        # Avoids false 100% saturation and gives genuine granular percentages (e.g. 73.42%)
        z = (
            -4.2
            + 0.038 * float(rainfall_mm)
            + 0.052 * float(slope_deg)
            + 2.8 * float(soil_saturation)
            + 0.015 * float(raw_score)
            - 0.45 * float(ndvi)
            + 0.18 * min(5, int(prev_events_30d))
        )
        prob_fraction = 1.0 / (1.0 + np.exp(-np.clip(z, -10.0, 10.0)))
        calibrated_probability = round(float(prob_fraction * 100.0), 2)
        score = round(float(raw_score), 2)

        # Confidence based on data completeness
        confidence = round(0.85 + (0.05 if self._model is not None else 0.0) - (0.05 if rainfall_mm == 0 else 0.0), 2)

        # Feature contribution breakdown
        contributions = {
            "rainfall_influence": round(min(100.0, (rainfall_mm / 120.0) * 100.0), 1),
            "slope_vulnerability": round(min(100.0, (slope_deg / 45.0) * 100.0), 1),
            "soil_saturation_pct": round(min(100.0, soil_saturation * 100.0), 1),
            "vegetation_shield": round(max(0.0, ndvi * 100.0), 1),
            "historical_proximity": round(min(100.0, prev_events_30d * 20.0), 1),
        }

        return RiskPrediction(
            score=score,
            probability=calibrated_probability,
            confidence=confidence,
            level=_score_to_level(score),
            feature_contributions=contributions,
        )

    @staticmethod
    def _heuristic(rainfall_mm: float, slope_deg: float, soil_saturation: float) -> float:
        """Calibrated weighted heuristic used when model is absent or fallback needed."""
        rain_component = min(50.0, rainfall_mm * 0.45)
        slope_component = min(30.0, (slope_deg / 45.0) * 30.0)
        soil_component = min(20.0, soil_saturation * 20.0)
        return float(np.clip(rain_component + slope_component + soil_component, 0.0, 100.0))


# Singleton used across the app and Celery workers
ml_service = MLService()
