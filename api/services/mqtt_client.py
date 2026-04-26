"""MQTT client service for subscribing to medtech device messages."""

import json
import logging
import threading
import asyncio
from typing import Optional

import paho.mqtt.client as mqtt_lib

from api.config import settings

logger = logging.getLogger(__name__)

# Global WebSocket broadcaster (set by stream router at startup)
_ws_broadcaster = None


def set_ws_broadcaster(broadcaster):
    """Register async broadcast function to be called on every MQTT message."""
    global _ws_broadcaster
    _ws_broadcaster = broadcaster


class MQTTClient:
    """MQTT client with auto-reconnect and message processing."""

    def __init__(self):
        self._client: Optional[mqtt_lib.Client] = None
        self._connected = False
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    def start(self, loop: asyncio.AbstractEventLoop):
        """Start MQTT client in a background daemon thread."""
        self._loop = loop
        thread = threading.Thread(target=self._run, daemon=True, name="mqtt-client")
        thread.start()
        logger.info("MQTT client thread started")

    def _run(self):
        """Run MQTT client loop (blocking – runs in background thread)."""
        self._client = mqtt_lib.Client(clean_session=True)
        self._client.on_connect = self._on_connect
        self._client.on_disconnect = self._on_disconnect
        self._client.on_message = self._on_message

        try:
            self._client.connect(
                settings.MQTT_BROKER,
                settings.MQTT_PORT,
                keepalive=60,
            )
            self._client.loop_forever(retry_first_connection=True)
        except Exception as e:
            logger.error(f"MQTT connection error: {e}")

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self._connected = True
            logger.info(f"MQTT connected to {settings.MQTT_BROKER}:{settings.MQTT_PORT}")
            client.subscribe(settings.MQTT_TOPIC_VITALS)
            client.subscribe(settings.MQTT_TOPIC_PREDICTIONS)
            logger.info(f"Subscribed to {settings.MQTT_TOPIC_VITALS} and {settings.MQTT_TOPIC_PREDICTIONS}")
        else:
            logger.error(f"MQTT connection failed with code {rc}")

    def _on_disconnect(self, client, userdata, rc):
        self._connected = False
        if rc != 0:
            logger.warning(f"MQTT unexpected disconnect (rc={rc}), will reconnect...")

    def _log_future_exception(self, future: "asyncio.Future") -> None:
        """Log any exception raised by a coroutine dispatched from the MQTT thread."""
        exc = future.exception()
        if exc is not None:
            logger.error("MQTT handler raised exception: %s", exc, exc_info=exc)

    def _on_message(self, client, userdata, msg):
        """Decode and dispatch incoming MQTT message to async handlers."""
        try:
            payload = json.loads(msg.payload.decode("utf-8"))
            logger.debug(f"MQTT message on {msg.topic}: {payload}")
            topic = msg.topic

            if topic == settings.MQTT_TOPIC_VITALS:
                future = asyncio.run_coroutine_threadsafe(
                    self._handle_vital(payload), self._loop
                )
                future.add_done_callback(self._log_future_exception)
            elif topic == settings.MQTT_TOPIC_PREDICTIONS:
                future = asyncio.run_coroutine_threadsafe(
                    self._handle_prediction(payload), self._loop
                )
                future.add_done_callback(self._log_future_exception)
        except json.JSONDecodeError as e:
            logger.error(f"MQTT message JSON decode error: {e}")
        except Exception as e:
            logger.error(f"MQTT message processing error: {e}")

    async def _handle_vital(self, payload: dict):
        """Validate, persist, check alerts, and broadcast a vital payload."""
        from api.models.mqtt_payload import VitalPayload
        from api.services import database
        from api.services.alert_engine import check_vital_alerts

        try:
            vital = VitalPayload(**payload)
        except Exception as e:
            logger.error(f"Invalid vital payload: {e}")
            return

        vital_dict = vital.model_dump()
        vital_id = await database.insert_vital(vital_dict)
        if vital_id is None:
            # Duplicate timestamp or DB error – skip InfluxDB write and alert
            # creation to avoid time-series duplicates and orphaned alerts.
            logger.debug("Vital insert returned None (duplicate or error); skipping InfluxDB/alerts")
        else:
            await database.write_vital_to_influx(vital_dict)
            alerts = check_vital_alerts(vital_dict, vital_id)
            for alert in alerts:
                await database.insert_alert(alert)

        if _ws_broadcaster:
            await _ws_broadcaster({"type": "vital", "data": vital_dict})

    async def _handle_prediction(self, payload: dict):
        """Validate, persist, check alerts, and broadcast a prediction payload."""
        from api.models.mqtt_payload import PredictionPayload
        from api.services import database
        from api.services.alert_engine import check_prediction_alerts

        try:
            pred = PredictionPayload(**payload)
        except Exception as e:
            logger.error(f"Invalid prediction payload: {e}")
            return

        pred_dict = pred.model_dump()
        pred_id = await database.insert_prediction(pred_dict)
        if pred_id is None:
            # Duplicate timestamp or DB error – skip InfluxDB write and alert
            # creation to avoid time-series duplicates and orphaned alerts.
            logger.debug("Prediction insert returned None (duplicate or error); skipping InfluxDB/alerts")
        else:
            await database.write_prediction_to_influx(pred_dict)
            alerts = check_prediction_alerts(pred_dict, pred_id)
            for alert in alerts:
                await database.insert_alert(alert)

        if _ws_broadcaster:
            await _ws_broadcaster({"type": "prediction", "data": pred_dict})

    @property
    def is_connected(self) -> bool:
        return self._connected

    def stop(self):
        """Gracefully stop the MQTT client."""
        if self._client:
            self._client.disconnect()
            self._client.loop_stop()


# Singleton MQTT client instance
mqtt_client = MQTTClient()
