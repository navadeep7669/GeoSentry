from __future__ import annotations
"""Dynamic Risk Engine.

Combines ML probability with environmental triggers, satellite data, and
exposure factors into a three-layer score:

  Environmental Risk  (0-100)  — physics/hazard side
  Exposure Score      (0-100)  — people/assets side
  Priority Score      (0-100)  — composite dispatch priority

The weights below are labelled MVP. Replace with validated model parameters
once regional calibration data is available.
"""

from dataclasses import dataclass

from app.config import settings
from app.models.report import RiskLevel
from app.services.ml_service import RiskPrediction


@dataclass
class DynamicRiskResult:
    environmental_risk: float
    exposure_score: float
    priority_score: float
    level: RiskLevel
    reasons: list[str]
    recommended_action: str


# ── Utility helpers ────────────────────────────────────────────────────────────

def clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, float(value)))


def _rainfall_score(rainfall_mm: float, rainfall_7d_mm: float = 0.0) -> float:
    """Combine 24h and 7-day rainfall into a single 0-100 signal.

    Thresholds (120 mm/day, 400 mm/7d) are empirical MVP values.
    A calibrated regional model should replace these.
    """
    recent = clamp((rainfall_mm / 120.0) * 100.0)
    accumulated = clamp((rainfall_7d_mm / 400.0) * 100.0)
    return 0.65 * recent + 0.35 * accumulated  # MVP weight


def _slope_score(slope_deg: float) -> float:
    """Piecewise slope hazard. MVP classification; replace with D_LSM curves."""
    if slope_deg < 10:
        return 10.0
    if slope_deg < 20:
        return 30.0
    if slope_deg < 30:
        return 60.0
    if slope_deg < 40:
        return 85.0
    return 100.0


def _classify(score: float) -> RiskLevel:
    if score >= settings.RISK_CRITICAL_THRESHOLD:
        return RiskLevel.critical
    if score >= settings.RISK_HIGH_THRESHOLD:
        return RiskLevel.high
    if score >= 26.0:
        return RiskLevel.moderate
    return RiskLevel.low


# ── Core scoring function ──────────────────────────────────────────────────────

def calculate_dynamic_risk(
    *,
    ml_prediction: RiskPrediction,
    rainfall_mm: float,
    rainfall_7d_mm: float = 0.0,
    soil_saturation: float = 0.5,
    slope_deg: float = 15.0,
    satellite_change: float = 0.0,
    historical_susceptibility: float = 0.4,
    population_exposure: float = 0.3,
    road_importance: float = 0.4,
    critical_infrastructure: float = 0.2,
    rate_of_change: float = 0.2,
    verified_field_reports: int = 0,
    external_hazard_probability: float | None = None,
) -> DynamicRiskResult:
    """Calculate composite landslide risk separating hazard from exposure.

    Args:
        ml_prediction: Output from the ML service (score 0-100).
        external_hazard_probability: Optional signal from LHASA-style adapter
            (0-1). Blended in when provided.

    Returns:
        DynamicRiskResult with all three layers and explainability.
    """
    rain = _rainfall_score(rainfall_mm, rainfall_7d_mm)

    # ── Environmental risk (MVP weights — label clearly) ─────────────────────
    env = (
        0.25 * ml_prediction.score                            # ML signal
        + 0.20 * rain                                         # rainfall
        + 0.15 * (clamp(soil_saturation, 0, 1) * 100)        # soil moisture
        + 0.15 * _slope_score(slope_deg)                      # terrain
        + 0.10 * (clamp(satellite_change, 0, 1) * 100)        # EO change
        + 0.10 * (clamp(historical_susceptibility, 0, 1) * 100)  # history
        + 0.05 * (clamp(rate_of_change, 0, 1) * 100)         # dynamics
    )

    # Blend in external hazard signal if available (e.g. LHASA adapter)
    if external_hazard_probability is not None:
        env = 0.80 * env + 0.20 * (clamp(external_hazard_probability, 0, 1) * 100)

    # Verified field reports add confidence evidence (capped)
    field_boost = min(
        verified_field_reports * settings.FIELD_REPORT_RISK_BOOST,
        settings.FIELD_REPORT_MAX_BOOST,
    )
    env = clamp(env + field_boost)

    # ── Exposure score (MVP weights) ──────────────────────────────────────────
    exposure = (
        0.45 * clamp(population_exposure, 0, 1)
        + 0.30 * clamp(road_importance, 0, 1)
        + 0.25 * clamp(critical_infrastructure, 0, 1)
    ) * 100.0

    # ── Priority (dispatch urgency) ───────────────────────────────────────────
    priority = clamp(0.70 * env + 0.30 * exposure)
    level = _classify(priority)

    # ── Explainability ────────────────────────────────────────────────────────
    reasons: list[str] = []
    if rain >= 70:
        reasons.append("high recent/accumulated rainfall")
    if soil_saturation >= 0.70:
        reasons.append("wet soil conditions")
    if slope_deg >= 30:
        reasons.append("steep terrain")
    if satellite_change >= 0.50:
        reasons.append("significant satellite-detected surface change")
    if historical_susceptibility >= 0.60:
        reasons.append("historically susceptible location")
    if external_hazard_probability is not None and external_hazard_probability >= 0.50:
        reasons.append("elevated hazard probability from hazard model")
    if verified_field_reports:
        reasons.append(f"{verified_field_reports} verified field report(s) nearby")
    if population_exposure >= 0.60:
        reasons.append("high population exposure")
    if road_importance >= 0.70:
        reasons.append("critical road connectivity at risk")
    if critical_infrastructure >= 0.60:
        reasons.append("critical infrastructure exposure")
    if rate_of_change >= 0.60:
        reasons.append("conditions are changing rapidly")
    if not reasons:
        reasons.append("no dominant trigger; continue routine monitoring")

    actions = {
        RiskLevel.low: "Monitor; no immediate intervention required.",
        RiskLevel.moderate: "Increase monitoring frequency; verify field conditions.",
        RiskLevel.high: (
            "Notify responsible authorities; inspect exposed roads and settlements."
        ),
        RiskLevel.critical: (
            "Immediate authority notification; assess evacuation, road closure, "
            "and emergency responder deployment."
        ),
        RiskLevel.unknown: "Insufficient data; continue monitoring.",
    }

    return DynamicRiskResult(
        environmental_risk=round(env, 2),
        exposure_score=round(exposure, 2),
        priority_score=round(priority, 2),
        level=level,
        reasons=reasons,
        recommended_action=actions[level],
    )