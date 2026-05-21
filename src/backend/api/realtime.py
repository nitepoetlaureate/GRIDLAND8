"""WebSocket endpoint for real-time aircraft and optional SEPTA snapshots."""
from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from backend.pipeline.diff import AircraftDiffer
from backend.pipeline.service import aircraft_snapshot
from backend.pipeline.sources import septa_vehicles
from backend.settings import get_settings
from backend.shared.geo import in_bbox

log = logging.getLogger(__name__)
router = APIRouter()


class _Hub:
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


def _apply_sub(state: dict[str, Any], sub: dict[str, Any]) -> None:
    state["lat"] = float(sub.get("lat", state["lat"]))
    state["lon"] = float(sub.get("lon", state["lon"]))
    state["distance_nm"] = int(sub.get("distance_nm", state["distance_nm"]))
    state["transit"] = bool(sub.get("transit", state.get("transit", False)))
    bbox = sub.get("bbox")
    if isinstance(bbox, dict) and all(k in bbox for k in ("min_lat", "min_lon", "max_lat", "max_lon")):
        state["bbox"] = {k: float(bbox[k]) for k in ("min_lat", "min_lon", "max_lat", "max_lon")}
    else:
        state.pop("bbox", None)


def _filter_transit(items: list[dict], state: dict[str, Any]) -> list[dict]:
    bbox = state.get("bbox")
    if not bbox:
        return items
    rail = [v for v in items if v.get("kind") == "regional_rail"]
    buses = [
        v for v in items
        if v.get("kind") != "regional_rail"
        and v.get("lat") is not None and v.get("lon") is not None
        and in_bbox(float(v["lat"]), float(v["lon"]),
                    bbox["min_lat"], bbox["min_lon"],
                    bbox["max_lat"], bbox["max_lon"])
    ]
    return buses + rail


async def _send_aircraft_frame(
    ws: WebSocket,
    state: dict[str, Any],
    differ: AircraftDiffer,
) -> None:
    snap = await aircraft_snapshot(
        float(state["lat"]), float(state["lon"]), int(state["distance_nm"]),
    )
    frame = differ.next_frame(snap["items"], snap["ts"])
    await ws.send_text(json.dumps(frame))


async def _send_transit_frame(ws: WebSocket, state: dict[str, Any]) -> None:
    if not state.get("transit"):
        return
    items, sources = await septa_vehicles.all_vehicles()
    items = _filter_transit(items, state)
    await ws.send_text(json.dumps({
        "type": "transit",
        "kind": "snapshot",
        "count": len(items),
        "vehicles": items,
        "sources": sources,
    }))


async def _send_live_tick(ws: WebSocket, state: dict[str, Any], differ: AircraftDiffer) -> None:
    await asyncio.gather(
        _send_aircraft_frame(ws, state, differ),
        _send_transit_frame(ws, state),
    )


async def _subscription_reader(
    ws: WebSocket,
    state: dict[str, Any],
    differ: AircraftDiffer,
) -> None:
    while True:
        raw = await ws.receive_text()
        try:
            sub = json.loads(raw)
            _apply_sub(state, sub)
            differ.reset()
            await _send_live_tick(ws, state, differ)
        except (json.JSONDecodeError, TypeError, ValueError):
            pass


async def _stream_live(ws: WebSocket, lat: float, lon: float, distance_nm: int,
                       transit: bool = False) -> None:
    interval = get_settings().realtime_poll_interval_s
    differ = AircraftDiffer()
    state: dict[str, Any] = {
        "lat": lat, "lon": lon, "distance_nm": distance_nm, "transit": transit,
    }
    reader = asyncio.create_task(_subscription_reader(ws, state, differ))
    try:
        await _send_live_tick(ws, state, differ)
        while True:
            await asyncio.sleep(interval)
            await _send_live_tick(ws, state, differ)
    except (WebSocketDisconnect, RuntimeError):
        return
    except Exception as e:  # noqa: BLE001
        log.exception("snapshot loop error: %s", e)
    finally:
        reader.cancel()
        try:
            await reader
        except asyncio.CancelledError:
            pass


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
        transit = bool(sub.get("transit", False))
        await _stream_live(ws, lat, lon, distance_nm, transit=transit)
    except WebSocketDisconnect:
        pass
    finally:
        hub.drop(ws)
