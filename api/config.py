"""Configuration management."""

import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    # API
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))

    # MQTT
    MQTT_BROKER: str = os.getenv("MQTT_BROKER", "localhost")
    MQTT_PORT: int = int(os.getenv("MQTT_PORT", "1883"))
    MQTT_TOPIC_VITALS: str = "medtech/vitals/latest"
    MQTT_TOPIC_PREDICTIONS: str = "medtech/predictions/sepsis"

    # PostgreSQL
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "medtech")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "medtech123")
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT: int = int(os.getenv("POSTGRES_PORT", "5432"))
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "telemetry")

    DATABASE_URL: str = (
        f"postgresql://{os.getenv('POSTGRES_USER', 'medtech')}:{os.getenv('POSTGRES_PASSWORD', 'medtech123')}@"
        f"{os.getenv('POSTGRES_HOST', 'localhost')}:{os.getenv('POSTGRES_PORT', '5432')}/{os.getenv('POSTGRES_DB', 'telemetry')}"
    )

    # InfluxDB
    INFLUXDB_URL: str = os.getenv("INFLUXDB_URL", "http://localhost:8086")
    INFLUXDB_BUCKET: str = os.getenv("INFLUXDB_BUCKET", "telemetry")
    INFLUXDB_ORG: str = os.getenv("INFLUXDB_ORG", "medtech")
    INFLUXDB_TOKEN: str = os.getenv("INFLUXDB_TOKEN", "")

    # Alert thresholds
    ALERT_RISK_THRESHOLD: float = float(os.getenv("ALERT_RISK_THRESHOLD", "70"))
    ALERT_RISK_MEDIUM_THRESHOLD: float = float(os.getenv("ALERT_RISK_MEDIUM_THRESHOLD", "40"))

    # Logging
    LOG_LEVEL: str = os.getenv("LOGLEVEL", "INFO")

    class Config:
        env_file = ".env"


settings = Settings()
