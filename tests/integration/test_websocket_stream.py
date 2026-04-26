"""Integration tests: WebSocket real-time stream."""

import json
import pytest
from fastapi.testclient import TestClient

pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def api_client():
    from api.main import app

    return TestClient(app)


class TestWebSocketStream:
    def test_websocket_connects_and_responds_to_ping(self, api_client):
        """Client can connect and exchange ping/pong."""
        with api_client.websocket_connect("/api/v1/stream") as ws:
            ws.send_text("ping")
            data = ws.receive_text()
            assert data == "pong"

    def test_multiple_websocket_connections(self, api_client):
        """Multiple clients can connect simultaneously."""
        with api_client.websocket_connect("/api/v1/stream") as ws1:
            with api_client.websocket_connect("/api/v1/stream") as ws2:
                ws1.send_text("ping")
                ws2.send_text("ping")
                assert ws1.receive_text() == "pong"
                assert ws2.receive_text() == "pong"

    def test_websocket_disconnect_graceful(self, api_client):
        """Client can disconnect without errors."""
        with api_client.websocket_connect("/api/v1/stream") as ws:
            ws.send_text("ping")
            ws.receive_text()
        # Connection closed cleanly – no exception means pass
