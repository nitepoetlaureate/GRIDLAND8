"""HTTP route exposing Mapillary photosphere panos near a point."""
from __future__ import annotations

from fastapi import APIRouter, Query

from backend.discovery.sources import mapillary
from backend.settings import get_settings

# #region agent log
import json as _json
import time as _time
from pathlib import Path as _Path
_DBG = _Path("/Users/michaelraftery/GRIDLAND8/.cursor/debug-716b73.log")


def _dbg(location: str, message: str, data: dict, hypothesis_id: str) -> None:
    try:
        _DBG.parent.mkdir(parents=True, exist_ok=True)
        with _DBG.open("a") as f:
            f.write(_json.dumps({
                "sessionId": "716b73",
                "runId": "photospheres",
                "hypothesisId": hypothesis_id,
                "location": location,
                "message": message,
                "data": data,
                "timestamp": int(_time.time() * 1000),
            }) + "\n")
    except Exception:
        pass
# #endregion

router = APIRouter(prefix="/api", tags=["photosphere"])


@router.get("/photospheres")
async def photospheres(
    lat: float = Query(..., ge=-90.0, le=90.0),
    lon: float = Query(..., ge=-180.0, le=180.0),
    radius_m: int = Query(200, ge=10, le=1000),
    limit: int = Query(25, ge=1, le=100),
) -> dict:
    s = get_settings()
    items = await mapillary.panos_near(lat, lon, radius_m=radius_m, limit=limit)
    # #region agent log
    _dbg(
        "api/photosphere.py:photospheres",
        "photosphere lookup",
        {
            "query": {"lat": lat, "lon": lon, "radius_m": radius_m},
            "mapillary_key_set": bool(s.mapillary_api_key),
            "items_returned": len(items),
        },
        "H4",
    )
    # #endregion
    return {"query": {"lat": lat, "lon": lon, "radius_m": radius_m},
            "count": len(items), "items": items}
