"""ADSB.fi — community ADS-B aggregator, no auth, JSON over HTTPS.

Docs: https://github.com/adsbfi/opendata
Endpoint shape used here:
  https://opendata.adsb.fi/api/v2/lat/{lat}/lon/{lon}/dist/{nm}
Returns: { "ac": [ { "hex": "...", "lat": ..., "lon": ..., ... }, ... ], ... }
"""
from __future__ import annotations

import logging

from backend.pipeline.models import Aircraft
from backend.shared.http import get_json, utc_now_iso

log = logging.getLogger(__name__)

ADSB_FI_URL = "https://opendata.adsb.fi/api/v2/lat/{lat}/lon/{lon}/dist/{nm}"

# 1 knot = 0.514444 m/s; 1 foot = 0.3048 m
_KT_TO_MS = 0.514444
_FT_TO_M = 0.3048


def normalize(records: list[dict]) -> list[Aircraft]:
    now = utc_now_iso()
    out: list[Aircraft] = []
    for r in records:
        lat = r.get("lat")
        lon = r.get("lon")
        if lat is None or lon is None:
            continue
        alt_ft = r.get("alt_baro")
        if alt_ft == "ground":
            alt_m = 0.0
            on_ground = True
        else:
            try:
                alt_m = float(alt_ft) * _FT_TO_M if alt_ft is not None else None
            except (TypeError, ValueError):
                alt_m = None
            on_ground = False
        gs_kt = r.get("gs")
        try:
            velocity_ms = float(gs_kt) * _KT_TO_MS if gs_kt is not None else None
        except (TypeError, ValueError):
            velocity_ms = None
        try:
            ac = Aircraft(
                icao24=str(r.get("hex", "")).lower(),
                callsign=(r.get("flight") or "").strip() or None,
                lat=float(lat),
                lon=float(lon),
                alt_m=alt_m,
                track_deg=float(r["track"]) if r.get("track") is not None else None,
                velocity_ms=velocity_ms,
                on_ground=on_ground,
                fetched_at=now,
            )
        except Exception as e:
            log.debug("dropping invalid aircraft record: %s", e)
            continue
        if ac.icao24:
            out.append(ac)
    return out


async def fetch(lat: float, lon: float, distance_nm: int = 250) -> list[Aircraft]:
    url = ADSB_FI_URL.format(lat=lat, lon=lon, nm=distance_nm)
    data = await get_json(url)
    if not data or not isinstance(data, dict):
        return []
    records = data.get("ac") or []
    return normalize(records)
