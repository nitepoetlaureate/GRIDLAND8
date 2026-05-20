import pytest

from backend.context import service as ctx_service
from backend.context.sources import nws, wikipedia


_NWS_POINT = {
    "properties": {
        "forecast": "https://api.weather.gov/gridpoints/PHI/49,75/forecast",
    }
}

_NWS_FORECAST = {
    "properties": {
        "periods": [
            {"name": "Today", "shortForecast": "Sunny", "temperature": 72,
             "windSpeed": "5 mph", "detailedForecast": "Sunny with light wind."},
            {"name": "Tonight", "shortForecast": "Clear", "temperature": 55,
             "windSpeed": "3 mph", "detailedForecast": "Clear sky."},
        ]
    }
}

_NWS_ALERTS = {
    "features": [
        {"id": "urn:oid:1", "properties": {
            "event": "Flood Watch", "severity": "Moderate",
            "urgency": "Expected", "headline": "Flood Watch in effect",
            "effective": "2026-05-20T00:00:00Z", "expires": "2026-05-21T00:00:00Z",
        }}
    ]
}

_WIKI = {
    "query": {
        "geosearch": [
            {"pageid": 1, "title": "Independence Hall", "lat": 39.949, "lon": -75.15, "dist": 500},
            {"pageid": 2, "title": "Liberty Bell", "lat": 39.949, "lon": -75.15, "dist": 510},
        ]
    }
}


@pytest.mark.asyncio
async def test_nws_forecast_two_step(monkeypatch):
    calls = {"n": 0}

    async def fake_get_json(url, **kwargs):
        calls["n"] += 1
        if "/points/" in url:
            return _NWS_POINT
        return _NWS_FORECAST

    monkeypatch.setattr(nws, "get_json", fake_get_json)
    forecast = await nws.forecast(39.95, -75.16)
    assert forecast is not None
    assert forecast["now"] == "Sunny"
    assert forecast["temperature_f"] == 72
    assert calls["n"] == 2


@pytest.mark.asyncio
async def test_nws_forecast_outside_us_returns_none(monkeypatch):
    async def fake_get_json(url, **kwargs):
        return None  # NWS 404 for non-US

    monkeypatch.setattr(nws, "get_json", fake_get_json)
    forecast = await nws.forecast(48.85, 2.35)
    assert forecast is None


@pytest.mark.asyncio
async def test_nws_alerts(monkeypatch):
    async def fake_get_json(url, **kwargs):
        return _NWS_ALERTS

    monkeypatch.setattr(nws, "get_json", fake_get_json)
    alerts = await nws.active_alerts(39.95, -75.16)
    assert len(alerts) == 1
    assert alerts[0]["event"] == "Flood Watch"


@pytest.mark.asyncio
async def test_wikipedia_nearby(monkeypatch):
    async def fake_get_json(url, **kwargs):
        return _WIKI

    monkeypatch.setattr(wikipedia, "get_json", fake_get_json)
    out = await wikipedia.nearby(39.95, -75.16, radius_m=2000, limit=10)
    assert len(out) == 2
    assert out[0]["title"] == "Independence Hall"
    assert out[0]["url"].startswith("https://en.wikipedia.org/?curid=")


def _stub_extra_sources(monkeypatch):
    """Stub the non-NWS/non-Wikipedia sources so they don't hit the network."""
    async def empty_list(*a, **k): return []
    monkeypatch.setattr(ctx_service.usgs, "recent_quakes", empty_list)
    monkeypatch.setattr(ctx_service.firms, "active_fires", empty_list)
    monkeypatch.setattr(ctx_service.openaq, "nearby_aq", empty_list)
    monkeypatch.setattr(ctx_service.aviation, "metars", empty_list)
    monkeypatch.setattr(ctx_service.septa_alerts, "near", empty_list)
    monkeypatch.setattr(ctx_service.philly311, "recent", empty_list)
    monkeypatch.setattr(ctx_service.usgs_water, "gauges_near", empty_list)


@pytest.mark.asyncio
async def test_context_service_aggregates(monkeypatch):
    async def fake_forecast(lat, lon): return {"now": "Cloudy"}
    async def fake_alerts(lat, lon): return [{"event": "Wind Advisory"}]
    async def fake_wiki(lat, lon, **kw): return [{"title": "X"}]

    monkeypatch.setattr(ctx_service.nws, "forecast", fake_forecast)
    monkeypatch.setattr(ctx_service.nws, "active_alerts", fake_alerts)
    monkeypatch.setattr(ctx_service.wikipedia, "nearby", fake_wiki)
    _stub_extra_sources(monkeypatch)
    bundle = await ctx_service.gather(39.95, -75.16)
    assert bundle.weather == {"now": "Cloudy"}
    assert len(bundle.alerts) == 1
    assert len(bundle.wikipedia) == 1
    assert bundle.quakes == []
    assert bundle.fires == []
    assert bundle.air_quality == []
    assert bundle.metars == []
    assert not bundle.errors


@pytest.mark.asyncio
async def test_context_service_isolates_failures(monkeypatch):
    async def boom(*a, **k): raise RuntimeError("upstream down")
    async def fake_wiki(lat, lon, **kw): return [{"title": "X"}]

    monkeypatch.setattr(ctx_service.nws, "forecast", boom)
    monkeypatch.setattr(ctx_service.nws, "active_alerts", boom)
    monkeypatch.setattr(ctx_service.wikipedia, "nearby", fake_wiki)
    _stub_extra_sources(monkeypatch)
    bundle = await ctx_service.gather(39.95, -75.16)
    assert bundle.weather is None
    assert bundle.alerts == []
    assert bundle.wikipedia == [{"title": "X"}]
    assert "weather" in bundle.errors
