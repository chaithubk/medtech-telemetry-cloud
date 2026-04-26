"""Unit tests for MQTTClient message handlers."""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestHandleVitalShortCircuit:
    """When insert_vital returns None (duplicate/error), InfluxDB write and
    alert creation must be skipped to prevent orphaned data."""

    @pytest.mark.asyncio
    async def test_influx_and_alerts_skipped_when_insert_returns_none(self):
        from api.services.mqtt_client import MQTTClient

        client = MQTTClient()
        payload = {
            "timestamp": 1_000_000, "hr": 75.0, "bp_sys": 120.0,
            "bp_dia": 80.0, "o2_sat": 98.0, "temperature": 37.0,
            "quality": 95, "source": "test",
        }

        with (
            patch("api.services.database.insert_vital", new_callable=AsyncMock, return_value=None),
            patch("api.services.database.write_vital_to_influx", new_callable=AsyncMock) as mock_influx,
            patch("api.services.database.insert_alert", new_callable=AsyncMock) as mock_alert,
        ):
            await client._handle_vital(payload)

        mock_influx.assert_not_called()
        mock_alert.assert_not_called()

    @pytest.mark.asyncio
    async def test_influx_and_alerts_written_when_insert_succeeds(self):
        from api.services.mqtt_client import MQTTClient

        client = MQTTClient()
        payload = {
            "timestamp": 1_000_000, "hr": 75.0, "bp_sys": 120.0,
            "bp_dia": 80.0, "o2_sat": 98.0, "temperature": 37.0,
            "quality": 95, "source": "test",
        }

        with (
            patch("api.services.database.insert_vital", new_callable=AsyncMock, return_value=42),
            patch("api.services.database.write_vital_to_influx", new_callable=AsyncMock) as mock_influx,
            patch("api.services.database.insert_alert", new_callable=AsyncMock) as mock_alert,
        ):
            await client._handle_vital(payload)

        mock_influx.assert_called_once()

    @pytest.mark.asyncio
    async def test_websocket_broadcast_still_fires_on_duplicate(self):
        """Real-time display should still receive the data even if it's a duplicate."""
        from api.services.mqtt_client import MQTTClient, set_ws_broadcaster

        client = MQTTClient()
        payload = {
            "timestamp": 1_000_000, "hr": 75.0, "bp_sys": 120.0,
            "bp_dia": 80.0, "o2_sat": 98.0, "temperature": 37.0,
            "quality": 95, "source": "test",
        }
        broadcaster = AsyncMock()
        set_ws_broadcaster(broadcaster)

        try:
            with (
                patch("api.services.database.insert_vital", new_callable=AsyncMock, return_value=None),
                patch("api.services.database.write_vital_to_influx", new_callable=AsyncMock),
                patch("api.services.database.insert_alert", new_callable=AsyncMock),
            ):
                await client._handle_vital(payload)

            broadcaster.assert_called_once()
            assert broadcaster.call_args[0][0]["type"] == "vital"
        finally:
            set_ws_broadcaster(None)  # restore global state


class TestHandlePredictionShortCircuit:
    @pytest.mark.asyncio
    async def test_influx_and_alerts_skipped_when_insert_returns_none(self):
        from api.services.mqtt_client import MQTTClient

        client = MQTTClient()
        payload = {
            "timestamp": 2_000_000, "risk_score": 30.0,
            "risk_level": "LOW", "confidence": 0.8,
        }

        with (
            patch("api.services.database.insert_prediction", new_callable=AsyncMock, return_value=None),
            patch("api.services.database.write_prediction_to_influx", new_callable=AsyncMock) as mock_influx,
            patch("api.services.database.insert_alert", new_callable=AsyncMock) as mock_alert,
        ):
            await client._handle_prediction(payload)

        mock_influx.assert_not_called()
        mock_alert.assert_not_called()


class TestLogFutureException:
    def test_exception_is_logged(self):
        import logging
        from api.services.mqtt_client import MQTTClient

        client = MQTTClient()
        future = MagicMock()
        future.exception.return_value = RuntimeError("boom")

        with patch.object(
            logging.getLogger("api.services.mqtt_client"), "error"
        ) as mock_log:
            client._log_future_exception(future)

        mock_log.assert_called_once()
        assert "boom" in str(mock_log.call_args)

    def test_no_exception_is_silent(self):
        import logging
        from api.services.mqtt_client import MQTTClient

        client = MQTTClient()
        future = MagicMock()
        future.exception.return_value = None

        with patch.object(
            logging.getLogger("api.services.mqtt_client"), "error"
        ) as mock_log:
            client._log_future_exception(future)

        mock_log.assert_not_called()
