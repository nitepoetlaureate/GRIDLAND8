"""Shared helpers for OpenDataPhilly Carto SQL API (phl.carto.com).

No API key required. See https://www.opendataphilly.org and
https://carto.com/developers/sql-api/
"""
from __future__ import annotations

import logging
import math

from backend.settings import get_settings
from backend.shared.http import get_json

log = logging.getLogger(__name__)

CARTO_SQL = "https://phl.carto.com/api/v2/sql"

# Greater Philadelphia service area (skip Carto calls from distant queries).
PHILLY_BBOX = (39.5, -75.8, 40.6, -74.6)  # south, west, north, east


def within_philly(lat: float, lon: float) -> bool:
    s_lat, w_lon, n_lat, e_lon = PHILLY_BBOX
    return s_lat <= lat <= n_lat and w_lon <= lon <= e_lon


def point_bbox(lat: float, lon: float, radius_km: float) -> tuple[float, float, float, float]:
    """Axis-aligned bounds: south, west, north, east."""
    dlat = radius_km / 111.0
    dlon = radius_km / max(0.001, 111.0 * math.cos(math.radians(lat)))
    return lat - dlat, lon - dlon, lat + dlat, lon + dlon


def xy_filter(alias: str, lat: float, lon: float, radius_km: float) -> str:
    """SQL fragment for point_x / point_y tables."""
    s, w, n, e = point_bbox(lat, lon, radius_km)
    return (
        f"{alias}.point_x BETWEEN {w} AND {e} "
        f"AND {alias}.point_y BETWEEN {s} AND {n}"
    )


def geom_envelope_filter(lat: float, lon: float, radius_km: float) -> str:
    s, w, n, e = point_bbox(lat, lon, radius_km)
    return f"the_geom && ST_MakeEnvelope({w}, {s}, {e}, {n}, 4326)"


async def carto_query(sql: str, *, ttl_s: float | None = None) -> list[dict]:
    s = get_settings()
    ttl = s.cache_ttl_opendataphilly_s if ttl_s is None else ttl_s
    payload = await get_json(CARTO_SQL, params={"q": sql}, ttl_s=ttl)
    if not isinstance(payload, dict):
        return []
    rows = payload.get("rows")
    return rows if isinstance(rows, list) else []
