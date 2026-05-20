import pytest

from backend.discovery.sources import mapillary
from backend.settings import reset_settings_cache


_PANO_PAYLOAD = {
    "data": [
        {"id": "img1", "captured_at": 1700000000,
         "compass_angle": 90.0, "is_pano": True,
         "sequence_id": "seq1",
         "thumb_2048_url": "https://images.mapillary.com/img1.jpg",
         "geometry": {"type": "Point", "coordinates": [-75.16, 39.95]}},
        {"id": "img2", "captured_at": 1700000001,
         "compass_angle": 100.0, "is_pano": True,
         "geometry": {"type": "Point", "coordinates": [-75.17, 39.95]},
         "thumb_2048_url": "https://images.mapillary.com/img2.jpg"},
        {"id": "noloc", "geometry": {}, "is_pano": True},  # filtered
    ]
}


@pytest.mark.asyncio
async def test_panos_skipped_without_key(monkeypatch):
    monkeypatch.delenv("MAPILLARY_API_KEY", raising=False)
    reset_settings_cache()
    out = await mapillary.panos_near(39.95, -75.16)
    assert out == []
    reset_settings_cache()


@pytest.mark.asyncio
async def test_panos_with_mocked_key(monkeypatch):
    monkeypatch.setenv("MAPILLARY_API_KEY", "TESTKEY")
    reset_settings_cache()

    async def fake_get_json(url, **kw):
        return _PANO_PAYLOAD
    monkeypatch.setattr(mapillary, "get_json", fake_get_json)
    out = await mapillary.panos_near(39.95, -75.16)
    assert len(out) == 2
    assert {p["id"] for p in out} == {"img1", "img2"}
    assert out[0]["thumb_2048_url"].startswith("https://images.mapillary.com")
    reset_settings_cache()


@pytest.mark.asyncio
async def test_photosphere_route(client, monkeypatch):
    monkeypatch.setenv("MAPILLARY_API_KEY", "TESTKEY")
    reset_settings_cache()

    async def fake_get_json(url, **kw):
        return _PANO_PAYLOAD
    monkeypatch.setattr(mapillary, "get_json", fake_get_json)
    r = client.get("/api/photospheres",
                   params={"lat": 39.95, "lon": -75.16, "radius_m": 250, "limit": 10})
    assert r.status_code == 200
    body = r.json()
    assert body["count"] == 2
    reset_settings_cache()
