"""Acceptance tests: Full system scenarios using mocked database layer.

These tests validate the complete API behaviour (all 5 acceptance scenarios)
without requiring running services. Database calls are mocked.
"""

import time
import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient

pytestmark = pytest.mark.acceptance


@pytest.fixture(scope="module")
def api_client():
    from api.main import app

    return TestClient(app)


class TestHealthyPatientFlow:
    """Scenario 1: Normal patient – green status, LOW risk."""

    @patch("api.routes.vitals.database.get_latest_vital", new_callable=AsyncMock)
    @patch("api.routes.predictions.database.get_latest_prediction", new_callable=AsyncMock)
    def test_healthy_vitals_displayed(self, mock_pred, mock_vital, api_client):
        mock_vital.return_value = {
            "id": 1,
            "timestamp": int(time.time() * 1000),
            "hr": 75.0,
            "bp_sys": 120.0,
            "bp_dia": 80.0,
            "o2_sat": 98.0,
            "temperature": 37.0,
            "quality": 95,
            "source": "simulator",
        }
        mock_pred.return_value = {
            "id": 1,
            "timestamp": int(time.time() * 1000),
            "risk_score": 20.0,
            "risk_level": "LOW",
            "confidence": 0.8,
        }

        resp = api_client.get("/api/v1/vitals/latest")
        assert resp.status_code == 200
        vital = resp.json()
        assert vital["hr"] == 75.0
        assert vital["o2_sat"] == 98.0

        resp = api_client.get("/api/v1/predictions/latest")
        assert resp.status_code == 200
        pred = resp.json()
        assert pred["risk_level"] == "LOW"
        assert pred["risk_score"] == 20.0


class TestTachycardiaAlert:
    """Scenario 2: Tachycardia – HR > 120 → MEDIUM alert."""

    @patch("api.routes.alerts.database.get_alerts", new_callable=AsyncMock)
    def test_tachycardia_alert_present(self, mock_alerts, api_client):
        mock_alerts.return_value = [
            {
                "id": 1,
                "vital_id": 10,
                "prediction_id": None,
                "alert_type": "hr_high",
                "message": "Heart rate elevated: 135.0",
                "severity": "MEDIUM",
                "acknowledged": False,
            }
        ]
        resp = api_client.get("/api/v1/alerts?acknowledged=false")
        assert resp.status_code == 200
        alerts = resp.json()
        assert len(alerts) > 0
        alert = next(a for a in alerts if a["alert_type"] == "hr_high")
        assert alert["severity"] == "MEDIUM"
        assert "135" in alert["message"]


class TestHighSepsisRiskAlert:
    """Scenario 3: High sepsis risk → HIGH alert, acknowledgeable."""

    @patch("api.routes.alerts.database.get_alerts", new_callable=AsyncMock)
    def test_high_sepsis_alert_present(self, mock_alerts, api_client):
        mock_alerts.return_value = [
            {
                "id": 2,
                "vital_id": None,
                "prediction_id": 5,
                "alert_type": "sepsis_risk_high",
                "message": "Sepsis risk HIGH: score=78.0",
                "severity": "HIGH",
                "acknowledged": False,
            }
        ]
        resp = api_client.get("/api/v1/alerts")
        assert resp.status_code == 200
        alerts = resp.json()
        high = next(a for a in alerts if a["alert_type"] == "sepsis_risk_high")
        assert high["severity"] == "HIGH"
        assert high["acknowledged"] is False

    @patch("api.routes.alerts.database.acknowledge_alert", new_callable=AsyncMock)
    def test_alert_can_be_acknowledged(self, mock_ack, api_client):
        mock_ack.return_value = True
        resp = api_client.post("/api/v1/alerts/2/acknowledge")
        assert resp.status_code == 200
        assert resp.json()["status"] == "acknowledged"
        assert resp.json()["id"] == 2


class TestTwentyFourHourAnalytics:
    """Scenario 4: 24-hour analytics summary and trend chart."""

    @patch("api.routes.analytics.database.get_analytics_summary", new_callable=AsyncMock)
    def test_summary_vital_count(self, mock_summary, api_client):
        mock_summary.return_value = {
            "period_hours": 24,
            "vital_count": 144,
            "prediction_count": 144,
            "avg_hr": 76.5,
            "avg_bp_sys": 122.0,
            "avg_o2_sat": 97.8,
            "avg_temperature": 37.0,
            "high_risk_count": 3,
        }
        resp = api_client.get("/api/v1/analytics/summary?hours=24")
        assert resp.status_code == 200
        data = resp.json()
        assert data["vital_count"] == 144
        assert data["period_hours"] == 24
        assert data["avg_hr"] == 76.5
        assert data["high_risk_count"] == 3

    @patch("api.routes.analytics.database.query_vitals_trends", new_callable=AsyncMock)
    def test_trend_chart_144_data_points(self, mock_trends, api_client):
        base_ts = int(time.time() * 1000) - 24 * 3600 * 1000
        mock_trends.return_value = [
            {"timestamp": base_ts + i * 600_000, "value": 72.0 + (i % 10)}
            for i in range(144)
        ]
        resp = api_client.get("/api/v1/analytics/trends?metric=hr&hours=24")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 144
        assert "timestamp" in data[0]
        assert "value" in data[0]


class TestWebSocketRealTime:
    """Scenario 5: WebSocket delivers real-time updates."""

    def test_websocket_stream_endpoint_exists(self, api_client):
        """WebSocket endpoint accepts connections."""
        with api_client.websocket_connect("/api/v1/stream") as ws:
            ws.send_text("ping")
            response = ws.receive_text()
            assert response == "pong"

    @patch("api.routes.vitals.database.get_latest_vital", new_callable=AsyncMock)
    def test_latest_vital_served_from_rest(self, mock_vital, api_client):
        """REST fallback returns latest vital correctly."""
        mock_vital.return_value = {
            "id": 99,
            "timestamp": int(time.time() * 1000),
            "hr": 78.0,
            "bp_sys": 118.0,
            "bp_dia": 77.0,
            "o2_sat": 98.5,
            "temperature": 37.0,
            "quality": 96,
            "source": "simulator",
        }
        resp = api_client.get("/api/v1/vitals/latest")
        assert resp.status_code == 200
        data = resp.json()
        assert data["hr"] == 78.0
