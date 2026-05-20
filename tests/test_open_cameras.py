"""Tests for NYC TMC, Castle Rock 511 (ON/AB), and NPS Webcams adapters."""
from __future__ import annotations

import pytest

from backend.discovery.sources import castlerock_511, nps_webcams, nyctmc


def _record_nyctmc(id_: str, lat: float, lon: float, online: bool = True) -> dict:
    return {
        "id": id_,
        "name": f"Cam {id_}",
        "latitude": lat,
        "longitude": lon,
        "area": "Manhattan",
        "isOnline": "true" if online else "false",
        "imageUrl": f"https://webcams.nyctmc.org/api/cameras/{id_}/image",
    }


def test_nyctmc_normalize_filters_outside_radius() -> None:
    records = [
        _record_nyctmc("a", 40.7589, -73.9851),  # Times Square
        _record_nyctmc("b", 40.7128, -74.0060),  # Lower Manhattan
        _record_nyctmc("c", 34.0522, -118.2437),  # LA — far away
    ]
    out = nyctmc.normalize(records, lat=40.75, lon=-74.0, radius_km=25.0)
    ids = sorted(c.id for c in out)
    assert ids == ["nyctmc_a", "nyctmc_b"]
    assert all(c.source == "nyctmc" for c in out)
    assert all(c.publication_status == "operator_published" for c in out)


def test_nyctmc_geofence_outside_nyc_skips_call() -> None:
    # Philadelphia query should not intersect NYC bbox at small radius.
    assert nyctmc._intersects_bbox(39.95, -75.16, 25.0, nyctmc.NYC_BBOX) is False
    # Camden NJ is close enough to NY metro bbox at 100km — should intersect.
    assert nyctmc._intersects_bbox(40.30, -74.20, 100.0, nyctmc.NYC_BBOX) is True


def _record_cr511(id_: int, lat: float, lon: float, n_views: int = 2) -> dict:
    return {
        "Id": id_,
        "Source": "Test",
        "SourceId": f"S-{id_}",
        "Roadway": "QEW",
        "Direction": "Westbound",
        "Latitude": lat,
        "Longitude": lon,
        "Location": "Test Location",
        "Views": [
            {"Id": v, "Url": f"https://example/v/{id_}/{v}",
             "Status": "Enabled", "Description": f"View {v}"}
            for v in range(1, n_views + 1)
        ],
    }


def test_castlerock_normalize_yields_one_per_view() -> None:
    dep = castlerock_511.Deployment("on511", "511on.ca", "MTO",
                                    (41.5, -95.2, 56.9, -74.3))
    recs = [_record_cr511(1, 43.65, -79.38, n_views=3)]  # Toronto
    out = castlerock_511.normalize(recs, dep, lat=43.65, lon=-79.38, radius_km=10.0)
    assert len(out) == 3
    assert all(c.source == "castlerock_511" for c in out)
    assert all(c.tags["deployment"] == "on511" for c in out)


def test_castlerock_drops_disabled_views() -> None:
    dep = castlerock_511.Deployment("ab511", "511.alberta.ca", "AT",
                                    (49.0, -120.0, 60.0, -110.0))
    rec = _record_cr511(1, 51.05, -114.07)  # Calgary
    rec["Views"][0]["Status"] = "Disabled"
    out = castlerock_511.normalize([rec], dep, lat=51.05, lon=-114.07, radius_km=20.0)
    assert len(out) == 1
    assert out[0].tags["deployment"] == "ab511"


def test_castlerock_filters_outside_radius() -> None:
    dep = castlerock_511.DEPLOYMENTS[0]  # Ontario
    recs = [
        _record_cr511(1, 43.65, -79.38, n_views=1),  # Toronto
        _record_cr511(2, 46.49, -84.34, n_views=1),  # Sault Ste. Marie — far
    ]
    out = castlerock_511.normalize(recs, dep, lat=43.65, lon=-79.38, radius_km=50.0)
    assert len(out) == 1


def test_nps_normalize_parses_images_and_skips_zero_coords() -> None:
    payload = [
        {"id": "yose-falls", "title": "Yosemite Falls",
         "latitude": "37.7456", "longitude": "-119.5936",
         "status": "Active", "url": "https://www.nps.gov/yose/...",
         "images": [{"url": "https://example/img.jpg"}],
         "relatedParks": ["yose"]},
        {"id": "bad-no-coords", "title": "Bad",
         "latitude": "0", "longitude": "0", "status": "Active"},
        {"id": "inactive-cam", "title": "Off",
         "latitude": "37.7", "longitude": "-119.5", "status": "Inactive"},
    ]
    out = nps_webcams.normalize(payload)
    assert len(out) == 1
    assert out[0].id == "nps_yose-falls"
    assert out[0].thumbnail_url == "https://example/img.jpg"
    assert out[0].tags["agency"] == "US National Park Service"


@pytest.mark.asyncio
async def test_nps_search_returns_empty_without_key(monkeypatch) -> None:
    from backend.settings import get_settings
    s = get_settings()
    monkeypatch.setattr(s, "nps_api_key", None)
    out = await nps_webcams.search(37.74, -119.59, 50.0)
    assert out == []


@pytest.mark.asyncio
async def test_nyctmc_search_skipped_for_philly(monkeypatch) -> None:
    called = {"n": 0}

    async def fake_get_json(*a, **kw):
        called["n"] += 1
        return []

    monkeypatch.setattr(nyctmc, "get_json", fake_get_json)
    out = await nyctmc.search(39.95, -75.16, 25.0)
    assert out == []
    assert called["n"] == 0
