"""Aviation Weather (METARs) — aviationweather.gov, no authentication.

Endpoint:
  https://aviationweather.gov/api/data/metar?bbox=south,west,north,east&format=json
"""
from __future__ import annotations

import logging
import math

from backend.settings import get_settings
from backend.shared.http import get_json

log = logging.getLogger(__name__)

METAR = "https://aviationweather.gov/api/data/metar"


def _bbox(lat: float, lon: float, radius_km: float) -> str:
    dlat = radius_km / 111.0
    dlon = radius_km / max(0.001, 111.0 * math.cos(math.radians(lat)))
    return f"{lat - dlat},{lon - dlon},{lat + dlat},{lon + dlon}"


async def metars(lat: float, lon: float, *, radius_km: float = 200.0,
                 limit: int = 20) -> list[dict]:
    s = get_settings()
    params = {
        "bbox": _bbox(lat, lon, radius_km),
        "format": "json",
        "taf": "false",
        "hours": 2,
    }
    data = await get_json(METAR, params=params, ttl_s=s.cache_ttl_metar_s)
    if not isinstance(data, list):
        return []
    out: list[dict] = []
    for row in data[: max(1, int(limit))]:
        if not isinstance(row, dict):
            continue
        out.append({
            "station": row.get("icaoId") or row.get("station_id"),
            "raw": row.get("rawOb") or row.get("raw_text"),
            "obs_time": row.get("obsTime") or row.get("observation_time"),
            "lat": row.get("lat"),
            "lon": row.get("lon"),
            "temp_c": row.get("temp"),
            "dewpoint_c": row.get("dewp"),
            "wind_dir": row.get("wdir"),
            "wind_kt": row.get("wspd"),
            "visibility_sm": row.get("visib"),
            "flight_category": row.get("fltcat"),
            "wx": row.get("wxString"),
        })
    return out
