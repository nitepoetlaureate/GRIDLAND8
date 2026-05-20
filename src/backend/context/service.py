"""Context aggregator — gather every contextual layer in parallel."""
from __future__ import annotations

import asyncio
import logging

from backend.context.models import ContextBundle
from backend.context.sources import (
    aviation,
    firms,
    nws,
    openaq,
    opendataphilly,
    philly311,
    septa_alerts,
    septa_detours,
    usgs,
    usgs_water,
    wikipedia,
)
from backend.pipeline.sources import indego
from backend.shared.http import utc_now_iso

log = logging.getLogger(__name__)


async def gather(lat: float, lon: float) -> ContextBundle:
    """Fan out to every context source in parallel. Each source degrades
    independently — a failure in one does not abort the others."""
    results = await asyncio.gather(
        nws.forecast(lat, lon),
        nws.active_alerts(lat, lon),
        wikipedia.nearby(lat, lon),
        usgs.recent_quakes(lat, lon),
        firms.active_fires(lat, lon),
        openaq.nearby_aq(lat, lon),
        aviation.metars(lat, lon),
        septa_alerts.near(lat, lon),
        philly311.recent(lat, lon),
        usgs_water.gauges_near(lat, lon),
        opendataphilly.gather(lat, lon, radius_km=25.0),
        septa_detours.near(lat, lon),
        indego.stations_near(lat, lon, radius_km=15.0),
        return_exceptions=True,
    )
    errors: dict[str, str] = {}
    (weather, alerts, wiki, quakes, fires, aq, metars_,
     transit_alerts, service_requests, water_gauges, odp_bundle,
     detours, indego_stations) = results
    if isinstance(weather, BaseException):
        errors["weather"] = str(weather); weather = None
    if isinstance(alerts, BaseException):
        errors["alerts"] = str(alerts); alerts = []
    if isinstance(wiki, BaseException):
        errors["wikipedia"] = str(wiki); wiki = []
    if isinstance(quakes, BaseException):
        errors["quakes"] = str(quakes); quakes = []
    if isinstance(fires, BaseException):
        errors["fires"] = str(fires); fires = []
    if isinstance(aq, BaseException):
        errors["air_quality"] = str(aq); aq = []
    if isinstance(metars_, BaseException):
        errors["metars"] = str(metars_); metars_ = []
    if isinstance(transit_alerts, BaseException):
        errors["transit_alerts"] = str(transit_alerts); transit_alerts = []
    if isinstance(service_requests, BaseException):
        errors["service_requests"] = str(service_requests); service_requests = []
    if isinstance(water_gauges, BaseException):
        errors["water_gauges"] = str(water_gauges); water_gauges = []
    if isinstance(odp_bundle, BaseException):
        errors["opendataphilly"] = str(odp_bundle); odp_bundle = None
    if isinstance(detours, BaseException):
        errors["septa_detours"] = str(detours); detours = []
    if isinstance(indego_stations, BaseException):
        errors["indego_stations"] = str(indego_stations); indego_stations = []
    return ContextBundle(
        query={"lat": lat, "lon": lon},
        weather=weather,
        alerts=alerts or [],
        wikipedia=wiki or [],
        quakes=quakes or [],
        fires=fires or [],
        air_quality=aq or [],
        metars=metars_ or [],
        transit_alerts=transit_alerts or [],
        septa_detours=detours or [],
        indego_stations=indego_stations or [],
        service_requests=service_requests or [],
        water_gauges=water_gauges or [],
        opendataphilly=odp_bundle if isinstance(odp_bundle, dict) else None,
        fetched_at=utc_now_iso(),
        errors=errors,
    )
