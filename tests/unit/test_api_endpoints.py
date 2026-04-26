"""Unit tests for REST API endpoints (database calls mocked)."""

import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def client():
    from api.main import app
    return TestClient(app)


class TestHealthEndpoint:
    def test_health_returns_200(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_health_response_structure(self, client):
        response = client.get("/health")
        data = response.json()
        assert "status" in data
        assert "message" in data


class TestVitalsEndpoints:
    @patch("api.routes.vitals.database.get_vitals", new_callable=AsyncMock)
    def test_get_vitals_returns_list(self, mock_db, client):
        mock_db.return_value = [
            {
                "id": 1, "timestamp": 1_000_000, "hr": 75.0,
                "bp_sys": 120.0, "bp_dia": 80.0,
                "o2_sat": 98.0, "temperature": 37.0,
                "quality": 95, "source": "device",
            }
        ]
        response = client.get("/api/v1/vitals")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert data[0]["hr"] == 75.0

    @patch("api.routes.vitals.database.get_vitals", new_callable=AsyncMock)
    def test_get_vitals_empty_returns_empty_list(self, mock_db, client):
        mock_db.return_value = []
        response = client.get("/api/v1/vitals")
        assert response.status_code == 200
        assert response.json() == []

    @patch("api.routes.vitals.database.get_vitals", new_callable=AsyncMock)
    def test_get_vitals_limit_param(self, mock_db, client):
        mock_db.return_value = []
        client.get("/api/v1/vitals?limit=5")
        mock_db.assert_called_once_with(limit=5, hours=None)

    @patch("api.routes.vitals.database.get_latest_vital", new_callable=AsyncMock)
    def test_get_latest_vital_returns_record(self, mock_db, client):
        mock_db.return_value = {"id": 1, "timestamp": 1_000_000, "hr": 75.0}
        response = client.get("/api/v1/vitals/latest")
        assert response.status_code == 200
        assert response.json()["hr"] == 75.0

    @patch("api.routes.vitals.database.get_latest_vital", new_callable=AsyncMock)
    def test_get_latest_vital_returns_404_when_empty(self, mock_db, client):
        mock_db.return_value = None
        response = client.get("/api/v1/vitals/latest")
        assert response.status_code == 404

    @patch("api.routes.vitals.database.get_vital_by_id", new_callable=AsyncMock)
    def test_get_vital_by_id_returns_record(self, mock_db, client):
        mock_db.return_value = {"id": 5, "timestamp": 1_000_000, "hr": 80.0}
        response = client.get("/api/v1/vitals/5")
        assert response.status_code == 200
        assert response.json()["id"] == 5

    @patch("api.routes.vitals.database.get_vital_by_id", new_callable=AsyncMock)
    def test_get_vital_by_id_returns_404(self, mock_db, client):
        mock_db.return_value = None
        response = client.get("/api/v1/vitals/999")
        assert response.status_code == 404

    @patch("api.routes.vitals.database.write_vital_to_influx", new_callable=AsyncMock)
    @patch("api.routes.vitals.database.insert_vital", new_callable=AsyncMock)
    def test_post_vital_valid_body_returns_created(self, mock_insert, mock_influx, client):
        mock_insert.return_value = 10
        mock_influx.return_value = True
        body = {
            "timestamp": 1_000_000, "hr": 75.0, "bp_sys": 120.0, "bp_dia": 80.0,
            "o2_sat": 98.0, "temperature": 37.0, "quality": 95, "source": "test",
        }
        response = client.post("/api/v1/vitals", json=body)
        assert response.status_code == 200
        assert response.json()["status"] == "created"
        assert response.json()["id"] == 10

    def test_post_vital_invalid_hr_returns_422(self, client):
        body = {"timestamp": 1_000_000, "hr": 999.0}  # hr > 300 is invalid
        response = client.post("/api/v1/vitals", json=body)
        assert response.status_code == 422

    def test_post_vital_missing_timestamp_returns_422(self, client):
        body = {"hr": 75.0}
        response = client.post("/api/v1/vitals", json=body)
        assert response.status_code == 422


class TestPredictionsEndpoints:
    @patch("api.routes.predictions.database.get_predictions", new_callable=AsyncMock)
    def test_get_predictions_returns_list(self, mock_db, client):
        mock_db.return_value = [
            {"id": 1, "timestamp": 1_000_000, "risk_score": 45.0, "risk_level": "LOW", "confidence": 0.75}
        ]
        response = client.get("/api/v1/predictions")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert data[0]["risk_score"] == 45.0

    @patch("api.routes.predictions.database.get_latest_prediction", new_callable=AsyncMock)
    def test_get_latest_prediction_returns_record(self, mock_db, client):
        mock_db.return_value = {
            "id": 1, "timestamp": 1_000_000,
            "risk_score": 30.0, "risk_level": "LOW", "confidence": 0.8,
        }
        response = client.get("/api/v1/predictions/latest")
        assert response.status_code == 200
        assert response.json()["risk_level"] == "LOW"

    @patch("api.routes.predictions.database.get_latest_prediction", new_callable=AsyncMock)
    def test_get_latest_prediction_returns_404_when_empty(self, mock_db, client):
        mock_db.return_value = None
        response = client.get("/api/v1/predictions/latest")
        assert response.status_code == 404

    @patch("api.routes.predictions.database.write_prediction_to_influx", new_callable=AsyncMock)
    @patch("api.routes.predictions.database.insert_prediction", new_callable=AsyncMock)
    def test_post_prediction_valid_body_returns_created(self, mock_insert, mock_influx, client):
        mock_insert.return_value = 5
        mock_influx.return_value = True
        body = {
            "timestamp": 1_000_000, "risk_score": 30.0, "risk_level": "LOW", "confidence": 0.8,
        }
        response = client.post("/api/v1/predictions", json=body)
        assert response.status_code == 200
        assert response.json()["status"] == "created"
        assert response.json()["id"] == 5

    def test_post_prediction_invalid_risk_level_returns_422(self, client):
        body = {
            "timestamp": 1_000_000, "risk_score": 30.0,
            "risk_level": "INVALID", "confidence": 0.8,
        }
        response = client.post("/api/v1/predictions", json=body)
        assert response.status_code == 422

    def test_post_prediction_missing_required_fields_returns_422(self, client):
        body = {"timestamp": 1_000_000}  # missing risk_score, risk_level, confidence
        response = client.post("/api/v1/predictions", json=body)
        assert response.status_code == 422


class TestAnalyticsEndpoints:
    @patch("api.routes.analytics.database.get_analytics_summary", new_callable=AsyncMock)
    def test_get_summary_returns_stats(self, mock_db, client):
        mock_db.return_value = {
            "period_hours": 24,
            "vital_count": 100,
            "prediction_count": 50,
            "avg_hr": 75.5,
            "high_risk_count": 3,
        }
        response = client.get("/api/v1/analytics/summary")
        assert response.status_code == 200
        data = response.json()
        assert data["vital_count"] == 100
        assert data["avg_hr"] == 75.5

    @patch("api.routes.analytics.database.query_vitals_trends", new_callable=AsyncMock)
    def test_get_trends_returns_data(self, mock_db, client):
        mock_db.return_value = [{"timestamp": 1_000_000, "value": 75.0}]
        response = client.get("/api/v1/analytics/trends?metric=hr")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["value"] == 75.0

    def test_get_trends_invalid_metric_returns_400(self, client):
        response = client.get("/api/v1/analytics/trends?metric=invalid_metric")
        assert response.status_code == 400


class TestAlertsEndpoints:
    @patch("api.routes.alerts.database.get_alerts", new_callable=AsyncMock)
    def test_get_alerts_returns_list(self, mock_db, client):
        mock_db.return_value = [
            {"id": 1, "alert_type": "hr_high", "severity": "MEDIUM", "acknowledged": False}
        ]
        response = client.get("/api/v1/alerts")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["severity"] == "MEDIUM"

    @patch("api.routes.alerts.database.get_alerts", new_callable=AsyncMock)
    def test_get_alerts_filtered_unacknowledged(self, mock_db, client):
        mock_db.return_value = []
        client.get("/api/v1/alerts?acknowledged=false")
        mock_db.assert_called_once_with(limit=20, acknowledged=False)

    @patch("api.routes.alerts.database.acknowledge_alert", new_callable=AsyncMock)
    def test_acknowledge_alert_returns_200(self, mock_db, client):
        mock_db.return_value = True
        response = client.post("/api/v1/alerts/1/acknowledge")
        assert response.status_code == 200
        assert response.json()["status"] == "acknowledged"
        assert response.json()["id"] == 1

    @patch("api.routes.alerts.database.acknowledge_alert", new_callable=AsyncMock)
    def test_acknowledge_nonexistent_alert_returns_404(self, mock_db, client):
        mock_db.return_value = False
        response = client.post("/api/v1/alerts/999/acknowledge")
        assert response.status_code == 404
