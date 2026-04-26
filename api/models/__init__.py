"""Models package – re-exports legacy models for backward compatibility."""

from pydantic import BaseModel
from typing import Optional


class Vital(BaseModel):
    """Vital signs reading."""

    timestamp: int
    hr: Optional[float] = None
    bp_sys: Optional[float] = None
    bp_dia: Optional[float] = None
    o2_sat: Optional[float] = None
    temperature: Optional[float] = None
    quality: Optional[int] = None
    source: Optional[str] = "device"


class Prediction(BaseModel):
    """Sepsis prediction."""

    timestamp: int
    risk_score: float
    risk_level: str
    confidence: float
    model_latency_ms: Optional[float] = None


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    message: str


class Analytics(BaseModel):
    """Analytics summary."""

    period_hours: int
    vital_count: int
    prediction_count: int
    avg_hr: Optional[float] = None
    avg_o2_sat: Optional[float] = None
    high_risk_count: int = 0
