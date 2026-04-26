"""Unit tests for database service functions (SQLAlchemy mocked)."""

import time
import pytest
from unittest.mock import MagicMock, patch, call


class TestInsertVitalSync:
    @patch("api.services.database.SessionLocal")
    def test_insert_vital_returns_id(self, mock_session_class):
        from api.services.database import _insert_vital_sync

        mock_session = MagicMock()
        mock_session_class.return_value.__enter__ = MagicMock(return_value=mock_session)
        mock_session_class.return_value.__exit__ = MagicMock(return_value=False)
        mock_result = MagicMock()
        mock_result.fetchone.return_value = (42,)
        mock_session.execute.return_value = mock_result

        vital = {
            "timestamp": int(time.time() * 1000),
            "hr": 75.0, "bp_sys": 120.0, "bp_dia": 80.0,
            "o2_sat": 98.0, "temperature": 37.0,
            "quality": 95, "source": "test",
        }
        result = _insert_vital_sync(vital)
        assert result == 42
        mock_session.commit.assert_called_once()

    @patch("api.services.database.SessionLocal")
    def test_insert_vital_duplicate_returns_none(self, mock_session_class):
        from api.services.database import _insert_vital_sync

        mock_session = MagicMock()
        mock_session_class.return_value.__enter__ = MagicMock(return_value=mock_session)
        mock_session_class.return_value.__exit__ = MagicMock(return_value=False)
        mock_result = MagicMock()
        mock_result.fetchone.return_value = None  # ON CONFLICT DO NOTHING → no row
        mock_session.execute.return_value = mock_result

        vital = {"timestamp": 999, "hr": 70.0, "bp_sys": 115.0, "bp_dia": 75.0,
                 "o2_sat": 97.0, "temperature": 36.9, "quality": 90, "source": "test"}
        result = _insert_vital_sync(vital)
        assert result is None

    @patch("api.services.database.SessionLocal")
    def test_insert_vital_exception_returns_none(self, mock_session_class):
        from api.services.database import _insert_vital_sync

        mock_session = MagicMock()
        mock_session_class.return_value.__enter__ = MagicMock(return_value=mock_session)
        mock_session_class.return_value.__exit__ = MagicMock(return_value=False)
        mock_session.execute.side_effect = Exception("DB error")

        vital = {"timestamp": 888, "hr": 70.0, "bp_sys": 115.0, "bp_dia": 75.0,
                 "o2_sat": 97.0, "temperature": 36.9, "quality": 90, "source": "test"}
        result = _insert_vital_sync(vital)
        assert result is None
        mock_session.rollback.assert_called_once()


class TestInsertPredictionSync:
    @patch("api.services.database.SessionLocal")
    def test_insert_prediction_returns_id(self, mock_session_class):
        from api.services.database import _insert_prediction_sync

        mock_session = MagicMock()
        mock_session_class.return_value.__enter__ = MagicMock(return_value=mock_session)
        mock_session_class.return_value.__exit__ = MagicMock(return_value=False)
        mock_result = MagicMock()
        mock_result.fetchone.return_value = (7,)
        mock_session.execute.return_value = mock_result

        pred = {"timestamp": 1000, "risk_score": 30.0, "risk_level": "LOW",
                "confidence": 0.8, "model_latency_ms": 55.0}
        result = _insert_prediction_sync(pred)
        assert result == 7

    @patch("api.services.database.SessionLocal")
    def test_insert_prediction_exception_returns_none(self, mock_session_class):
        from api.services.database import _insert_prediction_sync

        mock_session = MagicMock()
        mock_session_class.return_value.__enter__ = MagicMock(return_value=mock_session)
        mock_session_class.return_value.__exit__ = MagicMock(return_value=False)
        mock_session.execute.side_effect = Exception("DB error")

        pred = {"timestamp": 1000, "risk_score": 30.0, "risk_level": "LOW",
                "confidence": 0.8, "model_latency_ms": None}
        result = _insert_prediction_sync(pred)
        assert result is None


class TestGetLatestVitalSync:
    @patch("api.services.database.SessionLocal")
    def test_returns_dict_when_row_found(self, mock_session_class):
        from api.services.database import _get_latest_vital_sync

        mock_session = MagicMock()
        mock_session_class.return_value.__enter__ = MagicMock(return_value=mock_session)
        mock_session_class.return_value.__exit__ = MagicMock(return_value=False)
        mock_result = MagicMock()
        mock_result.mappings.return_value.fetchone.return_value = {
            "id": 1, "timestamp": 5000, "hr": 75.0
        }
        mock_session.execute.return_value = mock_result

        result = _get_latest_vital_sync()
        assert result is not None
        assert result["hr"] == 75.0

    @patch("api.services.database.SessionLocal")
    def test_returns_none_when_empty(self, mock_session_class):
        from api.services.database import _get_latest_vital_sync

        mock_session = MagicMock()
        mock_session_class.return_value.__enter__ = MagicMock(return_value=mock_session)
        mock_session_class.return_value.__exit__ = MagicMock(return_value=False)
        mock_result = MagicMock()
        mock_result.mappings.return_value.fetchone.return_value = None
        mock_session.execute.return_value = mock_result

        result = _get_latest_vital_sync()
        assert result is None


class TestAcknowledgeAlertSync:
    @patch("api.services.database.SessionLocal")
    def test_returns_true_when_updated(self, mock_session_class):
        from api.services.database import _acknowledge_alert_sync

        mock_session = MagicMock()
        mock_session_class.return_value.__enter__ = MagicMock(return_value=mock_session)
        mock_session_class.return_value.__exit__ = MagicMock(return_value=False)
        mock_result = MagicMock()
        mock_result.fetchone.return_value = (1,)
        mock_session.execute.return_value = mock_result

        assert _acknowledge_alert_sync(1) is True

    @patch("api.services.database.SessionLocal")
    def test_returns_false_when_not_found(self, mock_session_class):
        from api.services.database import _acknowledge_alert_sync

        mock_session = MagicMock()
        mock_session_class.return_value.__enter__ = MagicMock(return_value=mock_session)
        mock_session_class.return_value.__exit__ = MagicMock(return_value=False)
        mock_result = MagicMock()
        mock_result.fetchone.return_value = None
        mock_session.execute.return_value = mock_result

        assert _acknowledge_alert_sync(999) is False


class TestQueryVitalsTrends:
    def test_invalid_metric_raises_value_error(self):
        from api.services.database import _query_vitals_trends_sync

        with pytest.raises(ValueError, match="Invalid metric"):
            _query_vitals_trends_sync("'; DROP TABLE vitals; --", 24)

    def test_valid_metrics_pass_allowlist(self):
        """Valid metric names must not raise ValueError (DB call will fail, but not due to allowlist)."""
        from api.services.database import _query_vitals_trends_sync

        for metric in ("hr", "bp_sys", "bp_dia", "o2_sat", "temperature"):
            try:
                _query_vitals_trends_sync(metric, 1)
            except ValueError:
                pytest.fail(f"Valid metric '{metric}' raised ValueError")
            except Exception:
                pass  # DB connection error expected in unit test context
