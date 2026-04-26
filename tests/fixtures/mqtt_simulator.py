"""MQTT simulator for generating realistic medtech-platform messages without a real device."""

import json
import logging
import random
import time
from typing import List, Optional

import paho.mqtt.client as mqtt_lib

logger = logging.getLogger(__name__)

SCENARIOS = {
    "healthy": {
        "hr": (70, 80),
        "bp_sys": (115, 125),
        "bp_dia": (75, 85),
        "o2_sat": (97, 99),
        "temperature": (36.5, 37.2),
        "quality": 95,
    },
    "tachycardia": {
        "hr": (120, 140),
        "bp_sys": (125, 135),
        "bp_dia": (82, 90),
        "o2_sat": (96, 98),
        "temperature": (37.2, 38.0),
        "quality": 90,
    },
    "hypoxia": {
        "hr": (95, 110),
        "bp_sys": (135, 145),
        "bp_dia": (88, 95),
        "o2_sat": (88, 92),
        "temperature": (37.0, 37.5),
        "quality": 85,
    },
    "fever": {
        "hr": (88, 98),
        "bp_sys": (120, 130),
        "bp_dia": (80, 88),
        "o2_sat": (94, 97),
        "temperature": (39.0, 40.0),
        "quality": 88,
    },
}


def _rand(rng):
    """Return a random float within the given range tuple, or the value directly."""
    if isinstance(rng, tuple):
        return round(random.uniform(rng[0], rng[1]), 1)
    return rng


class MQTTSimulator:
    """Simulates medtech device MQTT messages for testing without real hardware."""

    def __init__(self, broker: str = "localhost", port: int = 1883):
        self.broker = broker
        self.port = port
        self._client: Optional[mqtt_lib.Client] = None
        self._connected = False

    def connect(self):
        """Connect to MQTT broker (blocks until connected or raises RuntimeError)."""
        self._client = mqtt_lib.Client(
            client_id=f"simulator-{int(time.time())}", clean_session=True
        )
        self._client.on_connect = self._on_connect
        self._client.on_disconnect = self._on_disconnect
        self._client.connect(self.broker, self.port, keepalive=60)
        self._client.loop_start()
        # Wait up to 2 seconds for connection
        for _ in range(20):
            if self._connected:
                break
            time.sleep(0.1)
        if not self._connected:
            self._client.loop_stop()
            raise RuntimeError(f"Failed to connect MQTTSimulator to {self.broker}:{self.port}")

    def disconnect(self):
        """Disconnect from MQTT broker."""
        if self._client:
            self._client.loop_stop()
            self._client.disconnect()
        self._connected = False

    def _on_connect(self, client, userdata, flags, rc):
        self._connected = rc == 0
        if rc == 0:
            logger.debug(f"MQTTSimulator connected to {self.broker}:{self.port}")

    def _on_disconnect(self, client, userdata, rc):
        self._connected = False

    def publish_vital(
        self,
        hr: float = 75,
        bp_sys: float = 120,
        bp_dia: float = 80,
        o2_sat: float = 98,
        temperature: float = 37.0,
        quality: int = 95,
        source: str = "simulator",
        timestamp: Optional[int] = None,
    ) -> dict:
        """Publish a single vital reading to medtech/vitals/latest."""
        payload = {
            "timestamp": timestamp or int(time.time() * 1000),
            "hr": hr,
            "bp_sys": bp_sys,
            "bp_dia": bp_dia,
            "o2_sat": o2_sat,
            "temperature": temperature,
            "quality": quality,
            "source": source,
        }
        self._client.publish("medtech/vitals/latest", json.dumps(payload), qos=1)
        logger.debug(f"Published vital: {payload}")
        return payload

    def publish_prediction(
        self,
        risk_score: float = 20.0,
        risk_level: str = "LOW",
        confidence: float = 0.8,
        model_latency_ms: float = 45.0,
        timestamp: Optional[int] = None,
    ) -> dict:
        """Publish a single prediction to medtech/predictions/sepsis."""
        payload = {
            "timestamp": timestamp or int(time.time() * 1000),
            "risk_score": risk_score,
            "risk_level": risk_level,
            "confidence": confidence,
            "model_latency_ms": model_latency_ms,
        }
        self._client.publish("medtech/predictions/sepsis", json.dumps(payload), qos=1)
        logger.debug(f"Published prediction: {payload}")
        return payload

    def publish_scenario(self, scenario: str = "healthy", source: str = "simulator") -> dict:
        """Publish a vital reading using a predefined scenario."""
        if scenario not in SCENARIOS:
            raise ValueError(f"Unknown scenario: {scenario}. Choose from {list(SCENARIOS.keys())}")
        params = SCENARIOS[scenario]
        return self.publish_vital(
            hr=_rand(params["hr"]),
            bp_sys=_rand(params["bp_sys"]),
            bp_dia=_rand(params["bp_dia"]),
            o2_sat=_rand(params["o2_sat"]),
            temperature=_rand(params["temperature"]),
            quality=params["quality"],
            source=source,
        )

    def publish_vital_sequence(
        self,
        scenarios: Optional[List[str]] = None,
        count: int = 10,
        interval_sec: float = 0.05,
        base_timestamp: Optional[int] = None,
    ) -> List[dict]:
        """Publish multiple vitals. Uses scenarios list or defaults to 'healthy'."""
        if scenarios is None:
            scenarios = ["healthy"] * count
        payloads = []
        ts = base_timestamp or int(time.time() * 1000)
        for i, scenario in enumerate(scenarios):
            params = SCENARIOS.get(scenario, SCENARIOS["healthy"])
            payload = self.publish_vital(
                hr=_rand(params["hr"]),
                bp_sys=_rand(params["bp_sys"]),
                bp_dia=_rand(params["bp_dia"]),
                o2_sat=_rand(params["o2_sat"]),
                temperature=_rand(params["temperature"]),
                quality=params["quality"],
                source="simulator",
                timestamp=ts + (i * 1000),
            )
            payloads.append(payload)
            if interval_sec > 0 and i < len(scenarios) - 1:
                time.sleep(interval_sec)
        return payloads

    def publish_prediction_sequence(
        self,
        scores: Optional[List[float]] = None,
        count: int = 10,
        interval_sec: float = 0.05,
        base_timestamp: Optional[int] = None,
    ) -> List[dict]:
        """Publish multiple predictions."""
        if scores is None:
            scores = [20.0] * count
        payloads = []
        ts = base_timestamp or int(time.time() * 1000)
        for i, score in enumerate(scores):
            level = "HIGH" if score >= 70 else "MEDIUM" if score >= 40 else "LOW"
            payload = self.publish_prediction(
                risk_score=score,
                risk_level=level,
                confidence=round(random.uniform(0.7, 0.95), 2),
                model_latency_ms=round(random.uniform(30, 100), 1),
                timestamp=ts + (i * 1000),
            )
            payloads.append(payload)
            if interval_sec > 0 and i < len(scores) - 1:
                time.sleep(interval_sec)
        return payloads
