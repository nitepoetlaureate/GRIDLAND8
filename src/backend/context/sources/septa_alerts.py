"""SEPTA system-wide service alerts (no authentication).

Endpoint: https://www3.septa.org/api/Alerts/get_alert_data.php?req1=all
Returns a list of route-keyed alert records.
"""
from __future__ import annotations

import logging

from backend.settings import get_settings
from backend.shared.http import get_json

log = logging.getLogger(__name__)

ENDPOINT = "https://www3.septa.org/api/Alerts/get_alert_data.php"

# Rough Greater Philadelphia bounding box; we only return alerts when the
# user's query point is plausibly in SEPTA's service territory.
PHILLY_BBOX = (39.5, -75.8, 40.6, -74.6)  # south, west, north, east


def _within(lat: float, lon: float) -> bool:
    s_lat, w_lon, n_lat, e_lon = PHILLY_BBOX
    return s_lat <= lat <= n_lat and w_lon <= lon <= e_lon


def normalize(rows: list[dict]) -> list[dict]:
    out: list[dict] = []
    for r in rows or []:
        if not isinstance(r, dict):
            continue
        current = (r.get("current_message") or "").strip()
        advisory = (r.get("advisory_message") or "").strip()
        detour = (r.get("detour_message") or "").strip()
        if not current and not advisory and not detour:
            continue
        out.append({
            "route_id": r.get("route_id"),
            "route_name": r.get("route_name"),
            "current_message": current or None,
            "advisory_message": advisory or None,
            "detour_message": detour or None,
            "detour_start": r.get("detour_start_date_time"),
            "detour_end": r.get("detour_end_date_time"),
            "last_updated": r.get("last_updated"),
        })
    return out


async def near(lat: float, lon: float) -> list[dict]:
    if not _within(lat, lon):
        return []
    s = get_settings()
    payload = await get_json(
        ENDPOINT, params={"req1": "all"}, ttl_s=s.cache_ttl_septa_alerts_s
    )
    if not isinstance(payload, list):
        return []
    # Keep at most 30 alerts (the API returns hundreds; we ship the most recent)
    return normalize(payload)[:30]
