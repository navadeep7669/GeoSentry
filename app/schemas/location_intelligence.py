from __future__ import annotations
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from app.models.report import RiskLevel


class EnvironmentalConditions(BaseModel):
    temperature_c: float
    rainfall_24h_mm: float
    rainfall_7d_mm: float
    humidity_pct: float
    elevation_m: float
    slope_deg: float
    soil_moisture_pct: float
    terrain_type: str
    ndvi_vegetation: float


class HistoricalProfile(BaseModel):
    historical_incident_count: int
    historical_susceptibility_pct: float
    historical_pattern_summary: str
    rainfall_response_relationship: str
    seasonal_vulnerability: str
    last_incident_year: Optional[int] = None


class RiskAssessment(BaseModel):
    landslide_probability_pct: float = Field(description="Calibrated Landslide Probability (0-100%)")
    environmental_hazard_score: float = Field(description="Physical Hazard Index (0-100)")
    exposure_score: float = Field(description="Human & Asset Exposure Index (0-100)")
    response_priority_score: float = Field(description="Emergency Dispatch Priority Index (0-100)")
    risk_level: RiskLevel
    risk_trend: str = Field(description="Increasing | Stable | Decreasing")
    model_confidence: float = Field(description="Model Confidence (0.0-1.0)")

    model_config = {"protected_namespaces": ()}


class ImpactExposure(BaseModel):
    nearby_roads: str
    population_exposure_level: str
    critical_infrastructure: str
    nearest_hospital_name: str
    nearest_hospital_distance_km: float
    available_trauma_beds: int
    hospital_helpline: str


class ExplainabilityFactor(BaseModel):
    factor: str
    severity: str
    details: str


class RainfallTimePoint(BaseModel):
    timestamp_label: str
    rainfall_mm: float
    soil_saturation_pct: float
    risk_score: float
    event_observed: Optional[str] = None


class LocationIntelligenceResponse(BaseModel):
    location_name: str
    district: str
    state: str
    latitude: float
    longitude: float
    environmental: EnvironmentalConditions
    historical: HistoricalProfile
    assessment: RiskAssessment
    impact: ImpactExposure
    explainability: List[ExplainabilityFactor]
    recommended_action: str
    rainfall_timeline: List[RainfallTimePoint]

    model_config = {"protected_namespaces": ()}
