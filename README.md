# GRIDLAND

Public infrastructure visibility platform — a CesiumJS 3D globe over a FastAPI backend that aggregates publicly exposed cameras, real-time aircraft, and contextual data from zero-auth and free-tier APIs.

## Status

v0.3 — Implemented sources:

| Layer       | Source       | Auth | Module | Publication |
|-------------|--------------|------|--------|-------------|
| Discovery   | OSM Overpass             | none | `backend.discovery.sources.osm`        | directory_listed |
| Discovery   | Caltrans CCTV (12 districts) | none | `backend.discovery.sources.caltrans`  | operator_published |
| Discovery   | WSDOT HighwayCameras     | free key (`WSDOT_API_KEY`) | `backend.discovery.sources.wsdot`     | operator_published |
| Discovery   | 511NY (NYSDOT)           | free key (`N511NY_API_KEY`) | `backend.discovery.sources.n511ny`   | operator_published |
| Discovery   | LiveCam Registry (NPS, USGS, Cornell, Explore, Smithsonian, MBA) | none | `backend.discovery.sources.livecams` | operator_published |
| Discovery   | NYC TMC traffic cameras (~948, all five boroughs) | none | `backend.discovery.sources.nyctmc` | operator_published |
| Discovery   | Castle Rock 511 (511 Ontario ~928, 511 Alberta ~367, extensible) | none | `backend.discovery.sources.castlerock_511` | operator_published |
| Discovery   | NPS Webcams (national park system) | free key (`NPS_API_KEY`) | `backend.discovery.sources.nps_webcams` | operator_published |
| Photosphere | Mapillary v4 (panos near point) | free key (`MAPILLARY_API_KEY`) | `backend.discovery.sources.mapillary` | operator_published |
| Realtime    | ADSB.fi (aircraft)       | none | `backend.pipeline.sources.adsb_fi`     | n/a |
| Realtime    | Celestrak (satellite TLE; client-side SGP4) | none | `backend.pipeline.sources.celestrak` | n/a |
| Realtime    | SEPTA TransitView + TrainView (Philly live transit) | none | `backend.pipeline.sources.septa_vehicles` | n/a |
| Context     | NWS forecast + alerts    | none | `backend.context.sources.nws`          | n/a |
| Context     | Wikipedia GeoSearch      | none | `backend.context.sources.wikipedia`    | n/a |
| Context     | USGS Earthquakes (FDSN)  | none | `backend.context.sources.usgs`         | n/a |
| Context     | NASA FIRMS (active fires) | free key (`NASA_FIRMS_MAP_KEY`) | `backend.context.sources.firms`     | n/a |
| Context     | OpenAQ v3 (air quality)  | free key (`OPENAQ_API_KEY`) | `backend.context.sources.openaq`        | n/a |
| Context     | aviationweather.gov METARs | none | `backend.context.sources.aviation`    | n/a |
| Context     | SEPTA service alerts (Philly)  | none | `backend.context.sources.septa_alerts` | n/a |
| Context     | Philadelphia 311 service requests | none | `backend.context.sources.philly311`    | n/a |
| Context     | USGS Water Services (stream gauges) | none | `backend.context.sources.usgs_water`   | n/a |
| Imagery     | NASA GIBS WMTS overlays (clouds / fires / AOD) | none | `src/frontend/cesium/gibs.js` | n/a |

Sources that require a free API key self-skip (return `[]`) when the key isn't set, so the system runs out of the box with no keys configured. Add keys in `.env` (see `config/.env.example`) to light them up.

## Quick start

```bash
make setup        # creates .venv, pip install -r requirements.txt, npm install
make test         # pytest (mocked HTTP, no network)
make backend &    # uvicorn on :8000
make frontend     # vite dev server on :5173 (proxies /api and /ws to :8000)
```

Or with Docker:

```bash
docker compose up --build
# backend → http://localhost:8000  ·  frontend → http://localhost
```

## HTTP API

| Method | Path | Params | Returns |
|--------|------|--------|---------|
| GET | `/health` | — | `{ "status": "ok", "version": "..." }` |
| GET | `/api/discover` | `lat`, `lon`, `radius_km` | `DiscoveryResponse` (CameraResult list across all 5 discovery sources) |
| GET | `/api/context` | `lat`, `lon` | `ContextBundle` (NWS + Wikipedia + USGS quakes + FIRMS fires + OpenAQ + METARs) |
| GET | `/api/photospheres` | `lat`, `lon`, `radius_m`, `limit` | `{ items: [...] }` (Mapillary panos; empty without key) |
| GET | `/api/satellites` | `group`, `limit` | `{ items: [{name, line1, line2}, ...] }` (Celestrak TLEs; SGP4 happens client-side) |
| GET | `/api/satellites/catalogs` | — | `{ catalogs: ["stations", "active", ...] }` |
| GET | `/api/septa/vehicles` | — | `{ count, bus_trolley, regional_rail, vehicles: [...] }` (live SEPTA bus/trolley/rail positions) |
| GET | `/api/whats_here` | `lat`, `lon`, `radius_km`, `photosphere_radius_m` | aggregated cameras + context + photospheres at a point |
| WS  | `/ws/live` | subscribe with `{lat, lon, distance_nm}` | first frame `kind:"snapshot"`, subsequent `kind:"diff"` (added/updated/removed by `icao24`) |

## Compliance

Enforced by `backend.compliance.guardrails` and tested in `tests/test_compliance.py`:

1. Reject any URL whose host is an RFC-1918, loopback, link-local, multicast, reserved, or RFC-5737 documentation IP.
2. Reject any URL embedding credentials (`user:pass@host`).
3. Drop sources whose ARIN org label matches residential ISP patterns.
4. Every `CameraResult` with a `thumbnail_url` must declare `blur_required: bool`.
5. Every record carries `fetched_at` (ISO 8601, UTC).
6. Every `CameraResult` carries a `publication_status`: `operator_published`, `directory_listed`, or `crowdsourced` — provenance attached to every output row.

Compliance is applied as a final gate in `backend.discovery.service.search_area`.

## Caching

`backend.shared.cache.TTLCache` provides single-flight (stampede-protected) per-URL caching. Per-source TTLs are configurable in `backend.settings`:

| Source | Default TTL |
|--------|-------------|
| Overpass            | 5 min  |
| DOT JSON (Caltrans/WSDOT/511NY) | 1 min  |
| NWS forecast        | 15 min |
| NWS alerts          | 1 min  |
| Wikipedia GeoSearch | 1 h    |
| Mapillary panos     | 10 min |
| USGS quakes         | 5 min  |
| NASA FIRMS fires    | 10 min |
| OpenAQ v3           | 10 min |
| METARs              | 5 min  |
| Celestrak TLE       | 6 h    |

## Configuration

`config/.env.example` documents every environment variable. None of the implemented sources require a key. Keys for unimplemented v2 sources are documented for completeness in `config/api-keys.example.json`.

## Repository layout

```
src/backend/
  main.py             FastAPI app
  settings.py         pydantic-settings
  shared/             httpx client, constants
  compliance/         guardrails.py, policy.json
  discovery/          models.py, service.py, sources/osm.py
  pipeline/           models.py, service.py, sources/adsb_fi.py
  context/            models.py, service.py, sources/{nws,wikipedia}.py
  api/                discovery.py, context.py, realtime.py (WS)

src/frontend/
  main.js             entry
  cesium/viewer.js    Ion-free Cesium viewer
  entities/           cameras.js, aircraft.js
  api.js, ws.js, style.css

tests/                pytest, all upstream HTTP mocked
docs/                 GRIDLAND-5..8 technical references
.mycelium/            change log (see CLAUDE.md)
```

## License

MIT. See `LICENSE`.
