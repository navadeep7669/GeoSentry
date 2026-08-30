from app.models.report import RiskLevel
from app.services.dynamic_risk_service import calculate_dynamic_risk
from app.services.ml_service import RiskPrediction

def test_dynamic_risk_prioritizes_exposure():
    low_model = RiskPrediction(score=55.0, level=RiskLevel.high)
    result = calculate_dynamic_risk(
        ml_prediction=low_model,
        rainfall_mm=80,
        rainfall_7d_mm=250,
        soil_saturation=0.75,
        slope_deg=35,
        satellite_change=0.6,
        historical_susceptibility=0.7,
        population_exposure=0.9,
        road_importance=0.9,
        critical_infrastructure=0.8,
        rate_of_change=0.7,
        verified_field_reports=1,
        external_hazard_probability=0.65,
    )
    assert result.priority_score >= result.environmental_risk - 20
    assert result.level in {RiskLevel.high, RiskLevel.critical}
    assert result.reasons
    assert result.recommended_action

def test_dynamic_risk_can_be_low():
    low_model = RiskPrediction(score=5.0, level=RiskLevel.low)
    result = calculate_dynamic_risk(
        ml_prediction=low_model,
        rainfall_mm=2,
        rainfall_7d_mm=10,
        soil_saturation=0.1,
        slope_deg=5,
        satellite_change=0.0,
        historical_susceptibility=0.05,
        population_exposure=0.05,
        road_importance=0.05,
        critical_infrastructure=0.05,
        rate_of_change=0.0,
    )
    assert result.level == RiskLevel.low
