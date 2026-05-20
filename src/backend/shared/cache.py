"""In-process TTL cache with single-flight (stampede protection).

- Keyed by an opaque string (method + url + sorted-params + body-hash).
- Per-key TTL in seconds. Expired entries are evicted on access (and lazily
  on insert when the table is full).
- Single-flight: concurrent fetches for the same key wait on the first
  request rather than firing N copies.
- Stateless; safe to drop on process restart. A future Redis backend can
  expose the same `Cache` protocol.
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import time
from collections import OrderedDict
from typing import Any, Awaitable, Callable


def make_key(method: str, url: str, *, params: dict | None = None,
             body: str | None = None) -> str:
    parts: list[str] = [method.upper(), url]
    if params:
        parts.append(json.dumps(sorted(params.items()), separators=(",", ":")))
    if body:
        parts.append(hashlib.sha1(body.encode("utf-8", errors="replace")).hexdigest())
    return "|".join(parts)


class TTLCache:
    """LRU + per-entry TTL. Not thread-safe; intended for a single asyncio loop."""

    def __init__(self, max_entries: int = 1024) -> None:
        self._max = max_entries
        self._store: OrderedDict[str, tuple[float, Any]] = OrderedDict()
        self._locks: dict[str, asyncio.Lock] = {}

    def __len__(self) -> int:
        return len(self._store)

    def _evict_expired(self, now: float) -> None:
        expired = [k for k, (exp, _) in self._store.items() if exp <= now]
        for k in expired:
            self._store.pop(k, None)

    def _evict_overflow(self) -> None:
        while len(self._store) > self._max:
            self._store.popitem(last=False)

    def get(self, key: str) -> Any | None:
        now = time.monotonic()
        item = self._store.get(key)
        if item is None:
            return None
        exp, value = item
        if exp <= now:
            self._store.pop(key, None)
            return None
        self._store.move_to_end(key)
        return value

    def set(self, key: str, value: Any, ttl_s: float) -> None:
        now = time.monotonic()
        self._store[key] = (now + ttl_s, value)
        self._store.move_to_end(key)
        self._evict_overflow()

    def clear(self) -> None:
        self._store.clear()
        self._locks.clear()

    async def get_or_fetch(self, key: str, ttl_s: float,
                            loader: Callable[[], Awaitable[Any]]) -> Any:
        """Return cached value or call `loader()` once, even under concurrency."""
        hit = self.get(key)
        if hit is not None:
            return hit
        lock = self._locks.setdefault(key, asyncio.Lock())
        async with lock:
            hit = self.get(key)
            if hit is not None:
                return hit
            value = await loader()
            if value is not None:
                self.set(key, value, ttl_s)
            return value


_default = TTLCache()


def default_cache() -> TTLCache:
    return _default
