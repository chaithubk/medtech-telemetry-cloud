"""Data models."""

from pydantic import BaseModel
from datetime import datetime
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

    class Config:
        json_schema_extra = {
            "example": {
                "timestamp": 1712973600000,
                "hr": 92,
                "bp_sys": 135,
                "bp_dia": 85,
                "o2_sat": 98,
                "temperature": 37.2,
                "quality": 95,
                "source": "device-001"
            }
        }


class Prediction(BaseModel):
    """Sepsis prediction."""
    timestamp: int
    risk_score: float
    risk_level: str
    confidence: float
    model_latency_ms: Optional[float] = None

    class Config:
        json_schema_extra = {
            "example": {
                "timestamp": 1712973600000,
                "risk_score": 45,
                "risk_level": "LOW",
                "confidence": 0.75,
                "model_latency_ms": 87.5
            }
        }


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
