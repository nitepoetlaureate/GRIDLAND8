"""Pipeline aggregator — produces snapshots of real-time entities."""
from __future__ import annotations

import asyncio
import logging

from backend.pipeline.models import Aircraft
from backend.pipeline.sources import adsb_fi
from backend.shared.http import utc_now_iso

log = logging.getLogger(__name__)


async def aircraft_snapshot(lat: float, lon: float, distance_nm: int) -> dict:
    """One snapshot of all aircraft inside the search radius."""
    aircraft: list[Aircraft] = await adsb_fi.fetch(lat, lon, distance_nm)
    return {
        "type": "aircraft",
        "ts": utc_now_iso(),
        "query": {"lat": lat, "lon": lon, "distance_nm": distance_nm},
        "count": len(aircraft),
        "items": [a.model_dump() for a in aircraft],
    }
