"""SEPTA live vehicle positions — buses, trolleys, regional rail trains.

Endpoints (no authentication, free):
  Buses/trolleys: https://www3.septa.org/hackathon/TransitViewAll/
                  returns {"routes": [{"<route_id>": [vehicle, ...]}, ...]}
  Regional rail: https://www3.septa.org/api/TrainView/index.php
                 returns list of {trainno, lat, lon, dest, line, late, ...}
"""
from __future__ import annotations

import asyncio
import logging

from backend.settings import get_settings
from backend.shared.http import get_json

log = logging.getLogger(__name__)

TRANSITVIEW = "https://www3.septa.org/hackathon/TransitViewAll/"
TRAINVIEW = "https://www3.septa.org/api/TrainView/index.php"


def _safe_float(v) -> float | None:
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def parse_transitview(payload: dict | None) -> list[dict]:
    if not isinstance(payload, dict):
        return []
    routes_field = payload.get("routes")
    if not isinstance(routes_field, list):
        return []
    out: list[dict] = []
    for entry in routes_field:
        if not isinstance(entry, dict):
            continue
        for route_id, vehicles in entry.items():
            if not isinstance(vehicles, list):
                continue
            for v in vehicles:
                if not isinstance(v, dict):
                    continue
                lat = _safe_float(v.get("lat"))
                lon = _safe_float(v.get("lng") or v.get("lon"))
                if lat is None or lon is None:
                    continue
                # Filter out schedule-only/zeroed vehicles (lat/lon at 0,0 or
                # `Offset==999` meaning unknown position).
                offset = v.get("Offset")
                try:
                    if offset is not None and int(offset) >= 998:
                        continue
                except (TypeError, ValueError):
                    pass
                vid = str(v.get("VehicleID") or v.get("label") or "")
                if not vid or vid in {"None", "0"}:
                    continue
                out.append({
                    "kind": "bus_trolley",
                    "id": f"septa_{route_id}_{vid}",
                    "lat": lat, "lon": lon,
                    "route": str(route_id),
                    "destination": v.get("destination") or "",
                    "direction": v.get("Direction") or "",
                    "heading": v.get("heading"),
                    "late_min": v.get("late"),
                    "next_stop": v.get("next_stop_name") or "",
                    "seat_availability": v.get("estimated_seat_availability") or "",
                })
    return out


def parse_trainview(payload: list | None) -> list[dict]:
    if not isinstance(payload, list):
        return []
    out: list[dict] = []
    for t in payload:
        if not isinstance(t, dict):
            continue
        lat = _safe_float(t.get("lat"))
        lon = _safe_float(t.get("lon"))
        if lat is None or lon is None:
            continue
        out.append({
            "kind": "regional_rail",
            "id": f"septa_train_{t.get('trainno')}",
            "lat": lat, "lon": lon,
            "route": str(t.get("line") or ""),
            "destination": t.get("dest") or "",
            "service": t.get("service") or "",
            "current_stop": t.get("currentstop") or "",
            "next_stop": t.get("nextstop") or "",
            "heading": _safe_float(t.get("heading")),
            "late_min": t.get("late"),
            "track": t.get("TRACK") or "",
            "consist": t.get("consist") or "",
        })
    return out


async def all_vehicles() -> tuple[list[dict], dict[str, str]]:
    """Return (vehicles, source_status). status values: ok | empty | error."""
    s = get_settings()
    tv, rr = await asyncio.gather(
        get_json(TRANSITVIEW, ttl_s=s.cache_ttl_septa_vehicles_s),
        get_json(TRAINVIEW, ttl_s=s.cache_ttl_septa_vehicles_s),
        return_exceptions=True,
    )
    out: list[dict] = []
    status: dict[str, str] = {}
    if isinstance(tv, BaseException):
        log.warning("SEPTA TransitView failed: %s", tv)
        status["transitview"] = "error"
    elif tv is None:
        log.warning("SEPTA TransitView returned no data")
        status["transitview"] = "error"
    else:
        parsed = parse_transitview(tv)
        out.extend(parsed)
        status["transitview"] = "ok" if parsed else "empty"
    if isinstance(rr, BaseException):
        log.warning("SEPTA TrainView failed: %s", rr)
        status["trainview"] = "error"
    elif rr is None:
        log.warning("SEPTA TrainView returned no data")
        status["trainview"] = "error"
    else:
        parsed = parse_trainview(rr)
        out.extend(parsed)
        status["trainview"] = "ok" if parsed else "empty"
    return out, status
