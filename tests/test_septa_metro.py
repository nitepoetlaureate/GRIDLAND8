"""SEPTA Metro MFL/BSL bundle tests."""
from __future__ import annotations

import pytest

from backend.pipeline.sources import septa_metro


def test_load_stations():
    st = septa_metro._load_stations()
    assert len(st["MFL"]) >= 10
    assert len(st["BSL"]) >= 6
    assert st["MFL"][0]["kind"] == "metro_station"


def test_parse_alerts_mfl_bsl():
    payload = [
        {"route_id": "rr_route_mfl", "route_name": "Market/Frankford Line",
         "current_message": "Delays westbound"},
        {"route_id": "rr_route_bsl", "route_name": "Broad Street Line",
         "advisory_message": "Single tracking"},
        {"route_id": "33", "route_name": "Bus 33", "current_message": "skip"},
    ]
    by = septa_metro.parse_alerts(payload)
    assert len(by["MFL"]) == 1
    assert len(by["BSL"]) == 1


def test_parse_transitview_metro_schedule_only():
    payload = {
        "bus": [{
            "lat": "39.952187", "lng": "-75.15995", "route_id": "L1",
            "VehicleID": "None", "BlockID": "70002", "destination": "69th St",
            "Offset": 998, "late": 998,
        }],
    }
    out = septa_metro.parse_transitview_route("L1", payload)
    assert len(out) == 1
    assert out[0]["line"] == "MFL"
    assert out[0]["gps_live"] is False


def test_attach_nearby_cameras():
    targets = [{"lat": 39.9526, "lon": -75.1652}]
    cameras = [
        {"id": "c1", "label": "Near", "lat": 39.953, "lon": -75.165, "source": "penndot"},
        {"id": "c2", "label": "Far", "lat": 40.1, "lon": -75.1, "source": "osm"},
    ]
    septa_metro.attach_nearby_cameras(targets, cameras, radius_km=0.5)
    assert len(targets[0]["nearby_cameras"]) == 1
    assert targets[0]["nearby_cameras"][0]["id"] == "c1"


@pytest.mark.asyncio
async def test_fetch_metro_vehicles(monkeypatch):
    async def fake_get(url, **kw):
        if "TransitView" in url and kw.get("params", {}).get("route") == "L1":
            return {"bus": [{"lat": "39.95", "lng": "-75.16", "route_id": "L1",
                             "trip": "1", "destination": "Frankford", "Offset": 998}]}
        return {"bus": []}

    monkeypatch.setattr(septa_metro, "get_json", fake_get)
    vehicles, sources = await septa_metro.fetch_metro_vehicles()
    assert any(v["line"] == "MFL" for v in vehicles)
    assert "transitview_L1" in sources
