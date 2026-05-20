import pytest

from backend.pipeline import service as pipeline_service
from backend.pipeline.sources import adsb_fi


_ADSB_OK = {
    "ac": [
        {"hex": "abc123", "flight": "UAL123  ", "lat": 39.9, "lon": -75.1,
         "alt_baro": 35000, "gs": 450.0, "track": 90.0},
        {"hex": "DEF456", "flight": "DAL456", "lat": 40.0, "lon": -74.9,
         "alt_baro": "ground", "gs": 5.0, "track": 180.0},
        {"hex": "noloc", "flight": "X", "lat": None, "lon": None},  # invalid
        {"hex": "bad",   "flight": "Y", "lat": "notnum", "lon": "notnum"},  # invalid
    ]
}


def test_normalize_handles_well_formed_records():
    out = adsb_fi.normalize(_ADSB_OK["ac"])
    assert len(out) == 2
    icaos = [a.icao24 for a in out]
    assert "abc123" in icaos
    assert "def456" in icaos  # lowercased


def test_normalize_callsign_stripped():
    out = adsb_fi.normalize(_ADSB_OK["ac"])
    callsigns = {a.callsign for a in out}
    assert "UAL123" in callsigns


def test_normalize_ground_aircraft():
    out = adsb_fi.normalize(_ADSB_OK["ac"])
    ground = [a for a in out if a.on_ground]
    assert len(ground) == 1
    assert ground[0].alt_m == 0.0


def test_normalize_altitude_conversion():
    out = adsb_fi.normalize(_ADSB_OK["ac"])
    airborne = [a for a in out if not a.on_ground][0]
    # 35000 ft * 0.3048 m/ft = 10668 m
    assert abs(airborne.alt_m - 10668.0) < 1.0


def test_normalize_velocity_conversion():
    out = adsb_fi.normalize(_ADSB_OK["ac"])
    airborne = [a for a in out if not a.on_ground][0]
    # 450 kt = 231.5 m/s
    assert abs(airborne.velocity_ms - 450 * 0.514444) < 0.01


def test_normalize_skips_invalid_records():
    out = adsb_fi.normalize(_ADSB_OK["ac"])
    icaos = {a.icao24 for a in out}
    assert "noloc" not in icaos
    assert "bad" not in icaos


@pytest.mark.asyncio
async def test_fetch_with_mocked_http(monkeypatch):
    async def fake_get_json(url, **kwargs):
        return _ADSB_OK
    monkeypatch.setattr(adsb_fi, "get_json", fake_get_json)
    out = await adsb_fi.fetch(39.95, -75.16, 250)
    assert len(out) == 2


@pytest.mark.asyncio
async def test_fetch_handles_empty(monkeypatch):
    async def fake_get_json(url, **kwargs):
        return None
    monkeypatch.setattr(adsb_fi, "get_json", fake_get_json)
    out = await adsb_fi.fetch(39.95, -75.16, 250)
    assert out == []


@pytest.mark.asyncio
async def test_aircraft_snapshot_shape(monkeypatch):
    async def fake_get_json(url, **kwargs):
        return _ADSB_OK
    monkeypatch.setattr(adsb_fi, "get_json", fake_get_json)
    snap = await pipeline_service.aircraft_snapshot(39.95, -75.16, 250)
    assert snap["type"] == "aircraft"
    assert snap["count"] == 2
    assert len(snap["items"]) == 2
    assert snap["ts"]
