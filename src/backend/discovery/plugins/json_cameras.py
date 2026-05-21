"""Load manual camera manifests from config/plugins/cameras/*.json."""
from __future__ import annotations

import json
import logging
from pathlib import Path

from backend.discovery.models import CameraResult
from backend.shared.http import utc_now_iso

log = logging.getLogger(__name__)

_PLUGIN_DIR = Path(__file__).resolve().parents[4] / "config" / "plugins" / "cameras"


def _load_manifests() -> list[dict]:
    if not _PLUGIN_DIR.is_dir():
        return []
    out: list[dict] = []
    for path in sorted(_PLUGIN_DIR.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as e:
            log.warning("plugin manifest %s: %s", path.name, e)
            continue
        cams = data if isinstance(data, list) else data.get("cameras", [])
        if isinstance(cams, list):
            out.extend(cams)
    return out


async def search(lat: float, lon: float, radius_km: float) -> list[CameraResult]:
    del lat, lon, radius_km  # manifests are global; compliance/geo filter later if needed
    now = utc_now_iso()
    results: list[CameraResult] = []
    for rec in _load_manifests():
        try:
            tags = dict(rec.get("tags") or {})
            stream = rec.get("stream")
            if isinstance(stream, dict):
                tags["stream_type"] = str(stream.get("type", ""))
                tags["stream_url"] = str(stream.get("url", ""))
            thumb = rec.get("thumbnail_url")
            if not thumb and isinstance(stream, dict) and stream.get("type") == "refresh_jpeg":
                thumb = stream.get("url")
            results.append(CameraResult(
                id=str(rec["id"]),
                lat=float(rec["lat"]),
                lon=float(rec["lon"]),
                source="plugin_json",
                publication_status=rec.get("publication_status", "operator_published"),
                label=str(rec.get("label") or rec["id"]),
                url=str(rec.get("url") or ""),
                thumbnail_url=thumb,
                blur_required=bool(rec.get("blur_required", False)),
                data_age_s=0,
                fetched_at=now,
                tags=tags,
            ))
        except (KeyError, TypeError, ValueError) as e:
            log.debug("skip plugin camera: %s", e)
    return results
