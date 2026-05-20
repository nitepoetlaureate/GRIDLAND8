"""USGS Water Services — current stream discharge/gauge data.

Free, no authentication.
Docs: https://waterservices.usgs.gov/

Returns active discharge gauges within a bounding box around (lat, lon).
"""
from __future__ import annotations

import logging
import math

from backend.settings import get_settings
from backend.shared.http import get_json

log = logging.getLogger(__name__)

ENDPOINT = "https://waterservices.usgs.gov/nwis/iv/"


def _bbox(lat: float, lon: float, radius_km: float) -> str:
    """USGS bBox parameter format: 'west,south,east,north', degrees."""
    dlat = radius_km / 111.0
    dlon = radius_km / max(0.001, 111.0 * math.cos(math.radians(lat)))
    west = max(lon - dlon, -180.0)
    south = max(lat - dlat, -90.0)
    east = min(lon + dlon, 180.0)
    north = min(lat + dlat, 90.0)
    return f"{west:.4f},{south:.4f},{east:.4f},{north:.4f}"


async def gauges_near(lat: float, lon: float, *, radius_km: float = 50.0,
                      limit: int = 20) -> list[dict]:
    s = get_settings()
    # USGS requires bbox width <= 7 degrees; clamp the radius accordingly.
    radius_km = min(max(radius_km, 5.0), 350.0)
    params = {
        "format": "json",
        "bBox": _bbox(lat, lon, radius_km),
        "parameterCd": "00060,00065",  # discharge (cfs), gauge height (ft)
        "siteStatus": "active",
        "period": "PT1H",
    }
    payload = await get_json(ENDPOINT, params=params,
                             ttl_s=s.cache_ttl_usgs_water_s)
    if not isinstance(payload, dict):
        return []
    series = (payload.get("value") or {}).get("timeSeries") or []
    out: list[dict] = []
    by_site: dict[str, dict] = {}
    for ts in series:
        try:
            info = ts.get("sourceInfo") or {}
            site_code = (info.get("siteCode") or [{}])[0].get("value", "")
            geo = (info.get("geoLocation") or {}).get("geogLocation") or {}
            s_lat = float(geo.get("latitude"))
            s_lon = float(geo.get("longitude"))
        except (TypeError, ValueError, IndexError):
            continue
        var = ((ts.get("variable") or {}).get("variableCode") or [{}])[0].get("value", "")
        values = ((ts.get("values") or [{}])[0].get("value") or [])
        latest = values[-1] if values else None
        site = by_site.setdefault(site_code, {
            "site_code": site_code,
            "name": info.get("siteName"),
            "lat": s_lat, "lon": s_lon,
            "measurements": {},
        })
        if latest:
            site["measurements"][var] = {
                "value": latest.get("value"),
                "datetime": latest.get("dateTime"),
                "unit": (ts.get("variable") or {}).get("unit", {}).get("unitCode"),
            }
    out = list(by_site.values())[: int(limit)]
    return out
