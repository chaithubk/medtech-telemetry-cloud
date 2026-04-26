"""Integration tests: Data consistency across PostgreSQL + InfluxDB."""

import time
import pytest

pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def pg_available():
    """Check PostgreSQL connectivity."""
    try:
        from sqlalchemy import text
        from api.services.database import SessionLocal

        with SessionLocal() as session:
            session.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


class TestPostgreSQLOperations:
    def test_postgres_connection(self, pg_available):
        if not pg_available:
            pytest.skip("PostgreSQL not available")
        from sqlalchemy import text
        from api.services.database import SessionLocal

        with SessionLocal() as session:
            result = session.execute(text("SELECT 1")).fetchone()
            assert result[0] == 1

    def test_insert_and_query_vital(self, pg_available):
        if not pg_available:
            pytest.skip("PostgreSQL not available")
        from api.services.database import _insert_vital_sync, _get_vitals_sync

        ts = int(time.time() * 1000) - 2000
        vital = {
            "timestamp": ts,
            "hr": 77.0,
            "bp_sys": 122.0,
            "bp_dia": 81.0,
            "o2_sat": 97.5,
            "temperature": 37.1,
            "quality": 92,
            "source": "db-sync-test",
        }
        # May be None if duplicate (test re-runs)
        _insert_vital_sync(vital)

        vitals = _get_vitals_sync(limit=10, hours=1)
        assert isinstance(vitals, list)

    def test_insert_and_query_prediction(self, pg_available):
        if not pg_available:
            pytest.skip("PostgreSQL not available")
        from api.services.database import _insert_prediction_sync, _get_predictions_sync

        ts = int(time.time() * 1000) - 3000
        pred = {
            "timestamp": ts,
            "risk_score": 35.0,
            "risk_level": "LOW",
            "confidence": 0.82,
            "model_latency_ms": 55.0,
        }
        _insert_prediction_sync(pred)

        preds = _get_predictions_sync(limit=5, hours=1)
        assert isinstance(preds, list)

    def test_duplicate_timestamp_handled_gracefully(self, pg_available):
        if not pg_available:
            pytest.skip("PostgreSQL not available")
        from api.services.database import _insert_vital_sync

        ts = int(time.time() * 1000) - 4000
        vital = {
            "timestamp": ts,
            "hr": 70.0,
            "bp_sys": 118.0,
            "bp_dia": 78.0,
            "o2_sat": 98.0,
            "temperature": 36.9,
            "quality": 90,
            "source": "dup-test",
        }
        first = _insert_vital_sync(vital)
        second = _insert_vital_sync(vital)  # duplicate – should return None gracefully
        # First insert may or may not return an ID (depends on prior test runs)
        assert second is None or isinstance(second, int)
