"""SEPTA bus detours — no authentication.

https://www3.septa.org/api/BusDetours/
Documented on OpenDataPhilly: https://www.opendataphilly.org/
"""
from __future__ import annotations

import logging

from backend.settings import get_settings
from backend.shared import opendataphilly as odp
from backend.shared.http import get_json

log = logging.getLogger(__name__)

ENDPOINT = "https://www3.septa.org/api/BusDetours/"


def normalize(payload: list | dict) -> list[dict]:
    if isinstance(payload, dict):
        items = [payload]
    elif isinstance(payload, list):
        items = payload
    else:
        return []
    out: list[dict] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        route_id = str(item.get("route_id") or "")
        for info in item.get("route_info") or []:
            if not isinstance(info, dict):
                continue
            out.append({
                "route_id": route_id,
                "direction": info.get("route_direction"),
                "reason": info.get("reason"),
                "start": info.get("start_location"),
                "end": info.get("end_location"),
                "starts": info.get("start_date_time"),
                "ends": info.get("end_date_time"),
                "message": info.get("current_message"),
            })
    return out


async def active(*, route_id: str | None = None) -> list[dict]:
    s = get_settings()
    url = ENDPOINT if not route_id else f"{ENDPOINT}{route_id}"
    payload = await get_json(url, ttl_s=s.cache_ttl_septa_detours_s)
    return normalize(payload)


async def near(lat: float, lon: float) -> list[dict]:
    """Return all current SEPTA bus detours when query is in the Philly service area."""
    if not odp.within_philly(lat, lon):
        return []
    return await active()
