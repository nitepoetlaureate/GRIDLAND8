# GRIDLAND Mycelium Changelog

Generated from .mycelium/log.json. Do not edit by hand.

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

### 2026-05-20T03:34:17-04:00 — cursor-opus (primary) — `record.py` [84e843e]
**Entry ID:** myc_202605200734170050
Expand to 5 new sources, add cache + WS diffing, upgrade Mycelium to auto-record via git trailers (the change that makes its own bookkeeping stop being voluntary)
---

### 2026-05-20T03:34:17-04:00 — cursor-opus (primary) — `CLAUDE.md` [84e843e]
**Entry ID:** myc_202605200734170051
Expand to 5 new sources, add cache + WS diffing, upgrade Mycelium to auto-record via git trailers (the change that makes its own bookkeeping stop being voluntary)
---

### 2026-05-20T03:34:17-04:00 — cursor-opus (primary) — `Makefile` [84e843e]
**Entry ID:** myc_202605200734170052
Expand to 5 new sources, add cache + WS diffing, upgrade Mycelium to auto-record via git trailers (the change that makes its own bookkeeping stop being voluntary)
---

### 2026-05-20T03:34:17-04:00 — cursor-opus (primary) — `README.md` [84e843e]
**Entry ID:** myc_202605200734170053
Expand to 5 new sources, add cache + WS diffing, upgrade Mycelium to auto-record via git trailers (the change that makes its own bookkeeping stop being voluntary)
---

### 2026-05-20T03:34:17-04:00 — cursor-opus (primary) — `.env.example` [84e843e]
**Entry ID:** myc_202605200734170054
Expand to 5 new sources, add cache + WS diffing, upgrade Mycelium to auto-record via git trailers (the change that makes its own bookkeeping stop being voluntary)
---

### 2026-05-20T03:34:17-04:00 — cursor-opus (primary) — `package-lock.json` [84e843e]
**Entry ID:** myc_202605200734170055
Expand to 5 new sources, add cache + WS diffing, upgrade Mycelium to auto-record via git trailers (the change that makes its own bookkeeping stop being voluntary)
---

### 2026-05-20T03:34:17-04:00 — cursor-opus (primary) — `package.json` [84e843e]
**Entry ID:** myc_202605200734170056
Expand to 5 new sources, add cache + WS diffing, upgrade Mycelium to auto-record via git trailers (the change that makes its own bookkeeping stop being voluntary)
---

### 2026-05-20T03:34:17-04:00 — cursor-opus (primary) — `commit-msg` [84e843e]
**Entry ID:** myc_202605200734170057
Expand to 5 new sources, add cache + WS diffing, upgrade Mycelium to auto-record via git trailers (the change that makes its own bookkeeping stop being voluntary)
---

### 2026-05-20T03:34:17-04:00 — cursor-opus (primary) — `post-commit` [84e843e]
**Entry ID:** myc_202605200734170058
Expand to 5 new sources, add cache + WS diffing, upgrade Mycelium to auto-record via git trailers (the change that makes its own bookkeeping stop being voluntary)
---

### 2026-05-20T03:34:17-04:00 — cursor-opus (primary) — `pre-push` [84e843e]
**Entry ID:** myc_202605200734170059
Expand to 5 new sources, add cache + WS diffing, upgrade Mycelium to auto-record via git trailers (the change that makes its own bookkeeping stop being voluntary)
---

### 2026-05-20T03:34:17-04:00 — cursor-opus (primary) — `install-hooks.sh` [84e843e]
**Entry ID:** myc_202605200734170060
Expand to 5 new sources, add cache + WS diffing, upgrade Mycelium to auto-record via git trailers (the change that makes its own bookkeeping stop being voluntary)
---

### 2026-05-20T03:34:17-04:00 — cursor-opus (primary) — `photosphere.py` [84e843e]
**Entry ID:** myc_202605200734170061
Expand to 5 new sources, add cache + WS diffing, upgrade Mycelium to auto-record via git trailers (the change that makes its own bookkeeping stop being voluntary)
---

### 2026-05-20T03:34:17-04:00 — cursor-opus (primary) — `realtime.py` [84e843e]
**Entry ID:** myc_202605200734170062
Expand to 5 new sources, add cache + WS diffing, upgrade Mycelium to auto-record via git trailers (the change that makes its own bookkeeping stop being voluntary)
---

### 2026-05-20T03:34:17-04:00 — cursor-opus (primary) — `models.py` [84e843e]
**Entry ID:** myc_202605200734170063
Expand to 5 new sources, add cache + WS diffing, upgrade Mycelium to auto-record via git trailers (the change that makes its own bookkeeping stop being voluntary)
---

### 2026-05-20T03:34:17-04:00 — cursor-opus (primary) — `service.py` [84e843e]
**Entry ID:** myc_202605200734170064
Expand to 5 new sources, add cache + WS diffing, upgrade Mycelium to auto-record via git trailers (the change that makes its own bookkeeping stop being voluntary)
---

### 2026-05-20T03:34:17-04:00 — cursor-opus (primary) — `caltrans.py` [84e843e]
**Entry ID:** myc_202605200734170065
Expand to 5 new sources, add cache + WS diffing, upgrade Mycelium to auto-record via git trailers (the change that makes its own bookkeeping stop being voluntary)
---

### 2026-05-20T03:34:17-04:00 — cursor-opus (primary) — `livecams.py` [84e843e]
**Entry ID:** myc_202605200734170066
Expand to 5 new sources, add cache + WS diffing, upgrade Mycelium to auto-record via git trailers (the change that makes its own bookkeeping stop being voluntary)
---

### 2026-05-20T03:34:17-04:00 — cursor-opus (primary) — `mapillary.py` [84e843e]
**Entry ID:** myc_202605200734170067
Expand to 5 new sources, add cache + WS diffing, upgrade Mycelium to auto-record via git trailers (the change that makes its own bookkeeping stop being voluntary)
---

### 2026-05-20T03:34:17-04:00 — cursor-opus (primary) — `n511ny.py` [84e843e]
**Entry ID:** myc_202605200734170068
Expand to 5 new sources, add cache + WS diffing, upgrade Mycelium to auto-record via git trailers (the change that makes its own bookkeeping stop being voluntary)
---

### 2026-05-20T03:34:17-04:00 — cursor-opus (primary) — `osm.py` [84e843e]
**Entry ID:** myc_202605200734170069
Expand to 5 new sources, add cache + WS diffing, upgrade Mycelium to auto-record via git trailers (the change that makes its own bookkeeping stop being voluntary)
---

### 2026-05-20T03:34:17-04:00 — cursor-opus (primary) — `wsdot.py` [84e843e]
**Entry ID:** myc_202605200734170070
Expand to 5 new sources, add cache + WS diffing, upgrade Mycelium to auto-record via git trailers (the change that makes its own bookkeeping stop being voluntary)
---

### 2026-05-20T03:34:17-04:00 — cursor-opus (primary) — `main.py` [84e843e]
**Entry ID:** myc_202605200734170071
Expand to 5 new sources, add cache + WS diffing, upgrade Mycelium to auto-record via git trailers (the change that makes its own bookkeeping stop being voluntary)
---

### 2026-05-20T03:34:17-04:00 — cursor-opus (primary) — `diff.py` [84e843e]
**Entry ID:** myc_202605200734170072
Expand to 5 new sources, add cache + WS diffing, upgrade Mycelium to auto-record via git trailers (the change that makes its own bookkeeping stop being voluntary)
---

### 2026-05-20T03:34:17-04:00 — cursor-opus (primary) — `settings.py` [84e843e]
**Entry ID:** myc_202605200734170073
Expand to 5 new sources, add cache + WS diffing, upgrade Mycelium to auto-record via git trailers (the change that makes its own bookkeeping stop being voluntary)
---

### 2026-05-20T03:34:17-04:00 — cursor-opus (primary) — `cache.py` [84e843e]
**Entry ID:** myc_202605200734170074
Expand to 5 new sources, add cache + WS diffing, upgrade Mycelium to auto-record via git trailers (the change that makes its own bookkeeping stop being voluntary)
---

### 2026-05-20T03:34:17-04:00 — cursor-opus (primary) — `constants.py` [84e843e]
**Entry ID:** myc_202605200734170075
Expand to 5 new sources, add cache + WS diffing, upgrade Mycelium to auto-record via git trailers (the change that makes its own bookkeeping stop being voluntary)
---

### 2026-05-20T03:34:17-04:00 — cursor-opus (primary) — `http.py` [84e843e]
**Entry ID:** myc_202605200734170076
Expand to 5 new sources, add cache + WS diffing, upgrade Mycelium to auto-record via git trailers (the change that makes its own bookkeeping stop being voluntary)
---

### 2026-05-20T03:34:17-04:00 — cursor-opus (primary) — `aircraft.js` [84e843e]
**Entry ID:** myc_202605200734170077
Expand to 5 new sources, add cache + WS diffing, upgrade Mycelium to auto-record via git trailers (the change that makes its own bookkeeping stop being voluntary)
---

### 2026-05-20T03:34:17-04:00 — cursor-opus (primary) — `main.js` [84e843e]
**Entry ID:** myc_202605200734170078
Expand to 5 new sources, add cache + WS diffing, upgrade Mycelium to auto-record via git trailers (the change that makes its own bookkeeping stop being voluntary)
---

### 2026-05-20T03:34:17-04:00 — cursor-opus (primary) — `transition.js` [84e843e]
**Entry ID:** myc_202605200734170079
Expand to 5 new sources, add cache + WS diffing, upgrade Mycelium to auto-record via git trailers (the change that makes its own bookkeeping stop being voluntary)
---

### 2026-05-20T03:34:17-04:00 — cursor-opus (primary) — `test_discovery_dot.py` [84e843e]
**Entry ID:** myc_202605200734170080
Expand to 5 new sources, add cache + WS diffing, upgrade Mycelium to auto-record via git trailers (the change that makes its own bookkeeping stop being voluntary)
---

### 2026-05-20T03:34:17-04:00 — cursor-opus (primary) — `test_http_cache.py` [84e843e]
**Entry ID:** myc_202605200734170081
Expand to 5 new sources, add cache + WS diffing, upgrade Mycelium to auto-record via git trailers (the change that makes its own bookkeeping stop being voluntary)
---

### 2026-05-20T03:34:17-04:00 — cursor-opus (primary) — `test_mapillary.py` [84e843e]
**Entry ID:** myc_202605200734170082
Expand to 5 new sources, add cache + WS diffing, upgrade Mycelium to auto-record via git trailers (the change that makes its own bookkeeping stop being voluntary)
---

### 2026-05-20T03:34:17-04:00 — cursor-opus (primary) — `test_mycelium_trailers.py` [84e843e]
**Entry ID:** myc_202605200734170083
Expand to 5 new sources, add cache + WS diffing, upgrade Mycelium to auto-record via git trailers (the change that makes its own bookkeeping stop being voluntary)
---

### 2026-05-20T03:34:17-04:00 — cursor-opus (primary) — `test_pipeline_diff.py` [84e843e]
**Entry ID:** myc_202605200734170084
Expand to 5 new sources, add cache + WS diffing, upgrade Mycelium to auto-record via git trailers (the change that makes its own bookkeeping stop being voluntary)
---

### 2026-05-20T04:01:22-04:00 — claude-opus-4-7 (primary) — `CHANGELOG.md` [0397a64]
**Entry ID:** myc_202605200801220085

---

### 2026-05-20T04:01:22-04:00 — claude-opus-4-7 (primary) — `log.json` [0397a64]
**Entry ID:** myc_202605200801220086

---

### 2026-05-20T04:01:22-04:00 — claude-opus-4-7 (primary) — `README.md` [0397a64]
**Entry ID:** myc_202605200801220087

---

### 2026-05-20T04:01:22-04:00 — claude-opus-4-7 (primary) — `index.html` [0397a64]
**Entry ID:** myc_202605200801220088

---

### 2026-05-20T04:01:22-04:00 — claude-opus-4-7 (primary) — `satellites.py` [0397a64]
**Entry ID:** myc_202605200801220089

---

### 2026-05-20T04:01:22-04:00 — claude-opus-4-7 (primary) — `whats_here.py` [0397a64]
**Entry ID:** myc_202605200801220090

---

### 2026-05-20T04:01:22-04:00 — claude-opus-4-7 (primary) — `models.py` [0397a64]
**Entry ID:** myc_202605200801220091

---

### 2026-05-20T04:01:22-04:00 — claude-opus-4-7 (primary) — `service.py` [0397a64]
**Entry ID:** myc_202605200801220092

---

### 2026-05-20T04:01:22-04:00 — claude-opus-4-7 (primary) — `aviation.py` [0397a64]
**Entry ID:** myc_202605200801220093

---

### 2026-05-20T04:01:22-04:00 — claude-opus-4-7 (primary) — `firms.py` [0397a64]
**Entry ID:** myc_202605200801220094

---

### 2026-05-20T04:01:22-04:00 — claude-opus-4-7 (primary) — `openaq.py` [0397a64]
**Entry ID:** myc_202605200801220095

---

### 2026-05-20T04:01:22-04:00 — claude-opus-4-7 (primary) — `usgs.py` [0397a64]
**Entry ID:** myc_202605200801220096

---

### 2026-05-20T04:01:22-04:00 — claude-opus-4-7 (primary) — `main.py` [0397a64]
**Entry ID:** myc_202605200801220097

---

### 2026-05-20T04:01:22-04:00 — claude-opus-4-7 (primary) — `celestrak.py` [0397a64]
**Entry ID:** myc_202605200801220098

---

### 2026-05-20T04:01:22-04:00 — claude-opus-4-7 (primary) — `settings.py` [0397a64]
**Entry ID:** myc_202605200801220099

---

### 2026-05-20T04:01:22-04:00 — claude-opus-4-7 (primary) — `api.js` [0397a64]
**Entry ID:** myc_202605200801220100

---

### 2026-05-20T04:01:22-04:00 — claude-opus-4-7 (primary) — `gibs.js` [0397a64]
**Entry ID:** myc_202605200801220101

---

### 2026-05-20T04:01:22-04:00 — claude-opus-4-7 (primary) — `aircraft.js` [0397a64]
**Entry ID:** myc_202605200801220102

---

### 2026-05-20T04:01:22-04:00 — claude-opus-4-7 (primary) — `cameras.js` [0397a64]
**Entry ID:** myc_202605200801220103

---

### 2026-05-20T04:01:22-04:00 — claude-opus-4-7 (primary) — `satellites.js` [0397a64]
**Entry ID:** myc_202605200801220104

---

### 2026-05-20T04:01:22-04:00 — claude-opus-4-7 (primary) — `main.js` [0397a64]
**Entry ID:** myc_202605200801220105

---

### 2026-05-20T04:01:22-04:00 — claude-opus-4-7 (primary) — `style.css` [0397a64]
**Entry ID:** myc_202605200801220106

---

### 2026-05-20T04:01:22-04:00 — claude-opus-4-7 (primary) — `test_context.py` [0397a64]
**Entry ID:** myc_202605200801220107

---

### 2026-05-20T04:01:22-04:00 — claude-opus-4-7 (primary) — `test_context_more.py` [0397a64]
**Entry ID:** myc_202605200801220108

---

### 2026-05-20T04:01:22-04:00 — claude-opus-4-7 (primary) — `test_satellites.py` [0397a64]
**Entry ID:** myc_202605200801220109

---

### 2026-05-20T04:01:22-04:00 — claude-opus-4-7 (primary) — `test_whats_here.py` [0397a64]
**Entry ID:** myc_202605200801220110

---

### 2026-05-20T04:52:37-04:00 — atlas (primary) — `CHANGELOG.md` [9b611a3]
**Entry ID:** myc_202605200852370111

---

### 2026-05-20T04:52:37-04:00 — atlas (primary) — `log.json` [9b611a3]
**Entry ID:** myc_202605200852370112

---

### 2026-05-20T04:52:37-04:00 — atlas (primary) — `README.md` [9b611a3]
**Entry ID:** myc_202605200852370113

---

### 2026-05-20T04:52:37-04:00 — atlas (primary) — `index.html` [9b611a3]
**Entry ID:** myc_202605200852370114

---

### 2026-05-20T04:52:37-04:00 — atlas (primary) — `photosphere.py` [9b611a3]
**Entry ID:** myc_202605200852370115

---

### 2026-05-20T04:52:37-04:00 — atlas (primary) — `transit.py` [9b611a3]
**Entry ID:** myc_202605200852370116

---

### 2026-05-20T04:52:37-04:00 — atlas (primary) — `models.py` [9b611a3]
**Entry ID:** myc_202605200852370117

---

### 2026-05-20T04:52:37-04:00 — atlas (primary) — `service.py` [9b611a3]
**Entry ID:** myc_202605200852370118

---

### 2026-05-20T04:52:37-04:00 — atlas (primary) — `philly311.py` [9b611a3]
**Entry ID:** myc_202605200852370119

---

### 2026-05-20T04:52:37-04:00 — atlas (primary) — `septa_alerts.py` [9b611a3]
**Entry ID:** myc_202605200852370120

---

### 2026-05-20T04:52:37-04:00 — atlas (primary) — `usgs_water.py` [9b611a3]
**Entry ID:** myc_202605200852370121

---

### 2026-05-20T04:52:37-04:00 — atlas (primary) — `models.py` [9b611a3]
**Entry ID:** myc_202605200852370122

---

### 2026-05-20T04:52:37-04:00 — atlas (primary) — `service.py` [9b611a3]
**Entry ID:** myc_202605200852370123

---

### 2026-05-20T04:52:37-04:00 — atlas (primary) — `caltrans.py` [9b611a3]
**Entry ID:** myc_202605200852370124

---

### 2026-05-20T04:52:37-04:00 — atlas (primary) — `castlerock_511.py` [9b611a3]
**Entry ID:** myc_202605200852370125

---

### 2026-05-20T04:52:37-04:00 — atlas (primary) — `livecams.py` [9b611a3]
**Entry ID:** myc_202605200852370126

---

### 2026-05-20T04:52:37-04:00 — atlas (primary) — `n511ny.py` [9b611a3]
**Entry ID:** myc_202605200852370127

---

### 2026-05-20T04:52:37-04:00 — atlas (primary) — `nps_webcams.py` [9b611a3]
**Entry ID:** myc_202605200852370128

---

### 2026-05-20T04:52:37-04:00 — atlas (primary) — `nyctmc.py` [9b611a3]
**Entry ID:** myc_202605200852370129

---

### 2026-05-20T04:52:37-04:00 — atlas (primary) — `wsdot.py` [9b611a3]
**Entry ID:** myc_202605200852370130

---

### 2026-05-20T04:52:37-04:00 — atlas (primary) — `main.py` [9b611a3]
**Entry ID:** myc_202605200852370131

---

### 2026-05-20T04:52:37-04:00 — atlas (primary) — `septa_vehicles.py` [9b611a3]
**Entry ID:** myc_202605200852370132

---

### 2026-05-20T04:52:37-04:00 — atlas (primary) — `settings.py` [9b611a3]
**Entry ID:** myc_202605200852370133

---

### 2026-05-20T04:52:37-04:00 — atlas (primary) — `constants.py` [9b611a3]
**Entry ID:** myc_202605200852370134

---

### 2026-05-20T04:52:37-04:00 — atlas (primary) — `viewer.js` [9b611a3]
**Entry ID:** myc_202605200852370135

---

### 2026-05-20T04:52:37-04:00 — atlas (primary) — `aircraft.js` [9b611a3]
**Entry ID:** myc_202605200852370136

---

### 2026-05-20T04:52:37-04:00 — atlas (primary) — `cameras.js` [9b611a3]
**Entry ID:** myc_202605200852370137

---

### 2026-05-20T04:52:37-04:00 — atlas (primary) — `satellites.js` [9b611a3]
**Entry ID:** myc_202605200852370138

---

### 2026-05-20T04:52:37-04:00 — atlas (primary) — `transit.js` [9b611a3]
**Entry ID:** myc_202605200852370139

---

### 2026-05-20T04:52:37-04:00 — atlas (primary) — `main.js` [9b611a3]
**Entry ID:** myc_202605200852370140

---

### 2026-05-20T04:52:37-04:00 — atlas (primary) — `test_context.py` [9b611a3]
**Entry ID:** myc_202605200852370141

---

### 2026-05-20T04:52:37-04:00 — atlas (primary) — `test_discovery_osm.py` [9b611a3]
**Entry ID:** myc_202605200852370142

---

### 2026-05-20T04:52:37-04:00 — atlas (primary) — `test_open_cameras.py` [9b611a3]
**Entry ID:** myc_202605200852370143

---

### 2026-05-20T04:52:37-04:00 — atlas (primary) — `test_philly_sources.py` [9b611a3]
**Entry ID:** myc_202605200852370144

---

### 2026-05-20T07:50:03-04:00 — Composer (primary) — `.gitignore` [e8b05e8]
**Entry ID:** myc_202605201150040145
Backend returned data but map layers failed to render due to parser and UX gaps.
---

### 2026-05-20T07:50:03-04:00 — Composer (primary) — `CHANGELOG.md` [e8b05e8]
**Entry ID:** myc_202605201150040146
Backend returned data but map layers failed to render due to parser and UX gaps.
---

### 2026-05-20T07:50:03-04:00 — Composer (primary) — `log.json` [e8b05e8]
**Entry ID:** myc_202605201150040147
Backend returned data but map layers failed to render due to parser and UX gaps.
---

### 2026-05-20T07:50:03-04:00 — Composer (primary) — `README.md` [e8b05e8]
**Entry ID:** myc_202605201150040148
Backend returned data but map layers failed to render due to parser and UX gaps.
---

### 2026-05-20T07:50:03-04:00 — Composer (primary) — `.env.example` [e8b05e8]
**Entry ID:** myc_202605201150040149
Backend returned data but map layers failed to render due to parser and UX gaps.
---

### 2026-05-20T07:50:03-04:00 — Composer (primary) — `docker-compose.yml` [e8b05e8]
**Entry ID:** myc_202605201150040150
Backend returned data but map layers failed to render due to parser and UX gaps.
---

### 2026-05-20T07:50:03-04:00 — Composer (primary) — `index.html` [e8b05e8]
**Entry ID:** myc_202605201150040151
Backend returned data but map layers failed to render due to parser and UX gaps.
---

### 2026-05-20T07:50:03-04:00 — Composer (primary) — `check-no-secrets.sh` [e8b05e8]
**Entry ID:** myc_202605201150040152
Backend returned data but map layers failed to render due to parser and UX gaps.
---

### 2026-05-20T07:50:03-04:00 — Composer (primary) — `pre-commit` [e8b05e8]
**Entry ID:** myc_202605201150040153
Backend returned data but map layers failed to render due to parser and UX gaps.
---

### 2026-05-20T07:50:03-04:00 — Composer (primary) — `install-hooks.sh` [e8b05e8]
**Entry ID:** myc_202605201150040154
Backend returned data but map layers failed to render due to parser and UX gaps.
---

### 2026-05-20T07:50:03-04:00 — Composer (primary) — `transit.py` [e8b05e8]
**Entry ID:** myc_202605201150040155
Backend returned data but map layers failed to render due to parser and UX gaps.
---

### 2026-05-20T07:50:03-04:00 — Composer (primary) — `models.py` [e8b05e8]
**Entry ID:** myc_202605201150040156
Backend returned data but map layers failed to render due to parser and UX gaps.
---

### 2026-05-20T07:50:03-04:00 — Composer (primary) — `service.py` [e8b05e8]
**Entry ID:** myc_202605201150040157
Backend returned data but map layers failed to render due to parser and UX gaps.
---

### 2026-05-20T07:50:03-04:00 — Composer (primary) — `opendataphilly.py` [e8b05e8]
**Entry ID:** myc_202605201150040158
Backend returned data but map layers failed to render due to parser and UX gaps.
---

### 2026-05-20T07:50:03-04:00 — Composer (primary) — `philly311.py` [e8b05e8]
**Entry ID:** myc_202605201150040159
Backend returned data but map layers failed to render due to parser and UX gaps.
---

### 2026-05-20T07:50:03-04:00 — Composer (primary) — `septa_detours.py` [e8b05e8]
**Entry ID:** myc_202605201150040160
Backend returned data but map layers failed to render due to parser and UX gaps.
---

### 2026-05-20T07:50:03-04:00 — Composer (primary) — `models.py` [e8b05e8]
**Entry ID:** myc_202605201150040161
Backend returned data but map layers failed to render due to parser and UX gaps.
---

### 2026-05-20T07:50:03-04:00 — Composer (primary) — `service.py` [e8b05e8]
**Entry ID:** myc_202605201150040162
Backend returned data but map layers failed to render due to parser and UX gaps.
---

### 2026-05-20T07:50:03-04:00 — Composer (primary) — `cam2.py` [e8b05e8]
**Entry ID:** myc_202605201150040163
Backend returned data but map layers failed to render due to parser and UX gaps.
---

### 2026-05-20T07:50:03-04:00 — Composer (primary) — `penndot.py` [e8b05e8]
**Entry ID:** myc_202605201150040164
Backend returned data but map layers failed to render due to parser and UX gaps.
---

### 2026-05-20T07:50:03-04:00 — Composer (primary) — `adsb_fi.py` [e8b05e8]
**Entry ID:** myc_202605201150040165
Backend returned data but map layers failed to render due to parser and UX gaps.
---

### 2026-05-20T07:50:03-04:00 — Composer (primary) — `indego.py` [e8b05e8]
**Entry ID:** myc_202605201150040166
Backend returned data but map layers failed to render due to parser and UX gaps.
---

### 2026-05-20T07:50:03-04:00 — Composer (primary) — `septa_vehicles.py` [e8b05e8]
**Entry ID:** myc_202605201150040167
Backend returned data but map layers failed to render due to parser and UX gaps.
---

### 2026-05-20T07:50:03-04:00 — Composer (primary) — `settings.py` [e8b05e8]
**Entry ID:** myc_202605201150040168
Backend returned data but map layers failed to render due to parser and UX gaps.
---

### 2026-05-20T07:50:03-04:00 — Composer (primary) — `constants.py` [e8b05e8]
**Entry ID:** myc_202605201150040169
Backend returned data but map layers failed to render due to parser and UX gaps.
---

### 2026-05-20T07:50:03-04:00 — Composer (primary) — `opendataphilly.py` [e8b05e8]
**Entry ID:** myc_202605201150040170
Backend returned data but map layers failed to render due to parser and UX gaps.
---

### 2026-05-20T07:50:03-04:00 — Composer (primary) — `viewer.js` [e8b05e8]
**Entry ID:** myc_202605201150040171
Backend returned data but map layers failed to render due to parser and UX gaps.
---

### 2026-05-20T07:50:03-04:00 — Composer (primary) — `aircraft.js` [e8b05e8]
**Entry ID:** myc_202605201150040172
Backend returned data but map layers failed to render due to parser and UX gaps.
---

### 2026-05-20T07:50:03-04:00 — Composer (primary) — `cameras.js` [e8b05e8]
**Entry ID:** myc_202605201150040173
Backend returned data but map layers failed to render due to parser and UX gaps.
---

### 2026-05-20T07:50:03-04:00 — Composer (primary) — `context-pois.js` [e8b05e8]
**Entry ID:** myc_202605201150040174
Backend returned data but map layers failed to render due to parser and UX gaps.
---

### 2026-05-20T07:50:03-04:00 — Composer (primary) — `indego.js` [e8b05e8]
**Entry ID:** myc_202605201150040175
Backend returned data but map layers failed to render due to parser and UX gaps.
---

### 2026-05-20T07:50:03-04:00 — Composer (primary) — `source-colors.js` [e8b05e8]
**Entry ID:** myc_202605201150040176
Backend returned data but map layers failed to render due to parser and UX gaps.
---

### 2026-05-20T07:50:03-04:00 — Composer (primary) — `transit.js` [e8b05e8]
**Entry ID:** myc_202605201150040177
Backend returned data but map layers failed to render due to parser and UX gaps.
---

### 2026-05-20T07:50:03-04:00 — Composer (primary) — `main.js` [e8b05e8]
**Entry ID:** myc_202605201150040178
Backend returned data but map layers failed to render due to parser and UX gaps.
---

### 2026-05-20T07:50:03-04:00 — Composer (primary) — `style.css` [e8b05e8]
**Entry ID:** myc_202605201150040179
Backend returned data but map layers failed to render due to parser and UX gaps.
---

### 2026-05-20T07:50:03-04:00 — Composer (primary) — `test_context.py` [e8b05e8]
**Entry ID:** myc_202605201150040180
Backend returned data but map layers failed to render due to parser and UX gaps.
---

### 2026-05-20T07:50:03-04:00 — Composer (primary) — `test_opendataphilly.py` [e8b05e8]
**Entry ID:** myc_202605201150040181
Backend returned data but map layers failed to render due to parser and UX gaps.
---

### 2026-05-20T07:50:03-04:00 — Composer (primary) — `test_philly_pack.py` [e8b05e8]
**Entry ID:** myc_202605201150040182
Backend returned data but map layers failed to render due to parser and UX gaps.
---

### 2026-05-20T07:50:03-04:00 — Composer (primary) — `test_philly_sources.py` [e8b05e8]
**Entry ID:** myc_202605201150040183
Backend returned data but map layers failed to render due to parser and UX gaps.
---

### 2026-05-20T07:50:03-04:00 — Composer (primary) — `test_pipeline_adsb.py` [e8b05e8]
**Entry ID:** myc_202605201150040184
Backend returned data but map layers failed to render due to parser and UX gaps.
---

### 2026-05-20T07:50:03-04:00 — Composer (primary) — `vite.config.js` [e8b05e8]
**Entry ID:** myc_202605201150040185
Backend returned data but map layers failed to render due to parser and UX gaps.
---

### 2026-05-20T18:00:27-04:00 — Composer (primary) — `CHANGELOG.md` [630e5d0]
**Entry ID:** myc_202605202200280186
Backend data reached the client but rendering, motion, and photosphere API shape blocked the UI.
---

### 2026-05-20T18:00:27-04:00 — Composer (primary) — `log.json` [630e5d0]
**Entry ID:** myc_202605202200280187
Backend data reached the client but rendering, motion, and photosphere API shape blocked the UI.
---

### 2026-05-20T18:00:27-04:00 — Composer (primary) — `index.html` [630e5d0]
**Entry ID:** myc_202605202200280188
Backend data reached the client but rendering, motion, and photosphere API shape blocked the UI.
---

### 2026-05-20T18:00:27-04:00 — Composer (primary) — `realtime.py` [630e5d0]
**Entry ID:** myc_202605202200280189
Backend data reached the client but rendering, motion, and photosphere API shape blocked the UI.
---

### 2026-05-20T18:00:27-04:00 — Composer (primary) — `mapillary.py` [630e5d0]
**Entry ID:** myc_202605202200280190
Backend data reached the client but rendering, motion, and photosphere API shape blocked the UI.
---

### 2026-05-20T18:00:27-04:00 — Composer (primary) — `osm.py` [630e5d0]
**Entry ID:** myc_202605202200280191
Backend data reached the client but rendering, motion, and photosphere API shape blocked the UI.
---

### 2026-05-20T18:00:27-04:00 — Composer (primary) — `aircraft.js` [630e5d0]
**Entry ID:** myc_202605202200280192
Backend data reached the client but rendering, motion, and photosphere API shape blocked the UI.
---

### 2026-05-20T18:00:27-04:00 — Composer (primary) — `camera-feed.js` [630e5d0]
**Entry ID:** myc_202605202200280193
Backend data reached the client but rendering, motion, and photosphere API shape blocked the UI.
---

### 2026-05-20T18:00:27-04:00 — Composer (primary) — `indego.js` [630e5d0]
**Entry ID:** myc_202605202200280194
Backend data reached the client but rendering, motion, and photosphere API shape blocked the UI.
---

### 2026-05-20T18:00:27-04:00 — Composer (primary) — `motion.js` [630e5d0]
**Entry ID:** myc_202605202200280195
Backend data reached the client but rendering, motion, and photosphere API shape blocked the UI.
---

### 2026-05-20T18:00:27-04:00 — Composer (primary) — `transit.js` [630e5d0]
**Entry ID:** myc_202605202200280196
Backend data reached the client but rendering, motion, and photosphere API shape blocked the UI.
---

### 2026-05-20T18:00:27-04:00 — Composer (primary) — `main.js` [630e5d0]
**Entry ID:** myc_202605202200280197
Backend data reached the client but rendering, motion, and photosphere API shape blocked the UI.
---

### 2026-05-20T18:00:27-04:00 — Composer (primary) — `transition.js` [630e5d0]
**Entry ID:** myc_202605202200280198
Backend data reached the client but rendering, motion, and photosphere API shape blocked the UI.
---

### 2026-05-20T18:00:27-04:00 — Composer (primary) — `style.css` [630e5d0]
**Entry ID:** myc_202605202200280199
Backend data reached the client but rendering, motion, and photosphere API shape blocked the UI.
---
