"""WSDOT (Washington State DOT) HighwayCameras — free key, JSON.

Endpoint:
  https://wsdot.com/Traffic/api/HighwayCameras/HighwayCamerasREST.svc/GetCamerasAsJson
    ?AccessCode={WSDOT_API_KEY}

Each record (camelCase varies between WSDOT services; we normalize):
  {"CameraID": ..., "CameraLocation": {"Latitude": ..., "Longitude": ...,
   "Description": ...}, "DisplayLatitude": ..., "DisplayLongitude": ...,
   "Title": "...", "ImageURL": "https://...", "IsActive": true,
   "Region": "...", "Description": "..."}
"""
from __future__ import annotations

import hashlib
import logging
import math

from backend.discovery.models import CameraResult
from backend.settings import get_settings
from backend.shared.constants import PUB_OPERATOR_PUBLISHED, SRC_WSDOT
from backend.shared.http import get_json, utc_now_iso

log = logging.getLogger(__name__)

ENDPOINT = ("https://wsdot.com/Traffic/api/HighwayCameras/HighwayCamerasREST.svc"
            "/GetCamerasAsJson")

# Washington State rough bounding box.
WA_BBOX = (45.5, -124.8, 49.0, -116.9)  # south, west, north, east


def _intersects_bbox(lat: float, lon: float, radius_km: float,
                     bbox: tuple[float, float, float, float]) -> bool:
    s_lat, w_lon, n_lat, e_lon = bbox
    dlat = radius_km / 111.0
    dlon = radius_km / max(0.001, 111.0 * math.cos(math.radians(lat)))
    return (lat + dlat) >= s_lat and (lat - dlat) <= n_lat \
        and (lon + dlon) >= w_lon and (lon - dlon) <= e_lon


def _lat_lon(record: dict) -> tuple[float | None, float | None]:
    loc = record.get("CameraLocation") or {}
    lat = (record.get("DisplayLatitude")
           or loc.get("Latitude") or loc.get("latitude"))
    lon = (record.get("DisplayLongitude")
           or loc.get("Longitude") or loc.get("longitude"))
    try:
        return float(lat), float(lon)
    except (TypeError, ValueError):
        return None, None


def normalize(records: list[dict], lat: float, lon: float, radius_km: float) -> list[CameraResult]:
    dlat = radius_km / 111.0
    dlon = radius_km / max(0.001, 111.0 * math.cos(math.radians(lat)))
    now = utc_now_iso()
    out: list[CameraResult] = []
    for r in records or []:
        r_lat, r_lon = _lat_lon(r)
        if r_lat is None or r_lon is None:
            continue
        if abs(r_lat - lat) > dlat or abs(r_lon - lon) > dlon:
            continue
        if r.get("IsActive") is False:
            continue
        img = (r.get("ImageURL") or "").strip()
        if not img:
            continue
        cam_id = ("wsdot_" +
                  hashlib.sha1(f"wsdot:{r.get('CameraID')}".encode()).hexdigest()[:14])
        title = (r.get("Title") or r.get("Description") or "WSDOT Camera").strip()
        try:
            cam = CameraResult(
                id=cam_id,
                lat=r_lat,
                lon=r_lon,
                source=SRC_WSDOT,
                publication_status=PUB_OPERATOR_PUBLISHED,
                label=title,
                url=img,
                thumbnail_url=img,
                blur_required=False,
                data_age_s=0,
                fetched_at=now,
                tags={"region": str(r.get("Region") or ""),
                      "roadway": str(r.get("Roadway") or r.get("RoadName") or ""),
                      "agency": "WSDOT"},
            )
        except Exception as e:
            log.debug("dropping wsdot record: %s", e)
            continue
        out.append(cam)
    return out


async def search(lat: float, lon: float, radius_km: float) -> list[CameraResult]:
    if not _intersects_bbox(lat, lon, radius_km, WA_BBOX):
        return []
    s = get_settings()
    if not s.wsdot_api_key:
        log.debug("WSDOT skipped: no api key")
        return []
    payload = await get_json(
        ENDPOINT, params={"AccessCode": s.wsdot_api_key}, ttl_s=s.cache_ttl_dot_s
    )
    if not isinstance(payload, list):
        return []
    return normalize(payload, lat, lon, radius_km)
