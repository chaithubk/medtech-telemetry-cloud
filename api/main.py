"""FastAPI application."""

import asyncio
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.config import settings
from api.routes import health, vitals, predictions
from api.routes import analytics, alerts, stream
from api.services.mqtt_client import mqtt_client

logging.basicConfig(level=settings.LOG_LEVEL)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="MedTech Telemetry Cloud",
    description="Real-time medical IoT data collection and analytics",
    version="2.0.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(health.router)
app.include_router(vitals.router, prefix="/api/v1", tags=["vitals"])
app.include_router(predictions.router, prefix="/api/v1", tags=["predictions"])
app.include_router(analytics.router, prefix="/api/v1", tags=["analytics"])
app.include_router(alerts.router, prefix="/api/v1", tags=["alerts"])
app.include_router(stream.router, prefix="/api/v1", tags=["stream"])


@app.on_event("startup")
async def startup():
    logger.info("🚀 MedTech Telemetry Cloud API started")
    logger.info(f"  MQTT Broker: {settings.MQTT_BROKER}:{settings.MQTT_PORT}")
    logger.info(f"  PostgreSQL: {settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}")
    logger.info(f"  InfluxDB: {settings.INFLUXDB_URL}")
    # Register WebSocket broadcaster with MQTT client
    stream.setup_broadcaster()
    # Start MQTT client in a background thread bound to the running event loop
    loop = asyncio.get_event_loop()
    mqtt_client.start(loop)


@app.on_event("shutdown")
async def shutdown():
    logger.info("🛑 MedTech Telemetry Cloud API shutting down")
    mqtt_client.stop()
