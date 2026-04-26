"""Configuration management."""

from pydantic import AliasChoices, Field, model_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    # API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000

    # MQTT
    MQTT_BROKER: str = "localhost"
    MQTT_PORT: int = 1883
    MQTT_TOPIC_VITALS: str = "medtech/vitals/latest"
    MQTT_TOPIC_PREDICTIONS: str = "medtech/predictions/sepsis"

    # PostgreSQL
    POSTGRES_USER: str = "medtech"
    POSTGRES_PASSWORD: str = "medtech123"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "telemetry"

    # Computed from POSTGRES_* fields; can be overridden by DATABASE_URL env var
    DATABASE_URL: str = ""

    # InfluxDB
    INFLUXDB_URL: str = "http://localhost:8086"
    INFLUXDB_BUCKET: str = "telemetry"
    INFLUXDB_ORG: str = "medtech"
    INFLUXDB_TOKEN: str = ""

    # Alert thresholds
    ALERT_RISK_THRESHOLD: float = 70.0
    ALERT_RISK_MEDIUM_THRESHOLD: float = 40.0

    # Logging – env var is LOGLEVEL for backward-compat; also accepts LOG_LEVEL
    LOG_LEVEL: str = Field(
        default="INFO",
        validation_alias=AliasChoices("LOG_LEVEL", "LOGLEVEL"),
    )

    @model_validator(mode="after")
    def build_database_url(self) -> "Settings":
        """Derive DATABASE_URL from POSTGRES_* fields unless explicitly provided."""
        if not self.DATABASE_URL:
            self.DATABASE_URL = (
                f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@"
                f"{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
            )
        return self

    class Config:
        env_file = ".env"


settings = Settings()
