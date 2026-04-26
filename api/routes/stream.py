"""WebSocket streaming endpoint for real-time vital and prediction updates."""

import asyncio
import json
import logging
from typing import Set

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from api.services import mqtt_client as mqtt_service

logger = logging.getLogger(__name__)
router = APIRouter()

# Set of all currently-connected WebSocket clients
_clients: Set[WebSocket] = set()


async def broadcast(message: dict):
    """Send a JSON message to every connected WebSocket client."""
    if not _clients:
        return
    payload = json.dumps(message, default=str)
    disconnected = set()
    for ws in list(_clients):
        try:
            await ws.send_text(payload)
        except Exception:
            disconnected.add(ws)
    _clients.difference_update(disconnected)


def setup_broadcaster():
    """Register broadcast function with the MQTT client service."""
    mqtt_service.set_ws_broadcaster(broadcast)


@router.websocket("/stream")
async def websocket_stream(websocket: WebSocket):
    """Real-time WebSocket stream delivering vitals and predictions as they arrive via MQTT."""
    await websocket.accept()
    _clients.add(websocket)
    logger.info(f"WebSocket client connected. Total clients: {len(_clients)}")
    try:
        while True:
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                if data == "ping":
                    await websocket.send_text("pong")
            except asyncio.TimeoutError:
                # Send keepalive ping to detect stale connections
                try:
                    await websocket.send_text(json.dumps({"type": "ping"}))
                except Exception:
                    break
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        _clients.discard(websocket)
        logger.info(f"WebSocket client removed. Total clients: {len(_clients)}")
