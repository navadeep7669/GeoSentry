from __future__ import annotations
import json
from fastapi import APIRouter, Query, HTTPException, Depends
from sqlalchemy import select, func, text
from geoalchemy2.functions import ST_AsGeoJSON, ST_Within, ST_DWithin, ST_MakePoint, ST_MakeEnvelope

from app.models.risk_zone import RiskZone
from app.models.risk_observation import RiskObservation
from app.models.report import RiskLevel
from app.schemas.risk_zone import RiskZoneResponse, RiskZoneListResponse
from app.dependencies import DB, CitizenOrAbove, OptionalUser
from app.schemas.dynamic_risk import DynamicRiskRequest, DynamicRiskResponse
from app.schemas.location_intelligence import LocationIntelligenceResponse
from app.services.hazard_service import estimate_lhasa_style_hazard_probability
from app.services.dynamic_risk_service import calculate_dynamic_risk
from app.services.ml_service import ml_service
from app.services.location_intelligence_service import (
    location_engine,
    INDIA_LANDSLIDE_INVENTORY,
)

router = APIRouter()


# ── Location-Specific Dynamic Risk Intelligence ───────────────────────────────

@router.get("/location-intelligence", response_model=LocationIntelligenceResponse)
async def get_location_intelligence(
    lat: float = Query(..., ge=-90.0, le=90.0, description="Latitude of queried point"),
    lon: float = Query(..., ge=-180.0, le=180.0, description="Longitude of queried point"),
    rainfall_24h: float | None = Query(None, ge=0.0, description="Optional 24h rainfall override (mm)"),
    slope_deg: float | None = Query(None, ge=0.0, le=90.0, description="Optional slope override (degrees)"),
    soil_moisture: float | None = Query(None, ge=0.0, le=1.0, description="Optional soil saturation override (0-1)"),
    verified_reports: int = Query(0, ge=0, description="Count of verified citizen reports nearby"),
):
    """Calculates granular location-specific dynamic landslide risk for any coordinate in India.

    Integrates:
    - Real-time / spatial weather & rainfall
    - Local terrain & slope vulnerability
    - Calibrated XGBoost ML prediction (genuine probability %)
    - NASA LHASA-style rainfall-anomaly hazard signal
    - GSI Historical landslide inventory & rainfall response threshold
    - Human population, road importance & critical infrastructure exposure
    - Dynamic verified field report boost
    - Plain-English 'Why this risk?' explainability breakdown
    """
    return await location_engine.evaluate_location(
        latitude=lat,
        longitude=lon,
        override_rainfall_24h=rainfall_24h,
        override_slope_deg=slope_deg,
        override_soil_moisture=soil_moisture,
        verified_field_reports_count=verified_reports,
    )


# ── National Overview GIS Feed (India-Wide Multi-Scale) ───────────────────────

@router.get("/national-overview")
async def get_national_overview():
    """Returns India-wide spatial landslide hazard overview and regional corridors."""
    features = []
    for item in INDIA_LANDSLIDE_INVENTORY:
        features.append({
            "name": item["name"],
            "district": item["district"],
            "state": item["state"],
            "region": item["region"],
            "lat": item["lat"],
            "lon": item["lon"],
            "radius_km": item["radius_km"],
            "slope_deg": item["base_slope"],
            "elevation_m": item["elevation"],
            "susceptibility": item["susceptibility"],
            "historical_events": item["historical_count"],
            "last_incident_year": item["last_incident"],
            "critical_road": item["road"],
            "nearest_hospital": {
                "name": item["hospital"],
                "distance_km": item["hospital_dist_km"],
                "trauma_beds": item["beds"],
                "helpline": item["helpline"],
            },
            "rainfall_response": item["rainfall_rule"],
        })

    return {
        "status": "operational",
        "coverage": "All-India (Western Ghats, Himalayan Arc & Northeastern Hills)",
        "total_corridors_monitored": len(features),
        "corridors": features,
    }


# ── Standard Spatial PostGIS Risk Zones Query ──────────────────────────────────

@router.get("", response_model=RiskZoneListResponse)
async def list_risk_zones(
    db: DB,
    current_user: CitizenOrAbove,
    bbox: str | None = Query(
        None,
        description="Comma-separated bounding box: min_lon,min_lat,max_lon,max_lat",
    ),
    lat: float | None = Query(None, description="Center latitude for radius query"),
    lon: float | None = Query(None, description="Center longitude for radius query"),
    radius_km: float = Query(10.0, description="Search radius in km (used with lat/lon)"),
    min_risk: RiskLevel | None = Query(None, description="Minimum risk level"),
    min_priority: float | None = Query(None, ge=0, le=100, description="Minimum priority_score (0-100)"),
    order_by: str = Query("updated_at", description="Sort: updated_at | priority_score | environmental_risk"),
    limit: int = Query(50, ge=1, le=200),
):
    """Spatial query for risk zones using PostGIS."""
    stmt = select(RiskZone, ST_AsGeoJSON(RiskZone.boundary).label("geojson"))

    if bbox:
        try:
            parts = [float(x.strip()) for x in bbox.split(",")]
            if len(parts) != 4:
                raise ValueError
            min_lon, min_lat, max_lon, max_lat = parts
        except ValueError:
            raise HTTPException(400, "bbox must be 4 comma-separated floats: min_lon,min_lat,max_lon,max_lat")

        envelope = ST_MakeEnvelope(min_lon, min_lat, max_lon, max_lat, 4326)
        stmt = stmt.where(ST_Within(RiskZone.boundary, envelope))

    elif lat is not None and lon is not None:
        stmt = stmt.where(
            ST_DWithin(
                RiskZone.centroid.cast(text("geography")),
                ST_MakePoint(lon, lat).cast(text("geography")),
                radius_km * 1000,
            )
        )

    level_order = {
        RiskLevel.low: 1,
        RiskLevel.moderate: 2,
        RiskLevel.high: 3,
        RiskLevel.critical: 4,
        RiskLevel.unknown: 0,
    }
    if min_risk:
        threshold = level_order[min_risk]
        allowed = [lvl for lvl, rank in level_order.items() if rank >= threshold]
        stmt = stmt.where(RiskZone.risk_level.in_(allowed))

    if min_priority is not None:
        stmt = stmt.where(RiskZone.priority_score >= min_priority)

    order_col = {
        "priority_score": RiskZone.priority_score.desc().nulls_last(),
        "environmental_risk": RiskZone.environmental_risk.desc().nulls_last(),
        "updated_at": RiskZone.updated_at.desc(),
    }.get(order_by, RiskZone.updated_at.desc())
    stmt = stmt.order_by(order_col).limit(limit)
    rows = (await db.execute(stmt)).all()

    items = []
    for zone, geojson_str in rows:
        resp = RiskZoneResponse.model_validate(zone)
        resp.boundary_geojson = json.loads(geojson_str) if geojson_str else None
        items.append(resp)

    return RiskZoneListResponse(total=len(items), items=items)


# ── Problem-Centered Dynamic Risk Evaluation ──────────────────────────────────

@router.post("/evaluate", response_model=DynamicRiskResponse)
async def evaluate_dynamic_risk(
    payload: DynamicRiskRequest,
    current_user: OptionalUser = None,
):
    """Evaluate a location using the problem-centered scoring path."""
    ml_service.load_model()
    prediction = ml_service.predict(
        rainfall_mm=payload.rainfall_24h_mm,
        humidity_pct=payload.humidity_pct,
        slope_deg=payload.slope_deg,
        elevation_m=payload.elevation_m,
        soil_saturation=payload.soil_saturation,
        ndvi=payload.ndvi,
        distance_to_water=payload.distance_to_water_km,
        prev_events_30d=payload.previous_events_30d,
    )
    hazard = estimate_lhasa_style_hazard_probability(
        payload.rainfall_24h_mm,
        payload.rainfall_7d_mm,
        payload.slope_deg,
        payload.soil_saturation,
    )
    dynamic = calculate_dynamic_risk(
        ml_prediction=prediction,
        rainfall_mm=payload.rainfall_24h_mm,
        rainfall_7d_mm=payload.rainfall_7d_mm,
        soil_saturation=payload.soil_saturation,
        slope_deg=payload.slope_deg,
        satellite_change=payload.satellite_change,
        historical_susceptibility=payload.historical_susceptibility,
        population_exposure=payload.population_exposure,
        road_importance=payload.road_importance,
        critical_infrastructure=payload.critical_infrastructure,
        rate_of_change=payload.rate_of_change,
        verified_field_reports=payload.verified_field_reports,
        external_hazard_probability=hazard,
    )
    return DynamicRiskResponse(
        latitude=payload.latitude,
        longitude=payload.longitude,
        model_probability=round(prediction.probability / 100.0, 4),
        hazard_probability=hazard,
        environmental_risk=dynamic.environmental_risk,
        exposure_score=dynamic.exposure_score,
        priority_score=dynamic.priority_score,
        risk_level=dynamic.level,
        reasons=dynamic.reasons,
        recommended_action=dynamic.recommended_action,
    )


@router.get("/priority", response_model=RiskZoneListResponse)
async def get_high_priority_zones(
    db: DB,
    current_user: CitizenOrAbove,
    min_priority: float = Query(51.0, ge=0, le=100),
    limit: int = Query(20, ge=1, le=100),
):
    """Zones ranked by priority_score — highest urgency first."""
    stmt = (
        select(RiskZone, ST_AsGeoJSON(RiskZone.boundary).label("geojson"))
        .where(RiskZone.priority_score >= min_priority)
        .order_by(RiskZone.priority_score.desc().nulls_last())
        .limit(limit)
    )
    rows = (await db.execute(stmt)).all()
    items = []
    for zone, geojson_str in rows:
        resp = RiskZoneResponse.model_validate(zone)
        resp.boundary_geojson = json.loads(geojson_str) if geojson_str else None
        items.append(resp)
    return RiskZoneListResponse(total=len(items), items=items)


@router.get("/{zone_id}/history")
async def get_zone_history(
    zone_id: int,
    db: DB,
    current_user: CitizenOrAbove,
    limit: int = Query(
        48, ge=1, le=500,
        description="Observations to return (default=48 ≈ 12h at 15min intervals)",
    ),
):
    """Time-series risk observations for a zone."""
    stmt = (
        select(RiskObservation)
        .where(RiskObservation.zone_id == zone_id)
        .order_by(RiskObservation.observed_at.desc())
        .limit(limit)
    )
    obs = (await db.execute(stmt)).scalars().all()
    return [
        {
            "id": o.id,
            "zone_id": o.zone_id,
            "observed_at": o.observed_at,
            "model_probability": o.model_probability,
            "hazard_probability": o.hazard_probability,
            "environmental_risk": o.environmental_risk,
            "exposure_score": o.exposure_score,
            "priority_score": o.priority_score,
            "risk_level": o.risk_level,
            "rainfall_24h_mm": o.rainfall_24h_mm,
            "soil_saturation": o.soil_saturation,
            "satellite_change": o.satellite_change,
            "reasons": o.reasons.split("; ") if o.reasons else [],
            "recommended_action": o.recommended_action,
        }
        for o in obs
    ]


@router.get("/{zone_id}", response_model=RiskZoneResponse)
async def get_risk_zone(zone_id: int, db: DB, current_user: CitizenOrAbove):
    row = (await db.execute(
        select(RiskZone, ST_AsGeoJSON(RiskZone.boundary).label("geojson"))
        .where(RiskZone.id == zone_id)
    )).first()

    if row is None:
        raise HTTPException(status_code=404, detail="Risk zone not found")

    zone, geojson_str = row
    resp = RiskZoneResponse.model_validate(zone)
    resp.boundary_geojson = json.loads(geojson_str) if geojson_str else None
    return resp
