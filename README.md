# GRIDLAND

Public infrastructure visibility platform — a CesiumJS 3D globe over a FastAPI backend that aggregates publicly exposed cameras, real-time aircraft, and contextual data from zero-auth and free-tier APIs.

## Status

v0.1 — working baseline. Implemented sources:

| Layer       | Source       | Auth | Module |
|-------------|--------------|------|--------|
| Discovery   | OSM Overpass | none | `backend.discovery.sources.osm` |
| Realtime    | ADSB.fi      | none | `backend.pipeline.sources.adsb_fi` |
| Context     | NWS          | none | `backend.context.sources.nws` |
| Context     | Wikipedia    | none | `backend.context.sources.wikipedia` |

Additional sources (FCC ASR, Mapillary, GreyNoise, ARIN RDAP, Celestrak, NASA FIRMS, Transitland, AISHub, Blitzortung) have technical references in `docs/GRIDLAND-5.md` through `docs/GRIDLAND-8.md` and are unimplemented placeholders for the same source-and-normalize pattern used by the modules listed above.

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
| GET | `/api/discover` | `lat`, `lon`, `radius_km` | `DiscoveryResponse` |
| GET | `/api/context` | `lat`, `lon` | `ContextBundle` |
| WS  | `/ws/live` | subscribe with `{lat, lon, distance_nm}` | aircraft frames every `realtime_poll_interval_s` |

## Compliance

Enforced by `backend.compliance.guardrails` and tested in `tests/test_compliance.py`:

1. Reject any URL whose host is an RFC-1918, loopback, link-local, multicast, reserved, or RFC-5737 documentation IP.
2. Reject any URL embedding credentials (`user:pass@host`).
3. Drop sources whose ARIN org label matches residential ISP patterns.
4. Every `CameraResult` with a `thumbnail_url` must declare `blur_required: bool`.
5. Every record carries `fetched_at` (ISO 8601, UTC).

Compliance is applied as a final gate in `backend.discovery.service.search_area`.

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
