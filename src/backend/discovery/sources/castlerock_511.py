"""Castle Rock 511 platform adapter.

Many state/provincial 511 systems use the Castle Rock platform with a common
JSON schema served at `https://<host>/api/v2/get/cameras?format=json`. Each
record looks like:

  {"Id": 1, "Source": "...", "SourceId": "...", "Roadway": "...",
   "Direction": "...", "Latitude": ..., "Longitude": ..., "Location": "...",
   "Views": [{"Id": 1, "Url": "https://.../map/Cctv/1",
              "Status": "Enabled", "Description": "..."}]}

Each `View` is a separate camera angle; we treat each view as one CameraResult.

Adding a new deployment: add a tuple to `DEPLOYMENTS`. Each entry must include
a geographic bounding box so we only call the host when the search circle
intersects its coverage.
"""
from __future__ import annotations

import hashlib
import logging
import math
from dataclasses import dataclass

from backend.discovery.models import CameraResult
from backend.settings import get_settings
from backend.shared.constants import PUB_OPERATOR_PUBLISHED, SRC_CR511
from backend.shared.http import get_json, utc_now_iso

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class Deployment:
    code: str
    host: str
    agency: str
    bbox: tuple[float, float, float, float]  # south, west, north, east


# Confirmed-working Castle Rock 511 deployments. Add more as they are verified.
DEPLOYMENTS: tuple[Deployment, ...] = (
    Deployment("on511", "511on.ca", "Ontario Ministry of Transportation",
               (41.5, -95.2, 56.9, -74.3)),
    Deployment("ab511", "511.alberta.ca", "Alberta Transportation",
               (49.0, -120.0, 60.0, -110.0)),
)


def _intersects_bbox(lat: float, lon: float, radius_km: float,
                     bbox: tuple[float, float, float, float]) -> bool:
    s_lat, w_lon, n_lat, e_lon = bbox
    dlat = radius_km / 111.0
    dlon = radius_km / max(0.001, 111.0 * math.cos(math.radians(lat)))
    return (lat + dlat) >= s_lat and (lat - dlat) <= n_lat \
        and (lon + dlon) >= w_lon and (lon - dlon) <= e_lon


def normalize(records: list[dict], dep: Deployment, lat: float, lon: float,
              radius_km: float) -> list[CameraResult]:
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
        views = r.get("Views") or []
        if not isinstance(views, list) or not views:
            continue
        roadway = str(r.get("Roadway") or "")
        location = str(r.get("Location") or "")
        direction = str(r.get("Direction") or "")
        rec_id = str(r.get("Id") or "")
        for view in views:
            if not isinstance(view, dict):
                continue
            if str(view.get("Status", "")).lower() != "enabled":
                continue
            url = (view.get("Url") or "").strip()
            if not url:
                continue
            view_id = str(view.get("Id") or "")
            unique = f"cr511:{dep.code}:{rec_id}:{view_id}"
            cam_id = f"cr511_{dep.code}_" + \
                hashlib.sha1(unique.encode()).hexdigest()[:12]
            desc = str(view.get("Description") or "").strip()
            label_bits = [roadway, location, direction, desc]
            label = " · ".join([b for b in label_bits if b]) or "511 Camera"
            try:
                cam = CameraResult(
                    id=cam_id,
                    lat=r_lat,
                    lon=r_lon,
                    source=SRC_CR511,
                    publication_status=PUB_OPERATOR_PUBLISHED,
                    label=label,
                    url=url,
                    thumbnail_url=url,
                    blur_required=False,
                    data_age_s=0,
                    fetched_at=now,
                    tags={"deployment": dep.code, "agency": dep.agency,
                          "roadway": roadway, "direction": direction},
                )
            except Exception as e:
                log.debug("dropping cr511 record: %s", e)
                continue
            out.append(cam)
    return out


async def _fetch_one(dep: Deployment, lat: float, lon: float,
                     radius_km: float) -> list[CameraResult]:
    if not _intersects_bbox(lat, lon, radius_km, dep.bbox):
        return []
    s = get_settings()
    url = f"https://{dep.host}/api/v2/get/cameras"
    payload = await get_json(url, params={"format": "json"},
                             ttl_s=s.cache_ttl_cr511_s)
    if not isinstance(payload, list):
        return []
    return normalize(payload, dep, lat, lon, radius_km)


async def search(lat: float, lon: float, radius_km: float) -> list[CameraResult]:
    import asyncio
    coros = [_fetch_one(d, lat, lon, radius_km) for d in DEPLOYMENTS]
    batches = await asyncio.gather(*coros, return_exceptions=True)
    out: list[CameraResult] = []
    for b in batches:
        if isinstance(b, BaseException):
            log.warning("cr511 deployment raised: %s", b)
            continue
        out.extend(b)
    return out
