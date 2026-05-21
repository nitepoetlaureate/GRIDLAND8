"""511PA (Pennsylvania) CCTV API — live still URLs when N511PA_API_KEY is set."""
from __future__ import annotations

import hashlib
import logging
import math

from backend.discovery.models import CameraResult
from backend.settings import get_settings
from backend.shared.constants import PUB_OPERATOR_PUBLISHED
from backend.shared.geo import in_bbox
from backend.shared.http import get_json, utc_now_iso

log = logging.getLogger(__name__)

ENDPOINT = "https://511pa.com/api/getcameras"


async def search(lat: float, lon: float, radius_km: float) -> list[CameraResult]:
    s = get_settings()
    if not s.n511pa_api_key:
        return []
    data = await get_json(
        ENDPOINT,
        params={"key": s.n511pa_api_key, "format": "json"},
        ttl_s=s.cache_ttl_penndot_s,
    )
    records: list = []
    if isinstance(data, list):
        records = data
    elif isinstance(data, dict) and isinstance(data.get("cameras"), list):
        records = data["cameras"]
    now = utc_now_iso()
    pad = radius_km / 111.0
    min_lat, max_lat = lat - pad, lat + pad
    cos_lat = max(0.5, abs(math.cos(math.radians(lat))))
    min_lon = lon - pad / cos_lat
    max_lon = lon + pad / cos_lat
    out: list[CameraResult] = []
    for r in records:
        if not isinstance(r, dict):
            continue
        try:
            rlat = float(r.get("Latitude") or r.get("lat"))
            rlon = float(r.get("Longitude") or r.get("lon"))
        except (TypeError, ValueError):
            continue
        if not in_bbox(rlat, rlon, min_lat, min_lon, max_lat, max_lon):
            continue
        cid = str(r.get("ID") or r.get("Id") or "")
        cam_id = "n511pa_" + hashlib.sha1(f"n511pa:{cid}".encode()).hexdigest()[:14]
        img = (r.get("ImageUrl") or r.get("imageUrl") or "").strip()
        page = (r.get("Url") or r.get("url") or "").strip()
        out.append(CameraResult(
            id=cam_id,
            lat=rlat,
            lon=rlon,
            source="penndot",
            publication_status=PUB_OPERATOR_PUBLISHED,
            label=(r.get("Name") or r.get("name") or "511PA Camera").strip(),
            url=page or f"https://www.511pa.com/map/Cctv/{cid}",
            thumbnail_url=img or None,
            blur_required=False,
            data_age_s=0,
            fetched_at=now,
            tags={"statewide_id": cid, "stream_type": "refresh_jpeg" if img else "",
                  "agency": "511PA"},
        ))
    return out
