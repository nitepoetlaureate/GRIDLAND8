# GRIDLAND Mycelium Changelog

This file is automatically appended by .mycelium/record.py after every file modification.
Format: timestamp — agent (phase) — filename — rationale

---

### 2026-05-20T06:51:20.718903+00:00 — cursor-opus (primary) — `pyproject.toml`
**Entry ID:** myc_202605200651200000
pyproject.toml with build system, pytest config (asyncio auto, src/ on path)
---

### 2026-05-20T06:51:20.771663+00:00 — cursor-opus (primary) — `main.py`
**Entry ID:** myc_202605200651200001
FastAPI app entry: create_app(), CORS middleware, registered /api/discover /api/context /ws/live /health
---

### 2026-05-20T06:51:20.825368+00:00 — cursor-opus (primary) — `settings.py`
**Entry ID:** myc_202605200651200002
pydantic-settings: host/port/cors/http/realtime/lat/lon/radius + all upstream API key slots
---

### 2026-05-20T06:51:20.877495+00:00 — cursor-opus (primary) — `http.py`
**Entry ID:** myc_202605200651200003
Shared async httpx client with timeout/retry/backoff; get_json and post_json never raise to callers; common User-Agent
---

### 2026-05-20T06:51:20.931098+00:00 — cursor-opus (primary) — `constants.py`
**Entry ID:** myc_202605200651200004
USER_AGENT plus source identifiers and normalized response field names; single source of truth for string literals
---

### 2026-05-20T06:51:20.987041+00:00 — cursor-opus (primary) — `guardrails.py`
**Entry ID:** myc_202605200651200005
RFC-1918/loopback/link-local/reserved/RFC-5737 host rejection, credential-in-url detection, residential-org regex set, blur_required and fetched_at validators, filter_compliant gate
---

### 2026-05-20T06:51:21.041267+00:00 — cursor-opus (primary) — `policy.json`
**Entry ID:** myc_202605200651210006
Policy data: RFC-1918 blocks, residential patterns, required fields per entity
---

### 2026-05-20T06:51:21.094996+00:00 — cursor-opus (primary) — `models.py`
**Entry ID:** myc_202605200651210007
CameraResult pydantic v2 model with lat/lon validation and url-no-creds field_validator; DiscoveryResponse wrapper
---

### 2026-05-20T06:51:21.148185+00:00 — cursor-opus (primary) — `osm.py`
**Entry ID:** myc_202605200651210008
OSM Overpass adapter: triple-mirror failover, bbox math, normalize() strips credentialed urls and validates via pydantic
---

### 2026-05-20T06:51:21.202612+00:00 — cursor-opus (primary) — `service.py`
**Entry ID:** myc_202605200651210009
search_area() fans out to sources concurrently then runs compliance.filter_compliant gate
---

### 2026-05-20T06:51:35.610480+00:00 — cursor-opus (primary) — `models.py`
**Entry ID:** myc_202605200651350010
Aircraft pydantic model with lat/lon validation
---

### 2026-05-20T06:51:35.672794+00:00 — cursor-opus (primary) — `adsb_fi.py`
**Entry ID:** myc_202605200651350011
ADSB.fi (no auth) adapter: ft->m and kt->m/s conversion, ground vs airborne handling, skips invalid records
---

### 2026-05-20T06:51:35.727533+00:00 — cursor-opus (primary) — `service.py`
**Entry ID:** myc_202605200651350012
aircraft_snapshot() returns envelope {type, ts, query, count, items} for WS broadcast
---

### 2026-05-20T06:51:35.783177+00:00 — cursor-opus (primary) — `models.py`
**Entry ID:** myc_202605200651350013
ContextBundle: weather, alerts, wikipedia, fetched_at, per-source errors
---

### 2026-05-20T06:51:35.837483+00:00 — cursor-opus (primary) — `nws.py`
**Entry ID:** myc_202605200651350014
NWS two-step forecast (points -> forecast) and /alerts/active endpoint; degrades to None outside US coverage
---

### 2026-05-20T06:51:35.892956+00:00 — cursor-opus (primary) — `wikipedia.py`
**Entry ID:** myc_202605200651350015
Wikipedia GeoSearch (no auth); returns title/lat/lon/distance/url
---

### 2026-05-20T06:51:35.949426+00:00 — cursor-opus (primary) — `service.py`
**Entry ID:** myc_202605200651350016
Parallel gather() with per-source exception isolation; failed sources show in errors dict, not aborting
---

### 2026-05-20T06:51:36.003699+00:00 — cursor-opus (primary) — `discovery.py`
**Entry ID:** myc_202605200651360017
GET /api/discover with lat/lon/radius_km validation, returns DiscoveryResponse
---

### 2026-05-20T06:51:36.056823+00:00 — cursor-opus (primary) — `context.py`
**Entry ID:** myc_202605200651360018
GET /api/context returns ContextBundle
---

### 2026-05-20T06:51:36.111044+00:00 — cursor-opus (primary) — `realtime.py`
**Entry ID:** myc_202605200651360019
WS /ws/live: capacity limit, JSON subscription, periodic aircraft snapshots, never crashes the loop on transient errors
---

### 2026-05-20T06:51:51.979616+00:00 — cursor-opus (primary) — `conftest.py`
**Entry ID:** myc_202605200651510020
Puts src/ on sys.path; client fixture wrapping create_app()
---

### 2026-05-20T06:51:52.035036+00:00 — cursor-opus (primary) — `test_app.py`
**Entry ID:** myc_202605200651520021
Health endpoint + OpenAPI spec sanity
---

### 2026-05-20T06:51:52.091635+00:00 — cursor-opus (primary) — `test_compliance.py`
**Entry ID:** myc_202605200651520022
27 assertions: private IPs (RFC-1918/loopback/link-local/IPv6/docs), URL credentials, residential ARIN orgs, blur+fetched_at
---

### 2026-05-20T06:51:52.146492+00:00 — cursor-opus (primary) — `test_discovery_osm.py`
**Entry ID:** myc_202605200651520023
OSM normalize: non-nodes filtered, credentialed urls stripped, mocked Overpass and mirror-failure paths, end-to-end compliance via service.search_area
---

### 2026-05-20T06:51:52.199867+00:00 — cursor-opus (primary) — `test_pipeline_adsb.py`
**Entry ID:** myc_202605200651520024
ADSB.fi normalize: ft->m, kt->m/s, ground sentinel, invalid records dropped, aircraft_snapshot envelope
---

### 2026-05-20T06:51:52.254125+00:00 — cursor-opus (primary) — `test_context.py`
**Entry ID:** myc_202605200651520025
NWS two-step, outside-US 404, alerts, wikipedia, context.gather aggregation and per-source failure isolation
---

### 2026-05-20T06:51:52.312002+00:00 — cursor-opus (primary) — `test_api_routes.py`
**Entry ID:** myc_202605200651520026
Route smoke tests for /api/discover (incl 422 on invalid lat) and /api/context
---

### 2026-05-20T06:51:52.367599+00:00 — cursor-opus (primary) — `index.html`
**Entry ID:** myc_202605200651520027
Vite entry; HUD with lat/lon/radius inputs, status, counts, context panel; loads main.js as ES module
---

### 2026-05-20T06:51:52.421834+00:00 — cursor-opus (primary) — `vite.config.js`
**Entry ID:** myc_202605200651520028
vite-plugin-cesium; proxy /api->8000 and /ws->8000 for dev parity with Docker
---

### 2026-05-20T06:51:52.475169+00:00 — cursor-opus (primary) — `style.css`
**Entry ID:** myc_202605200651520029
Dark monospace HUD with status color states (ok/warn/error)
---

### 2026-05-20T06:52:17.386980+00:00 — cursor-opus (primary) — `api.js`
**Entry ID:** myc_202605200652170030
REST client: discover/context/health
---

### 2026-05-20T06:52:17.438563+00:00 — cursor-opus (primary) — `ws.js`
**Entry ID:** myc_202605200652170031
LiveSocket with auto-reconnect (exp backoff to 30s), status callbacks, resubscribe on subscription change
---

### 2026-05-20T06:52:17.494974+00:00 — cursor-opus (primary) — `viewer.js`
**Entry ID:** myc_202605200652170032
Ion-free Cesium viewer: OSM imagery, no terrain, minimal widget chrome; flyTo helper
---

### 2026-05-20T06:52:17.550447+00:00 — cursor-opus (primary) — `aircraft.js`
**Entry ID:** myc_202605200652170033
AircraftLayer reconciles incoming snapshots; reuses entities by icao24; expires stale > 30s
---

### 2026-05-20T06:52:17.605574+00:00 — cursor-opus (primary) — `cameras.js`
**Entry ID:** myc_202605200652170034
CameraLayer: billboards pinned to lat/lon with relative-to-ground height reference
---

### 2026-05-20T06:52:17.657073+00:00 — cursor-opus (primary) — `main.js`
**Entry ID:** myc_202605200652170035
Boot: health probe, viewer init, live socket subscribe, scan() drives discovery+context+resubscribe in parallel
---

### 2026-05-20T06:52:17.710206+00:00 — cursor-opus (primary) — `Dockerfile.backend`
**Entry ID:** myc_202605200652170036
Python 3.11-slim, PYTHONPATH=/app/src, curl health-check, uvicorn entry
---

### 2026-05-20T06:52:17.765971+00:00 — cursor-opus (primary) — `Dockerfile.frontend`
**Entry ID:** myc_202605200652170037
Node 20 build -> nginx:alpine; nginx serves /api and /ws via proxy_pass to backend
---

### 2026-05-20T06:52:17.821084+00:00 — cursor-opus (primary) — `nginx.conf`
**Entry ID:** myc_202605200652170038
Frontend container proxy: /api->backend:8000, /ws->backend:8000 with Upgrade headers, SPA fallback
---

### 2026-05-20T06:52:17.875116+00:00 — cursor-opus (primary) — `docker-compose.yml`
**Entry ID:** myc_202605200652170039
Backend + frontend services, frontend depends_on backend healthcheck
---

### 2026-05-20T06:52:17.926970+00:00 — cursor-opus (primary) — `ci.yml`
**Entry ID:** myc_202605200652170040
CI: pytest on Python 3.11 and Vite build on Node 20
---

### 2026-05-20T06:52:17.981840+00:00 — cursor-opus (primary) — `LICENSE`
**Entry ID:** myc_202605200652170041
MIT license restoring the claim made in README
---

### 2026-05-20T06:52:18.039940+00:00 — cursor-opus (primary) — `Makefile`
**Entry ID:** myc_202605200652180042
Convenience targets: setup/test/backend/frontend/docker/clean
---

### 2026-05-20T06:52:18.093172+00:00 — cursor-opus (primary) — `requirements.txt`
**Entry ID:** myc_202605200652180043
Repinned to 2026-era versions of FastAPI/pydantic/httpx; removed unused boto3/jose/mmh3/responses/psutil
---

### 2026-05-20T06:52:18.147311+00:00 — cursor-opus (primary) — `package.json`
**Entry ID:** myc_202605200652180044
Removed broken eslint --ext lint script; node engine >=20; trimmed unused deps
---

### 2026-05-20T06:52:18.202259+00:00 — cursor-opus (primary) — `README.md`
**Entry ID:** myc_202605200652180045
Rewrote: status table of implemented sources, real quick-start, API table, compliance summary, repo layout
---

### 2026-05-20T06:52:18.257004+00:00 — cursor-opus (primary) — `CLAUDE.md`
**Entry ID:** myc_202605200652180046
Stripped to: Mycelium protocol, project conventions, and per-domain how-to-add-a-source recipes
---

### 2026-05-20T06:52:18.309020+00:00 — cursor-opus (primary) — `CLAUDE.md`
**Entry ID:** myc_202605200652180047
Reduced to a pointer to /CLAUDE.md plus the Mycelium requirement
---

### 2026-05-20T06:55:43.207977+00:00 — cursor-opus (primary) — `README.md`
**Entry ID:** myc_202605200655430048
Documents how to relocate ci.yml back to .github/workflows after granting workflow scope to gh
---

### 2026-05-20T06:55:43.264593+00:00 — cursor-opus (qa_gate) — `.`
**Entry ID:** myc_202605200655430049
48/48 tests passing locally; vite build succeeds (Cesium assets emitted to dist/cesium 15M); FastAPI app imports and registers all 4 routes; initial commit 0a8b87a pushed to github.com/nitepoetlaureate/GRIDLAND8
---
