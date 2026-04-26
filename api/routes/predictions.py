"""Predictions endpoints."""

from fastapi import APIRouter, Query, HTTPException
from typing import Optional
from api.services import database

router = APIRouter()


@router.get("/predictions", tags=["predictions"])
async def get_predictions(
    limit: int = Query(10, ge=1, le=100),
    hours: Optional[int] = Query(None, ge=1, le=720),
):
    """Get recent predictions from PostgreSQL."""
    return await database.get_predictions(limit=limit, hours=hours)


@router.get("/predictions/latest", tags=["predictions"])
async def get_latest_prediction():
    """Get most recent prediction."""
    pred = await database.get_latest_prediction()
    if pred is None:
        raise HTTPException(status_code=404, detail="No predictions found")
    return pred


@router.post("/predictions", tags=["predictions"])
async def create_prediction(prediction: dict):
    """Ingest prediction directly (non-MQTT path)."""
    pred_id = await database.insert_prediction(prediction)
    if pred_id:
        await database.write_prediction_to_influx(prediction)
        return {"status": "created", "id": pred_id}
    return {"status": "duplicate", "message": "Prediction with this timestamp already exists"}
