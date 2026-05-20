"""Tests for Caltrans, WSDOT, 511NY adapters and the livecam registry."""
from __future__ import annotations

import pytest

from backend.discovery.sources import caltrans, livecams, n511ny, wsdot
from backend.settings import get_settings, reset_settings_cache


# ── Caltrans ─────────────────────────────────────────────────────────────────

_CALTRANS_PAYLOAD = {
    "data": [
        {"cctv": {
            "index": "1",
            "inService": "true",
            "location": {
                "district": "4", "locationName": "I-80 EB at 7th St",
                "nearbyPlace": "Oakland", "longitude": "-122.27",
                "latitude": "37.80", "direction": "EB", "route": "80",
            },
            "imageData": {
                "streamingVideoURL": "https://cwwp2.dot.ca.gov/live/d4/x.m3u8",
                "static": {"currentImageURL": "https://cwwp2.dot.ca.gov/still/d4/x.jpg"},
            },
        }},
        {"cctv": {
            "index": "2",
            "inService": "false",  # filtered
            "location": {"longitude": "-122.30", "latitude": "37.81"},
            "imageData": {},
        }},
        {"cctv": {
            "index": "3",
            "inService": "true",
            "location": {"longitude": "-119.0", "latitude": "35.0"},  # out of bbox
            "imageData": {"streamingVideoURL": "https://x"},
        }},
    ]
}


def test_caltrans_normalize_in_bbox():
    out = caltrans.normalize(_CALTRANS_PAYLOAD, 37.80, -122.27, 50)
    assert len(out) == 1
    cam = out[0]
    assert cam.source == "caltrans"
    assert cam.publication_status == "operator_published"
    assert cam.url.startswith("https://cwwp2.dot.ca.gov/live")
    assert cam.blur_required is False
    assert "Oakland" in cam.label
    assert cam.tags["agency"] == "Caltrans"


def test_caltrans_skips_out_of_service():
    out = caltrans.normalize(_CALTRANS_PAYLOAD, 37.80, -122.30, 100)
    ids = [c.id for c in out]
    assert all("2" not in i for i in ids) or len(out) == 1


def test_caltrans_skips_out_of_bbox():
    out = caltrans.normalize(_CALTRANS_PAYLOAD, 37.80, -122.27, 1)
    assert all(abs(c.lat - 37.80) < 0.02 for c in out)


@pytest.mark.asyncio
async def test_caltrans_search_uses_mocked_http(monkeypatch):
    async def fake_get_json(url, **kw):
        return _CALTRANS_PAYLOAD
    monkeypatch.setattr(caltrans, "get_json", fake_get_json)
    out = await caltrans.search(37.80, -122.27, 50)
    assert any(c.source == "caltrans" for c in out)


# ── WSDOT ────────────────────────────────────────────────────────────────────

_WSDOT_PAYLOAD = [
    {"CameraID": 9001, "IsActive": True, "Title": "I-90 MP 12",
     "ImageURL": "https://images.wsdot.wa.gov/nw/090vc12.jpg",
     "DisplayLatitude": 47.5, "DisplayLongitude": -121.9,
     "Region": "Northwest", "Roadway": "I-90"},
    {"CameraID": 9002, "IsActive": False, "Title": "off",
     "ImageURL": "https://x", "DisplayLatitude": 47.5, "DisplayLongitude": -121.9},
    {"CameraID": 9003, "IsActive": True, "Title": "far",
     "ImageURL": "https://images.wsdot.wa.gov/nw/x.jpg",
     "DisplayLatitude": 60.0, "DisplayLongitude": -130.0},
]


def test_wsdot_normalize():
    out = wsdot.normalize(_WSDOT_PAYLOAD, 47.5, -121.9, 50)
    assert len(out) == 1
    assert out[0].source == "wsdot"
    assert out[0].publication_status == "operator_published"
    assert out[0].url.startswith("https://images.wsdot.wa.gov")
    assert out[0].tags["agency"] == "WSDOT"


@pytest.mark.asyncio
async def test_wsdot_skipped_without_key(monkeypatch):
    reset_settings_cache()
    monkeypatch.delenv("WSDOT_API_KEY", raising=False)
    out = await wsdot.search(47.5, -121.9, 50)
    assert out == []


@pytest.mark.asyncio
async def test_wsdot_search_with_mocked_key(monkeypatch):
    monkeypatch.setenv("WSDOT_API_KEY", "TESTKEY")
    reset_settings_cache()

    async def fake_get_json(url, **kw):
        return _WSDOT_PAYLOAD
    monkeypatch.setattr(wsdot, "get_json", fake_get_json)
    out = await wsdot.search(47.5, -121.9, 50)
    assert len(out) == 1
    reset_settings_cache()


# ── 511NY ────────────────────────────────────────────────────────────────────

_N511NY_PAYLOAD = [
    {"ID": "100", "Name": "I-87 NB at Albany", "Latitude": 42.65,
     "Longitude": -73.75, "VideoUrl": "https://511ny.org/video/100.m3u8",
     "Disabled": "0", "Region": "Capital District", "RoadwayName": "I-87"},
    {"ID": "101", "Name": "Disabled", "Latitude": 42.65, "Longitude": -73.75,
     "VideoUrl": "https://x", "Disabled": "1"},
    {"ID": "102", "Name": "Far away", "Latitude": 40.7, "Longitude": -74.0,
     "VideoUrl": "https://x", "Disabled": "0"},
]


def test_n511ny_normalize():
    out = n511ny.normalize(_N511NY_PAYLOAD, 42.65, -73.75, 50)
    assert len(out) == 1
    assert out[0].source == "n511ny"
    assert out[0].publication_status == "operator_published"


@pytest.mark.asyncio
async def test_n511ny_skipped_without_key(monkeypatch):
    monkeypatch.delenv("N511NY_API_KEY", raising=False)
    reset_settings_cache()
    out = await n511ny.search(42.65, -73.75, 50)
    assert out == []
    reset_settings_cache()


# ── Livecams (no network) ────────────────────────────────────────────────────

def test_livecams_in_bbox_returns_local_cams():
    out = livecams.normalize(livecams.LIVECAMS, 44.46, -110.83, 50,
                              include_global=False)
    names = {c.label for c in out}
    assert any("Old Faithful" in n for n in names)
    assert "ISS Live (NASA)" not in names


def test_livecams_far_away_returns_empty():
    out = livecams.normalize(livecams.LIVECAMS, 0.5, 0.5, 50,
                              include_global=False)
    assert out == []


@pytest.mark.asyncio
async def test_livecams_search_yellowstone():
    out = await livecams.search(44.46, -110.83, 50)
    assert any(c.source == "livecam" for c in out)
    assert all(c.publication_status == "operator_published" for c in out)
