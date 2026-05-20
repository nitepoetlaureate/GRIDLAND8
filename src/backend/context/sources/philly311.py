"""Philadelphia 311 service requests via OpenDataPhilly Carto SQL API.

Table: public_cases_fc on phl.carto.com — no authentication required.
"""
from __future__ import annotations

import logging

from backend.settings import get_settings
from backend.shared import opendataphilly as odp

log = logging.getLogger(__name__)


async def recent(lat: float, lon: float, *, radius_km: float = 2.0,
                 days: int = 7, limit: int = 50) -> list[dict]:
    if not odp.within_philly(lat, lon):
        return []
    s_lat, w_lon, n_lat, e_lon = odp.point_bbox(lat, lon, radius_km)
    sql = (
        "SELECT cartodb_id, service_name, status, requested_datetime, lat, lon "
        "FROM public_cases_fc "
        f"WHERE requested_datetime > now() - interval '{int(days)} days' "
        f"AND lat BETWEEN {s_lat} AND {n_lat} "
        f"AND lon BETWEEN {w_lon} AND {e_lon} "
        "ORDER BY requested_datetime DESC "
        f"LIMIT {int(limit)}"
    )
    rows = await odp.carto_query(sql, ttl_s=get_settings().cache_ttl_phila311_s)
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
