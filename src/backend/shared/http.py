"""Shared async HTTP client with timeout, retry, and a fixed User-Agent."""
from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator

import httpx

from backend.settings import get_settings
from backend.shared.constants import USER_AGENT

log = logging.getLogger(__name__)


def _client_kwargs() -> dict[str, Any]:
    s = get_settings()
    return {
        "timeout": httpx.Timeout(s.http_timeout_s, connect=min(5.0, s.http_timeout_s)),
        "headers": {"User-Agent": USER_AGENT, "Accept": "application/json"},
        "follow_redirects": True,
    }


@asynccontextmanager
async def client() -> AsyncIterator[httpx.AsyncClient]:
    async with httpx.AsyncClient(**_client_kwargs()) as c:
        yield c


async def get_json(url: str, *, params: dict | None = None,
                   headers: dict | None = None) -> Any:
    """GET a URL and return parsed JSON. Retries on transient failures.

    Returns None on permanent failure. Never raises to callers; sources must
    degrade gracefully when an upstream is down.
    """
    s = get_settings()
    last_exc: Exception | None = None
    for attempt in range(s.http_retries + 1):
        try:
            async with client() as c:
                r = await c.get(url, params=params, headers=headers)
                if r.status_code >= 500:
                    raise httpx.HTTPStatusError("server", request=r.request, response=r)
                if r.status_code == 429:
                    await asyncio.sleep(min(2 ** attempt, 8))
                    continue
                r.raise_for_status()
                return r.json()
        except (httpx.TimeoutException, httpx.TransportError, httpx.HTTPStatusError) as e:
            last_exc = e
            log.warning("GET %s failed (attempt %d): %s", url, attempt + 1, e)
            await asyncio.sleep(min(2 ** attempt, 4))
    log.error("GET %s gave up after %d attempts: %s", url, s.http_retries + 1, last_exc)
    return None


async def post_json(url: str, *, data: str | None = None, params: dict | None = None,
                    headers: dict | None = None) -> Any:
    """POST a body and return parsed JSON. Used for Overpass query language."""
    s = get_settings()
    last_exc: Exception | None = None
    for attempt in range(s.http_retries + 1):
        try:
            async with client() as c:
                r = await c.post(url, content=data, params=params, headers=headers)
                if r.status_code >= 500:
                    raise httpx.HTTPStatusError("server", request=r.request, response=r)
                if r.status_code == 429:
                    await asyncio.sleep(min(2 ** attempt, 8))
                    continue
                r.raise_for_status()
                return r.json()
        except (httpx.TimeoutException, httpx.TransportError, httpx.HTTPStatusError) as e:
            last_exc = e
            log.warning("POST %s failed (attempt %d): %s", url, attempt + 1, e)
            await asyncio.sleep(min(2 ** attempt, 4))
    log.error("POST %s gave up after %d attempts: %s", url, s.http_retries + 1, last_exc)
    return None


def utc_now_iso() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat(timespec="seconds")
