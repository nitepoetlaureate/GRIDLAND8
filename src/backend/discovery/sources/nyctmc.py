"""NYC TMC (NYC DOT) traffic cameras — public, no authentication.

Endpoint: https://webcams.nyctmc.org/api/cameras
Each record: {id, name, latitude, longitude, area, isOnline, imageUrl}
Image URL: https://webcams.nyctmc.org/api/cameras/{id}/image  (still JPEG; refreshes)

~948 cameras across all five boroughs.
"""
from __future__ import annotations

import logging
import math

from backend.discovery.models import CameraResult
from backend.settings import get_settings
from backend.shared.constants import PUB_OPERATOR_PUBLISHED, SRC_NYCTMC
from backend.shared.http import get_json, utc_now_iso

log = logging.getLogger(__name__)

ENDPOINT = "https://webcams.nyctmc.org/api/cameras"

# NYC + immediate metro (Westchester, Long Island, Northern NJ).
NYC_BBOX = (40.40, -74.30, 41.10, -73.40)  # south, west, north, east


def _intersects_bbox(lat: float, lon: float, radius_km: float,
                     bbox: tuple[float, float, float, float]) -> bool:
    s_lat, w_lon, n_lat, e_lon = bbox
    dlat = radius_km / 111.0
    dlon = radius_km / max(0.001, 111.0 * math.cos(math.radians(lat)))
    return (lat + dlat) >= s_lat and (lat - dlat) <= n_lat \
        and (lon + dlon) >= w_lon and (lon - dlon) <= e_lon


def normalize(records: list[dict], lat: float, lon: float,
              radius_km: float) -> list[CameraResult]:
    dlat = radius_km / 111.0
    dlon = radius_km / max(0.001, 111.0 * math.cos(math.radians(lat)))
    now = utc_now_iso()
    out: list[CameraResult] = []
    for r in records or []:
        try:
            r_lat = float(r.get("latitude"))
            r_lon = float(r.get("longitude"))
        except (TypeError, ValueError):
            continue
        if abs(r_lat - lat) > dlat or abs(r_lon - lon) > dlon:
            continue
        img = (r.get("imageUrl") or "").strip()
        cam_id = str(r.get("id") or "")
        if not cam_id:
            continue
        is_online = str(r.get("isOnline", "false")).lower() == "true"
        try:
            cam = CameraResult(
                id=f"nyctmc_{cam_id}",
                lat=r_lat,
                lon=r_lon,
                source=SRC_NYCTMC,
                publication_status=PUB_OPERATOR_PUBLISHED,
                label=(r.get("name") or "NYC DOT Camera").strip(),
                url=img,
                thumbnail_url=img if is_online else None,
                blur_required=False,
                data_age_s=0,
                fetched_at=now,
                tags={"area": str(r.get("area") or ""),
                      "agency": "NYC DOT TMC",
                      "online": "1" if is_online else "0"},
            )
        except Exception as e:
            log.debug("dropping nyctmc record: %s", e)
            continue
        out.append(cam)
    return out


async def search(lat: float, lon: float, radius_km: float) -> list[CameraResult]:
    if not _intersects_bbox(lat, lon, radius_km, NYC_BBOX):
        return []
    s = get_settings()
    payload = await get_json(ENDPOINT, ttl_s=s.cache_ttl_nyctmc_s)
    if not isinstance(payload, list):
        return []
    return normalize(payload, lat, lon, radius_km)
