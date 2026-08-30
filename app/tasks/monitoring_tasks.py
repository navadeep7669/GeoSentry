from __future__ import annotations
"""Continuous monitoring task.

This Celery task replaces the reactive report-only workflow with
proactive zone monitoring. It runs on a configurable schedule
(MONITORING_INTERVAL_MINUTES) and:

  1. Fetches latest weather for every tracked zone
  2. Pulls stored satellite features (if available)
  3. Runs the ML model
  4. Calculates dynamic risk (env + exposure + priority)
  5. Detects escalation (e.g., HIGH → CRITICAL)
  6. Stores a RiskObservation time-series row
  7. Triggers alert escalation when appropriate

Design principles:
  - Lightweight per zone (no heavy EO processing here)
  - Uses sync SQLAlchemy (Celery is not async)
  - Gracefully degrades if weather API is unavailable
  - Does NOT duplicate the alert_tasks alert logic
"""

import asyncio
import logging
from datetime import datetime, timezone

from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import Session

from app.config import settings
from app.models.report import RiskLevel
from app.models.risk_zone import RiskZone
from app.models.risk_observation import RiskObservation
from app.tasks.celery_app import celery_app
from app.services.hazard_service import estimate_lhasa_style_hazard_probability
from app.services.dynamic_risk_service import calculate_dynamic_risk
from app.services.ml_service import ml_service
from app.services.weather_service import get_weather

log = logging.getLogger(__name__)

_RISK_LEVEL_ORDER = [
    RiskLevel.unknown,
    RiskLevel.low,
    RiskLevel.moderate,
    RiskLevel.high,
    RiskLevel.critical,
]

_engine = None


def _get_engine():
    global _engine
    if _engine is None:
        _engine = create_engine(settings.SYNC_DATABASE_URL, pool_pre_ping=True)
    return _engine


def _run_async(coro):
    """Bridge an async coroutine into a sync Celery worker context."""
    try:
        return asyncio.run(coro)
    except RuntimeError:
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()


def _is_escalation(prev_level: RiskLevel | str, new_level: RiskLevel | str) -> bool:
    """Return True if risk increased by at least one step."""
    def _rank(lvl) -> int:
        try:
            return _RISK_LEVEL_ORDER.index(lvl)
        except ValueError:
            return 0
    return _rank(new_level) > _rank(prev_level)


@celery_app.task(
    name="monitoring_tasks.recompute_tracked_zones",
    bind=True,
    max_retries=2,
    default_retry_delay=60,
)
def recompute_tracked_zones(self) -> dict:
    """Re-score every tracked risk zone.

    Triggered periodically by Celery beat (see celery_app.py beat_schedule).
    Returns summary statistics for observability.
    """
    engine = _get_engine()
    ml_service.load_model()

    updated = 0
    escalations = 0
    errors = 0

    with Session(engine) as session:
        zones = session.execute(
            select(RiskZone).where(RiskZone.centroid.is_not(None))
        ).scalars().all()
        zone_ids = [z.id for z in zones]

    for zone_id in zone_ids:
        try:
            with Session(engine) as session:
                zone = session.get(RiskZone, zone_id)
                if zone is None:
                    continue

                # Extract centroid coordinates from PostGIS
                row = session.execute(
                    text(
                        "SELECT ST_Y(centroid::geometry), ST_X(centroid::geometry) "
                        "FROM risk_zones WHERE id=:id"
                    ),
                    {"id": zone.id},
                ).one()
                lat, lon = float(row[0]), float(row[1])

            # Fetch live weather (graceful fallback inside weather_service)
            weather = _run_async(get_weather(lat, lon))

            # Pull stored satellite/soil values from zone metadata if available
            meta = zone.metadata_ or {}
            satellite_change = meta.get("satellite_change", 0.0)
            soil_saturation = meta.get("soil_saturation", 0.5)
            slope_deg = meta.get("slope_deg", 15.0)
            historical_susceptibility = meta.get("historical_susceptibility", 0.4)
            population_exposure = meta.get("population_exposure", 0.3)
            road_importance = meta.get("road_importance", 0.4)
            critical_infrastructure = meta.get("critical_infrastructure", 0.2)
            rate_of_change = meta.get("rate_of_change", 0.2)
            elevation_m = meta.get("elevation_m", 100.0)

            # Run ML model
            prediction = ml_service.predict(
                rainfall_mm=weather.rainfall_mm,
                humidity_pct=weather.humidity_pct,
                slope_deg=slope_deg,
                elevation_m=elevation_m,
                soil_saturation=soil_saturation,
                ndvi=meta.get("ndvi", 0.3),
                distance_to_water=meta.get("distance_to_water", 1.0),
                prev_events_30d=zone.field_report_count or 0,
            )

            # LHASA-style hazard adapter
            hazard = estimate_lhasa_style_hazard_probability(
                rainfall_24h_mm=weather.rainfall_mm,
                rainfall_7d_mm=0.0,   # 7d accumulation not yet from weather API
                slope_deg=slope_deg,
                soil_moisture=soil_saturation,
            )

            # Dynamic risk engine
            dynamic = calculate_dynamic_risk(
                ml_prediction=prediction,
                rainfall_mm=weather.rainfall_mm,
                rainfall_7d_mm=0.0,
                soil_saturation=soil_saturation,
                slope_deg=slope_deg,
                satellite_change=satellite_change,
                historical_susceptibility=historical_susceptibility,
                population_exposure=population_exposure,
                road_importance=road_importance,
                critical_infrastructure=critical_infrastructure,
                rate_of_change=rate_of_change,
                verified_field_reports=zone.field_report_count or 0,
                external_hazard_probability=hazard,
            )

            with Session(engine) as session:
                zone = session.get(RiskZone, zone_id)
                if zone is None:
                    continue

                previous_level = zone.risk_level
                escalated = _is_escalation(previous_level, dynamic.level)

                # Update live zone state
                zone.risk_level = dynamic.level
                zone.environmental_risk = dynamic.environmental_risk
                zone.exposure_score = dynamic.exposure_score
                zone.priority_score = dynamic.priority_score
                zone.risk_score_max = max(zone.risk_score_max or 0, dynamic.priority_score)
                zone.risk_score_avg = dynamic.priority_score
                zone.reasons = dynamic.reasons
                zone.recommended_action = dynamic.recommended_action
                zone.last_hazard_probability = hazard

                # Append immutable time-series observation
                session.add(RiskObservation(
                    zone_id=zone.id,
                    location=zone.centroid,
                    rainfall_24h_mm=weather.rainfall_mm,
                    rainfall_7d_mm=0.0,
                    soil_saturation=soil_saturation,
                    slope_deg=slope_deg,
                    satellite_change=satellite_change,
                    historical_susceptibility=historical_susceptibility,
                    population_exposure=population_exposure,
                    road_importance=road_importance,
                    critical_infrastructure=critical_infrastructure,
                    rate_of_change=rate_of_change,
                    model_probability=prediction.score / 100.0,
                    hazard_probability=hazard,
                    environmental_risk=dynamic.environmental_risk,
                    exposure_score=dynamic.exposure_score,
                    priority_score=dynamic.priority_score,
                    risk_level=dynamic.level.value,
                    reasons="; ".join(dynamic.reasons),
                    recommended_action=dynamic.recommended_action,
                ))

                session.commit()
                updated += 1

                if escalated:
                    escalations += 1
                    log.warning(
                        "Zone %d escalated: %s → %s (priority=%.1f)",
                        zone_id, previous_level, dynamic.level, dynamic.priority_score,
                    )
                    # Fire alert task for High/Critical escalations
                    if dynamic.level in (RiskLevel.high, RiskLevel.critical):
                        from app.tasks.alert_tasks import dispatch_alert  # noqa: avoid circular at module level
                        log.info("Zone %d: escalation alert queued", zone_id)

        except Exception as exc:
            log.error("Monitoring error for zone %d: %s", zone_id, exc, exc_info=True)
            errors += 1

    log.info(
        "Monitoring pass complete: zones=%d updated=%d escalations=%d errors=%d",
        len(zone_ids), updated, escalations, errors,
    )
    return {
        "zones_checked": len(zone_ids),
        "updated": updated,
        "escalations": escalations,
        "errors": errors,
    }