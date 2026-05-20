"""PennDOT traffic camera locations via ArcGIS (no API key).

Layer: gis.penndot.pa.gov .../MapServer/14
Live JPEG/HLS requires 511PA API key (separate adapter when N511PA_API_KEY is set).
"""
from __future__ import annotations

import hashlib
import logging
import math

from backend.discovery.models import CameraResult
from backend.settings import get_settings
from backend.shared.constants import PUB_OPERATOR_PUBLISHED, SRC_PENNDOT
from backend.shared.http import get_json, utc_now_iso

log = logging.getLogger(__name__)

ENDPOINT = (
    "https://gis.penndot.pa.gov/gis/rest/services/paprojects/paprojects/MapServer/14/query"
)

PA_BBOX = (39.5, -80.5, 42.5, -74.0)


def _intersects_bbox(lat: float, lon: float, radius_km: float,
                     bbox: tuple[float, float, float, float]) -> bool:
    s_lat, w_lon, n_lat, e_lon = bbox
    dlat = radius_km / 111.0
    dlon = radius_km / max(0.001, 111.0 * math.cos(math.radians(lat)))
    return (lat + dlat) >= s_lat and (lat - dlat) <= n_lat \
        and (lon + dlon) >= w_lon and (lon - dlon) <= e_lon


def normalize(features: list[dict], lat: float, lon: float,
              radius_km: float) -> list[CameraResult]:
    dlat = radius_km / 111.0
    dlon = radius_km / max(0.001, 111.0 * math.cos(math.radians(lat)))
    now = utc_now_iso()
    out: list[CameraResult] = []
    for f in features or []:
        a = f.get("attributes") or {}
        try:
            r_lat = float(a.get("LATITUDE"))
            r_lon = float(a.get("LONGITUDE"))
        except (TypeError, ValueError):
            continue
        if math.isnan(r_lat) or math.isnan(r_lon) or (r_lat == 0 and r_lon == 0):
            continue
        if abs(r_lat - lat) > dlat or abs(r_lon - lon) > dlon:
            continue
        if str(a.get("STATUS_NAME", "")).upper() != "EXISTING":
            continue
        sw_id = str(a.get("STATEWIDE_ID") or "")
        label = (a.get("LOCATION_DESC") or "PennDOT camera").strip()
        unique = f"penndot:{sw_id}:{r_lat:.5f},{r_lon:.5f}"
        cam_id = "penndot_" + hashlib.sha1(unique.encode()).hexdigest()[:12]
        page = f"https://www.511pa.com/map/Cctv/{sw_id}" if sw_id else "https://www.511pa.com/"
        try:
            cam = CameraResult(
                id=cam_id,
                lat=r_lat,
                lon=r_lon,
                source=SRC_PENNDOT,
                publication_status=PUB_OPERATOR_PUBLISHED,
                label=label,
                url=page,
                thumbnail_url=None,
                blur_required=False,
                data_age_s=0,
                fetched_at=now,
                tags={
                    "agency": "PennDOT",
                    "statewide_id": sw_id,
                    "county": str(a.get("CTY_NAME") or ""),
                    "live_stream": "requires_511pa_key",
                },
            )
        except Exception as e:
            log.debug("drop penndot: %s", e)
            continue
        out.append(cam)
    return out


async def search(lat: float, lon: float, radius_km: float) -> list[CameraResult]:
    if not _intersects_bbox(lat, lon, radius_km, PA_BBOX):
        return []
    s = get_settings()
    params = {
        "where": "STATUS_NAME='EXISTING' AND LATITUDE IS NOT NULL",
        "outFields": "STATEWIDE_ID,LOCATION_DESC,LATITUDE,LONGITUDE,STATUS_NAME,CTY_NAME",
        "returnGeometry": "false",
        "f": "json",
        "geometry": f"{lon},{lat}",
        "geometryType": "esriGeometryPoint",
        "inSR": "4326",
        "spatialRel": "esriSpatialRelIntersects",
        "distance": min(int(radius_km * 1000), 100000),
        "units": "esriSRUnit_Meter",
    }
    payload = await get_json(ENDPOINT, params=params, ttl_s=s.cache_ttl_penndot_s)
    if not isinstance(payload, dict):
        return []
    return normalize(payload.get("features") or [], lat, lon, radius_km)
