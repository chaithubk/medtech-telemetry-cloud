"""Pydantic models for MQTT payload validation."""

from pydantic import BaseModel, ConfigDict, field_validator
from typing import Optional


class VitalPayload(BaseModel):
    """Vital signs reading from medtech device."""

    model_config = ConfigDict(protected_namespaces=())

    timestamp: int
    hr: Optional[float] = None
    bp_sys: Optional[float] = None
    bp_dia: Optional[float] = None
    o2_sat: Optional[float] = None
    temperature: Optional[float] = None
    quality: Optional[int] = None
    source: str = "device"

    @field_validator("timestamp")
    @classmethod
    def timestamp_must_be_non_negative(cls, v: int) -> int:
        if v < 0:
            raise ValueError("timestamp must be non-negative")
        return v

    @field_validator("hr")
    @classmethod
    def hr_range(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and not (0 < v < 300):
            raise ValueError("hr must be between 0 and 300")
        return v

    @field_validator("o2_sat")
    @classmethod
    def o2_sat_range(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and not (0 <= v <= 100):
            raise ValueError("o2_sat must be between 0 and 100")
        return v


class PredictionPayload(BaseModel):
    """Sepsis prediction from edge analytics."""

    model_config = ConfigDict(protected_namespaces=())

    timestamp: int
    risk_score: float
    risk_level: str
    confidence: float
    model_latency_ms: Optional[float] = None

    @field_validator("timestamp")
    @classmethod
    def timestamp_must_be_non_negative(cls, v: int) -> int:
        if v < 0:
            raise ValueError("timestamp must be non-negative")
        return v

    @field_validator("risk_score")
    @classmethod
    def risk_score_range(cls, v: float) -> float:
        if not (0 <= v <= 100):
            raise ValueError("risk_score must be between 0 and 100")
        return v

    @field_validator("confidence")
    @classmethod
    def confidence_range(cls, v: float) -> float:
        if not (0 <= v <= 1):
            raise ValueError("confidence must be between 0 and 1")
        return v

    @field_validator("risk_level")
    @classmethod
    def risk_level_valid(cls, v: str) -> str:
        valid = {"LOW", "MEDIUM", "HIGH"}
        if v.upper() not in valid:
            raise ValueError(f"risk_level must be one of {valid}")
        return v.upper()
