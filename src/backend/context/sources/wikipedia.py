"""Wikipedia GeoSearch — no authentication required.

Returns articles within a radius of a point. Used for cultural/historic context.
"""
from __future__ import annotations

import logging

from backend.shared.http import get_json

log = logging.getLogger(__name__)

WIKI_API = "https://en.wikipedia.org/w/api.php"


async def nearby(lat: float, lon: float, radius_m: int = 10000, limit: int = 10) -> list[dict]:
    params = {
        "action": "query",
        "format": "json",
        "list": "geosearch",
        "gscoord": f"{lat}|{lon}",
        "gsradius": min(max(int(radius_m), 10), 10000),
        "gslimit": min(max(int(limit), 1), 50),
        "origin": "*",
    }
    data = await get_json(WIKI_API, params=params)
    if not data or not isinstance(data, dict):
        return []
    results = (data.get("query") or {}).get("geosearch") or []
    out: list[dict] = []
    for r in results:
        title = r.get("title")
        if not title:
            continue
        out.append({
            "title": title,
            "lat": r.get("lat"),
            "lon": r.get("lon"),
            "distance_m": r.get("dist"),
            "page_id": r.get("pageid"),
            "url": f"https://en.wikipedia.org/?curid={r.get('pageid')}",
        })
    return out
