"""HTTP routes for camera discovery."""
from __future__ import annotations

from fastapi import APIRouter, Query

from backend.discovery.models import DiscoveryResponse
from backend.discovery.service import search_area

router = APIRouter(prefix="/api", tags=["discovery"])


@router.get("/discover", response_model=DiscoveryResponse)
async def discover(
    lat: float = Query(..., ge=-90.0, le=90.0),
    lon: float = Query(..., ge=-180.0, le=180.0),
    radius_km: float = Query(25.0, gt=0.0, le=200.0),
) -> DiscoveryResponse:
    return await search_area(lat, lon, radius_km)
