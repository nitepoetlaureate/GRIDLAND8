"""Proxy refreshable camera stills (CORS-safe for the feed panel)."""
from __future__ import annotations

import logging
from urllib.parse import urlparse

import httpx
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response

from backend.settings import get_settings

log = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["cameras"])

_ALLOW_HOSTS = (
    "511pa.com", "www.511pa.com",
    "511ny.org", "www.511ny.org",
    "nyctmc.org", "webcams.nyctmc.org",
    "video.dot.ca.gov", "www.wsdot.wa.gov",
)


def _allowed(url: str) -> bool:
    try:
        host = urlparse(url).hostname or ""
    except Exception:
        return False
    return any(host == h or host.endswith("." + h) for h in _ALLOW_HOSTS)


@router.get("/cameras/frame")
async def camera_frame(url: str = Query(..., min_length=10)) -> Response:
    if not _allowed(url):
        raise HTTPException(400, "URL host not allowed for proxy")
    s = get_settings()
    try:
        async with httpx.AsyncClient(timeout=s.http_timeout_s, follow_redirects=True) as client:
            r = await client.get(url)
            r.raise_for_status()
    except httpx.HTTPError as e:
        log.warning("camera proxy fetch failed: %s", e)
        raise HTTPException(502, "upstream fetch failed") from e
    ctype = r.headers.get("content-type", "image/jpeg")
    return Response(content=r.content, media_type=ctype,
                    headers={"Cache-Control": "no-cache"})
