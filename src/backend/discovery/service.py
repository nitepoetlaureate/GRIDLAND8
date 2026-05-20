"""Top-level discovery service. Fans out to every registered source in parallel."""
from __future__ import annotations

import asyncio
import logging
from collections import Counter

from backend.compliance.guardrails import filter_compliant
from backend.discovery.models import CameraResult, DiscoveryResponse
from backend.discovery.sources import osm
from backend.shared.http import utc_now_iso

log = logging.getLogger(__name__)


async def search_area(lat: float, lon: float, radius_km: float) -> DiscoveryResponse:
    """Query every source in parallel; gather, normalize, compliance-filter."""
    coros = [osm.search(lat, lon, radius_km)]
    results_per_source: list[list[CameraResult]] = await asyncio.gather(
        *coros, return_exceptions=False
    )
    flat: list[CameraResult] = [r for batch in results_per_source for r in batch]

    raw_dicts = [r.model_dump() for r in flat]
    clean = filter_compliant(raw_dicts)

    counts = Counter(r["source"] for r in clean)
    return DiscoveryResponse(
        query={"lat": lat, "lon": lon, "radius_km": radius_km},
        results=[CameraResult(**r) for r in clean],
        fetched_at=utc_now_iso(),
        counts_by_source=dict(counts),
    )
