"""NWS (US National Weather Service). No authentication required.

Flow:
  1) GET /points/{lat,lon}  → returns forecast + observation station URLs.
  2) GET .properties.forecast  → forecast periods.
  3) GET /alerts/active?point=lat,lon  → active alerts.

Coverage is US-only. Outside the US, the points endpoint returns 404 and we
emit nothing.
"""
from __future__ import annotations

import logging

from backend.shared.http import get_json

log = logging.getLogger(__name__)

NWS_POINTS = "https://api.weather.gov/points/{lat},{lon}"
NWS_ALERTS = "https://api.weather.gov/alerts/active"


async def forecast(lat: float, lon: float) -> dict | None:
    point = await get_json(NWS_POINTS.format(lat=lat, lon=lon))
    if not point or not isinstance(point, dict):
        return None
    forecast_url = (point.get("properties") or {}).get("forecast")
    if not forecast_url:
        return None
    data = await get_json(forecast_url)
    if not data or not isinstance(data, dict):
        return None
    periods = (data.get("properties") or {}).get("periods") or []
    if not periods:
        return None
    return {
        "now": periods[0].get("shortForecast"),
        "temperature_f": periods[0].get("temperature"),
        "wind": periods[0].get("windSpeed"),
        "detailed": periods[0].get("detailedForecast"),
        "next_24h": [
            {
                "name": p.get("name"),
                "temperature_f": p.get("temperature"),
                "short": p.get("shortForecast"),
            }
            for p in periods[:4]
        ],
    }


async def active_alerts(lat: float, lon: float) -> list[dict]:
    data = await get_json(NWS_ALERTS, params={"point": f"{lat},{lon}"})
    if not data or not isinstance(data, dict):
        return []
    features = data.get("features") or []
    out: list[dict] = []
    for f in features:
        props = f.get("properties") or {}
        out.append({
            "id": f.get("id"),
            "event": props.get("event"),
            "severity": props.get("severity"),
            "urgency": props.get("urgency"),
            "headline": props.get("headline"),
            "effective": props.get("effective"),
            "expires": props.get("expires"),
        })
    return out
