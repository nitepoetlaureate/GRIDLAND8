"""Tests for /api/whats_here aggregator."""
from __future__ import annotations

import pytest

from backend.api import whats_here as wh
from backend.context import service as ctx_service
from backend.discovery import service as discovery_service
from backend.discovery.models import CameraResult, DiscoveryResponse
from backend.context.models import ContextBundle


@pytest.fixture
def stub_layers(monkeypatch):
    async def fake_discover(lat, lon, radius_km):
        return DiscoveryResponse(
            query={"lat": lat, "lon": lon, "radius_km": radius_km},
            results=[CameraResult(
                id="cam1", source="osm", lat=lat, lon=lon, label="cam1",
                url="https://example.org/cam1.jpg",
                fetched_at="2026-05-20T00:00:00+00:00",
            )],
            fetched_at="2026-05-20T00:00:00+00:00",
            counts_by_source={"osm": 1},
        )

    async def fake_gather(lat, lon):
        return ContextBundle(
            query={"lat": lat, "lon": lon},
            weather={"now": "Sunny"},
            alerts=[], wikipedia=[],
            quakes=[], fires=[], air_quality=[], metars=[],
            fetched_at="2026-05-20T00:00:00+00:00",
            errors={},
        )

    async def fake_panos(lat, lon, **kw):
        return [{"id": "pano1", "lat": lat, "lon": lon,
                 "thumb_2048_url": "https://images.mapillary.com/pano1.jpg"}]

    monkeypatch.setattr(discovery_service, "search_area", fake_discover)
    monkeypatch.setattr(ctx_service, "gather", fake_gather)
    monkeypatch.setattr(wh.mapillary, "panos_near", fake_panos)


def test_whats_here_aggregates(client, stub_layers):
    r = client.get("/api/whats_here",
                   params={"lat": 39.95, "lon": -75.16, "radius_km": 1})
    assert r.status_code == 200
    body = r.json()
    assert body["query"]["lat"] == 39.95
    assert body["cameras"]["results"][0]["id"] == "cam1"
    assert body["context"]["weather"]["now"] == "Sunny"
    assert body["photospheres"][0]["id"] == "pano1"
    assert body["errors"] == {}


def test_whats_here_isolates_failures(client, monkeypatch):
    async def boom(*a, **k): raise RuntimeError("upstream gone")

    async def ok_ctx(lat, lon):
        return ContextBundle(
            query={"lat": lat, "lon": lon},
            fetched_at="2026-05-20T00:00:00+00:00",
        )

    async def empty_panos(*a, **k): return []

    monkeypatch.setattr(discovery_service, "search_area", boom)
    monkeypatch.setattr(ctx_service, "gather", ok_ctx)
    monkeypatch.setattr(wh.mapillary, "panos_near", empty_panos)
    r = client.get("/api/whats_here", params={"lat": 0, "lon": 0})
    assert r.status_code == 200
    body = r.json()
    assert body["cameras"] is None
    assert "cameras" in body["errors"]
    assert body["context"] is not None
