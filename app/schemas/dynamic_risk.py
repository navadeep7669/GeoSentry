from __future__ import annotations

from pydantic import BaseModel, Field

from app.models.report import RiskLevel


class DynamicRiskRequest(BaseModel):
    """Full set of inputs for the dynamic risk engine.

    All geographic and numeric values are validated at the boundary.
    Default values represent moderate conditions and are safe for testing.
    """
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)

    # ── Weather / hydrology ────────────────────────────────────────────────
    rainfall_24h_mm: float = Field(ge=0, default=40.0,
        description="Total rainfall in last 24 hours (mm)")
    rainfall_7d_mm: float = Field(ge=0, default=120.0,
        description="Total accumulated rainfall over 7 days (mm)")
    humidity_pct: float = Field(ge=0, le=100, default=60.0)
    soil_saturation: float = Field(ge=0, le=1, default=0.55,
        description="Soil saturation fraction 0..1")

    # ── Terrain ────────────────────────────────────────────────────────────
    slope_deg: float = Field(ge=0, le=90, default=25.0,
        description="Slope angle in degrees")
    elevation_m: float = Field(ge=-1000, default=100.0)

    # ── ML feature inputs ──────────────────────────────────────────────────
    ndvi: float = Field(ge=-1, le=1, default=0.3,
        description="Normalized Difference Vegetation Index")
    distance_to_water_km: float = Field(ge=0, default=1.0)
    previous_events_30d: int = Field(ge=0, default=0,
        description="Nearby validated reports in last 30 days")

    # ── Satellite / Earth observation ──────────────────────────────────────
    satellite_change: float = Field(ge=0, le=1, default=0.0,
        description="Normalized surface-change indicator from EO (0..1)")

    # ── Historical / susceptibility ────────────────────────────────────────
    historical_susceptibility: float = Field(ge=0, le=1, default=0.4,
        description="Background susceptibility from landslide inventory (0..1)")

    # ── Exposure (prioritization layer) ────────────────────────────────────
    population_exposure: float = Field(ge=0, le=1, default=0.3,
        description="Normalized population density in potentially affected area")
    road_importance: float = Field(ge=0, le=1, default=0.4,
        description="Road criticality (0=minor track, 1=national highway)")
    critical_infrastructure: float = Field(ge=0, le=1, default=0.2,
        description="Nearby critical infrastructure score (0..1)")

    # ── Dynamics ────────────────────────────────────────────────────────────
    rate_of_change: float = Field(ge=0, le=1, default=0.2,
        description="How rapidly conditions are changing (0..1)")
    verified_field_reports: int = Field(ge=0, default=0,
        description="Number of VERIFIED (validator-approved) reports nearby")


class DynamicRiskResponse(BaseModel):
    """Full risk evaluation output separating hazard from exposure and priority."""
    latitude: float
    longitude: float

    # ML and hazard signals
    model_probability: float
    hazard_probability: float

    # Three-layer scoring
    environmental_risk: float
    exposure_score: float
    priority_score: float

    # Verdict
    risk_level: RiskLevel
    reasons: list[str]
    recommended_action: str

    model_config = {"protected_namespaces": ()}