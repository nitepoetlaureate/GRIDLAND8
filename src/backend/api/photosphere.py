"""HTTP route exposing Mapillary photosphere panos near a point."""
from __future__ import annotations

from fastapi import APIRouter, Query

from backend.discovery.sources import mapillary

router = APIRouter(prefix="/api", tags=["photosphere"])


@router.get("/photospheres")
async def photospheres(
    lat: float = Query(..., ge=-90.0, le=90.0),
    lon: float = Query(..., ge=-180.0, le=180.0),
    radius_m: int = Query(200, ge=10, le=1000),
    limit: int = Query(25, ge=1, le=100),
) -> dict:
    items = await mapillary.panos_near(lat, lon, radius_m=radius_m, limit=limit)
    return {"query": {"lat": lat, "lon": lon, "radius_m": radius_m},
            "count": len(items), "items": items}
