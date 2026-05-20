"""Tests for the new context sources: USGS quakes, NASA FIRMS, OpenAQ, METAR."""
from __future__ import annotations

import pytest

from backend.context.sources import aviation, firms, openaq, usgs
from backend.settings import reset_settings_cache


_USGS_GEOJSON = {
    "features": [
        {
            "id": "q1",
            "properties": {
                "mag": 3.2, "place": "5 km E of City", "time": 1717000000000,
                "url": "https://earthquake.usgs.gov/...", "type": "earthquake",
                "alert": None, "tsunami": 0,
            },
            "geometry": {"type": "Point", "coordinates": [-75.1, 39.9, 8.5]},
        },
        {
            "id": "no-coords",
            "properties": {"mag": 1.0, "place": "?", "time": 0},
            "geometry": {"type": "Point", "coordinates": []},
        },
    ]
}


@pytest.mark.asyncio
async def test_usgs_recent_quakes_parses_geojson(monkeypatch):
    async def fake_get_json(url, **kw):
        return _USGS_GEOJSON
    monkeypatch.setattr(usgs, "get_json", fake_get_json)
    out = await usgs.recent_quakes(39.95, -75.16, radius_km=200, days=1)
    assert len(out) == 1
    assert out[0]["mag"] == 3.2
    assert out[0]["lat"] == 39.9
    assert out[0]["depth_km"] == 8.5


_FIRMS_CSV = (
    "latitude,longitude,bright_ti4,acq_date,acq_time,satellite,confidence,frp,daynight\n"
    "39.95,-75.16,320.1,2026-05-19,1530,N,n,12.5,D\n"
    "0.0,0.0,0,2026-05-19,0,N,n,0,D\n"  # should be filtered
)


@pytest.mark.asyncio
async def test_firms_skipped_without_key(monkeypatch):
    monkeypatch.delenv("NASA_FIRMS_MAP_KEY", raising=False)
    reset_settings_cache()
    out = await firms.active_fires(39.95, -75.16)
    assert out == []
    reset_settings_cache()


def test_firms_parse_csv_filters_zero_zero():
    rows = firms.parse_csv(_FIRMS_CSV)
    assert len(rows) == 1
    assert rows[0]["satellite"] == "N"
    assert rows[0]["lat"] == 39.95


@pytest.mark.asyncio
async def test_firms_with_key(monkeypatch):
    monkeypatch.setenv("NASA_FIRMS_MAP_KEY", "TESTKEY")
    reset_settings_cache()

    async def fake_fetch_csv(url):
        return _FIRMS_CSV
    monkeypatch.setattr(firms, "_fetch_csv", fake_fetch_csv)
    out = await firms.active_fires(39.95, -75.16, radius_km=100, days=1)
    assert len(out) == 1
    assert out[0]["confidence"] == "n"
    reset_settings_cache()


@pytest.mark.asyncio
async def test_openaq_skipped_without_key(monkeypatch):
    monkeypatch.delenv("OPENAQ_API_KEY", raising=False)
    reset_settings_cache()
    out = await openaq.nearby_aq(39.95, -75.16)
    assert out == []
    reset_settings_cache()


@pytest.mark.asyncio
async def test_openaq_with_key(monkeypatch):
    monkeypatch.setenv("OPENAQ_API_KEY", "TESTKEY")
    reset_settings_cache()

    payload = {
        "results": [
            {
                "id": 7, "name": "Station A",
                "coordinates": {"latitude": 39.95, "longitude": -75.16},
                "country": {"code": "US"},
                "sensors": [{"parameter": {"name": "pm25"}}, {"parameter": {"name": "o3"}}],
                "datetimeLast": {"local": "2026-05-19T12:00:00-04:00"},
            }
        ]
    }

    async def fake_get_json(url, **kw):
        assert "X-API-Key" in (kw.get("headers") or {})
        return payload
    monkeypatch.setattr(openaq, "get_json", fake_get_json)
    out = await openaq.nearby_aq(39.95, -75.16)
    assert len(out) == 1
    assert "pm25" in out[0]["sensors"]
    reset_settings_cache()


_METAR_PAYLOAD = [
    {"icaoId": "KPHL", "rawOb": "KPHL 191500Z 27010KT 10SM CLR 22/12",
     "obsTime": 1717000000, "lat": 39.87, "lon": -75.24,
     "temp": 22, "dewp": 12, "wdir": 270, "wspd": 10,
     "visib": 10, "fltcat": "VFR", "wxString": None},
]


@pytest.mark.asyncio
async def test_metars(monkeypatch):
    async def fake_get_json(url, **kw):
        return _METAR_PAYLOAD
    monkeypatch.setattr(aviation, "get_json", fake_get_json)
    out = await aviation.metars(39.95, -75.16)
    assert len(out) == 1
    assert out[0]["station"] == "KPHL"
    assert out[0]["flight_category"] == "VFR"
