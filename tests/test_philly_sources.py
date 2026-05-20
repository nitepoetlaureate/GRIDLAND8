"""Tests for the Philly-specific sources added in wave 4."""
from __future__ import annotations

import pytest

from backend.context.sources import philly311, septa_alerts, usgs_water
from backend.pipeline.sources import septa_vehicles


_TRANSITVIEW_SAMPLE = {
    "routes": [
        {"33": [
            {"lat": "39.95", "lng": "-75.16", "VehicleID": "3411", "label": "3411",
             "route_id": "33", "destination": "5th-Market", "Direction": "SouthBound",
             "heading": 104, "late": -2, "Offset": "-2",
             "next_stop_name": "Market St & 13th St",
             "estimated_seat_availability": "MANY_SEATS_AVAILABLE"},
            {"lat": "39.99", "lng": "-75.17", "VehicleID": "0", "label": "0",
             "route_id": "33", "Offset": "999"},  # filtered (scheduled-only)
        ]},
        {"L1_OWL": [
            {"lat": "39.95", "lng": "-75.16", "VehicleID": "3689",
             "route_id": "L1_OWL", "destination": "69th St",
             "Offset": "-0"},
        ]},
    ]
}

_TRAINVIEW_SAMPLE = [
    {"lat": "39.94", "lon": "-75.19", "trainno": "401", "service": "LOCAL",
     "dest": "Airport", "currentstop": "Penn Medicine", "nextstop": "Eastwick",
     "line": "Airport", "heading": "236", "late": 1, "TRACK": "1",
     "consist": "302,410,422"},
]


def test_septa_parse_transitview_filters_schedule_only():
    out = septa_vehicles.parse_transitview(_TRANSITVIEW_SAMPLE)
    assert len(out) == 2
    ids = {v["id"] for v in out}
    assert "septa_33_3411" in ids
    assert "septa_L1_OWL_3689" in ids


def test_septa_parse_trainview():
    out = septa_vehicles.parse_trainview(_TRAINVIEW_SAMPLE)
    assert len(out) == 1
    assert out[0]["kind"] == "regional_rail"
    assert out[0]["destination"] == "Airport"


@pytest.mark.asyncio
async def test_septa_all_vehicles_merges(monkeypatch):
    async def fake_get(url, **kw):
        return _TRANSITVIEW_SAMPLE if "TransitViewAll" in url else _TRAINVIEW_SAMPLE
    monkeypatch.setattr(septa_vehicles, "get_json", fake_get)
    out, _status = await septa_vehicles.all_vehicles()
    kinds = {v["kind"] for v in out}
    assert kinds == {"bus_trolley", "regional_rail"}


def test_septa_vehicles_route(client, monkeypatch):
    async def fake_get(url, **kw):
        return _TRANSITVIEW_SAMPLE if "TransitViewAll" in url else _TRAINVIEW_SAMPLE
    monkeypatch.setattr(septa_vehicles, "get_json", fake_get)
    r = client.get("/api/septa/vehicles")
    assert r.status_code == 200
    body = r.json()
    assert body["count"] == 3
    assert body["bus_trolley"] == 2
    assert body["regional_rail"] == 1


# ── SEPTA alerts ─────────────────────────────────────────────────────────────

_ALERTS_SAMPLE = [
    {"route_id": "MFL", "route_name": "Market-Frankford Line",
     "current_message": "Delays westbound", "advisory_message": "",
     "detour_message": "", "last_updated": "2026-05-20 04:00:00"},
    {"route_id": "BSL", "route_name": "Broad Street Line",
     "current_message": "", "advisory_message": "", "detour_message": ""},  # filtered
]


@pytest.mark.asyncio
async def test_septa_alerts_filters_outside_philly(monkeypatch):
    async def fake_get(url, **kw):
        return _ALERTS_SAMPLE
    monkeypatch.setattr(septa_alerts, "get_json", fake_get)
    # Tokyo — should be skipped entirely
    out = await septa_alerts.near(35.68, 139.69)
    assert out == []


@pytest.mark.asyncio
async def test_septa_alerts_in_philly(monkeypatch):
    async def fake_get(url, **kw):
        return _ALERTS_SAMPLE
    monkeypatch.setattr(septa_alerts, "get_json", fake_get)
    out = await septa_alerts.near(39.9526, -75.1652)
    assert len(out) == 1
    assert out[0]["route_id"] == "MFL"
    assert out[0]["current_message"] == "Delays westbound"


# ── Philly 311 ───────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_philly311_skipped_outside_philly(monkeypatch):
    from backend.shared import opendataphilly as odp

    async def fake_carto(*a, **kw):
        raise AssertionError("should not be called when outside Philly")
    monkeypatch.setattr(odp, "carto_query", fake_carto)
    out = await philly311.recent(35.68, 139.69)
    assert out == []


@pytest.mark.asyncio
async def test_philly311_normalizes(monkeypatch):
    from backend.shared import opendataphilly as odp

    payload = [
        {"cartodb_id": 1, "service_name": "Pothole",
         "status": "Open", "requested_datetime": "2026-05-19T12:00:00Z",
         "lat": 39.95, "lon": -75.16},
        {"cartodb_id": 2, "service_name": "Streetlight Out",
         "status": "Closed", "requested_datetime": "2026-05-18T12:00:00Z",
         "lat": "39.96", "lon": "-75.17"},
    ]

    async def fake_carto(sql, **kw):
        return payload
    monkeypatch.setattr(odp, "carto_query", fake_carto)
    out = await philly311.recent(39.9526, -75.1652, radius_km=5)
    assert len(out) == 2
    assert out[0]["service_name"] == "Pothole"
    assert isinstance(out[1]["lat"], float)


# ── USGS water gauges ────────────────────────────────────────────────────────

_USGS_WATER_SAMPLE = {
    "value": {
        "timeSeries": [
            {
                "sourceInfo": {
                    "siteName": "Schuylkill River at Philadelphia",
                    "siteCode": [{"value": "01474500"}],
                    "geoLocation": {"geogLocation": {"latitude": 39.9697, "longitude": -75.1875}},
                },
                "variable": {
                    "variableCode": [{"value": "00060"}],
                    "unit": {"unitCode": "ft3/s"},
                },
                "values": [{"value": [{"value": "1820", "dateTime": "2026-05-20T03:00:00.000"}]}],
            },
            {
                "sourceInfo": {
                    "siteName": "Schuylkill River at Philadelphia",
                    "siteCode": [{"value": "01474500"}],
                    "geoLocation": {"geogLocation": {"latitude": 39.9697, "longitude": -75.1875}},
                },
                "variable": {
                    "variableCode": [{"value": "00065"}],
                    "unit": {"unitCode": "ft"},
                },
                "values": [{"value": [{"value": "3.42", "dateTime": "2026-05-20T03:00:00.000"}]}],
            },
        ]
    }
}


@pytest.mark.asyncio
async def test_usgs_water_groups_by_site(monkeypatch):
    async def fake_get(url, **kw):
        return _USGS_WATER_SAMPLE
    monkeypatch.setattr(usgs_water, "get_json", fake_get)
    out = await usgs_water.gauges_near(39.9526, -75.1652)
    assert len(out) == 1
    site = out[0]
    assert site["site_code"] == "01474500"
    assert "00060" in site["measurements"]
    assert "00065" in site["measurements"]
    assert site["measurements"]["00060"]["value"] == "1820"
