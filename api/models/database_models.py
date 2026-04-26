"""SQLAlchemy ORM models."""

from sqlalchemy import Column, Integer, BigInteger, Float, String, Boolean, Text, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


class VitalRecord(Base):
    __tablename__ = "vitals"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(BigInteger, nullable=False, unique=True)
    hr = Column(Float)
    bp_sys = Column(Float)
    bp_dia = Column(Float)
    o2_sat = Column(Float)
    temperature = Column(Float)
    quality = Column(Integer)
    source = Column(String(255))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now())


class PredictionRecord(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(BigInteger, nullable=False, unique=True)
    risk_score = Column(Float, nullable=False)
    risk_level = Column(String(50), nullable=False)
    confidence = Column(Float, nullable=False)
    model_latency_ms = Column(Float)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now())


class AlertRecord(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    vital_id = Column(Integer, ForeignKey("vitals.id"), nullable=True)
    prediction_id = Column(Integer, ForeignKey("predictions.id"), nullable=True)
    alert_type = Column(String(100), nullable=False)
    message = Column(Text)
    severity = Column(String(50))
    acknowledged = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
    acknowledged_at = Column(DateTime, nullable=True)
