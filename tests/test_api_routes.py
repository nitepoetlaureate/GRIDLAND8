"""End-to-end route tests with mocked sources."""
from __future__ import annotations

import pytest

from backend.context import service as ctx_service
from backend.discovery import service as disco_service
from backend.discovery.models import CameraResult, DiscoveryResponse


@pytest.mark.asyncio
async def test_discover_route(client, monkeypatch):
    async def fake_search_area(lat, lon, radius_km):
        return DiscoveryResponse(
            query={"lat": lat, "lon": lon, "radius_km": radius_km},
            results=[
                CameraResult(
                    id="osm_test",
                    lat=lat,
                    lon=lon,
                    source="osm",
                    label="test",
                    url="https://camera.example.gov/",
                    blur_required=True,
                    fetched_at="2026-05-20T00:00:00+00:00",
                )
            ],
            fetched_at="2026-05-20T00:00:00+00:00",
            counts_by_source={"osm": 1},
        )

    monkeypatch.setattr("backend.api.discovery.search_area", fake_search_area)
    r = client.get("/api/discover", params={"lat": 39.95, "lon": -75.16, "radius_km": 25})
    assert r.status_code == 200
    body = r.json()
    assert body["counts_by_source"] == {"osm": 1}
    assert len(body["results"]) == 1


def test_discover_validates_inputs(client):
    r = client.get("/api/discover", params={"lat": 999, "lon": 0})
    assert r.status_code == 422
    r = client.get("/api/discover", params={"lat": 0, "lon": 0, "radius_km": -1})
    assert r.status_code == 422


def test_context_route(client, monkeypatch):
    from backend.context.models import ContextBundle

    async def fake_gather(lat, lon):
        return ContextBundle(
            query={"lat": lat, "lon": lon},
            weather={"now": "Sunny"},
            alerts=[],
            wikipedia=[],
            fetched_at="2026-05-20T00:00:00+00:00",
        )

    monkeypatch.setattr("backend.api.context.gather", fake_gather)
    r = client.get("/api/context", params={"lat": 39.95, "lon": -75.16})
    assert r.status_code == 200
    body = r.json()
    assert body["weather"] == {"now": "Sunny"}
    assert body["fetched_at"]
