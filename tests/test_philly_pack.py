"""Philly no-key pack: SEPTA detours, Indego GBFS, PennDOT ArcGIS."""
from __future__ import annotations

import pytest

from backend.context.sources import septa_detours
from backend.discovery.sources import penndot
from backend.pipeline.sources import indego


@pytest.mark.asyncio
async def test_septa_detours_normalize():
    payload = [{
        "route_id": "23",
        "route_info": [{
            "route_direction": "NB",
            "reason": "Construction",
            "current_message": "Detour in effect",
        }],
    }]
    out = septa_detours.normalize(payload)
    assert len(out) == 1
    assert out[0]["route_id"] == "23"
    assert out[0]["message"] == "Detour in effect"


@pytest.mark.asyncio
async def test_indego_merge():
    info = {"data": {"stations": [
        {"station_id": "1", "name": "Dock A", "lat": 39.95, "lon": -75.16},
    ]}}
    status = {"data": {"stations": [
        {"station_id": "1", "num_bikes_available": 3, "num_docks_available": 10,
         "is_renting": True, "is_returning": True},
    ]}}
    merged = indego._merge(info["data"]["stations"], status["data"]["stations"])
    assert merged[0]["bikes"] == 3
    assert merged[0]["name"] == "Dock A"


@pytest.mark.asyncio
async def test_penndot_normalize_filters_status():
    features = [{
        "attributes": {
            "STATEWIDE_ID": "123",
            "LOCATION_DESC": "I-95 @ Cottman",
            "LATITUDE": 39.96,
            "LONGITUDE": -75.16,
            "STATUS_NAME": "EXISTING",
            "CTY_NAME": "PHILADELPHIA",
        },
    }]
    out = penndot.normalize(features, 39.95, -75.16, 50.0)
    assert len(out) == 1
    assert out[0].source == "penndot"
    assert "511pa.com" in (out[0].url or "")
