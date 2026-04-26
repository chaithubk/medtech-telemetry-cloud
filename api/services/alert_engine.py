"""Alert threshold checking engine."""

import logging
from typing import List, Optional

from api.config import settings

logger = logging.getLogger(__name__)

ALERT_THRESHOLDS = {
    "hr_high": {"field": "hr", "op": ">", "value": 120, "message": "Heart rate elevated", "severity": "MEDIUM"},
    "hr_low": {"field": "hr", "op": "<", "value": 50, "message": "Heart rate critically low", "severity": "HIGH"},
    "o2_sat_low": {"field": "o2_sat", "op": "<", "value": 92, "message": "Oxygen saturation low", "severity": "HIGH"},
    "temperature_high": {"field": "temperature", "op": ">", "value": 38.5, "message": "Fever detected", "severity": "MEDIUM"},
    "bp_sys_high": {"field": "bp_sys", "op": ">", "value": 180, "message": "Hypertensive crisis", "severity": "HIGH"},
}


def check_vital_alerts(vital: dict, vital_id: Optional[int] = None) -> List[dict]:
    """Check vital signs against alert thresholds. Returns list of triggered alerts."""
    alerts = []
    for alert_type, threshold in ALERT_THRESHOLDS.items():
        value = vital.get(threshold["field"])
        if value is None:
            continue
        triggered = False
        if threshold["op"] == ">" and value > threshold["value"]:
            triggered = True
        elif threshold["op"] == "<" and value < threshold["value"]:
            triggered = True
        if triggered:
            alerts.append({
                "vital_id": vital_id,
                "prediction_id": None,
                "alert_type": alert_type,
                "message": f"{threshold['message']}: {value}",
                "severity": threshold["severity"],
            })
            logger.warning(f"Alert triggered: {alert_type} (value={value})")
    return alerts


def check_prediction_alerts(prediction: dict, prediction_id: Optional[int] = None) -> List[dict]:
    """Check prediction risk score against alert thresholds. Returns list of triggered alerts."""
    alerts = []
    risk_score = prediction.get("risk_score", 0)

    if risk_score > settings.ALERT_RISK_THRESHOLD:
        alerts.append({
            "vital_id": None,
            "prediction_id": prediction_id,
            "alert_type": "sepsis_risk_high",
            "message": f"Sepsis risk HIGH: score={risk_score:.1f}",
            "severity": "HIGH",
        })
        logger.warning(f"Alert triggered: sepsis_risk_high (score={risk_score})")
    elif risk_score > settings.ALERT_RISK_MEDIUM_THRESHOLD:
        alerts.append({
            "vital_id": None,
            "prediction_id": prediction_id,
            "alert_type": "sepsis_risk_medium",
            "message": f"Sepsis risk MEDIUM: score={risk_score:.1f}",
            "severity": "MEDIUM",
        })
        logger.warning(f"Alert triggered: sepsis_risk_medium (score={risk_score})")
    return alerts
