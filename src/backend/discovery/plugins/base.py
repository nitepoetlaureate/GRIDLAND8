"""Protocol for Python camera source plugins."""
from __future__ import annotations

from typing import Protocol

from backend.discovery.models import CameraResult


class CameraSourcePlugin(Protocol):
    async def search(self, lat: float, lon: float, radius_km: float) -> list[CameraResult]:
        ...
