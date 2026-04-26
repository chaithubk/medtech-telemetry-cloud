"""Vitals endpoints."""

from fastapi import APIRouter, Query, HTTPException
from typing import Optional
from api.services import database

router = APIRouter()


@router.get("/vitals", tags=["vitals"])
async def get_vitals(
    limit: int = Query(10, ge=1, le=100),
    hours: Optional[int] = Query(None, ge=1, le=720),
):
    """Get recent vital readings from PostgreSQL."""
    return await database.get_vitals(limit=limit, hours=hours)


@router.get("/vitals/latest", tags=["vitals"])
async def get_latest_vital():
    """Get most recent vital reading."""
    vital = await database.get_latest_vital()
    if vital is None:
        raise HTTPException(status_code=404, detail="No vitals found")
    return vital


@router.get("/vitals/{vital_id}", tags=["vitals"])
async def get_vital(vital_id: int):
    """Get vital reading by ID."""
    vital = await database.get_vital_by_id(vital_id)
    if vital is None:
        raise HTTPException(status_code=404, detail=f"Vital {vital_id} not found")
    return vital


@router.post("/vitals", tags=["vitals"])
async def create_vital(vital: dict):
    """Ingest vital reading directly (non-MQTT path)."""
    vital_id = await database.insert_vital(vital)
    if vital_id:
        await database.write_vital_to_influx(vital)
        return {"status": "created", "id": vital_id}
    return {"status": "duplicate", "message": "Vital with this timestamp already exists"}
