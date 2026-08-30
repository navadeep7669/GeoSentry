from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel
from app.models.report import RiskLevel


class RiskZoneResponse(BaseModel):
    id: int
    risk_level: RiskLevel
    risk_score_avg: float | None
    risk_score_max: float | None
    report_ids: list[int]
    name: str | None
    description: str | None
    computed_at: datetime
    updated_at: datetime
    # Dynamic-risk extension fields (nullable for backward compatibility)
    external_id: str | None = None
    environmental_risk: float | None = None
    exposure_score: float | None = None
    priority_score: float | None = None
    reasons: list[str] = []
    recommended_action: str | None = None
    last_hazard_probability: float | None = None
    field_report_count: int = 0
    # GeoJSON representation of boundary (populated by router)
    boundary_geojson: dict | None = None

    model_config = {"from_attributes": True}


class RiskZoneListResponse(BaseModel):
    total: int
    items: list[RiskZoneResponse]