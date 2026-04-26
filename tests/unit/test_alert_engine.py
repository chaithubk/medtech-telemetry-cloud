"""Unit tests for the alert engine threshold checking."""

import pytest

from api.services.alert_engine import check_vital_alerts, check_prediction_alerts


class TestVitalAlerts:
    def test_normal_vitals_no_alerts(self):
        vital = {"hr": 75, "bp_sys": 120, "bp_dia": 80, "o2_sat": 98, "temperature": 37.0}
        assert check_vital_alerts(vital) == []

    def test_high_hr_triggers_alert(self):
        vital = {"hr": 135, "bp_sys": 120, "bp_dia": 80, "o2_sat": 98, "temperature": 37.0}
        alerts = check_vital_alerts(vital)
        types = [a["alert_type"] for a in alerts]
        assert "hr_high" in types

    def test_low_hr_triggers_alert(self):
        vital = {"hr": 40, "bp_sys": 110, "bp_dia": 70, "o2_sat": 98, "temperature": 37.0}
        alerts = check_vital_alerts(vital)
        assert any(a["alert_type"] == "hr_low" for a in alerts)

    def test_low_o2_sat_triggers_alert(self):
        vital = {"hr": 75, "bp_sys": 120, "bp_dia": 80, "o2_sat": 88, "temperature": 37.0}
        alerts = check_vital_alerts(vital)
        assert any(a["alert_type"] == "o2_sat_low" for a in alerts)

    def test_fever_triggers_alert(self):
        vital = {"hr": 90, "bp_sys": 120, "bp_dia": 80, "o2_sat": 96, "temperature": 39.5}
        alerts = check_vital_alerts(vital)
        assert any(a["alert_type"] == "temperature_high" for a in alerts)

    def test_hypertensive_crisis_triggers_alert(self):
        vital = {"hr": 90, "bp_sys": 190, "bp_dia": 80, "o2_sat": 97, "temperature": 37.0}
        alerts = check_vital_alerts(vital)
        assert any(a["alert_type"] == "bp_sys_high" for a in alerts)

    def test_none_field_is_skipped(self):
        vital = {"hr": None, "bp_sys": None, "o2_sat": None, "temperature": None}
        assert check_vital_alerts(vital) == []

    def test_vital_id_propagated(self):
        vital = {"hr": 135, "bp_sys": 120, "bp_dia": 80, "o2_sat": 98, "temperature": 37.0}
        alerts = check_vital_alerts(vital, vital_id=42)
        assert alerts[0]["vital_id"] == 42
        assert alerts[0]["prediction_id"] is None

    def test_severity_medium_for_hr_high(self):
        vital = {"hr": 125, "bp_sys": 120, "bp_dia": 80, "o2_sat": 98, "temperature": 37.0}
        alerts = check_vital_alerts(vital)
        hr_alert = next(a for a in alerts if a["alert_type"] == "hr_high")
        assert hr_alert["severity"] == "MEDIUM"

    def test_severity_high_for_o2_low(self):
        vital = {"hr": 75, "o2_sat": 88}
        alerts = check_vital_alerts(vital)
        o2_alert = next(a for a in alerts if a["alert_type"] == "o2_sat_low")
        assert o2_alert["severity"] == "HIGH"


class TestPredictionAlerts:
    def test_low_risk_no_alert(self):
        pred = {"risk_score": 20.0, "risk_level": "LOW", "confidence": 0.8}
        assert check_prediction_alerts(pred) == []

    def test_medium_risk_triggers_medium_alert(self):
        pred = {"risk_score": 50.0, "risk_level": "MEDIUM", "confidence": 0.75}
        alerts = check_prediction_alerts(pred)
        assert any(a["alert_type"] == "sepsis_risk_medium" for a in alerts)
        medium = next(a for a in alerts if a["alert_type"] == "sepsis_risk_medium")
        assert medium["severity"] == "MEDIUM"

    def test_high_risk_triggers_high_alert(self):
        pred = {"risk_score": 75.0, "risk_level": "HIGH", "confidence": 0.85}
        alerts = check_prediction_alerts(pred)
        assert any(a["alert_type"] == "sepsis_risk_high" for a in alerts)
        high = next(a for a in alerts if a["alert_type"] == "sepsis_risk_high")
        assert high["severity"] == "HIGH"

    def test_high_risk_does_not_also_trigger_medium(self):
        pred = {"risk_score": 80.0, "risk_level": "HIGH", "confidence": 0.9}
        alerts = check_prediction_alerts(pred)
        types = [a["alert_type"] for a in alerts]
        assert "sepsis_risk_high" in types
        assert "sepsis_risk_medium" not in types

    def test_prediction_id_propagated(self):
        pred = {"risk_score": 75.0, "risk_level": "HIGH", "confidence": 0.85}
        alerts = check_prediction_alerts(pred, prediction_id=7)
        assert alerts[0]["prediction_id"] == 7
        assert alerts[0]["vital_id"] is None
