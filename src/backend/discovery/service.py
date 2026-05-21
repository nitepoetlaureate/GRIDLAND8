"""Top-level discovery service. Fans out to every registered source in parallel."""
from __future__ import annotations

import asyncio
import logging
from collections import Counter

from backend.compliance.guardrails import filter_compliant
from backend.discovery.models import CameraResult, DiscoveryResponse, SourceStatus
from backend.discovery.plugins import json_cameras
from backend.discovery.sources import (
    caltrans,
    cam2,
    castlerock_511,
    livecams,
    n511ny,
    n511pa,
    nps_webcams,
    nyctmc,
    osm,
    penndot,
    wsdot,
)
from backend.shared.http import utc_now_iso

log = logging.getLogger(__name__)

_SOURCES = (
    osm.search,
    caltrans.search,
    wsdot.search,
    n511ny.search,
    livecams.search,
    nyctmc.search,
    castlerock_511.search,
    nps_webcams.search,
    penndot.search,
    n511pa.search,
    cam2.search,
    json_cameras.search,
)
_SOURCE_NAMES = (
    "osm",
    "caltrans",
    "wsdot",
    "n511ny",
    "livecams",
    "nyctmc",
    "castlerock_511",
    "nps_webcams",
    "penndot",
    "n511pa",
    "cam2",
    "plugin_json",
)


def _status_from_batch(batch: list[CameraResult] | BaseException,
                       raw_len: int) -> SourceStatus:
    if isinstance(batch, BaseException):
        return SourceStatus(count=0, status="error",
                            detail=type(batch).__name__)
    if raw_len == 0:
        return SourceStatus(count=0, status="empty")
    return SourceStatus(count=len(batch), status="ok")


async def search_area(lat: float, lon: float, radius_km: float) -> DiscoveryResponse:
    coros = [src(lat, lon, radius_km) for src in _SOURCES]
    batches = await asyncio.gather(*coros, return_exceptions=True)
    flat: list[CameraResult] = []
    sources: dict[str, SourceStatus] = {}
    for name, b in zip(_SOURCE_NAMES, batches):
        if isinstance(b, BaseException):
            log.warning("source %s raised: %s", name, b)
            sources[name] = SourceStatus(count=0, status="error",
                                         detail=type(b).__name__)
            continue
        sources[name] = _status_from_batch(b, len(b))
        flat.extend(b)

    raw_dicts = [r.model_dump() for r in flat]
    clean = filter_compliant(raw_dicts)
    counts = Counter(r["source"] for r in clean)
    for src_name, st in sources.items():
        if st.status == "ok" and counts.get(src_name, 0) == 0 and st.count > 0:
            sources[src_name] = SourceStatus(
                count=0, status="empty",
                detail="filtered_by_compliance",
            )

    return DiscoveryResponse(
        query={"lat": lat, "lon": lon, "radius_km": radius_km},
        results=[CameraResult(**r) for r in clean],
        fetched_at=utc_now_iso(),
        counts_by_source=dict(counts),
        sources=sources,
    )
