"""OSM discovery tests — all upstream HTTP is mocked, never reaches the network."""
from __future__ import annotations

import pytest

from backend.discovery.sources import osm
from backend.discovery import service


_OVERPASS_OK = {
    "elements": [
        {
            "type": "node",
            "id": 1001,
            "lat": 39.9526,
            "lon": -75.1652,
            "tags": {
                "man_made": "surveillance",
                "surveillance:type": "camera",
                "operator": "City of Philadelphia",
                "name": "I-95 NB Cam 3",
            },
        },
        {
            "type": "node",
            "id": 1002,
            "lat": 39.97,
            "lon": -75.13,
            "tags": {
                "surveillance": "public",
                "url": "http://camera.example.gov/feed.m3u8",
            },
        },
        {
            "type": "node",
            "id": 1003,
            "lat": 39.96,
            "lon": -75.14,
            "tags": {
                "surveillance": "public",
                "url": "http://admin:admin@camera.example.com/feed",
            },
        },
        {"type": "way", "id": 9999, "tags": {"name": "ignored"}},
        {"type": "node", "id": 1004, "tags": {"surveillance": "yes"}},  # no lat/lon
    ]
}


class TestNormalize:
    def test_normalize_filters_non_nodes(self):
        results = osm.normalize(_OVERPASS_OK["elements"])
        assert all(r.source == "osm" for r in results)
        assert all(r.lat is not None and r.lon is not None for r in results)
        ids = {r.id for r in results}
        assert len(ids) == len(results)

    def test_normalize_strips_credentialed_urls(self):
        results = osm.normalize(_OVERPASS_OK["elements"])
        bad = [r for r in results if "admin:admin" in (r.url or "")]
        assert bad == []

    def test_normalize_preserves_clean_url(self):
        results = osm.normalize(_OVERPASS_OK["elements"])
        urls = [r.url for r in results if r.url]
        assert "http://camera.example.gov/feed.m3u8" in urls

    def test_normalize_labels(self):
        results = osm.normalize(_OVERPASS_OK["elements"])
        labels = [r.label for r in results]
        assert "I-95 NB Cam 3" in labels


class TestBboxMath:
    def test_bbox_format(self):
        bbox = osm._bbox_from(39.9526, -75.1652, 25)
        parts = [float(p) for p in bbox.split(",")]
        assert len(parts) == 4
        south, west, north, east = parts
        assert south < north
        assert west < east


@pytest.mark.asyncio
async def test_search_uses_mocked_http(monkeypatch):
    async def fake_post_json(url, **kwargs):
        return _OVERPASS_OK
    monkeypatch.setattr(osm, "post_json", fake_post_json)
    results = await osm.search(39.95, -75.16, 25)
    assert len(results) >= 2
    assert all(r.source == "osm" for r in results)


@pytest.mark.asyncio
async def test_search_handles_all_mirrors_failing(monkeypatch):
    async def fake_post_json(url, **kwargs):
        return None
    monkeypatch.setattr(osm, "post_json", fake_post_json)
    results = await osm.search(39.95, -75.16, 25)
    assert results == []


@pytest.mark.asyncio
async def test_service_returns_compliant_results_only(monkeypatch):
    async def fake_overpass(lat, lon, radius_km):
        return _OVERPASS_OK["elements"]
    monkeypatch.setattr(osm, "fetch_overpass", fake_overpass)
    resp = await service.search_area(39.95, -75.16, 25)
    osm_results = [r for r in resp.results if r.source == "osm"]
    assert resp.counts_by_source.get("osm", 0) == len(osm_results)
    for r in osm_results:
        assert "admin:admin" not in (r.url or "")
        assert r.blur_required is True
        assert r.fetched_at
