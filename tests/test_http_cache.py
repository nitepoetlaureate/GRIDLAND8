import asyncio
import time

import pytest

from backend.shared.cache import TTLCache, make_key


def test_make_key_stable():
    k1 = make_key("GET", "https://x/y", params={"b": 2, "a": 1})
    k2 = make_key("GET", "https://x/y", params={"a": 1, "b": 2})
    assert k1 == k2


def test_make_key_distinguishes_body():
    a = make_key("POST", "https://x/y", body="alpha")
    b = make_key("POST", "https://x/y", body="beta")
    assert a != b


def test_set_and_get():
    c = TTLCache(max_entries=4)
    c.set("k", 42, ttl_s=60)
    assert c.get("k") == 42


def test_ttl_expiry(monkeypatch):
    c = TTLCache(max_entries=4)
    times = [1000.0]
    monkeypatch.setattr(time, "monotonic", lambda: times[0])
    c.set("k", 42, ttl_s=10)
    times[0] = 1005.0
    assert c.get("k") == 42
    times[0] = 1015.0
    assert c.get("k") is None


def test_lru_eviction():
    c = TTLCache(max_entries=2)
    c.set("a", 1, ttl_s=60)
    c.set("b", 2, ttl_s=60)
    c.get("a")
    c.set("c", 3, ttl_s=60)
    assert c.get("b") is None
    assert c.get("a") == 1
    assert c.get("c") == 3


@pytest.mark.asyncio
async def test_get_or_fetch_single_flight():
    c = TTLCache(max_entries=8)
    calls = {"n": 0}
    started = asyncio.Event()
    release = asyncio.Event()

    async def loader():
        calls["n"] += 1
        started.set()
        await release.wait()
        return {"v": calls["n"]}

    t1 = asyncio.create_task(c.get_or_fetch("k", 60, loader))
    await started.wait()
    t2 = asyncio.create_task(c.get_or_fetch("k", 60, loader))
    await asyncio.sleep(0.05)
    release.set()
    r1 = await t1
    r2 = await t2
    assert r1 == r2 == {"v": 1}
    assert calls["n"] == 1


@pytest.mark.asyncio
async def test_get_or_fetch_does_not_cache_none():
    c = TTLCache(max_entries=8)
    calls = {"n": 0}

    async def loader():
        calls["n"] += 1
        return None

    await c.get_or_fetch("k", 60, loader)
    await c.get_or_fetch("k", 60, loader)
    assert calls["n"] == 2


@pytest.mark.asyncio
async def test_http_get_uses_cache(monkeypatch):
    from backend.shared import http
    from backend.shared.cache import default_cache

    default_cache().clear()
    calls = {"n": 0}

    async def fake_do_get(url, params, headers):
        calls["n"] += 1
        return {"hit": calls["n"]}

    monkeypatch.setattr(http, "_do_get", fake_do_get)
    r1 = await http.get_json("https://x.test/", ttl_s=60)
    r2 = await http.get_json("https://x.test/", ttl_s=60)
    assert r1 == r2 == {"hit": 1}
    assert calls["n"] == 1

    r3 = await http.get_json("https://x.test/", ttl_s=0)
    assert calls["n"] == 2
