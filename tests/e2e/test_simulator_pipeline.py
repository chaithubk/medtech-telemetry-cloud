"""E2E simulator pipeline test.

Validates the complete path:
  publish_live_vitals.sh -> MQTT broker -> API subscriber
  -> PostgreSQL storage -> REST endpoints -> WebSocket broadcast

Requires a running docker-compose stack.
Set E2E_API_BASE / E2E_WS_URL / MQTT_HOST / MQTT_PORT to override defaults.
"""

import asyncio
import json
import os
import subprocess
import time

import pytest
import requests
import websockets

pytestmark = pytest.mark.e2e

API_BASE = os.getenv("E2E_API_BASE", "http://localhost:8000")
WS_URL = os.getenv("E2E_WS_URL", "ws://localhost:8000/api/v1/stream")
MQTT_HOST = os.getenv("MQTT_HOST", "localhost")
MQTT_PORT = os.getenv("MQTT_PORT", "1883")

# Unique source tag so tests can assert on their own messages
_SOURCE = "e2e-ci-sim"


def _run_simulator(count: int = 5, interval: float = 0.5) -> subprocess.CompletedProcess:
    """Run the bundled simulator script for a fixed number of messages."""
    env = {
        **os.environ,
        "HOST": MQTT_HOST,
        "PORT": MQTT_PORT,
        "COUNT": str(count),
        "INTERVAL": str(interval),
        "SOURCE": _SOURCE,
    }
    return subprocess.run(
        ["bash", "scripts/publish_live_vitals.sh"],
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )


@pytest.fixture(scope="module", autouse=True)
def publish_vitals():
    """Publish 8 vitals before the test module runs, then allow time to process."""
    result = _run_simulator(count=8, interval=0.3)
    assert result.returncode == 0, (
        f"Simulator script failed.\nstdout: {result.stdout}\nstderr: {result.stderr}"
    )
    time.sleep(3)  # give the API time to persist all messages


class TestAPIReceivesSimulatorData:
    """REST endpoint checks after the simulator has run."""

    def test_health_endpoint(self):
        resp = requests.get(f"{API_BASE}/health", timeout=10)
        assert resp.status_code == 200

    def test_latest_vital_is_from_simulator(self):
        resp = requests.get(f"{API_BASE}/api/v1/vitals/latest", timeout=10)
        assert resp.status_code == 200
        vital = resp.json()
        assert vital.get("source") == _SOURCE, (
            f"Expected source={_SOURCE!r}, got {vital.get('source')!r}"
        )

    def test_latest_vital_has_all_required_fields(self):
        resp = requests.get(f"{API_BASE}/api/v1/vitals/latest", timeout=10)
        assert resp.status_code == 200
        vital = resp.json()
        for field in ("hr", "bp_sys", "bp_dia", "o2_sat", "temperature", "quality"):
            assert field in vital, f"Field missing from stored vital: {field}"
            assert vital[field] is not None

    def test_vital_values_within_simulated_ranges(self):
        resp = requests.get(f"{API_BASE}/api/v1/vitals/latest", timeout=10)
        vital = resp.json()
        assert 65 <= vital["hr"] <= 110, f"HR out of simulated range: {vital['hr']}"
        assert 94.0 <= vital["o2_sat"] <= 100.0, f"SpO2 out of range: {vital['o2_sat']}"
        assert 36.0 <= vital["temperature"] <= 38.5, f"Temp out of range: {vital['temperature']}"

    def test_vitals_list_contains_simulator_records(self):
        resp = requests.get(f"{API_BASE}/api/v1/vitals?limit=20", timeout=10)
        assert resp.status_code == 200
        vitals = resp.json()
        sim_records = [v for v in vitals if v.get("source") == _SOURCE]
        assert len(sim_records) >= 5, (
            f"Expected at least 5 simulator vitals in list, found {len(sim_records)}"
        )

    def test_analytics_summary_reflects_ingested_data(self):
        resp = requests.get(f"{API_BASE}/api/v1/analytics/summary?hours=1", timeout=10)
        assert resp.status_code == 200
        summary = resp.json()
        count = summary.get("vital_count", 0)
        assert count >= 5, f"Analytics vital_count too low after simulation: {count}"


class TestWebSocketBroadcast:
    """WebSocket receives a vital broadcast while the simulator publishes."""

    @pytest.mark.asyncio
    async def test_websocket_delivers_vital_message(self):
        received: list[dict] = []

        async def _listen():
            async with websockets.connect(WS_URL, open_timeout=10) as ws:
                # Read up to 20 frames or until we find a vital, whichever comes first
                for _ in range(20):
                    try:
                        raw = await asyncio.wait_for(ws.recv(), timeout=8)
                        msg = json.loads(raw)
                        if msg.get("type") == "vital":
                            received.append(msg)
                            return
                    except asyncio.TimeoutError:
                        break

        # Start listener, give it half a second to connect, then publish
        listen_task = asyncio.create_task(_listen())
        await asyncio.sleep(0.5)
        _run_simulator(count=3, interval=0.5)
        await asyncio.wait_for(listen_task, timeout=20)

        assert len(received) > 0, "WebSocket did not deliver any vital messages"
        payload = received[0].get("data", received[0])
        assert "hr" in payload, f"vital message missing 'hr': {payload}"
