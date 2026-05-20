"""OpenAQ v3 — air quality monitoring stations near a point.

Docs: https://docs.openaq.org/  (v3 generally requires `X-API-Key`; free tier).
Self-skips when no key is configured.
"""
from __future__ import annotations

import logging

from backend.settings import get_settings
from backend.shared.http import get_json

log = logging.getLogger(__name__)

LOCATIONS = "https://api.openaq.org/v3/locations"


async def nearby_aq(lat: float, lon: float, *, radius_m: int = 25000,
                    limit: int = 10) -> list[dict]:
    s = get_settings()
    api_key = getattr(s, "openaq_api_key", None)
    if not api_key:
        return []
    params = {
        "coordinates": f"{lat},{lon}",
        "radius": max(100, min(int(radius_m), 25000)),
        "limit": max(1, min(int(limit), 50)),
    }
    headers = {"X-API-Key": api_key}
    data = await get_json(LOCATIONS, params=params, headers=headers,
                          ttl_s=s.cache_ttl_openaq_s)
    if not isinstance(data, dict):
        return []
    out: list[dict] = []
    for loc in data.get("results") or []:
        coords = loc.get("coordinates") or {}
        out.append({
            "id": loc.get("id"),
            "name": loc.get("name"),
            "lat": coords.get("latitude"),
            "lon": coords.get("longitude"),
            "country": (loc.get("country") or {}).get("code"),
            "sensors": [s.get("parameter", {}).get("name") for s in (loc.get("sensors") or [])],
            "last_active": loc.get("datetimeLast", {}).get("local"),
        })
    return out
