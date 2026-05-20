"""/api/whats_here — single point query that fans out to every registered layer.

Used by the frontend when the user clicks on the globe: returns everything
GRIDLAND knows about that geographic point in one round trip.
"""
from __future__ import annotations

import asyncio

from fastapi import APIRouter, Query

from backend.context import service as ctx_service
from backend.discovery import service as discovery_service
from backend.discovery.sources import mapillary

router = APIRouter(prefix="/api", tags=["whats_here"])


@router.get("/whats_here")
async def whats_here(
    lat: float = Query(..., ge=-90.0, le=90.0),
    lon: float = Query(..., ge=-180.0, le=180.0),
    radius_km: float = Query(1.0, ge=0.05, le=25.0),
    photosphere_radius_m: int = Query(200, ge=10, le=2000),
) -> dict:
    cameras_task = discovery_service.search_area(lat, lon, radius_km)
    context_task = ctx_service.gather(lat, lon)
    pano_task = mapillary.panos_near(lat, lon,
                                     radius_m=photosphere_radius_m, limit=10)
    cameras, context, panos = await asyncio.gather(
        cameras_task, context_task, pano_task, return_exceptions=True,
    )

    errors: dict[str, str] = {}
    if isinstance(cameras, BaseException):
        errors["cameras"] = str(cameras); cameras = None
    if isinstance(context, BaseException):
        errors["context"] = str(context); context = None
    if isinstance(panos, BaseException):
        errors["photospheres"] = str(panos); panos = []

    return {
        "query": {"lat": lat, "lon": lon, "radius_km": radius_km},
        "cameras": cameras.model_dump() if cameras is not None else None,
        "context": context.model_dump() if context is not None else None,
        "photospheres": panos or [],
        "errors": errors,
    }
