"""HTTP routes for contextual layers."""
from __future__ import annotations

from fastapi import APIRouter, Query

from backend.context.models import ContextBundle
from backend.context.service import gather

router = APIRouter(prefix="/api", tags=["context"])


@router.get("/context", response_model=ContextBundle)
async def context(
    lat: float = Query(..., ge=-90.0, le=90.0),
    lon: float = Query(..., ge=-180.0, le=180.0),
) -> ContextBundle:
    return await gather(lat, lon)
