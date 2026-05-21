"""Real-time entity models."""
from __future__ import annotations

from pydantic import BaseModel, Field


class Aircraft(BaseModel):
    icao24: str
    callsign: str | None = None
    lat: float = Field(..., ge=-90.0, le=90.0)
    lon: float = Field(..., ge=-180.0, le=180.0)
    alt_m: float | None = None
    track_deg: float | None = None
    velocity_ms: float | None = None
    on_ground: bool = False
    origin_country: str | None = None
    fetched_at: str
    # Enriched from ADS-B.fi (no extra API key required)
    aircraft_type: str | None = None
    type_desc: str | None = None
    registration: str | None = None
    operator: str | None = None
    squawk: str | None = None
    category: str | None = None
    vertical_rate_fpm: float | None = None
    nav_altitude_mcp_ft: float | None = None
    distance_nm: float | None = None
    # Flight-plan airports — populate when route API is wired (see docs/TODO.md)
    origin_airport: str | None = None
    destination_airport: str | None = None
