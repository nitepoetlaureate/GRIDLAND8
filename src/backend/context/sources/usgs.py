"""USGS Earthquakes — FDSN event service. No authentication required.

Docs: https://earthquake.usgs.gov/fdsnws/event/1/
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from backend.settings import get_settings
from backend.shared.http import get_json

log = logging.getLogger(__name__)

FDSN = "https://earthquake.usgs.gov/fdsnws/event/1/query"


async def recent_quakes(lat: float, lon: float, *, radius_km: float = 500.0,
                        min_magnitude: float = 2.5, days: int = 7,
                        limit: int = 30) -> list[dict]:
    s = get_settings()
    starttime = (datetime.now(timezone.utc) - timedelta(days=days)).date().isoformat()
    params = {
        "format": "geojson",
        "latitude": lat,
        "longitude": lon,
        "maxradiuskm": max(1, min(radius_km, 20000)),
        "minmagnitude": min_magnitude,
        "starttime": starttime,
        "orderby": "time",
        "limit": max(1, min(limit, 200)),
    }
    data = await get_json(FDSN, params=params, ttl_s=s.cache_ttl_quakes_s)
    if not isinstance(data, dict):
        return []
    out: list[dict] = []
    for f in data.get("features") or []:
        geom = f.get("geometry") or {}
        coords = geom.get("coordinates") or []
        if len(coords) < 2:
            continue
        props = f.get("properties") or {}
        out.append({
            "id": f.get("id"),
            "mag": props.get("mag"),
            "place": props.get("place"),
            "time": props.get("time"),  # epoch ms
            "url": props.get("url"),
            "lat": coords[1],
            "lon": coords[0],
            "depth_km": coords[2] if len(coords) > 2 else None,
            "type": props.get("type"),
            "alert": props.get("alert"),
            "tsunami": props.get("tsunami"),
        })
    return out
