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
    fetched_at: str
