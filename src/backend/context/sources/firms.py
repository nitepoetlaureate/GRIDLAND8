"""NASA FIRMS — active fire detections. Free MAP_KEY required.

Endpoint shape (CSV):
  https://firms.modaps.eosdis.nasa.gov/api/area/csv/{MAP_KEY}/{SOURCE}/{west,south,east,north}/{days}

Sources we use: VIIRS_SNPP_NRT (375 m, near real-time). Falls back to MODIS_NRT
if VIIRS returns nothing.
"""
from __future__ import annotations

import csv
import io
import logging
import math

import httpx

from backend.settings import get_settings
from backend.shared.cache import default_cache, make_key
from backend.shared.constants import USER_AGENT

log = logging.getLogger(__name__)

BASE = "https://firms.modaps.eosdis.nasa.gov/api/area/csv"
SOURCE_ORDER = ("VIIRS_SNPP_NRT", "MODIS_NRT")


def _bbox(lat: float, lon: float, radius_km: float) -> tuple[float, float, float, float]:
    dlat = radius_km / 111.0
    dlon = radius_km / max(0.001, 111.0 * math.cos(math.radians(lat)))
    return lon - dlon, lat - dlat, lon + dlon, lat + dlat  # west,south,east,north


def parse_csv(text: str) -> list[dict]:
    if not text or text.startswith("<"):  # HTML error pages
        return []
    reader = csv.DictReader(io.StringIO(text))
    out: list[dict] = []
    for row in reader:
        try:
            lat = float(row.get("latitude") or 0)
            lon = float(row.get("longitude") or 0)
        except ValueError:
            continue
        if lat == 0.0 and lon == 0.0:
            continue
        out.append({
            "lat": lat,
            "lon": lon,
            "brightness": float(row.get("bright_ti4") or row.get("brightness") or 0) or None,
            "acq_date": row.get("acq_date"),
            "acq_time": row.get("acq_time"),
            "satellite": row.get("satellite"),
            "confidence": row.get("confidence"),
            "frp": float(row.get("frp") or 0) or None,
            "daynight": row.get("daynight"),
        })
    return out


async def _fetch_csv(url: str) -> str:
    """FIRMS returns CSV (not JSON), so a thin local fetcher with cache."""
    s = get_settings()
    cache = default_cache()
    key = make_key("GET", url) + "|csv"
    hit = cache.get(key)
    if hit is not None:
        return hit

    async def loader() -> str | None:
        try:
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(s.http_timeout_s),
                headers={"User-Agent": USER_AGENT},
                follow_redirects=True,
            ) as c:
                r = await c.get(url)
                if r.status_code != 200:
                    return None
                return r.text
        except Exception as e:
            log.warning("FIRMS fetch failed: %s", e)
            return None

    val = await cache.get_or_fetch(key, s.cache_ttl_firms_s, loader)
    return val or ""


async def active_fires(lat: float, lon: float, *, radius_km: float = 500.0,
                       days: int = 1) -> list[dict]:
    s = get_settings()
    if not s.nasa_firms_map_key:
        return []
    west, south, east, north = _bbox(lat, lon, radius_km)
    bbox_str = f"{west},{south},{east},{north}"
    days = max(1, min(int(days), 10))
    for source in SOURCE_ORDER:
        url = f"{BASE}/{s.nasa_firms_map_key}/{source}/{bbox_str}/{days}"
        text = await _fetch_csv(url)
        rows = parse_csv(text)
        if rows:
            return rows
    return []
