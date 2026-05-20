"""Philadelphia 311 service requests via OpenDataPhilly CartoDB SQL API.

Endpoint: https://phl.carto.com/api/v2/sql?q=SELECT ... FROM public_cases_fc ...
No authentication required.
"""
from __future__ import annotations

import logging
import math

from backend.settings import get_settings
from backend.shared.http import get_json

log = logging.getLogger(__name__)

ENDPOINT = "https://phl.carto.com/api/v2/sql"

# Only serve Philadelphia-area queries (saves a wasted network round-trip).
PHILLY_BBOX = (39.5, -75.8, 40.6, -74.6)


def _within(lat: float, lon: float) -> bool:
    s_lat, w_lon, n_lat, e_lon = PHILLY_BBOX
    return s_lat <= lat <= n_lat and w_lon <= lon <= e_lon


def _bbox(lat: float, lon: float, radius_km: float) -> tuple[float, float, float, float]:
    dlat = radius_km / 111.0
    dlon = radius_km / max(0.001, 111.0 * math.cos(math.radians(lat)))
    return lat - dlat, lon - dlon, lat + dlat, lon + dlon


async def recent(lat: float, lon: float, *, radius_km: float = 2.0,
                 days: int = 7, limit: int = 50) -> list[dict]:
    if not _within(lat, lon):
        return []
    s_lat, w_lon, n_lat, e_lon = _bbox(lat, lon, radius_km)
    sql = (
        "SELECT cartodb_id, service_name, status, requested_datetime, lat, lon "
        "FROM public_cases_fc "
        f"WHERE requested_datetime > now() - interval '{int(days)} days' "
        f"AND lat BETWEEN {s_lat} AND {n_lat} "
        f"AND lon BETWEEN {w_lon} AND {e_lon} "
        "ORDER BY requested_datetime DESC "
        f"LIMIT {int(limit)}"
    )
    s = get_settings()
    payload = await get_json(ENDPOINT, params={"q": sql},
                             ttl_s=s.cache_ttl_phila311_s)
    if not isinstance(payload, dict):
        return []
    rows = payload.get("rows") or []
    out: list[dict] = []
    for r in rows:
        try:
            out.append({
                "id": r.get("cartodb_id"),
                "service_name": r.get("service_name"),
                "status": r.get("status"),
                "requested_at": r.get("requested_datetime"),
                "lat": float(r.get("lat")),
                "lon": float(r.get("lon")),
            })
        except (TypeError, ValueError):
            continue
    return out
