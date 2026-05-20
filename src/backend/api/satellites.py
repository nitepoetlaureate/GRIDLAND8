"""HTTP route exposing satellite TLE catalogs from Celestrak.

The frontend uses satellite.js to propagate positions client-side; we only
serve TLE triplets here.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from backend.pipeline.sources import celestrak
from backend.settings import get_settings

router = APIRouter(prefix="/api", tags=["satellites"])


@router.get("/satellites")
async def satellites(
    group: str = Query("stations", description="Celestrak group name"),
    limit: int = Query(200, ge=1, le=5000),
) -> dict:
    s = get_settings()
    if group not in s.tle_catalogs:
        raise HTTPException(
            status_code=400,
            detail=f"group must be one of {sorted(s.tle_catalogs)}",
        )
    items = await celestrak.catalog(group)
    items = items[: int(limit)]
    return {"group": group, "count": len(items), "items": items}


@router.get("/satellites/catalogs")
async def list_catalogs() -> dict:
    s = get_settings()
    return {"catalogs": sorted(s.tle_catalogs)}
