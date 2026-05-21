"""Aggregate live pipeline health for the HUD."""
from __future__ import annotations

from fastapi import APIRouter

from backend.api.realtime import get_hub
from backend.pipeline.sources import septa_vehicles

router = APIRouter(prefix="/api", tags=["live"])


@router.get("/live/status")
async def live_status() -> dict:
    hub = get_hub()
    items, sources = await septa_vehicles.all_vehicles()
    bus = sum(1 for v in items if v.get("kind") == "bus_trolley")
    rail = sum(1 for v in items if v.get("kind") == "regional_rail")
    return {
        "ws_clients": hub.size,
        "septa": {"count": len(items), "bus_trolley": bus,
                  "regional_rail": rail, "sources": sources},
    }
