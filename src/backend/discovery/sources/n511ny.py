"""511NY (New York State DOT / Thruway) cameras — free key, JSON.

Endpoint:
  https://511ny.org/api/getcameras?key={N511NY_API_KEY}&format=json

Each record (representative shape):
  {"ID": "1234", "Name": "I-87 NB at Albany", "Latitude": 42.65,
   "Longitude": -73.75, "Url": "https://511ny.org/map/Cctv/1234",
   "VideoUrl": "https://...m3u8", "Disabled": "0",
   "Region": "Capital District", "RoadwayName": "I-87"}
"""
from __future__ import annotations

import hashlib
import logging
import math

from backend.discovery.models import CameraResult
from backend.settings import get_settings
from backend.shared.constants import PUB_OPERATOR_PUBLISHED, SRC_N511NY
from backend.shared.http import get_json, utc_now_iso

log = logging.getLogger(__name__)

ENDPOINT = "https://511ny.org/api/getcameras"


def normalize(records: list[dict], lat: float, lon: float, radius_km: float) -> list[CameraResult]:
    dlat = radius_km / 111.0
    dlon = radius_km / max(0.001, 111.0 * math.cos(math.radians(lat)))
    now = utc_now_iso()
    out: list[CameraResult] = []
    for r in records or []:
        try:
            r_lat = float(r.get("Latitude"))
            r_lon = float(r.get("Longitude"))
        except (TypeError, ValueError):
            continue
        if abs(r_lat - lat) > dlat or abs(r_lon - lon) > dlon:
            continue
        if str(r.get("Disabled", "0")) not in ("0", "false", "False"):
            continue
        url = (r.get("VideoUrl") or r.get("Url") or "").strip()
        if not url:
            continue
        cam_id = ("n511ny_" +
                  hashlib.sha1(f"n511ny:{r.get('ID')}".encode()).hexdigest()[:14])
        try:
            cam = CameraResult(
                id=cam_id,
                lat=r_lat,
                lon=r_lon,
                source=SRC_N511NY,
                publication_status=PUB_OPERATOR_PUBLISHED,
                label=(r.get("Name") or "511NY Camera").strip(),
                url=url,
                thumbnail_url=r.get("ImageUrl") or None,
                blur_required=False,
                data_age_s=0,
                fetched_at=now,
                tags={"region": str(r.get("Region") or ""),
                      "roadway": str(r.get("RoadwayName") or ""),
                      "agency": "NYSDOT/511NY"},
            )
        except Exception as e:
            log.debug("dropping 511ny record: %s", e)
            continue
        out.append(cam)
    return out


async def search(lat: float, lon: float, radius_km: float) -> list[CameraResult]:
    s = get_settings()
    if not s.n511ny_api_key:
        log.debug("511NY skipped: no api key")
        return []
    payload = await get_json(
        ENDPOINT, params={"key": s.n511ny_api_key, "format": "json"},
        ttl_s=s.cache_ttl_dot_s,
    )
    if not isinstance(payload, list):
        return []
    return normalize(payload, lat, lon, radius_km)
