"""SEPTA Metro (Market-Frankford L1 / Broad Street B1) — alerts, elevators, stations, vehicles.

SEPTA does not publish public live subway GPS or station camera streams. We combine:
  - Alerts API (rr_route_mfl, rr_route_bsl, L1, B1, …)
  - Elevator outages API (MFL/BSL lines)
  - Static station coordinates (config/septa_metro_stations.json)
  - TransitView route L1/B1 (+ owl variants) — often schedule-only (Offset 998)
  - Nearby traffic cameras from discovery (PennDOT/OSM) within ~400 m of stations/vehicles
"""
from __future__ import annotations

import asyncio
import json
import logging
import math
from pathlib import Path
from typing import Any

from backend.settings import get_settings
from backend.shared.http import get_json

log = logging.getLogger(__name__)

TRANSITVIEW_ROUTE = "https://www3.septa.org/api/TransitView/index.php"
ALERTS = "https://www3.septa.org/api/Alerts/get_alert_data.php"
ELEVATORS = "https://www3.septa.org/api/elevator/index.php"

# TransitView route_id values for subway / metro lines
METRO_ROUTE_IDS = frozenset({
    "L1", "B1", "L1_OWL", "B1_OWL", "MFL", "BSL",
})

METRO_LINE_FOR_ROUTE = {
    "L1": "MFL", "L1_OWL": "MFL", "MFL": "MFL",
    "B1": "BSL", "B1_OWL": "BSL", "BSL": "BSL",
}

ALERT_LINE_HINTS = (
    ("mfl", "MFL"), ("market", "MFL"), ("frankford", "MFL"),
    ("bsl", "BSL"), ("broad", "BSL"),
    ("l1", "MFL"), ("b1", "BSL"),
)


def _safe_float(v) -> float | None:
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _load_stations() -> dict[str, list[dict]]:
    path = Path(__file__).resolve().parents[4] / "config" / "septa_metro_stations.json"
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except OSError as e:
        log.warning("metro stations config missing: %s", e)
        return {"MFL": [], "BSL": []}
    out: dict[str, list[dict]] = {}
    for line, rows in raw.items():
        if not isinstance(rows, list):
            continue
        out[line] = [
            {
                "id": f"septa_metro_station_{r['id']}",
                "line": line,
                "name": r.get("name") or r["id"],
                "lat": float(r["lat"]),
                "lon": float(r["lon"]),
                "kind": "metro_station",
            }
            for r in rows
            if isinstance(r, dict) and r.get("lat") is not None
        ]
    return out


def _alert_line(route_id: str, route_name: str) -> str | None:
    blob = f"{route_id} {route_name}".lower()
    for hint, line in ALERT_LINE_HINTS:
        if hint in blob:
            return line
    return None


def parse_alerts(payload: list | None) -> dict[str, list[dict]]:
    by_line: dict[str, list[dict]] = {"MFL": [], "BSL": []}
    if not isinstance(payload, list):
        return by_line
    for r in payload:
        if not isinstance(r, dict):
            continue
        line = _alert_line(str(r.get("route_id") or ""), str(r.get("route_name") or ""))
        if not line:
            continue
        current = (r.get("current_message") or "").strip()
        advisory = (r.get("advisory_message") or "").strip()
        detour = (r.get("detour_message") or "").strip()
        if not current and not advisory and not detour:
            continue
        by_line[line].append({
            "route_id": r.get("route_id"),
            "route_name": r.get("route_name"),
            "current_message": current or None,
            "advisory_message": advisory or None,
            "detour_message": detour or None,
            "last_updated": r.get("last_updated"),
        })
    for line in by_line:
        by_line[line] = by_line[line][:15]
    return by_line


def parse_elevators(payload: dict | None) -> dict[str, list[dict]]:
    by_line: dict[str, list[dict]] = {"MFL": [], "BSL": []}
    if not isinstance(payload, dict):
        return by_line
    for row in payload.get("results") or []:
        if not isinstance(row, dict):
            continue
        line_name = str(row.get("line") or "")
        line = None
        if "market" in line_name.lower() or "frankford" in line_name.lower():
            line = "MFL"
        elif "broad" in line_name.lower():
            line = "BSL"
        if not line:
            continue
        by_line[line].append({
            "station": row.get("station"),
            "elevator": row.get("elevator"),
            "message": row.get("message"),
            "alternate_url": row.get("alternate_url"),
        })
    return by_line


def parse_transitview_route(route_id: str, payload: dict | None) -> list[dict]:
    """Parse one TransitView route; include schedule-only metro rows (Offset 998)."""
    if not isinstance(payload, dict):
        return []
    line = METRO_LINE_FOR_ROUTE.get(route_id)
    if not line:
        return []
    buses = payload.get("bus")
    if not isinstance(buses, list):
        return []
    out: list[dict] = []
    for v in buses:
        if not isinstance(v, dict):
            continue
        lat = _safe_float(v.get("lat"))
        lon = _safe_float(v.get("lng") or v.get("lon"))
        if lat is None or lon is None:
            continue
        offset = v.get("Offset")
        gps_live = True
        try:
            if offset is not None and int(offset) >= 998:
                gps_live = False
        except (TypeError, ValueError):
            pass
        vid = str(v.get("VehicleID") or v.get("BlockID") or v.get("trip") or "")
        if vid in {"", "None", "0"}:
            vid = str(v.get("trip") or v.get("BlockID") or "run")
        out.append({
            "kind": "metro_vehicle",
            "line": line,
            "route": route_id,
            "id": f"septa_metro_{route_id}_{vid}",
            "lat": lat,
            "lon": lon,
            "destination": v.get("destination") or "",
            "direction": v.get("Direction") or "",
            "late_min": v.get("late"),
            "next_stop": v.get("next_stop_name") or "",
            "gps_live": gps_live,
            "seat_availability": v.get("estimated_seat_availability") or "",
        })
    return out


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(min(1.0, a)))


def attach_nearby_cameras(
    targets: list[dict],
    cameras: list[dict],
    radius_km: float = 0.4,
    limit: int = 5,
) -> None:
    """Mutate targets in place with nearby_cameras[] from discovery results."""
    if not cameras:
        return
    for t in targets:
        lat, lon = t.get("lat"), t.get("lon")
        if lat is None or lon is None:
            continue
        hits: list[dict] = []
        for c in cameras:
            clat, clon = c.get("lat"), c.get("lon")
            if clat is None or clon is None:
                continue
            d = haversine_km(float(lat), float(lon), float(clat), float(clon))
            if d <= radius_km:
                hits.append({
                    "id": c.get("id"),
                    "label": c.get("label"),
                    "source": c.get("source"),
                    "lat": clat,
                    "lon": clon,
                    "distance_km": round(d, 3),
                    "thumbnail_url": c.get("thumbnail_url"),
                    "url": c.get("url"),
                    "has_feed": bool(c.get("thumbnail_url")),
                })
        hits.sort(key=lambda x: x["distance_km"])
        t["nearby_cameras"] = hits[:limit]


async def fetch_metro_vehicles() -> tuple[list[dict], dict[str, str]]:
    s = get_settings()
    statuses: dict[str, str] = {}
    out: list[dict] = []
    for route_id in ("L1", "B1", "L1_OWL", "B1_OWL"):
        try:
            payload = await get_json(
                TRANSITVIEW_ROUTE,
                params={"route": route_id},
                ttl_s=s.cache_ttl_septa_vehicles_s,
            )
            parsed = parse_transitview_route(route_id, payload)
            statuses[f"transitview_{route_id}"] = "ok" if parsed else "empty"
            out.extend(parsed)
        except Exception as e:
            log.warning("TransitView %s failed: %s", route_id, e)
            statuses[f"transitview_{route_id}"] = "error"
    return out, statuses


async def bundle(
    lat: float,
    lon: float,
    *,
    cameras: list[dict] | None = None,
) -> dict[str, Any]:
    """Full MFL/BSL metro snapshot for map + detail panels."""
    s = get_settings()
    stations_by_line = _load_stations()
    alerts_task = get_json(ALERTS, params={"req1": "all"}, ttl_s=s.cache_ttl_septa_alerts_s)
    elev_task = get_json(ELEVATORS, ttl_s=s.cache_ttl_septa_alerts_s)
    vehicles_task = fetch_metro_vehicles()

    alerts_raw, elev_raw, (vehicles, veh_sources) = await asyncio.gather(
        alerts_task, elev_task, vehicles_task,
        return_exceptions=True,
    )

    errors: dict[str, str] = {}
    if isinstance(alerts_raw, BaseException):
        errors["alerts"] = str(alerts_raw)
        alerts_by_line = {"MFL": [], "BSL": []}
    else:
        alerts_by_line = parse_alerts(alerts_raw if isinstance(alerts_raw, list) else None)

    if isinstance(elev_raw, BaseException):
        errors["elevators"] = str(elev_raw)
        elev_by_line = {"MFL": [], "BSL": []}
    else:
        elev_by_line = parse_elevators(elev_raw if isinstance(elev_raw, dict) else None)

    if isinstance(vehicles, BaseException):
        errors["vehicles"] = str(vehicles)
        vehicles = []
        veh_sources = {}

    cam_list = cameras or []
    all_stations = stations_by_line.get("MFL", []) + stations_by_line.get("BSL", [])
    attach_nearby_cameras(all_stations, cam_list, radius_km=0.45, limit=6)
    attach_nearby_cameras(vehicles, cam_list, radius_km=0.35, limit=4)

    lines = []
    for code, label in (("MFL", "Market-Frankford Line"), ("BSL", "Broad Street Line")):
        st = stations_by_line.get(code, [])
        veh = [v for v in vehicles if v.get("line") == code]
        lines.append({
            "code": code,
            "name": label,
            "stations": st,
            "vehicles": veh,
            "alerts": alerts_by_line.get(code, []),
            "elevators": elev_by_line.get(code, []),
            "station_count": len(st),
            "vehicle_count": len(veh),
            "live_gps_count": sum(1 for v in veh if v.get("gps_live")),
        })

    return {
        "lines": lines,
        "vehicles": vehicles,
        "stations": all_stations,
        "sources": veh_sources,
        "errors": errors,
        "camera_note": (
            "SEPTA does not publish public station/train video APIs. "
            "Nearby traffic cameras (PennDOT/OSM) are matched by location only."
        ),
    }
