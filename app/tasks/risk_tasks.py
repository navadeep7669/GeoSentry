from __future__ import annotations
import asyncio
import logging
from datetime import datetime, timezone

from sqlalchemy import select, text
from sqlalchemy.orm import Session
from sqlalchemy import create_engine

from app.config import settings
from app.tasks.celery_app import celery_app
from app.models.report import Report, RiskLevel
from app.models.risk_zone import RiskZone

logger = logging.getLogger(__name__)

# Sync engine for Celery workers (Celery is not async)
_sync_engine = None


def _get_sync_engine():
    global _sync_engine
    if _sync_engine is None:
        _sync_engine = create_engine(settings.SYNC_DATABASE_URL, pool_pre_ping=True)
    return _sync_engine


def _get_soil_data(lat: float, lon: float) -> dict:
    """
    Look up slope and soil saturation from the soil_data table or CSV fallback.
    Grid resolution: 0.1 degrees (~11 km).
    """
    try:
        engine = _get_sync_engine()
        with engine.connect() as conn:
            result = conn.execute(
                text("""
                    SELECT slope_deg, soil_saturation, ndvi, distance_to_water_km
                    FROM soil_data
                    ORDER BY ST_Distance(
                        ST_MakePoint(longitude, latitude)::geography,
                        ST_MakePoint(:lon, :lat)::geography
                    )
                    LIMIT 1
                """),
                {"lat": lat, "lon": lon},
            ).fetchone()
            if result:
                return {
                    "slope_deg": float(result.slope_deg),
                    "soil_saturation": float(result.soil_saturation),
                    "ndvi": float(result.ndvi),
                    "distance_to_water": float(result.distance_to_water_km),
                }
    except Exception as exc:
        logger.warning("soil_data DB lookup failed: %s — using defaults", exc)

    # CSV fallback — load from app/ml/soil_data.csv
    try:
        import pandas as pd
        import numpy as np
        df = pd.read_csv("app/ml/soil_data.csv")
        df["dist"] = np.sqrt((df["latitude"] - lat) ** 2 + (df["longitude"] - lon) ** 2)
        row = df.loc[df["dist"].idxmin()]
        return {
            "slope_deg": float(row.get("slope_deg", 15.0)),
            "soil_saturation": float(row.get("soil_saturation", 0.5)),
            "ndvi": float(row.get("ndvi", 0.3)),
            "distance_to_water": float(row.get("distance_to_water_km", 1.0)),
        }
    except Exception as exc2:
        logger.warning("CSV soil_data fallback failed: %s — using hardcoded defaults", exc2)

    return {"slope_deg": 15.0, "soil_saturation": 0.5, "ndvi": 0.3, "distance_to_water": 1.0}


def _count_prev_events(lat: float, lon: float, radius_km: float = 5.0) -> int:
    """Count validated reports within radius_km in the last 30 days."""
    try:
        engine = _get_sync_engine()
        with engine.connect() as conn:
            row = conn.execute(
                text("""
                    SELECT COUNT(*) as cnt FROM reports
                    WHERE status = 'validated'
                    AND created_at > NOW() - INTERVAL '30 days'
                    AND ST_DWithin(
                        location::geography,
                        ST_MakePoint(:lon, :lat)::geography,
                        :radius_m
                    )
                """),
                {"lat": lat, "lon": lon, "radius_m": radius_km * 1000},
            ).fetchone()
            return int(row.cnt) if row else 0
    except Exception as exc:
        logger.warning("prev_events query failed: %s", exc)
        return 0


@celery_app.task(name="risk_tasks.recompute_risk", bind=True, max_retries=3, default_retry_delay=60)
def recompute_risk(self, report_id: int) -> dict:
    """
    1. Fetch validated report from DB
    2. Call weather API (sync via asyncio.run)
    3. Lookup soil/slope data
    4. Run ML model → risk_score, risk_level
    5. Update report + upsert RiskZone
    """
    from app.services.ml_service import ml_service
    from app.services.weather_service import get_weather

    ml_service.load_model()

    engine = _get_sync_engine()
    with Session(engine) as session:
        report = session.get(Report, report_id)
        if report is None:
            logger.error("Report %d not found", report_id)
            return {"error": f"Report {report_id} not found"}

        lat, lon = report.latitude, report.longitude
        elevation = report.elevation_m or 100.0

    # Fetch weather (async → sync bridge)
    try:
        weather = asyncio.run(get_weather(lat, lon))
    except RuntimeError:
        # Already inside an event loop (e.g., during testing)
        loop = asyncio.new_event_loop()
        weather = loop.run_until_complete(get_weather(lat, lon))
        loop.close()

    soil = _get_soil_data(lat, lon)
    prev_events = _count_prev_events(lat, lon)

    prediction = ml_service.predict(
        rainfall_mm=weather.rainfall_mm,
        humidity_pct=weather.humidity_pct,
        slope_deg=soil["slope_deg"],
        elevation_m=elevation,
        soil_saturation=soil["soil_saturation"],
        ndvi=soil["ndvi"],
        distance_to_water=soil["distance_to_water"],
        prev_events_30d=prev_events,
    )

    with Session(engine) as session:
        report = session.get(Report, report_id)
        if report is None:
            return {"error": "Report vanished between steps"}

        report.risk_score = prediction.score
        report.risk_level = prediction.level
        report.rainfall_mm = weather.rainfall_mm
        report.humidity_pct = weather.humidity_pct
        report.risk_computed_at = datetime.now(tz=timezone.utc)

        # Upsert RiskZone: create a ~1km² buffer polygon around the point
        zone = session.execute(
            select(RiskZone).where(
                text(f"ST_DWithin(centroid::geography, ST_MakePoint({lon},{lat})::geography, 1000)")
            )
        ).scalar_one_or_none()

        if zone is None:
            zone = RiskZone(
                boundary=text(
                    f"ST_Multi(ST_Buffer(ST_MakePoint({lon},{lat})::geography, 1000)::geometry)"
                ),
                centroid=f"SRID=4326;POINT({lon} {lat})",
                risk_level=prediction.level,
                risk_score_avg=prediction.score,
                risk_score_max=prediction.score,
                report_ids=[report_id],
            )
            session.add(zone)
        else:
            ids = zone.report_ids or []
            if report_id not in ids:
                ids.append(report_id)
            zone.report_ids = ids
            all_scores = [prediction.score, zone.risk_score_max or 0]
            zone.risk_score_max = max(all_scores)
            zone.risk_score_avg = (zone.risk_score_avg or prediction.score + prediction.score) / 2
            # Escalate risk level (never downgrade automatically)
            level_order = [RiskLevel.low, RiskLevel.moderate, RiskLevel.high, RiskLevel.critical]
            if level_order.index(prediction.level) > level_order.index(zone.risk_level):
                zone.risk_level = prediction.level

        session.commit()
        logger.info(
            "Risk computed for report %d: score=%.1f level=%s",
            report_id, prediction.score, prediction.level,
        )

    return {
        "report_id": report_id,
        "risk_score": prediction.score,
        "risk_level": prediction.level.value,
    }
