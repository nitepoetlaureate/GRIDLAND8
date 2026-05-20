"""Mapillary Graph API v4 — photosphere lookup near a point.

Used to power the photosphere transition when the user dives below ~80 m.
Operates only with an explicit, free-tier-registered API key (CC BY-SA 4.0
image corpus). If the key is unset, the source returns an empty list and
the frontend simply falls back to the globe view.
"""
from __future__ import annotations

import logging

from backend.settings import get_settings
from backend.shared.http import get_json

log = logging.getLogger(__name__)

GRAPH_BASE = "https://graph.mapillary.com"


async def panos_near(lat: float, lon: float, radius_m: int = 200,
                     limit: int = 25) -> list[dict]:
    """Return up to `limit` pano image records within `radius_m`.

    Each record: {id, captured_at, compass_angle, geometry, sequence_id,
    is_pano, thumb_2048_url}.
    """
    s = get_settings()
    if not s.mapillary_api_key:
        return []
    params = {
        "fields": "id,captured_at,compass_angle,geometry,sequence_id,is_pano,thumb_2048_url",
        "lat": lat,
        "lng": lon,
        "radius": max(10, min(int(radius_m), 50)),
        "limit": max(1, min(int(limit), 100)),
        "is_pano": "true",
    }
    headers = {"Authorization": f"OAuth {s.mapillary_api_key}"}
    data = await get_json(
        f"{GRAPH_BASE}/images",
        params=params,
        headers=headers,
        ttl_s=s.cache_ttl_mapillary_s,
    )
    if not isinstance(data, dict):
        return []
    out: list[dict] = []
    for rec in data.get("data") or []:
        geom = rec.get("geometry") or {}
        coords = geom.get("coordinates")
        if not (isinstance(coords, list) and len(coords) == 2):
            continue
        out.append({
            "id": rec.get("id"),
            "lat": coords[1],
            "lon": coords[0],
            "captured_at": rec.get("captured_at"),
            "compass_angle": rec.get("compass_angle"),
            "sequence_id": rec.get("sequence_id"),
            "is_pano": rec.get("is_pano"),
            "thumb_2048_url": rec.get("thumb_2048_url"),
        })
    return out
