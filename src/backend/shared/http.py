"""Shared async HTTP with timeout, retry, fixed User-Agent, and TTL cache."""
from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator

import httpx

from backend.settings import get_settings
from backend.shared.cache import default_cache, make_key
from backend.shared.constants import USER_AGENT

log = logging.getLogger(__name__)

# Sentinel: ttl_s=0 disables caching for this call (default).
NO_CACHE = 0.0


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


async def _do_get(url: str, params: dict | None, headers: dict | None) -> Any:
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
    log.error("GET %s gave up: %s", url, last_exc)
    return None


async def _do_post(url: str, data: str | None, params: dict | None,
                   headers: dict | None) -> Any:
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
    log.error("POST %s gave up: %s", url, last_exc)
    return None


async def get_json(url: str, *, params: dict | None = None,
                   headers: dict | None = None, ttl_s: float = NO_CACHE) -> Any:
    """GET parsed JSON. If ttl_s > 0, cache successful responses.

    Failures are not cached. Callers may pass ttl_s to opt in.
    """
    if ttl_s <= 0:
        return await _do_get(url, params, headers)
    cache = default_cache()
    key = make_key("GET", url, params=params)
    return await cache.get_or_fetch(key, ttl_s, lambda: _do_get(url, params, headers))


async def post_json(url: str, *, data: str | None = None, params: dict | None = None,
                    headers: dict | None = None, ttl_s: float = NO_CACHE) -> Any:
    if ttl_s <= 0:
        return await _do_post(url, data, params, headers)
    cache = default_cache()
    key = make_key("POST", url, params=params, body=data)
    return await cache.get_or_fetch(key, ttl_s,
                                     lambda: _do_post(url, data, params, headers))


def utc_now_iso() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat(timespec="seconds")
