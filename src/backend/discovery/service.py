"""Top-level discovery service. Fans out to every registered source in parallel."""
from __future__ import annotations

import asyncio
import logging
from collections import Counter

from backend.compliance.guardrails import filter_compliant
from backend.discovery.models import CameraResult, DiscoveryResponse
from backend.discovery.sources import caltrans, livecams, n511ny, osm, wsdot
from backend.shared.http import utc_now_iso

log = logging.getLogger(__name__)

# Each entry is an async callable taking (lat, lon, radius_km) and returning
# list[CameraResult]. Sources that need a key but don't have one self-skip.
_SOURCES = (osm.search, caltrans.search, wsdot.search, n511ny.search, livecams.search)


async def search_area(lat: float, lon: float, radius_km: float) -> DiscoveryResponse:
    coros = [src(lat, lon, radius_km) for src in _SOURCES]
    batches = await asyncio.gather(*coros, return_exceptions=True)
    flat: list[CameraResult] = []
    for b in batches:
        if isinstance(b, BaseException):
            log.warning("source raised: %s", b)
            continue
        flat.extend(b)

    raw_dicts = [r.model_dump() for r in flat]
    clean = filter_compliant(raw_dicts)
    counts = Counter(r["source"] for r in clean)
    return DiscoveryResponse(
        query={"lat": lat, "lon": lon, "radius_km": radius_km},
        results=[CameraResult(**r) for r in clean],
        fetched_at=utc_now_iso(),
        counts_by_source=dict(counts),
    )
