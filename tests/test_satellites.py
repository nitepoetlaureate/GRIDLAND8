"""Tests for the Celestrak TLE source and /api/satellites route."""
from __future__ import annotations

import pytest

from backend.pipeline.sources import celestrak


_TLE_STATIONS = (
    "ISS (ZARYA)\n"
    "1 25544U 98067A   24139.50000000  .00000000  00000-0  00000-0 0  9990\n"
    "2 25544  51.6400 100.0000 0001000 100.0000 260.0000 15.50000000000000\n"
    "TIANGONG\n"
    "1 48274U 21035A   24139.50000000  .00000000  00000-0  00000-0 0  9991\n"
    "2 48274  41.4700 100.0000 0001000 100.0000 260.0000 15.60000000000000\n"
    "GARBAGE LINE WITHOUT TLE PAIR\n"
)


def test_parse_tle_text():
    parsed = celestrak.parse_tle_text(_TLE_STATIONS)
    assert len(parsed) == 2
    assert parsed[0]["name"] == "ISS (ZARYA)"
    assert parsed[0]["line1"].startswith("1 25544")
    assert parsed[1]["name"] == "TIANGONG"


@pytest.mark.asyncio
async def test_catalog_uses_cache(monkeypatch):
    async def fake_fetch(group: str) -> str:
        return _TLE_STATIONS
    monkeypatch.setattr(celestrak, "_fetch_tle", fake_fetch)
    rows = await celestrak.catalog("stations")
    assert len(rows) == 2


@pytest.mark.asyncio
async def test_catalog_rejects_unknown_group():
    rows = await celestrak.catalog("not-a-real-group")
    assert rows == []


def test_satellites_route(client, monkeypatch):
    async def fake_catalog(group: str):
        return celestrak.parse_tle_text(_TLE_STATIONS)
    monkeypatch.setattr(celestrak, "catalog", fake_catalog)
    r = client.get("/api/satellites", params={"group": "stations", "limit": 5})
    assert r.status_code == 200
    body = r.json()
    assert body["count"] == 2
    assert body["items"][0]["name"] == "ISS (ZARYA)"


def test_satellites_route_rejects_bad_group(client):
    r = client.get("/api/satellites", params={"group": "fictional"})
    assert r.status_code == 400


def test_satellite_catalogs_listed(client):
    r = client.get("/api/satellites/catalogs")
    assert r.status_code == 200
    catalogs = r.json()["catalogs"]
    assert "stations" in catalogs
