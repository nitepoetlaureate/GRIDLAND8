"""Context aggregator — gather every contextual layer in parallel."""
from __future__ import annotations

import asyncio
import logging

from backend.context.models import ContextBundle
from backend.context.sources import nws, wikipedia
from backend.shared.http import utc_now_iso

log = logging.getLogger(__name__)


async def gather(lat: float, lon: float) -> ContextBundle:
    """Fan out to every context source in parallel. Each source degrades
    independently — a failure in one does not abort the others."""
    results = await asyncio.gather(
        nws.forecast(lat, lon),
        nws.active_alerts(lat, lon),
        wikipedia.nearby(lat, lon),
        return_exceptions=True,
    )
    errors: dict[str, str] = {}
    weather, alerts, wiki = results
    if isinstance(weather, BaseException):
        errors["weather"] = str(weather)
        weather = None
    if isinstance(alerts, BaseException):
        errors["alerts"] = str(alerts)
        alerts = []
    if isinstance(wiki, BaseException):
        errors["wikipedia"] = str(wiki)
        wiki = []
    return ContextBundle(
        query={"lat": lat, "lon": lon},
        weather=weather,
        alerts=alerts or [],
        wikipedia=wiki or [],
        fetched_at=utc_now_iso(),
        errors=errors,
    )
