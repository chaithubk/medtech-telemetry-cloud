"""FastAPI application."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from api.config import settings
from api.routes import health, vitals, predictions

logging.basicConfig(level=settings.LOG_LEVEL)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="MedTech Telemetry Cloud",
    description="Real-time medical IoT data collection and analytics",
    version="0.1.0",
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


@app.on_event("startup")
async def startup():
    logger.info("🚀 MedTech Telemetry Cloud API started")
    logger.info(f"  MQTT Broker: {settings.MQTT_BROKER}:{settings.MQTT_PORT}")
    logger.info(f"  PostgreSQL: {settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}")
    logger.info(f"  InfluxDB: {settings.INFLUXDB_URL}")


@app.on_event("shutdown")
async def shutdown():
    logger.info("🛑 MedTech Telemetry Cloud API shutting down")
