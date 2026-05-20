"""SEPTA transit live vehicle endpoint.

GET /api/septa/vehicles → {count, bus_trolley, regional_rail, vehicles: [...]}

Vehicles are unfiltered (Philly region only); the frontend renders them as a
separate entity layer and clips them client-side by viewport.
"""
from __future__ import annotations

from fastapi import APIRouter

from backend.pipeline.sources import indego, septa_vehicles

router = APIRouter(prefix="/api", tags=["transit"])


@router.get("/septa/vehicles")
async def vehicles() -> dict:
    items, sources = await septa_vehicles.all_vehicles()
    bus = sum(1 for v in items if v.get("kind") == "bus_trolley")
    rail = sum(1 for v in items if v.get("kind") == "regional_rail")
    return {"count": len(items), "bus_trolley": bus,
            "regional_rail": rail, "vehicles": items, "sources": sources}


@router.get("/indego/stations")
async def indego_stations(lat: float, lon: float, radius_km: float = 15.0) -> dict:
    stations = await indego.stations_near(lat, lon, radius_km=radius_km)
    renting = sum(1 for s in stations if s.get("is_renting"))
    return {"count": len(stations), "renting": renting, "stations": stations}
