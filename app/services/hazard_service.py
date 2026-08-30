from __future__ import annotations
"""LHASA-style hazard probability adapter.

This module provides a clean interface between the hazard/susceptibility
model layer and the dynamic risk engine.

IMPORTANT: This is NOT NASA's operational LHASA model.
It is a lightweight signal that preserves the same interface so the
calculation can be replaced with a real validated model later without
changing any downstream code.

A production deployment should replace this with:
  - NASA LHASA v2 (IMERG + SMAP + terrain)
  - A regional calibrated model (e.g., India Meteorological Department)
  - A D_LSM-derived susceptibility signal
"""


def estimate_lhasa_style_hazard_probability(
    rainfall_24h_mm: float,
    rainfall_7d_mm: float,
    slope_deg: float,
    soil_moisture: float,
) -> float:
    """Estimate a simplified hazard probability (0..1) from environmental inputs.

    MVP weighting (not scientifically validated for any specific region):
      - 50% rainfall anomaly signal
      - 30% slope factor
      - 20% soil moisture

    Replace with a real validated model by:
      1. Implementing a new function with the same signature.
      2. Calling it here (or passing it as a dependency).
      3. The rest of the pipeline requires no changes.

    Args:
        rainfall_24h_mm: Rainfall in last 24 hours (mm).
        rainfall_7d_mm:  Accumulated rainfall over 7 days (mm).
        slope_deg:       Slope angle (degrees).
        soil_moisture:   Soil moisture fraction (0..1).

    Returns:
        Hazard probability in [0.0, 1.0].
    """
    rain_anomaly = min(
        1.0,
        0.6 * rainfall_24h_mm / 120.0 + 0.4 * rainfall_7d_mm / 400.0,
    )
    slope_factor = min(1.0, slope_deg / 45.0)
    probability = (
        0.50 * rain_anomaly
        + 0.30 * slope_factor
        + 0.20 * soil_moisture
    )
    return round(max(0.0, min(1.0, probability)), 4)