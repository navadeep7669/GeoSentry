from __future__ import annotations
"""
XGBoost training script for the Landslide Risk Model.

Usage:
    python -m app.ml.trainer

Trains on app/ml/soil_data.csv (which includes synthetic feature rows).
Outputs app/ml/model.pkl.

Feature columns in soil_data.csv:
    rainfall_mm, humidity_pct, slope_deg, elevation_m,
    soil_saturation, ndvi, distance_to_water_km, prev_events_30d,
    risk_score  (0.0–1.0 target)
"""
import os
import logging
import pandas as pd
import numpy as np
import joblib
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score
from xgboost import XGBRegressor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

FEATURE_COLS = [
    "rainfall_mm", "humidity_pct", "slope_deg", "elevation_m",
    "soil_saturation", "ndvi", "distance_to_water_km", "prev_events_30d",
]
TARGET_COL = "risk_score"
MODEL_PATH = os.path.join(os.path.dirname(__file__), "model.pkl")
DATA_PATH = os.path.join(os.path.dirname(__file__), "soil_data.csv")


def train() -> None:
    logger.info("Loading training data from %s", DATA_PATH)
    df_raw = pd.read_csv(DATA_PATH)

    # If rainfall_mm or humidity_pct are missing, create augmented feature matrix
    if "rainfall_mm" not in df_raw.columns or "humidity_pct" not in df_raw.columns:
        logger.info("Augmenting soil data with simulated rainfall/humidity scenarios")
        records = []
        np.random.seed(42)
        for _, row in df_raw.iterrows():
            for _ in range(25):  # 25 weather scenarios per location
                rain = float(np.random.exponential(scale=20.0))
                humidity = float(np.clip(np.random.normal(65.0, 20.0), 10.0, 100.0))
                slope = float(row["slope_deg"])
                elev = float(row["elevation_m"])
                soil_sat = float(np.clip(row["soil_saturation"] + (rain / 200.0), 0.0, 1.0))
                ndvi_val = float(row["ndvi"])
                dist_w = float(row["distance_to_water_km"])
                prev_ev = int(row.get("prev_events_30d", 0))

                # Heuristic risk formula for synthetic ground truth (0-100)
                raw_score = (
                    rain * 0.45
                    + (humidity / 100.0) * 10.0
                    + (slope / 45.0) * 25.0
                    + soil_sat * 20.0
                    - max(0.0, ndvi_val) * 10.0
                    + min(5, prev_ev) * 3.0
                    + np.random.normal(0, 2.0)
                )
                score = float(np.clip(raw_score, 0.0, 100.0))

                records.append({
                    "rainfall_mm": rain,
                    "humidity_pct": humidity,
                    "slope_deg": slope,
                    "elevation_m": elev,
                    "soil_saturation": soil_sat,
                    "ndvi": ndvi_val,
                    "distance_to_water_km": dist_w,
                    "prev_events_30d": prev_ev,
                    "risk_score": score,
                })
        df = pd.DataFrame(records)
    else:
        df = df_raw

    X = df[FEATURE_COLS]
    y = df[TARGET_COL]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = XGBRegressor(
        n_estimators=300,
        max_depth=6,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        objective="reg:squarederror",
        random_state=42,
        n_jobs=-1,
    )

    logger.info("Training XGBoost on %d samples …", len(X_train))
    model.fit(X_train, y_train, eval_set=[(X_test, y_test)], verbose=False)

    y_pred = model.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)
    logger.info("Test MAE=%.4f  R²=%.4f", mae, r2)

    joblib.dump(model, MODEL_PATH)
    logger.info("Model saved to %s", MODEL_PATH)


if __name__ == "__main__":
    train()
