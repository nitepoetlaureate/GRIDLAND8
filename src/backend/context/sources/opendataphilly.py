"""OpenDataPhilly Carto layers — all verified public SQL tables (no API key).

Tables integrated (phl.carto.com):
  public_cases_fc          → via philly311.py (311 service requests)
  incidents_part1_part2    → crime_incidents
  shootings                → shootings
  snow_emergency_routes    → snow_routes (citywide when in Philly)
  ppr_properties           → parks
  polling_places           → polling_places
  zoning_overlays          → zoning_overlays
  red_light_camera_locations → red_light_cameras (no reliable geometry)
  pwd_parcels              → parcel_count only (privacy: no owner rows)
  police_districts         → police_district (point-in-polygon)
"""
from __future__ import annotations

import asyncio
import logging

from backend.shared import opendataphilly as odp

log = logging.getLogger(__name__)


async def _crime(lat: float, lon: float, radius_km: float, *, days: int = 7,
                 limit: int = 40) -> list[dict]:
    xy = odp.xy_filter("i", lat, lon, radius_km)
    sql = (
        "SELECT cartodb_id, dispatch_date_time, text_general_code, ucr_general, "
        "location_block, point_x, point_y "
        "FROM incidents_part1_part2 i "
        f"WHERE {xy} "
        f"AND dispatch_date_time > now() - interval '{int(days)} days' "
        "ORDER BY dispatch_date_time DESC "
        f"LIMIT {int(limit)}"
    )
    rows = await odp.carto_query(sql)
    out: list[dict] = []
    for r in rows:
        try:
            out.append({
                "id": r.get("cartodb_id"),
                "at": r.get("dispatch_date_time"),
                "type": r.get("text_general_code"),
                "ucr": r.get("ucr_general"),
                "block": r.get("location_block"),
                "lat": float(r["point_y"]),
                "lon": float(r["point_x"]),
            })
        except (TypeError, ValueError, KeyError):
            continue
    return out


async def _shootings(lat: float, lon: float, radius_km: float, *, days: int = 365,
                     limit: int = 25) -> list[dict]:
    xy = odp.xy_filter("s", lat, lon, radius_km)
    sql = (
        "SELECT cartodb_id, date_, location, code, point_x, point_y "
        "FROM shootings s "
        f"WHERE {xy} "
        f"AND date_ > now() - interval '{int(days)} days' "
        "ORDER BY date_ DESC "
        f"LIMIT {int(limit)}"
    )
    rows = await odp.carto_query(sql)
    out: list[dict] = []
    for r in rows:
        try:
            out.append({
                "id": r.get("cartodb_id"),
                "at": r.get("date_"),
                "location": r.get("location"),
                "code": r.get("code"),
                "lat": float(r["point_y"]),
                "lon": float(r["point_x"]),
            })
        except (TypeError, ValueError, KeyError):
            continue
    return out


async def _snow_routes() -> list[dict]:
    sql = "SELECT _from, _to, street FROM snow_emergency_routes ORDER BY street"
    rows = await odp.carto_query(sql)
    return [{"from": r.get("_from"), "to": r.get("_to"), "street": r.get("street")}
            for r in rows if isinstance(r, dict)]


async def _parks(lat: float, lon: float, radius_km: float,
                 limit: int = 30) -> list[dict]:
    env = odp.geom_envelope_filter(lat, lon, radius_km)
    sql = (
        "SELECT cartodb_id, "
        "COALESCE(park_name, official_name, label) AS park_name, "
        "address_911, acreage, "
        "ST_Y(ST_Centroid(the_geom)) AS lat, ST_X(ST_Centroid(the_geom)) AS lon "
        "FROM ppr_properties "
        f"WHERE {env} "
        f"LIMIT {int(limit)}"
    )
    rows = await odp.carto_query(sql)
    out: list[dict] = []
    for r in rows:
        try:
            lat_v = float(r.get("lat"))
            lon_v = float(r.get("lon"))
        except (TypeError, ValueError):
            continue
        out.append({
            "id": r.get("cartodb_id"),
            "name": r.get("park_name"),
            "address": r.get("address_911"),
            "acreage": r.get("acreage"),
            "lat": lat_v,
            "lon": lon_v,
        })
    return out


async def _polling(lat: float, lon: float, radius_km: float,
                   limit: int = 20) -> list[dict]:
    env = odp.geom_envelope_filter(lat, lon, radius_km)
    sql = (
        "SELECT cartodb_id, placename, street_address, ward, division, "
        "ST_Y(ST_Centroid(the_geom)) AS lat, ST_X(ST_Centroid(the_geom)) AS lon "
        "FROM polling_places "
        f"WHERE {env} "
        f"LIMIT {int(limit)}"
    )
    rows = await odp.carto_query(sql)
    out: list[dict] = []
    for r in rows:
        try:
            out.append({
                "id": r.get("cartodb_id"),
                "name": r.get("placename"),
                "address": r.get("street_address"),
                "ward": r.get("ward"),
                "lat": float(r["lat"]),
                "lon": float(r["lon"]),
            })
        except (TypeError, ValueError, KeyError):
            continue
    return out


async def _zoning(lat: float, lon: float, radius_km: float,
                  limit: int = 15) -> list[dict]:
    env = odp.geom_envelope_filter(lat, lon, radius_km)
    sql = (
        "SELECT cartodb_id, overlay_name, type, code_section, "
        "ST_Y(ST_Centroid(the_geom)) AS lat, ST_X(ST_Centroid(the_geom)) AS lon "
        "FROM zoning_overlays "
        f"WHERE {env} "
        f"LIMIT {int(limit)}"
    )
    rows = await odp.carto_query(sql)
    out: list[dict] = []
    for r in rows:
        try:
            out.append({
                "id": r.get("cartodb_id"),
                "name": (r.get("overlay_name") or "")[:120],
                "type": r.get("type"),
                "code_section": r.get("code_section"),
                "lat": float(r["lat"]),
                "lon": float(r["lon"]),
            })
        except (TypeError, ValueError, KeyError):
            continue
    return out


async def _red_light_cameras() -> list[dict]:
    """PPA red-light enforcement sites (geometry often null — text locations only)."""
    sql = (
        "SELECT site_id, intersection, site_location, warnings, citations, sensor_type "
        "FROM red_light_camera_locations ORDER BY intersection"
    )
    rows = await odp.carto_query(sql)
    return [{
        "site_id": r.get("site_id"),
        "intersection": r.get("intersection"),
        "location": r.get("site_location"),
        "warnings": r.get("warnings"),
        "citations": r.get("citations"),
        "sensor_type": r.get("sensor_type"),
    } for r in rows if isinstance(r, dict)]


async def _police_district(lat: float, lon: float) -> dict | None:
    sql = (
        "SELECT dist_num, district_, location, phone "
        "FROM police_districts "
        f"WHERE ST_Contains(the_geom, ST_SetSRID(ST_Point({lon}, {lat}), 4326)) "
        "LIMIT 1"
    )
    rows = await odp.carto_query(sql)
    if not rows:
        return None
    r = rows[0]
    return {
        "district_num": r.get("dist_num"),
        "name": r.get("district_"),
        "location": r.get("location"),
        "phone": r.get("phone"),
    }


async def _parcel_count(lat: float, lon: float, radius_km: float) -> int:
    env = odp.geom_envelope_filter(lat, lon, radius_km)
    sql = f"SELECT count(*) AS n FROM pwd_parcels WHERE {env}"
    rows = await odp.carto_query(sql)
    try:
        return int(rows[0]["n"])
    except (IndexError, KeyError, TypeError, ValueError):
        return 0


async def gather(lat: float, lon: float, radius_km: float = 2.0) -> dict:
    """Fetch every OpenDataPhilly Carto layer for a Philly-area point."""
    if not odp.within_philly(lat, lon):
        return {"skipped": "outside_philly_bbox", "layers": {}}

    r_km = max(0.5, min(radius_km, 50.0))
    tasks = {
        "crime_incidents": _crime(lat, lon, r_km),
        "shootings": _shootings(lat, lon, r_km),
        "snow_routes": _snow_routes(),
        "parks": _parks(lat, lon, r_km),
        "polling_places": _polling(lat, lon, r_km),
        "zoning_overlays": _zoning(lat, lon, r_km),
        "red_light_cameras": _red_light_cameras(),
        "parcel_count": _parcel_count(lat, lon, r_km),
        "police_district": _police_district(lat, lon),
    }
    names = list(tasks.keys())
    results = await asyncio.gather(*tasks.values(), return_exceptions=True)
    layers: dict = {}
    errors: dict[str, str] = {}
    for name, res in zip(names, results):
        if isinstance(res, BaseException):
            log.warning("ODP layer %s failed: %s", name, res)
            errors[name] = str(res)
            layers[name] = (
                [] if name not in ("parcel_count", "police_district")
                else (0 if name == "parcel_count" else None)
            )
        else:
            layers[name] = res
    return {
        "source": "opendataphilly",
        "endpoint": odp.CARTO_SQL,
        "radius_km": r_km,
        "layers": layers,
        "errors": errors,
    }
