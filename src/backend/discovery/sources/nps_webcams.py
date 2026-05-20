"""National Park Service Webcams.

Endpoint: https://developer.nps.gov/api/v1/webcams
Free key (header `X-Api-Key` or query `api_key`) — registration at
https://www.nps.gov/subjects/developer/get-started.htm.

Returns webcam metadata for the entire national park system (~100+ active
cameras). Each record includes title, description, latitude, longitude,
images[], and a link to the park's webcam page.
"""
from __future__ import annotations

import logging

from backend.discovery.models import CameraResult
from backend.settings import get_settings
from backend.shared.constants import PUB_OPERATOR_PUBLISHED, SRC_NPS
from backend.shared.http import get_json, utc_now_iso

log = logging.getLogger(__name__)

ENDPOINT = "https://developer.nps.gov/api/v1/webcams"


def _first_image_url(images: list | None) -> str | None:
    if not isinstance(images, list):
        return None
    for img in images:
        if not isinstance(img, dict):
            continue
        u = img.get("url")
        if u:
            return u
    return None


def normalize(records: list[dict]) -> list[CameraResult]:
    now = utc_now_iso()
    out: list[CameraResult] = []
    for r in records or []:
        if not isinstance(r, dict):
            continue
        try:
            r_lat = float(r.get("latitude"))
            r_lon = float(r.get("longitude"))
        except (TypeError, ValueError):
            continue
        if r_lat == 0.0 and r_lon == 0.0:
            continue
        status = (r.get("status") or "").strip().lower()
        if status in {"inactive", "construction"}:
            continue
        cam_id = str(r.get("id") or r.get("title") or "")
        if not cam_id:
            continue
        title = (r.get("title") or "NPS Webcam").strip()
        url = (r.get("url") or "").strip()
        thumb = _first_image_url(r.get("images"))
        try:
            cam = CameraResult(
                id=f"nps_{cam_id[:24]}",
                lat=r_lat, lon=r_lon,
                source=SRC_NPS,
                publication_status=PUB_OPERATOR_PUBLISHED,
                label=title,
                url=url,
                thumbnail_url=thumb,
                blur_required=False,
                data_age_s=0,
                fetched_at=now,
                tags={
                    "agency": "US National Park Service",
                    "park_code": ",".join([pc for pc in (r.get("relatedParks") or [])
                                            if isinstance(pc, str)][:4]) if isinstance(r.get("relatedParks"), list) else "",
                    "category": "parks",
                },
            )
        except Exception as e:
            log.debug("dropping NPS record: %s", e)
            continue
        out.append(cam)
    return out


def _in_box(r_lat: float, r_lon: float, lat: float, lon: float,
            radius_km: float) -> bool:
    import math
    dlat = radius_km / 111.0
    dlon = radius_km / max(0.001, 111.0 * math.cos(math.radians(lat)))
    return abs(r_lat - lat) <= dlat and abs(r_lon - lon) <= dlon


async def search(lat: float, lon: float, radius_km: float) -> list[CameraResult]:
    s = get_settings()
    if not s.nps_api_key:
        return []
    # The NPS endpoint doesn't accept lat/lon filtering; we fetch the full
    # catalog (cached aggressively) and filter client-side.
    payload = await get_json(
        ENDPOINT,
        params={"api_key": s.nps_api_key, "limit": 200},
        ttl_s=s.cache_ttl_nps_webcams_s,
    )
    if not isinstance(payload, dict):
        return []
    data = payload.get("data") or []
    candidates = normalize(data)
    return [c for c in candidates if _in_box(c.lat, c.lon, lat, lon, radius_km)]
