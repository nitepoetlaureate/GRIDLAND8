"""Purdue CAM2 camera database — optional credentials.

Register at https://www.cam2project.net/ for clientID/clientSecret.
Historical API host was https://cam2-api.herokuapp.com (often offline).
"""
from __future__ import annotations

import hashlib
import logging
import math

from backend.discovery.models import CameraResult
from backend.settings import get_settings
from backend.shared.constants import PUB_DIRECTORY_LISTED, SRC_CAM2
import json

from backend.shared.http import get_json, post_json, utc_now_iso

log = logging.getLogger(__name__)

AUTH_URL = "https://cam2-api.herokuapp.com/auth"
SEARCH_URL = "https://cam2-api.herokuapp.com/cameras/search"


def _in_radius(lat: float, lon: float, radius_km: float,
               r_lat: float, r_lon: float) -> bool:
    dlat = radius_km / 111.0
    dlon = radius_km / max(0.001, 111.0 * math.cos(math.radians(lat)))
    return abs(r_lat - lat) <= dlat and abs(r_lon - lon) <= dlon


def normalize(records: list[dict], lat: float, lon: float,
              radius_km: float) -> list[CameraResult]:
    now = utc_now_iso()
    out: list[CameraResult] = []
    for r in records or []:
        try:
            r_lat = float(r.get("latitude"))
            r_lon = float(r.get("longitude"))
        except (TypeError, ValueError):
            continue
        if not _in_radius(lat, lon, radius_km, r_lat, r_lon):
            continue
        cam_id_raw = str(r.get("cameraID") or r.get("id") or "")
        unique = f"cam2:{cam_id_raw}:{r_lat:.5f},{r_lon:.5f}"
        cam_id = "cam2_" + hashlib.sha1(unique.encode()).hexdigest()[:12]
        label = (r.get("cameraDescription") or r.get("description")
                 or "CAM2 camera").strip()
        url = (r.get("cameraURL") or r.get("url") or "").strip() or None
        try:
            out.append(CameraResult(
                id=cam_id,
                lat=r_lat,
                lon=r_lon,
                source=SRC_CAM2,
                publication_status=PUB_DIRECTORY_LISTED,
                label=label[:200],
                url=url,
                thumbnail_url=None,
                blur_required=False,
                data_age_s=0,
                fetched_at=now,
                tags={"agency": "CAM2", "camera_id": cam_id_raw},
            ))
        except Exception as e:
            log.debug("drop cam2: %s", e)
    return out


async def _token(client_id: str, client_secret: str) -> str | None:
    payload = await post_json(
        AUTH_URL,
        data=json.dumps({"clientID": client_id, "clientSecret": client_secret}),
        headers={"Content-Type": "application/json"},
        ttl_s=3600.0,
    )
    if not isinstance(payload, dict):
        return None
    return payload.get("token") or payload.get("access_token")


async def search(lat: float, lon: float, radius_km: float) -> list[CameraResult]:
    s = get_settings()
    if not s.cam2_client_id or not s.cam2_client_secret:
        return []
    token = await _token(s.cam2_client_id, s.cam2_client_secret)
    if not token:
        log.info("CAM2 auth unavailable (API may be retired)")
        return []
    headers = {"Authorization": f"Bearer {token}"}
    page = 1
    collected: list[dict] = []
    while page <= 5:
        payload = await get_json(
            SEARCH_URL,
            params={"page": page, "limit": 100},
            headers=headers,
            ttl_s=3600.0,
        )
        if not isinstance(payload, dict):
            break
        rows = payload.get("cameras") or payload.get("data") or []
        if not rows:
            break
        collected.extend(rows)
        if len(rows) < 100:
            break
        page += 1
    return normalize(collected, lat, lon, radius_km)
