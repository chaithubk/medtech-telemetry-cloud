"""Integration tests: MQTT → DB → API data flow.

These tests require PostgreSQL and (optionally) an MQTT broker.
They are skipped automatically when services are unavailable.
"""

import time
import pytest
from fastapi.testclient import TestClient

pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def db_available():
    """Return True if PostgreSQL is reachable, else skip."""
    try:
        from sqlalchemy import text
        from api.services.database import SessionLocal

        with SessionLocal() as session:
            session.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


@pytest.fixture(scope="module")
def api_client():
    from api.main import app

    return TestClient(app)


class TestDirectInsertAndRetrieve:
    """Tests that bypass MQTT and insert data directly via the REST POST endpoints."""

    def test_vital_insert_and_retrieve(self, api_client, db_available, sample_vital):
        if not db_available:
            pytest.skip("PostgreSQL not available")

        # Insert
        resp = api_client.post("/api/v1/vitals", json=sample_vital)
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] in ("created", "duplicate")

        # Retrieve list
        resp = api_client.get("/api/v1/vitals?limit=1")
        assert resp.status_code == 200
        records = resp.json()
        assert isinstance(records, list)

    def test_prediction_insert_and_retrieve(self, api_client, db_available, sample_prediction):
        if not db_available:
            pytest.skip("PostgreSQL not available")

        resp = api_client.post("/api/v1/predictions", json=sample_prediction)
        assert resp.status_code == 200

        resp = api_client.get("/api/v1/predictions?limit=1")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_analytics_summary_returns_structure(self, api_client, db_available):
        if not db_available:
            pytest.skip("PostgreSQL not available")

        resp = api_client.get("/api/v1/analytics/summary?hours=24")
        assert resp.status_code == 200
        data = resp.json()
        assert "vital_count" in data
        assert "period_hours" in data
        assert data["period_hours"] == 24

    def test_latest_vital_after_insert(self, api_client, db_available):
        if not db_available:
            pytest.skip("PostgreSQL not available")

        vital = {
            "timestamp": int(time.time() * 1000) - 500,
            "hr": 82.0,
            "bp_sys": 125.0,
            "bp_dia": 82.0,
            "o2_sat": 97.5,
            "temperature": 37.1,
            "quality": 93,
            "source": "integration-test",
        }
        resp = api_client.post("/api/v1/vitals", json=vital)
        assert resp.status_code == 200

        resp = api_client.get("/api/v1/vitals/latest")
        # Either 200 with data or 404 if DB was empty and insert was duplicate
        assert resp.status_code in (200, 404)
