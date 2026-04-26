"""Analytics endpoints."""

from fastapi import APIRouter, Query, HTTPException
from api.services import database

router = APIRouter()

VALID_METRICS = {"hr", "bp_sys", "bp_dia", "o2_sat", "temperature"}


@router.get("/analytics/summary", tags=["analytics"])
async def get_summary(hours: int = Query(24, ge=1, le=720)):
    """Get aggregated analytics summary from PostgreSQL."""
    return await database.get_analytics_summary(hours=hours)


@router.get("/analytics/trends", tags=["analytics"])
async def get_trends(
    metric: str = Query("hr"),
    hours: int = Query(24, ge=1, le=720),
):
    """Get time-series trend data for a vital metric from InfluxDB."""
    if metric not in VALID_METRICS:
        raise HTTPException(status_code=400, detail=f"metric must be one of {sorted(VALID_METRICS)}")
    return await database.query_vitals_trends(metric=metric, hours=hours)
