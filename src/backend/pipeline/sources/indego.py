"""Indego bike share (Philly) — GBFS, no API key.

Root: https://gbfs.bcycle.com/bcycle_indego/gbfs.json
"""
from __future__ import annotations

import logging

from backend.settings import get_settings
from backend.shared import opendataphilly as odp
from backend.shared.http import get_json

log = logging.getLogger(__name__)

GBFS_ROOT = "https://gbfs.bcycle.com/bcycle_indego/gbfs.json"


async def _feed_urls() -> dict[str, str]:
    root = await get_json(GBFS_ROOT, ttl_s=get_settings().cache_ttl_indego_s)
    feeds = {}
    try:
        for f in root["data"]["en"]["feeds"]:
            feeds[f["name"]] = f["url"]
    except (KeyError, TypeError):
        pass
    return feeds


def _merge(station_info: list[dict], station_status: list[dict]) -> list[dict]:
    status_by_id = {}
    for s in station_status or []:
        if isinstance(s, dict) and s.get("station_id") is not None:
            status_by_id[str(s["station_id"])] = s
    out: list[dict] = []
    for st in station_info or []:
        if not isinstance(st, dict):
            continue
        sid = str(st.get("station_id") or "")
        stat = status_by_id.get(sid, {})
        try:
            lat = float(st.get("lat"))
            lon = float(st.get("lon"))
        except (TypeError, ValueError):
            continue
        out.append({
            "station_id": sid,
            "name": st.get("name"),
            "lat": lat,
            "lon": lon,
            "bikes": stat.get("num_bikes_available"),
            "docks": stat.get("num_docks_available"),
            "is_renting": stat.get("is_renting"),
            "is_returning": stat.get("is_returning"),
        })
    return out


def _in_radius(stations: list[dict], lat: float, lon: float,
               radius_km: float) -> list[dict]:
    import math
    dlat = radius_km / 111.0
    dlon = radius_km / max(0.001, 111.0 * math.cos(math.radians(lat)))
    return [s for s in stations
            if abs(s["lat"] - lat) <= dlat and abs(s["lon"] - lon) <= dlon]


async def stations_near(lat: float, lon: float, *, radius_km: float = 15.0) -> list[dict]:
    if not odp.within_philly(lat, lon):
        return []
    feeds = await _feed_urls()
    info_url = feeds.get("station_information")
    status_url = feeds.get("station_status")
    if not info_url or not status_url:
        return []
    s = get_settings()
    info = await get_json(info_url, ttl_s=s.cache_ttl_indego_s)
    status = await get_json(status_url, ttl_s=s.cache_ttl_indego_s)
    try:
        info_rows = info["data"]["stations"]
        status_rows = status["data"]["stations"]
    except (KeyError, TypeError):
        return []
    merged = _merge(info_rows, status_rows)
    return _in_radius(merged, lat, lon, min(radius_km, 50.0))
