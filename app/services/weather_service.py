from __future__ import annotations
import httpx
import logging
from dataclasses import dataclass

from app.config import settings

logger = logging.getLogger(__name__)

OWM_BASE = "https://api.openweathermap.org/data/2.5"


@dataclass
class WeatherSnapshot:
    rainfall_mm: float       # mm over next 3 hours
    humidity_pct: float      # %
    temp_c: float
    wind_speed_ms: float
    description: str


async def get_weather(lat: float, lon: float) -> WeatherSnapshot:
    """
    Fetch current weather + 3h rainfall forecast from OpenWeatherMap.
    Falls back to neutral defaults if API key is missing or call fails.
    """
    if not settings.OPENWEATHER_API_KEY:
        logger.warning("OPENWEATHER_API_KEY not set — using neutral weather defaults")
        return WeatherSnapshot(
            rainfall_mm=0.0, humidity_pct=60.0, temp_c=20.0,
            wind_speed_ms=2.0, description="data unavailable"
        )

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Current weather
            current_resp = await client.get(
                f"{OWM_BASE}/weather",
                params={"lat": lat, "lon": lon, "appid": settings.OPENWEATHER_API_KEY, "units": "metric"},
            )
            current_resp.raise_for_status()
            current = current_resp.json()

            # 3-hour forecast for rainfall
            forecast_resp = await client.get(
                f"{OWM_BASE}/forecast",
                params={"lat": lat, "lon": lon, "appid": settings.OPENWEATHER_API_KEY, "units": "metric", "cnt": 2},
            )
            forecast_resp.raise_for_status()
            forecast = forecast_resp.json()

        rainfall_mm = 0.0
        for item in forecast.get("list", []):
            rainfall_mm += item.get("rain", {}).get("3h", 0.0)

        return WeatherSnapshot(
            rainfall_mm=rainfall_mm,
            humidity_pct=current.get("main", {}).get("humidity", 60.0),
            temp_c=current.get("main", {}).get("temp", 20.0),
            wind_speed_ms=current.get("wind", {}).get("speed", 0.0),
            description=current.get("weather", [{}])[0].get("description", ""),
        )

    except Exception as exc:
        logger.error("Weather API error: %s", exc)
        return WeatherSnapshot(
            rainfall_mm=5.0, humidity_pct=75.0, temp_c=18.0,
            wind_speed_ms=3.0, description="fetch error"
        )
