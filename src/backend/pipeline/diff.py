"""State machine for emitting aircraft snapshots as snapshot/diff frames.

Wire shapes:
  Initial frame  : {"type": "aircraft", "kind": "snapshot",
                    "ts": "...", "items": [...]}
  Subsequent     : {"type": "aircraft", "kind": "diff", "ts": "...",
                    "added":   [aircraft, ...],
                    "updated": [aircraft, ...],
                    "removed": [icao24, ...]}

`updated` is emitted only when a per-icao24 record's relevant fields change
(position, altitude, track, velocity, on_ground, callsign).
"""
from __future__ import annotations

from typing import Any

_TRACKED_FIELDS = ("lat", "lon", "alt_m", "track_deg", "velocity_ms",
                   "on_ground", "callsign")


def _changed(a: dict, b: dict) -> bool:
    for f in _TRACKED_FIELDS:
        if a.get(f) != b.get(f):
            return True
    return False


class AircraftDiffer:
    """Holds the last-broadcast snapshot keyed by icao24."""

    def __init__(self) -> None:
        self._state: dict[str, dict] = {}
        self._opened = False

    def reset(self) -> None:
        self._state.clear()
        self._opened = False

    def next_frame(self, items: list[dict], ts: str) -> dict[str, Any]:
        idx = {it["icao24"]: it for it in items if it.get("icao24")}
        if not self._opened:
            self._state = idx
            self._opened = True
            return {"type": "aircraft", "kind": "snapshot", "ts": ts,
                    "count": len(items), "items": list(idx.values())}

        added: list[dict] = []
        updated: list[dict] = []
        for k, v in idx.items():
            prev = self._state.get(k)
            if prev is None:
                added.append(v)
            elif _changed(prev, v):
                updated.append(v)
        removed = [k for k in self._state if k not in idx]
        self._state = idx
        return {"type": "aircraft", "kind": "diff", "ts": ts,
                "added": added, "updated": updated, "removed": removed}
