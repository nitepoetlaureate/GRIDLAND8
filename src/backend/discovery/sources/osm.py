"""OSM Overpass — surveillance camera nodes inside a bounding box.

No authentication required. Endpoint is rate-limited per IP; the client falls
back to alternate Overpass mirrors if the primary is overloaded.
"""
from __future__ import annotations

import hashlib
import logging
from typing import Iterable

from backend.discovery.models import CameraResult
from backend.settings import get_settings
from backend.shared.constants import PUB_DIRECTORY_LISTED, SRC_OSM
from backend.shared.http import post_json, utc_now_iso

log = logging.getLogger(__name__)

OVERPASS_ENDPOINTS = (
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.openstreetmap.fr/api/interpreter",
)

# bbox order in Overpass: south,west,north,east
_QUERY_TMPL = """[out:json][timeout:25];
(
  node["man_made"="surveillance"]({bbox});
  node["surveillance"]({bbox});
  node["camera:type"]({bbox});
);
out body;
"""


def _bbox_from(lat: float, lon: float, radius_km: float) -> str:
    """Approximate bounding box in lat/lon degrees from (lat, lon, radius_km)."""
    dlat = radius_km / 111.0
    # 111 km / degree latitude; degree longitude varies by cos(lat)
    import math
    dlon = radius_km / max(0.001, 111.0 * math.cos(math.radians(lat)))
    return f"{lat - dlat},{lon - dlon},{lat + dlat},{lon + dlon}"


async def fetch_overpass(lat: float, lon: float, radius_km: float) -> list[dict]:
    bbox = _bbox_from(lat, lon, radius_km)
    body = _QUERY_TMPL.format(bbox=bbox)
    headers = {"Content-Type": "text/plain; charset=utf-8"}
    ttl = get_settings().cache_ttl_overpass_s
    for url in OVERPASS_ENDPOINTS:
        data = await post_json(url, data=body, headers=headers, ttl_s=ttl)
        if data and isinstance(data, dict) and "elements" in data:
            return data["elements"]
        log.warning("Overpass mirror %s returned no data, trying next", url)
    return []


def _label_from_tags(tags: dict) -> str:
    return (
        tags.get("name")
        or tags.get("operator")
        or tags.get("surveillance:type")
        or tags.get("camera:type")
        or "OSM surveillance camera"
    )


def normalize(elements: Iterable[dict]) -> list[CameraResult]:
    """Convert raw Overpass `node` elements to CameraResult objects."""
    now = utc_now_iso()
    out: list[CameraResult] = []
    for el in elements:
        if el.get("type") != "node":
            continue
        lat, lon = el.get("lat"), el.get("lon")
        if lat is None or lon is None:
            continue
        tags = el.get("tags") or {}
        node_id = el.get("id")
        url = tags.get("contact:webcam") or tags.get("webcam") or tags.get("url") or ""
        stream = str(tags.get("camera:stream") or tags.get("surveillance:stream") or "")
        thumb = stream if stream.startswith("http") else None
        if url and "@" in url.split("://", 1)[-1].split("/", 1)[0]:
            url = ""
        unique = f"osm:{node_id}" if node_id is not None else f"osm:{lat:.5f},{lon:.5f}"
        result_id = hashlib.sha1(unique.encode()).hexdigest()[:16]
        try:
            cam = CameraResult(
                id=f"osm_{result_id}",
                lat=float(lat),
                lon=float(lon),
                source=SRC_OSM,
                publication_status=PUB_DIRECTORY_LISTED,
                label=_label_from_tags(tags),
                url=url,
                thumbnail_url=thumb,
                blur_required=True,
                data_age_s=0,
                fetched_at=now,
                tags={k: str(v) for k, v in tags.items() if k in
                      ("operator", "surveillance:type", "camera:type", "name",
                       "camera:stream", "surveillance:stream")},
            )
        except Exception as e:  # pydantic validation error
            log.debug("dropping invalid OSM node %s: %s", node_id, e)
            continue
        out.append(cam)
    return out


async def search(lat: float, lon: float, radius_km: float) -> list[CameraResult]:
    elements = await fetch_overpass(lat, lon, radius_km)
    return normalize(elements)
