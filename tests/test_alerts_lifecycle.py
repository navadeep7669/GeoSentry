import pytest
from app.services.alert_service import AlertService, alert_service
from app.models.alert import AlertSeverity, AlertStatus


def test_alert_service_lifecycle_and_escalation():
    svc = AlertService()

    # 1. Active alerts listing
    alerts = svc.get_all_alerts()
    assert len(alerts) >= 3

    # 2. Alert creation with role-based routing
    new_alert = svc.create_alert({
        "title": "CRITICAL: Imminent Debris Flow - Kedarnath Reach",
        "severity": "critical",
        "location_name": "Kedarnath Valley",
        "message": "Critical rainfall triggers slope movement",
        "probability_pct": 96.5,
        "priority_score": 91.2,
        "impact_summary": "Pilgrim transit route NH-107 at high risk."
    }, authority_id=1)

    assert new_alert["severity"] == "critical"
    assert new_alert["status"] == "new"
    assert "citizens" in new_alert["recipient_groups"]
    assert "authorities" in new_alert["recipient_groups"]
    assert "medical" in new_alert["recipient_groups"]
    assert "higher_officials" in new_alert["recipient_groups"]
    alert_id = new_alert["id"]

    # 3. Deduplication check
    dup = svc.create_alert({
        "title": "CRITICAL: Imminent Debris Flow - Kedarnath Reach",
        "severity": "critical",
        "location_name": "Kedarnath Valley",
        "message": "Duplicate event within 30 min cooldown",
    }, authority_id=1)
    assert dup["id"] == alert_id  # Returns existing alert rather than creating spam!

    # 4. Acknowledgement by District Magistrate
    acked = svc.acknowledge_alert(alert_id, user_name="District Magistrate Rudraprayag", notes="Emergency cell active.")
    assert acked["status"] == "acknowledged"
    assert acked["acknowledged_by"] == "District Magistrate Rudraprayag"
    assert any("acknowledged" in t["event"].lower() for t in acked["timeline"])

    # 5. Response Action (IN_PROGRESS)
    responded = svc.update_response_status(alert_id, status="in_progress", action="NDRF Unit 8 deployed to valley crossing.", actor="Incident Commander")
    assert responded["status"] == "in_progress"
    assert responded["response_action"] == "NDRF Unit 8 deployed to valley crossing."

    # 6. Escalation to State Authority (SDMA)
    escalated = svc.escalate_alert(alert_id, escalated_to="Uttarakhand SDMA", reason="Rainfall >120mm forecasted overnight.")
    assert escalated["escalated"] is True
    assert "higher_officials" in escalated["recipient_groups"]

    # 7. Role-based filtering
    citizen_alerts = svc.get_all_alerts(role="citizen")
    assert all("citizens" in a["recipient_groups"] for a in citizen_alerts)

    medical_alerts = svc.get_all_alerts(role="medical")
    assert all("medical" in a["recipient_groups"] for a in medical_alerts)

