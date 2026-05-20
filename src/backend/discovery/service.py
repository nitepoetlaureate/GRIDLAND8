"""Top-level discovery service. Fans out to every registered source in parallel."""
from __future__ import annotations

import asyncio
import logging
from collections import Counter

from backend.compliance.guardrails import filter_compliant
from backend.discovery.models import CameraResult, DiscoveryResponse
from backend.discovery.sources import (
    caltrans,
    castlerock_511,
    livecams,
    n511ny,
    nps_webcams,
    nyctmc,
    osm,
    wsdot,
)
from backend.shared.http import utc_now_iso

# #region agent log
import json as _json
import time as _time
from pathlib import Path as _Path
_DBG = _Path("/Users/michaelraftery/GRIDLAND8/.cursor/debug-716b73.log")


def _dbg(location: str, message: str, data: dict, hypothesis_id: str) -> None:
    try:
        _DBG.parent.mkdir(parents=True, exist_ok=True)
        with _DBG.open("a") as f:
            f.write(_json.dumps({
                "sessionId": "716b73",
                "runId": "discovery",
                "hypothesisId": hypothesis_id,
                "location": location,
                "message": message,
                "data": data,
                "timestamp": int(_time.time() * 1000),
            }) + "\n")
    except Exception:
        pass
# #endregion

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
)


async def search_area(lat: float, lon: float, radius_km: float) -> DiscoveryResponse:
    coros = [src(lat, lon, radius_km) for src in _SOURCES]
    batches = await asyncio.gather(*coros, return_exceptions=True)
    flat: list[CameraResult] = []
    raw_counts: dict[str, int | str] = {}
    for name, b in zip(_SOURCE_NAMES, batches):
        if isinstance(b, BaseException):
            log.warning("source %s raised: %s", name, b)
            raw_counts[name] = f"error: {type(b).__name__}"
            continue
        raw_counts[name] = len(b)
        flat.extend(b)

    raw_dicts = [r.model_dump() for r in flat]
    clean = filter_compliant(raw_dicts)
    counts = Counter(r["source"] for r in clean)

    # #region agent log
    _dbg(
        "discovery/service.py:search_area",
        "search_area finished",
        {
            "query": {"lat": lat, "lon": lon, "radius_km": radius_km},
            "raw_counts_pre_compliance": raw_counts,
            "compliant_counts": dict(counts),
            "raw_total": len(flat),
            "compliant_total": len(clean),
            "dropped_by_compliance": len(flat) - len(clean),
        },
        "H2",
    )
    # #endregion

    return DiscoveryResponse(
        query={"lat": lat, "lon": lon, "radius_km": radius_km},
        results=[CameraResult(**r) for r in clean],
        fetched_at=utc_now_iso(),
        counts_by_source=dict(counts),
    )
