"""Pytest configuration and shared fixtures."""

import os
import time

import pytest

# Set test environment variables before importing any app modules
os.environ.setdefault("MQTT_BROKER", os.getenv("TEST_MQTT_BROKER", "localhost"))
os.environ.setdefault("MQTT_PORT", "1883")
os.environ.setdefault("POSTGRES_HOST", os.getenv("TEST_POSTGRES_HOST", "localhost"))
os.environ.setdefault("POSTGRES_PORT", "5432")
os.environ.setdefault("POSTGRES_USER", "medtech")
os.environ.setdefault("POSTGRES_PASSWORD", "medtech123")
os.environ.setdefault("POSTGRES_DB", "telemetry")
os.environ.setdefault("INFLUXDB_URL", os.getenv("TEST_INFLUXDB_URL", "http://localhost:8086"))
os.environ.setdefault("INFLUXDB_TOKEN", "")
os.environ.setdefault("INFLUXDB_ORG", "medtech")
os.environ.setdefault("INFLUXDB_BUCKET", "telemetry")
os.environ.setdefault("LOGLEVEL", "WARNING")


@pytest.fixture(scope="session")
def mqtt_simulator():
    """Return a connected MQTTSimulator; skip if broker unavailable."""
    from tests.fixtures.mqtt_simulator import MQTTSimulator

    broker = os.getenv("TEST_MQTT_BROKER", "localhost")
    sim = MQTTSimulator(broker=broker, port=1883)
    try:
        sim.connect()
        yield sim
    except RuntimeError:
        pytest.skip("MQTT broker not available")
    finally:
        sim.disconnect()


@pytest.fixture
def sample_vital():
    """Return a sample vital payload dict."""
    return {
        "timestamp": int(time.time() * 1000),
        "hr": 75.0,
        "bp_sys": 120.0,
        "bp_dia": 80.0,
        "o2_sat": 98.0,
        "temperature": 37.0,
        "quality": 95,
        "source": "test",
    }


@pytest.fixture
def sample_prediction():
    """Return a sample prediction payload dict."""
    return {
        "timestamp": int(time.time() * 1000),
        "risk_score": 25.0,
        "risk_level": "LOW",
        "confidence": 0.80,
        "model_latency_ms": 45.0,
    }
