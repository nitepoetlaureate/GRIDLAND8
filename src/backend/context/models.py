"""Context bundle returned by /api/context."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class ContextBundle(BaseModel):
    query: dict
    weather: dict | None = None
    alerts: list[dict] = []
    wikipedia: list[dict] = []
    fetched_at: str
    errors: dict[str, str] = {}
