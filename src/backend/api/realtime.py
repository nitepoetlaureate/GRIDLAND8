"""WebSocket endpoint for real-time aircraft (and future entity) broadcasts.

Wire protocol — each frame is a JSON envelope:
  {"type": "aircraft", "ts": "...", "query": {...}, "count": N, "items": [...]}

Client sends an initial JSON message to subscribe:
  {"lat": 39.95, "lon": -75.16, "distance_nm": 250}
"""
from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from backend.pipeline.service import aircraft_snapshot
from backend.settings import get_settings

log = logging.getLogger(__name__)
router = APIRouter()


class _Hub:
    """Tracks active clients and enforces max_ws_clients."""

    def __init__(self, limit: int) -> None:
        self._clients: set[WebSocket] = set()
        self._limit = limit

    async def accept(self, ws: WebSocket) -> bool:
        if len(self._clients) >= self._limit:
            await ws.close(code=1013, reason="server at capacity")
            return False
        await ws.accept()
        self._clients.add(ws)
        return True

    def drop(self, ws: WebSocket) -> None:
        self._clients.discard(ws)

    @property
    def size(self) -> int:
        return len(self._clients)


_hub: _Hub | None = None


def get_hub() -> _Hub:
    global _hub
    if _hub is None:
        _hub = _Hub(get_settings().max_ws_clients)
    return _hub


async def _stream_aircraft(ws: WebSocket, lat: float, lon: float, distance_nm: int) -> None:
    interval = get_settings().realtime_poll_interval_s
    while True:
        try:
            snap = await aircraft_snapshot(lat, lon, distance_nm)
            await ws.send_text(json.dumps(snap))
        except (WebSocketDisconnect, RuntimeError):
            return
        except Exception as e:  # noqa: BLE001 - log and continue
            log.exception("snapshot loop error: %s", e)
        await asyncio.sleep(interval)


@router.websocket("/ws/live")
async def ws_live(ws: WebSocket) -> None:
    hub = get_hub()
    if not await hub.accept(ws):
        return
    try:
        raw = await ws.receive_text()
        try:
            sub: dict[str, Any] = json.loads(raw)
        except json.JSONDecodeError:
            await ws.send_text(json.dumps({"error": "expected JSON subscription"}))
            await ws.close(code=1003)
            return
        s = get_settings()
        lat = float(sub.get("lat", s.default_lat))
        lon = float(sub.get("lon", s.default_lon))
        distance_nm = int(sub.get("distance_nm", s.realtime_aircraft_radius_nm))
        await _stream_aircraft(ws, lat, lon, distance_nm)
    except WebSocketDisconnect:
        pass
    finally:
        hub.drop(ws)
