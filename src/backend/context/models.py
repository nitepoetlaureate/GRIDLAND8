"""Context bundle returned by /api/context."""
from __future__ import annotations

from pydantic import BaseModel


class ContextBundle(BaseModel):
    query: dict
    weather: dict | None = None
    alerts: list[dict] = []
    wikipedia: list[dict] = []
    quakes: list[dict] = []
    fires: list[dict] = []
    air_quality: list[dict] = []
    metars: list[dict] = []
    transit_alerts: list[dict] = []
    service_requests: list[dict] = []
    water_gauges: list[dict] = []
    fetched_at: str
    errors: dict[str, str] = {}
