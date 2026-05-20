"""Caltrans (California DOT) CCTV — per-district JSON, no authentication.

Endpoint pattern (one file per district 1-12):
  https://cwwp2.dot.ca.gov/data/d{N}/cctv/cctvStatusD{N}.json

Each record:
  {"cctv": {"index": "...", "recordTimestamp": {...},
            "location": {"district": "..", "locationName": "..",
                         "nearbyPlace": "..", "longitude": "-120.1",
                         "latitude": "37.8", "elevation": "..", "direction": ".."},
            "inService": "true",
            "imageData": {"static": {...}, "streamingVideoURL": "https://..."}}}
"""
from __future__ import annotations

import asyncio
import hashlib
import logging

from backend.discovery.models import CameraResult
from backend.settings import get_settings
from backend.shared.constants import PUB_OPERATOR_PUBLISHED, SRC_CALTRANS
from backend.shared.http import get_json, utc_now_iso

log = logging.getLogger(__name__)

ENDPOINT = "https://cwwp2.dot.ca.gov/data/d{district}/cctv/cctvStatusD{district}.json"


def _in_bbox(lat: float, lon: float, c_lat: float, c_lon: float,
             dlat: float, dlon: float) -> bool:
    return abs(lat - c_lat) <= dlat and abs(lon - c_lon) <= dlon


def normalize(payload: dict, lat: float, lon: float, radius_km: float) -> list[CameraResult]:
    """Filter records inside the search circle (bounding box approx) and normalize."""
    import math

    dlat = radius_km / 111.0
    dlon = radius_km / max(0.001, 111.0 * math.cos(math.radians(lat)))
    now = utc_now_iso()
    results: list[CameraResult] = []
    items = (payload or {}).get("data") or []
    for entry in items:
        c = entry.get("cctv") or entry
        loc = c.get("location") or {}
        try:
            r_lat = float(loc.get("latitude"))
            r_lon = float(loc.get("longitude"))
        except (TypeError, ValueError):
            continue
        if not _in_bbox(r_lat, r_lon, lat, lon, dlat, dlon):
            continue
        in_service = str(c.get("inService", "false")).lower() == "true"
        if not in_service:
            continue
        img = c.get("imageData") or {}
        stream = (img.get("streamingVideoURL") or "").strip()
        static = ((img.get("static") or {}).get("currentImageURL") or "").strip()
        url = stream or static or ""
        unique = f"caltrans:{loc.get('district')}:{c.get('index')}:{r_lat:.5f},{r_lon:.5f}"
        cam_id = "caltrans_" + hashlib.sha1(unique.encode()).hexdigest()[:14]
        label_parts = [
            loc.get("locationName") or "",
            loc.get("nearbyPlace") or "",
            (loc.get("direction") or "").upper(),
        ]
        label = " · ".join([p for p in label_parts if p]) or "Caltrans CCTV"
        try:
            cam = CameraResult(
                id=cam_id,
                lat=r_lat,
                lon=r_lon,
                source=SRC_CALTRANS,
                publication_status=PUB_OPERATOR_PUBLISHED,
                label=label,
                url=url,
                thumbnail_url=static or None,
                blur_required=False,  # operator-published traffic cam
                data_age_s=0,
                fetched_at=now,
                tags={"district": str(loc.get("district") or ""),
                      "route": str(loc.get("route") or ""),
                      "agency": "Caltrans"},
            )
        except Exception as e:
            log.debug("dropping caltrans record: %s", e)
            continue
        results.append(cam)
    return results


async def search(lat: float, lon: float, radius_km: float) -> list[CameraResult]:
    s = get_settings()
    ttl = s.cache_ttl_dot_s
    coros = [
        get_json(ENDPOINT.format(district=d), ttl_s=ttl)
        for d in s.caltrans_districts
    ]
    payloads = await asyncio.gather(*coros, return_exceptions=True)
    out: list[CameraResult] = []
    for p in payloads:
        if isinstance(p, BaseException) or not isinstance(p, dict):
            continue
        out.extend(normalize(p, lat, lon, radius_km))
    return out
