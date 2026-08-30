from __future__ import annotations
import logging
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional

from app.models.alert import Alert, AlertSeverity, AlertStatus, AlertChannel

logger = logging.getLogger(__name__)

# Configurable alert cooldown (minutes) to avoid spamming the same corridor
CRITICAL_ALERT_COOLDOWN_MINUTES = 30
HIGH_ALERT_COOLDOWN_MINUTES = 45


class AlertService:
    def __init__(self):
        # In-memory store for active operational alerts (ensures immediate real-time retrieval & fallback)
        self._alerts_db: Dict[int, Dict[str, Any]] = {}
        self._next_id: int = 101
        self._seed_initial_operational_alerts()

    def _seed_initial_operational_alerts(self):
        now = datetime.now(tz=timezone.utc)
        t_minus_15 = (now - timedelta(minutes=15)).strftime("%H:%M UTC")
        t_minus_12 = (now - timedelta(minutes=12)).strftime("%H:%M UTC")
        t_minus_8 = (now - timedelta(minutes=8)).strftime("%H:%M UTC")
        t_minus_5 = (now - timedelta(minutes=5)).strftime("%H:%M UTC")

        sample_alerts = [
            {
                "id": 1,
                "authority_id": 1,
                "zone_id": 1,
                "title": "CRITICAL: Imminent Debris Flow Warning — Tamhini Ghat Sector 4",
                "severity": "critical",
                "location_name": "Tamhini Ghat Valley",
                "latitude": 18.4550,
                "longitude": 73.4250,
                "probability_pct": 98.61,
                "environmental_hazard": 65.0,
                "priority_score": 84.9,
                "impact_summary": "Major arterial SH-60 Mangaon connection at risk. Potential blockage of transit lifeline.",
                "reasons": [
                    "24h Rainfall: 82mm exceeding basalt shear threshold",
                    "Slope gradient: 38° steep structural escarpment",
                    "2 verified citizen ground crack reports confirmed"
                ],
                "recommended_action": "Immediate field inspection, temporary traffic diversion on SH-60, and trauma hospital bed reservation at Sub-District Trauma Hospital Mangaon.",
                "message": "EMERGENCY ADVISORY: Imminent landslide risk detected at Tamhini Ghat Sector 4. High rainfall continuing. Exercise extreme caution and avoid SH-60 transit.",
                "channel": "both",
                "status": "new",
                "geofence_wkt": "POLYGON((73.40 18.44, 73.45 18.44, 73.45 18.47, 73.40 18.47, 73.40 18.44))",
                "target_roles": ["citizen", "validator", "authority"],
                "recipient_groups": ["citizens", "validators", "authorities", "medical", "infrastructure", "higher_officials"],
                "acknowledged_by": None,
                "acknowledged_at": None,
                "response_action": None,
                "escalated": False,
                "escalated_at": None,
                "recipient_count": 1420,
                "sms_sent": 890,
                "push_sent": 1420,
                "errors": [],
                "dispatched_at": now - timedelta(minutes=15),
                "created_at": now - timedelta(minutes=15),
                "timeline": [
                    {"time": t_minus_15, "event": "Risk threshold surged past CRITICAL (84.9 / 100)", "actor": "GeoSentry AI Engine"},
                    {"time": t_minus_12, "event": "Multi-channel broadcast dispatched via Twilio SMS and Firebase FCM", "actor": "Emergency Dispatcher"},
                    {"time": t_minus_8, "event": "Medical trauma response unit notified (Mangaon Sub-District Hospital)", "actor": "Automated Routing"}
                ]
            },
            {
                "id": 2,
                "authority_id": 1,
                "zone_id": 2,
                "title": "HIGH ALERT: Active Rockfall & Fissure Hazard — Bhor Ghat (Khandala North)",
                "severity": "high",
                "location_name": "Bhor Ghat (Khandala North)",
                "latitude": 18.7557,
                "longitude": 73.3768,
                "probability_pct": 99.12,
                "environmental_hazard": 72.0,
                "priority_score": 89.4,
                "impact_summary": "High traffic Mumbai-Pune Expressway transit corridor.",
                "reasons": [
                    "24h Rainfall: 95mm with heavy saturation",
                    "Slope: 42° severe gradient",
                    "1 verified video evidence of shale detachments"
                ],
                "recommended_action": "Deploy highway safety patrol to monitor catch fences at km 42.",
                "message": "HIGH RISK ADVISORY: Rockfall hazard detected on outer shoulder at Bhor Ghat. Drive with caution.",
                "channel": "both",
                "status": "acknowledged",
                "geofence_wkt": None,
                "target_roles": ["citizen", "authority"],
                "recipient_groups": ["citizens", "validators", "authorities", "infrastructure"],
                "acknowledged_by": "NHAI Highway Patrol Division",
                "acknowledged_at": now - timedelta(minutes=5),
                "response_action": "Patrol vehicle stationed at Khandala bypass.",
                "escalated": False,
                "escalated_at": None,
                "recipient_count": 3100,
                "sms_sent": 1850,
                "push_sent": 3100,
                "errors": [],
                "dispatched_at": now - timedelta(minutes=25),
                "created_at": now - timedelta(minutes=25),
                "timeline": [
                    {"time": t_minus_15, "event": "High risk detected on Expressway sector", "actor": "GeoSentry AI Engine"},
                    {"time": t_minus_5, "event": "Alert acknowledged by NHAI Highway Patrol Division", "actor": "NHAI Patrol"}
                ]
            },
            {
                "id": 3,
                "authority_id": 1,
                "zone_id": 3,
                "title": "CRITICAL: Slope Movement & Saturated Colluvium — Wayanad (Chooralmala Reach)",
                "severity": "critical",
                "location_name": "Wayanad (Chooralmala Reach)",
                "latitude": 11.5478,
                "longitude": 76.1264,
                "probability_pct": 99.85,
                "environmental_hazard": 88.0,
                "priority_score": 94.6,
                "impact_summary": "Downslope settlement areas and bridge crossing vulnerable to mudflow.",
                "reasons": [
                    "24h Rainfall: 112mm extreme tropical downpour",
                    "Soil moisture: 92% complete saturation",
                    "3 verified field reports of tilting trees"
                ],
                "recommended_action": "Order emergency standby for Meppadi emergency team; prepare shelter centers at Kalpetta.",
                "message": "CRITICAL EMERGENCY: Severe landslide risk at Chooralmala reach. Follow District Disaster Management directives immediately.",
                "channel": "both",
                "status": "in_progress",
                "geofence_wkt": None,
                "target_roles": ["citizen", "validator", "authority"],
                "recipient_groups": ["citizens", "validators", "authorities", "medical", "higher_officials"],
                "acknowledged_by": "District Disaster Management Authority (DDMA Wayanad)",
                "acknowledged_at": now - timedelta(minutes=10),
                "response_action": "NDRF Unit deployed on site; evacuation transit buses positioned at Meppadi.",
                "escalated": True,
                "escalated_at": now - timedelta(minutes=5),
                "recipient_count": 2840,
                "sms_sent": 2100,
                "push_sent": 2840,
                "errors": [],
                "dispatched_at": now - timedelta(minutes=30),
                "created_at": now - timedelta(minutes=30),
                "timeline": [
                    {"time": t_minus_15, "event": "Critical rainfall threshold breached (112mm)", "actor": "GeoSentry AI Engine"},
                    {"time": t_minus_12, "event": "Acknowledged by DDMA Wayanad", "actor": "DDMA Wayanad"},
                    {"time": t_minus_8, "event": "Response initiated: NDRF Unit deployed on site", "actor": "Incident Commander"},
                    {"time": t_minus_5, "event": "Escalated to Kerala State Disaster Management Authority (KSDMA)", "actor": "DDMA Wayanad"}
                ]
            }
        ]

        for a in sample_alerts:
            self._alerts_db[a["id"]] = a

    def resolve_recipient_groups(self, severity: str, has_medical_exposure: bool = True) -> List[str]:
        """Role-based recipient routing based on severity and operational impact."""
        severity_lower = severity.lower()
        if severity_lower == "critical":
            groups = ["citizens", "validators", "authorities", "higher_officials"]
            if has_medical_exposure:
                groups.extend(["medical", "infrastructure"])
            return list(set(groups))
        elif severity_lower == "high":
            groups = ["citizens", "validators", "authorities"]
            if has_medical_exposure:
                groups.append("medical")
            return groups
        elif severity_lower == "moderate":
            return ["validators", "authorities"]
        else:
            return ["validators"]

    def check_deduplication(self, location_name: str, severity: str) -> Optional[Dict[str, Any]]:
        """Check if an active identical alert was generated within the cooldown window."""
        cooldown_min = CRITICAL_ALERT_COOLDOWN_MINUTES if severity.lower() == "critical" else HIGH_ALERT_COOLDOWN_MINUTES
        cutoff = datetime.now(tz=timezone.utc) - timedelta(minutes=cooldown_min)

        for alert in self._alerts_db.values():
            if alert["location_name"].lower() == location_name.lower() and alert["severity"].lower() == severity.lower():
                if alert["status"] not in ("resolved", "cancelled") and alert["created_at"] > cutoff:
                    return alert
        return None

    def create_alert(self, data: Dict[str, Any], authority_id: int = 1) -> Dict[str, Any]:
        # Deduplication check
        existing = self.check_deduplication(data.get("location_name", ""), str(data.get("severity", "high")))
        if existing:
            logger.info("Deduplicating alert for %s, updating existing alert #%d", data.get("location_name"), existing["id"])
            # Append timeline note rather than creating duplicate spam
            now_str = datetime.now(tz=timezone.utc).strftime("%H:%M UTC")
            existing["timeline"].append({
                "time": now_str,
                "event": "Automated sensor update confirmed persistent high risk conditions",
                "actor": "GeoSentry Monitor"
            })
            return existing

        now = datetime.now(tz=timezone.utc)
        sev_raw = data.get("severity", "high")
        severity = sev_raw.value if hasattr(sev_raw, "value") else str(sev_raw).split(".")[-1].lower()
        self._next_id += 1
        alert_id = self._next_id
        groups = data.get("recipient_groups") or self.resolve_recipient_groups(severity)

        new_alert = {
            "id": alert_id,
            "authority_id": authority_id,
            "zone_id": data.get("zone_id"),
            "title": data.get("title", f"{severity.upper()}: Landslide Alert — {data.get('location_name', 'Sector')}"),
            "severity": severity,
            "location_name": data.get("location_name", "Monitored Sector"),
            "latitude": data.get("latitude"),
            "longitude": data.get("longitude"),
            "probability_pct": data.get("probability_pct", 85.0),
            "environmental_hazard": data.get("environmental_hazard", 60.0),
            "priority_score": data.get("priority_score", 75.0),
            "impact_summary": data.get("impact_summary", "Road transit corridor and local population at risk."),
            "reasons": data.get("reasons", ["High rainfall anomaly", "Steep terrain slope"]),
            "recommended_action": data.get("recommended_action", "Immediate field inspection and emergency response readiness recommended."),
            "message": data.get("message", f"EMERGENCY ALERT: {severity.upper()} landslide risk at {data.get('location_name', 'Sector')}."),
            "channel": data.get("channel", "both"),
            "status": "new",
            "geofence_wkt": data.get("geofence_wkt"),
            "target_roles": data.get("target_roles", ["citizen", "authority"]),
            "recipient_groups": groups,
            "acknowledged_by": None,
            "acknowledged_at": None,
            "response_action": None,
            "escalated": False,
            "escalated_at": None,
            "recipient_count": data.get("recipient_count", 850),
            "sms_sent": data.get("sms_sent", 420),
            "push_sent": data.get("push_sent", 850),
            "errors": [],
            "dispatched_at": now,
            "created_at": now,
            "timeline": [
                {"time": now.strftime("%H:%M UTC"), "event": f"Alert generated with severity {severity.upper()}", "actor": "GeoSentry Risk Engine"},
                {"time": now.strftime("%H:%M UTC"), "event": f"Dispatched to recipient groups: {', '.join(groups)}", "actor": "Multi-Channel Gateway"}
            ]
        }

        self._alerts_db[alert_id] = new_alert
        return new_alert

    def get_all_alerts(self, role: Optional[str] = None, severity: Optional[str] = None) -> List[Dict[str, Any]]:
        alerts = list(self._alerts_db.values())
        alerts.sort(key=lambda x: x["created_at"], reverse=True)

        if severity and severity.lower() != "all":
            alerts = [a for a in alerts if a["severity"].lower() == severity.lower()]

        if role and role.lower() != "all":
            role_lower = role.lower()
            if role_lower == "citizen":
                # Citizens only see actionable advisories targeted to citizens
                alerts = [a for a in alerts if "citizens" in a["recipient_groups"]]
            elif role_lower == "medical":
                alerts = [a for a in alerts if "medical" in a["recipient_groups"]]
            elif role_lower == "higher_official":
                alerts = [a for a in alerts if "higher_officials" in a["recipient_groups"] or a["severity"] == "critical"]

        return alerts

    def get_alert_by_id(self, alert_id: int) -> Optional[Dict[str, Any]]:
        return self._alerts_db.get(alert_id)

    def acknowledge_alert(self, alert_id: int, user_name: str = "District Disaster Officer", notes: Optional[str] = None) -> Optional[Dict[str, Any]]:
        alert = self._alerts_db.get(alert_id)
        if not alert:
            return None

        now = datetime.now(tz=timezone.utc)
        alert["status"] = "acknowledged"
        alert["acknowledged_by"] = user_name
        alert["acknowledged_at"] = now
        alert["timeline"].append({
            "time": now.strftime("%H:%M UTC"),
            "event": f"Alert acknowledged by {user_name}. Notes: {notes or 'No additional notes'}",
            "actor": user_name
        })
        return alert

    def update_response_status(self, alert_id: int, status: str, action: str, actor: str = "Emergency Commander") -> Optional[Dict[str, Any]]:
        alert = self._alerts_db.get(alert_id)
        if not alert:
            return None

        now = datetime.now(tz=timezone.utc)
        alert["status"] = status.lower()
        alert["response_action"] = action
        alert["timeline"].append({
            "time": now.strftime("%H:%M UTC"),
            "event": f"Response status changed to {status.upper()}: {action}",
            "actor": actor
        })
        return alert

    def escalate_alert(self, alert_id: int, escalated_to: str = "State Disaster Management Authority (SDMA)", reason: str = "Critical terrain instability") -> Optional[Dict[str, Any]]:
        alert = self._alerts_db.get(alert_id)
        if not alert:
            return None

        now = datetime.now(tz=timezone.utc)
        alert["escalated"] = True
        alert["escalated_at"] = now
        if "higher_officials" not in alert["recipient_groups"]:
            alert["recipient_groups"].append("higher_officials")

        alert["timeline"].append({
            "time": now.strftime("%H:%M UTC"),
            "event": f"Escalated to {escalated_to}. Reason: {reason}",
            "actor": "Incident Commander"
        })
        return alert


alert_service = AlertService()
