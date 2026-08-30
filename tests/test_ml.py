from __future__ import annotations
import pytest
from app.services.ml_service import MLService, _score_to_level
from app.models.report import RiskLevel


def make_svc() -> MLService:
    svc = MLService()
    # Don't load model — test heuristic path
    svc._model = None
    return svc


def test_heuristic_low_risk():
    svc = make_svc()
    result = svc.predict(
        rainfall_mm=0.0, humidity_pct=40.0, slope_deg=5.0,
        elevation_m=200.0, soil_saturation=0.1,
    )
    assert result.level == RiskLevel.low
    assert 0 <= result.score <= 25


def test_heuristic_moderate_risk():
    svc = make_svc()
    result = svc.predict(
        rainfall_mm=15.0, humidity_pct=70.0, slope_deg=20.0,
        elevation_m=600.0, soil_saturation=0.4,
    )
    assert result.score >= 20
    assert result.level in (RiskLevel.low, RiskLevel.moderate, RiskLevel.high)


def test_heuristic_critical_risk():
    svc = make_svc()
    result = svc.predict(
        rainfall_mm=40.0, humidity_pct=95.0, slope_deg=42.0,
        elevation_m=900.0, soil_saturation=0.95,
    )
    assert result.score >= 50
    assert result.level in (RiskLevel.high, RiskLevel.critical)


def test_score_to_level_boundaries():
    assert _score_to_level(0.0) == RiskLevel.low
    assert _score_to_level(24.9) == RiskLevel.low
    assert _score_to_level(25.0) == RiskLevel.moderate
    assert _score_to_level(49.9) == RiskLevel.moderate
    assert _score_to_level(50.0) == RiskLevel.high
    assert _score_to_level(74.9) == RiskLevel.high
    assert _score_to_level(75.0) == RiskLevel.critical
    assert _score_to_level(100.0) == RiskLevel.critical


def test_prediction_score_range():
    svc = make_svc()
    for rainfall in [0, 10, 25, 50]:
        for slope in [5, 20, 35, 45]:
            result = svc.predict(
                rainfall_mm=float(rainfall), humidity_pct=70.0,
                slope_deg=float(slope), elevation_m=500.0,
                soil_saturation=0.5,
            )
            assert 0.0 <= result.score <= 100.0
