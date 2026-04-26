"""Database operations for PostgreSQL and InfluxDB."""

import logging
from typing import Optional, List, Dict, Any
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
import asyncio
import time

from api.config import settings

logger = logging.getLogger(__name__)

# PostgreSQL setup
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
    connect_args={"connect_timeout": 10},
)
SessionLocal = sessionmaker(bind=engine)

# InfluxDB setup
_influx_client: Optional[InfluxDBClient] = None
_influx_write_api = None
_influx_query_api = None


def get_influx_client() -> InfluxDBClient:
    global _influx_client, _influx_write_api, _influx_query_api
    if _influx_client is None:
        _influx_client = InfluxDBClient(
            url=settings.INFLUXDB_URL,
            token=settings.INFLUXDB_TOKEN,
            org=settings.INFLUXDB_ORG,
        )
        _influx_write_api = _influx_client.write_api(write_options=SYNCHRONOUS)
        _influx_query_api = _influx_client.query_api()
    return _influx_client


def _insert_vital_sync(data: dict) -> Optional[int]:
    """Insert vital into PostgreSQL (synchronous)."""
    with SessionLocal() as session:
        try:
            result = session.execute(
                text("""
                    INSERT INTO vitals (timestamp, hr, bp_sys, bp_dia, o2_sat, temperature, quality, source)
                    VALUES (:timestamp, :hr, :bp_sys, :bp_dia, :o2_sat, :temperature, :quality, :source)
                    ON CONFLICT (timestamp) DO NOTHING
                    RETURNING id
                """),
                data
            )
            session.commit()
            row = result.fetchone()
            return row[0] if row else None
        except Exception as e:
            session.rollback()
            logger.error(f"Error inserting vital: {e}")
            return None


def _insert_prediction_sync(data: dict) -> Optional[int]:
    """Insert prediction into PostgreSQL (synchronous)."""
    with SessionLocal() as session:
        try:
            result = session.execute(
                text("""
                    INSERT INTO predictions (timestamp, risk_score, risk_level, confidence, model_latency_ms)
                    VALUES (:timestamp, :risk_score, :risk_level, :confidence, :model_latency_ms)
                    ON CONFLICT (timestamp) DO NOTHING
                    RETURNING id
                """),
                data
            )
            session.commit()
            row = result.fetchone()
            return row[0] if row else None
        except Exception as e:
            session.rollback()
            logger.error(f"Error inserting prediction: {e}")
            return None


def _get_latest_vital_sync() -> Optional[dict]:
    with SessionLocal() as session:
        result = session.execute(
            text("SELECT * FROM vitals ORDER BY timestamp DESC LIMIT 1")
        )
        row = result.mappings().fetchone()
        return dict(row) if row else None


def _get_vitals_sync(limit: int, hours: Optional[int]) -> List[dict]:
    with SessionLocal() as session:
        if hours:
            cutoff = int(time.time() * 1000) - (hours * 3600 * 1000)
            result = session.execute(
                text("SELECT * FROM vitals WHERE timestamp >= :cutoff ORDER BY timestamp DESC LIMIT :limit"),
                {"cutoff": cutoff, "limit": limit}
            )
        else:
            result = session.execute(
                text("SELECT * FROM vitals ORDER BY timestamp DESC LIMIT :limit"),
                {"limit": limit}
            )
        return [dict(row) for row in result.mappings()]


def _get_vital_by_id_sync(vital_id: int) -> Optional[dict]:
    with SessionLocal() as session:
        result = session.execute(
            text("SELECT * FROM vitals WHERE id = :id"),
            {"id": vital_id}
        )
        row = result.mappings().fetchone()
        return dict(row) if row else None


def _get_latest_prediction_sync() -> Optional[dict]:
    with SessionLocal() as session:
        result = session.execute(
            text("SELECT * FROM predictions ORDER BY timestamp DESC LIMIT 1")
        )
        row = result.mappings().fetchone()
        return dict(row) if row else None


def _get_predictions_sync(limit: int, hours: Optional[int]) -> List[dict]:
    with SessionLocal() as session:
        if hours:
            cutoff = int(time.time() * 1000) - (hours * 3600 * 1000)
            result = session.execute(
                text("SELECT * FROM predictions WHERE timestamp >= :cutoff ORDER BY timestamp DESC LIMIT :limit"),
                {"cutoff": cutoff, "limit": limit}
            )
        else:
            result = session.execute(
                text("SELECT * FROM predictions ORDER BY timestamp DESC LIMIT :limit"),
                {"limit": limit}
            )
        return [dict(row) for row in result.mappings()]


def _get_analytics_summary_sync(hours: int) -> dict:
    with SessionLocal() as session:
        cutoff = int(time.time() * 1000) - (hours * 3600 * 1000)
        v = session.execute(
            text("""
                SELECT COUNT(*) as cnt, AVG(hr) as avg_hr, AVG(bp_sys) as avg_bp_sys,
                       AVG(o2_sat) as avg_o2_sat, AVG(temperature) as avg_temp
                FROM vitals WHERE timestamp >= :cutoff
            """),
            {"cutoff": cutoff}
        ).mappings().fetchone()
        p = session.execute(
            text("SELECT COUNT(*) as cnt FROM predictions WHERE timestamp >= :cutoff AND risk_level = 'HIGH'"),
            {"cutoff": cutoff}
        ).mappings().fetchone()
        pc = session.execute(
            text("SELECT COUNT(*) as cnt FROM predictions WHERE timestamp >= :cutoff"),
            {"cutoff": cutoff}
        ).mappings().fetchone()
        return {
            "period_hours": hours,
            "vital_count": v["cnt"] or 0,
            "prediction_count": pc["cnt"] or 0,
            "avg_hr": round(v["avg_hr"], 1) if v["avg_hr"] else None,
            "avg_bp_sys": round(v["avg_bp_sys"], 1) if v["avg_bp_sys"] else None,
            "avg_o2_sat": round(v["avg_o2_sat"], 1) if v["avg_o2_sat"] else None,
            "avg_temperature": round(v["avg_temp"], 1) if v["avg_temp"] else None,
            "high_risk_count": p["cnt"] or 0,
        }


def _get_alerts_sync(limit: int, acknowledged: Optional[bool]) -> List[dict]:
    with SessionLocal() as session:
        if acknowledged is not None:
            result = session.execute(
                text("SELECT * FROM alerts WHERE acknowledged = :ack ORDER BY created_at DESC LIMIT :limit"),
                {"ack": acknowledged, "limit": limit}
            )
        else:
            result = session.execute(
                text("SELECT * FROM alerts ORDER BY created_at DESC LIMIT :limit"),
                {"limit": limit}
            )
        return [dict(row) for row in result.mappings()]


def _insert_alert_sync(data: dict) -> Optional[int]:
    with SessionLocal() as session:
        try:
            result = session.execute(
                text("""
                    INSERT INTO alerts (vital_id, prediction_id, alert_type, message, severity)
                    VALUES (:vital_id, :prediction_id, :alert_type, :message, :severity)
                    RETURNING id
                """),
                data
            )
            session.commit()
            row = result.fetchone()
            return row[0] if row else None
        except Exception as e:
            session.rollback()
            logger.error(f"Error inserting alert: {e}")
            return None


def _acknowledge_alert_sync(alert_id: int) -> bool:
    with SessionLocal() as session:
        try:
            result = session.execute(
                text("""
                    UPDATE alerts SET acknowledged = TRUE, acknowledged_at = NOW()
                    WHERE id = :id RETURNING id
                """),
                {"id": alert_id}
            )
            session.commit()
            return result.fetchone() is not None
        except Exception as e:
            session.rollback()
            logger.error(f"Error acknowledging alert: {e}")
            return False


def _write_vital_influx_sync(data: dict) -> bool:
    try:
        client = get_influx_client()
        write_api = client.write_api(write_options=SYNCHRONOUS)
        # Build point conditionally to avoid None fields
        point = Point("vitals").tag("source", data.get("source", "device"))
        point = point.time(data["timestamp"] * 1_000_000)  # ms → ns
        if data.get("hr") is not None:
            point = point.field("hr", float(data["hr"]))
        if data.get("bp_sys") is not None:
            point = point.field("bp_sys", float(data["bp_sys"]))
        if data.get("bp_dia") is not None:
            point = point.field("bp_dia", float(data["bp_dia"]))
        if data.get("o2_sat") is not None:
            point = point.field("o2_sat", float(data["o2_sat"]))
        if data.get("temperature") is not None:
            point = point.field("temperature", float(data["temperature"]))
        if data.get("quality") is not None:
            point = point.field("quality", int(data["quality"]))
        write_api.write(bucket=settings.INFLUXDB_BUCKET, org=settings.INFLUXDB_ORG, record=point)
        return True
    except Exception as e:
        logger.warning(f"InfluxDB write vital failed: {e}")
        return False


def _write_prediction_influx_sync(data: dict) -> bool:
    try:
        client = get_influx_client()
        write_api = client.write_api(write_options=SYNCHRONOUS)
        point = (
            Point("predictions")
            .tag("risk_level", data.get("risk_level", "UNKNOWN"))
            .field("risk_score", float(data["risk_score"]))
            .field("confidence", float(data["confidence"]))
            .time(data["timestamp"] * 1_000_000)  # ms → ns
        )
        if data.get("model_latency_ms") is not None:
            point = point.field("model_latency_ms", float(data["model_latency_ms"]))
        write_api.write(bucket=settings.INFLUXDB_BUCKET, org=settings.INFLUXDB_ORG, record=point)
        return True
    except Exception as e:
        logger.warning(f"InfluxDB write prediction failed: {e}")
        return False


def _query_vitals_trends_sync(metric: str, hours: int) -> List[dict]:
    try:
        client = get_influx_client()
        query_api = client.query_api()
        flux = f'''
            from(bucket: "{settings.INFLUXDB_BUCKET}")
              |> range(start: -{hours}h)
              |> filter(fn: (r) => r["_measurement"] == "vitals")
              |> filter(fn: (r) => r["_field"] == "{metric}")
              |> sort(columns: ["_time"])
        '''
        tables = query_api.query(flux, org=settings.INFLUXDB_ORG)
        results = []
        for table in tables:
            for record in table.records:
                results.append({
                    "timestamp": int(record.get_time().timestamp() * 1000),
                    "value": record.get_value(),
                })
        return results
    except Exception as e:
        logger.warning(f"InfluxDB query vitals trends failed: {e}")
        return []


# Async wrappers
async def insert_vital(data: dict) -> Optional[int]:
    return await asyncio.to_thread(_insert_vital_sync, data)

async def insert_prediction(data: dict) -> Optional[int]:
    return await asyncio.to_thread(_insert_prediction_sync, data)

async def get_latest_vital() -> Optional[dict]:
    return await asyncio.to_thread(_get_latest_vital_sync)

async def get_vitals(limit: int = 10, hours: Optional[int] = None) -> List[dict]:
    return await asyncio.to_thread(_get_vitals_sync, limit, hours)

async def get_vital_by_id(vital_id: int) -> Optional[dict]:
    return await asyncio.to_thread(_get_vital_by_id_sync, vital_id)

async def get_latest_prediction() -> Optional[dict]:
    return await asyncio.to_thread(_get_latest_prediction_sync)

async def get_predictions(limit: int = 10, hours: Optional[int] = None) -> List[dict]:
    return await asyncio.to_thread(_get_predictions_sync, limit, hours)

async def get_analytics_summary(hours: int = 24) -> dict:
    return await asyncio.to_thread(_get_analytics_summary_sync, hours)

async def get_alerts(limit: int = 20, acknowledged: Optional[bool] = None) -> List[dict]:
    return await asyncio.to_thread(_get_alerts_sync, limit, acknowledged)

async def insert_alert(data: dict) -> Optional[int]:
    return await asyncio.to_thread(_insert_alert_sync, data)

async def acknowledge_alert(alert_id: int) -> bool:
    return await asyncio.to_thread(_acknowledge_alert_sync, alert_id)

async def write_vital_to_influx(data: dict) -> bool:
    return await asyncio.to_thread(_write_vital_influx_sync, data)

async def write_prediction_to_influx(data: dict) -> bool:
    return await asyncio.to_thread(_write_prediction_influx_sync, data)

async def query_vitals_trends(metric: str, hours: int) -> List[dict]:
    return await asyncio.to_thread(_query_vitals_trends_sync, metric, hours)
