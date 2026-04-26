"""Vitals endpoints."""

from fastapi import APIRouter, Query
from typing import List, Optional
from api.models import Vital

router = APIRouter()


@router.get("/vitals", tags=["vitals"])
async def get_vitals(
    limit: int = Query(10, ge=1, le=100),
    hours: Optional[int] = None
):
    """Get recent vital readings."""
    return {
        "status": "implementation_pending",
        "message": "Vitals endpoint to be implemented by Copilot"
    }


@router.post("/vitals", tags=["vitals"])
async def create_vital(vital: Vital):
    """Ingest vital reading."""
    return {
        "status": "created",
        "message": "Vital ingestion placeholder"
    }
