"""Alerts endpoints."""

from fastapi import APIRouter, Query, HTTPException
from typing import Optional
from api.services import database

router = APIRouter()


@router.get("/alerts", tags=["alerts"])
async def get_alerts(
    limit: int = Query(20, ge=1, le=100),
    acknowledged: Optional[bool] = Query(None),
):
    """Get alerts, optionally filtered by acknowledgement status."""
    return await database.get_alerts(limit=limit, acknowledged=acknowledged)


@router.post("/alerts/{alert_id}/acknowledge", tags=["alerts"])
async def acknowledge_alert(alert_id: int):
    """Acknowledge an alert by ID."""
    success = await database.acknowledge_alert(alert_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Alert {alert_id} not found")
    return {"status": "acknowledged", "id": alert_id}
