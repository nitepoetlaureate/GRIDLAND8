"""SEPTA transit live vehicle endpoint and Indego GBFS."""
from __future__ import annotations

from fastapi import APIRouter, Query

from backend.discovery import service as discovery_service
from backend.pipeline.sources import indego, septa_metro, septa_vehicles
from backend.shared.geo import in_bbox

router = APIRouter(prefix="/api", tags=["transit"])


def _filter_bbox(
    items: list[dict],
    min_lat: float | None,
    min_lon: float | None,
    max_lat: float | None,
    max_lon: float | None,
) -> list[dict]:
    """Viewport bbox applies to buses/trolleys only; regional rail is system-wide (~60)."""
    if None in (min_lat, min_lon, max_lat, max_lon):
        return items
    rail = [v for v in items if v.get("kind") == "regional_rail"]
    buses = [
        v for v in items
        if v.get("kind") != "regional_rail"
        and v.get("lat") is not None and v.get("lon") is not None
        and in_bbox(float(v["lat"]), float(v["lon"]),
                    min_lat, min_lon, max_lat, max_lon)
    ]
    return buses + rail


@router.get("/septa/vehicles")
async def vehicles(
    min_lat: float | None = Query(None),
    min_lon: float | None = Query(None),
    max_lat: float | None = Query(None),
    max_lon: float | None = Query(None),
) -> dict:
    items, sources = await septa_vehicles.all_vehicles()
    items = _filter_bbox(items, min_lat, min_lon, max_lat, max_lon)
    bus = sum(1 for v in items if v.get("kind") == "bus_trolley")
    rail = sum(1 for v in items if v.get("kind") == "regional_rail")
    return {"count": len(items), "bus_trolley": bus,
            "regional_rail": rail, "vehicles": items, "sources": sources}


@router.get("/indego/stations")
async def indego_stations(
    lat: float,
    lon: float,
    radius_km: float = 15.0,
    min_lat: float | None = Query(None),
    min_lon: float | None = Query(None),
    max_lat: float | None = Query(None),
    max_lon: float | None = Query(None),
) -> dict:
    stations = await indego.stations_near(lat, lon, radius_km=radius_km)
    if None not in (min_lat, min_lon, max_lat, max_lon):
        stations = [
            s for s in stations
            if s.get("lat") is not None and s.get("lon") is not None
            and in_bbox(float(s["lat"]), float(s["lon"]),
                        min_lat, min_lon, max_lat, max_lon)
        ]
    renting = sum(1 for s in stations if s.get("is_renting"))
    return {"count": len(stations), "renting": renting, "stations": stations}


@router.get("/septa/metro")
async def septa_metro(
    lat: float = Query(39.9526),
    lon: float = Query(-75.1652),
    radius_km: float = Query(25.0, ge=1, le=80),
) -> dict:
    """MFL/BSL stations, alerts, elevators, TransitView L1/B1 vehicles, nearby cameras."""
    discover = await discovery_service.search_area(lat, lon, radius_km)
    cameras = discover.results if discover else []
    data = await septa_metro.bundle(lat, lon, cameras=cameras)
    data["camera_count"] = len(cameras)
    return data
