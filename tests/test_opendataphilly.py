"""Tests for OpenDataPhilly Carto integration."""
from __future__ import annotations

import pytest

from backend.context.sources import opendataphilly
from backend.shared import opendataphilly as odp


@pytest.mark.asyncio
async def test_gather_skipped_outside_philly():
    out = await opendataphilly.gather(40.7, -74.0, radius_km=5)
    assert out.get("skipped") == "outside_philly_bbox"


@pytest.mark.asyncio
async def test_crime_normalize(monkeypatch):
    async def fake_carto(sql, **kw):
        return [{
            "cartodb_id": 1,
            "dispatch_date_time": "2026-05-19T12:00:00Z",
            "text_general_code": "Theft",
            "ucr_general": "I",
            "location_block": "100 BLOCK MAIN ST",
            "point_x": -75.16,
            "point_y": 39.95,
        }]

    monkeypatch.setattr(odp, "carto_query", fake_carto)
    out = await opendataphilly._crime(39.95, -75.16, 5.0)
    assert len(out) == 1
    assert out[0]["type"] == "Theft"
    assert out[0]["lat"] == 39.95


@pytest.mark.asyncio
async def test_gather_merges_layers(monkeypatch):
    async def fake_crime(*a, **k):
        return [{"id": 1, "type": "Theft"}]

    async def fake_shootings(*a, **k):
        return []

    async def fake_snow():
        return [{"street": "6TH ST"}]

    async def fake_parks(*a, **k):
        return [{"name": "Fairmount Park", "lat": 39.9, "lon": -75.2}]

    async def fake_polling(*a, **k):
        return []

    async def fake_zoning(*a, **k):
        return []

    async def fake_red():
        return [{"site_id": "PI001", "intersection": "Roosevelt Blvd"}]

    async def fake_parcels(*a, **k):
        return 1200

    async def fake_police(*a, **k):
        return {"district_num": 9, "name": "Central", "phone": "215-686-3090"}

    monkeypatch.setattr(opendataphilly, "_crime", fake_crime)
    monkeypatch.setattr(opendataphilly, "_shootings", fake_shootings)
    monkeypatch.setattr(opendataphilly, "_snow_routes", fake_snow)
    monkeypatch.setattr(opendataphilly, "_parks", fake_parks)
    monkeypatch.setattr(opendataphilly, "_polling", fake_polling)
    monkeypatch.setattr(opendataphilly, "_zoning", fake_zoning)
    monkeypatch.setattr(opendataphilly, "_red_light_cameras", fake_red)
    monkeypatch.setattr(opendataphilly, "_parcel_count", fake_parcels)
    monkeypatch.setattr(opendataphilly, "_police_district", fake_police)

    bundle = await opendataphilly.gather(39.9526, -75.1652, radius_km=10)
    layers = bundle["layers"]
    assert layers["crime_incidents"][0]["type"] == "Theft"
    assert layers["snow_routes"][0]["street"] == "6TH ST"
    assert layers["parcel_count"] == 1200
    assert len(layers["red_light_cameras"]) == 1
    assert layers["police_district"]["name"] == "Central"
