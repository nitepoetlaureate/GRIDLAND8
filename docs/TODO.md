# GRIDLAND roadmap / TODO

Tracked enhancements beyond the current Philly MVP.

## Flight plans (origin / destination airports)

**Current:** ADS-B.fi gives aircraft type (`t`/`desc`), operator, registration, track, MCP altitude, squawk — no filed route.

**Not required for basic enrichment** — already shown in the entity detail panel.

**Optional APIs** (pick one; all need review for keys, terms, rate limits):

| Source | What you get | Auth |
|--------|----------------|------|
| [ADS-B Exchange](https://www.adsbexchange.com/data/) | Route strings on some feeds | Commercial |
| [Aviation Edge](https://aviation-edge.com/) | Flight status O&D | API key |
| [OpenSky](https://opensky-network.org/data/api) | Historical flights by callsign | Free tier / account |
| FlightRadar24 / FlightAware | Full route + ETA | Paid |

**Implementation sketch:** `backend/pipeline/sources/flight_route.py` keyed by callsign+icao24; merge into `Aircraft.origin_airport` / `destination_airport` on snapshot.

## Aircraft “cameras”

Commercial airliners do not publish public onboard video. Possible future sources:

- ADS-B–correlated **test / GA** streams (manual plugin entries only)
- External sites that embed feeds (same `stream.url` pattern as traffic cams)

**Action:** use manual camera plugins (below); do not expect FR24 to provide video.

## Satellite imagery / “feeds”

**Current:** TLE positions only (`SatelliteLayer`).

**Possible:**

- ISS live (public MJPEG/HLS URLs) as `config/plugins/cameras/iss.json` entries
- NOAA / NASA GIBS layers (already partial in `GibsLayers`)
- Planet / Maxar — commercial, not in scope without keys

**Action:** plugin JSON per satellite with `stream` + optional `tle_override`.

## Manual IP / RTSP camera plugin system

**Current:** `config/plugins/cameras/*.json` merged at discover time (`plugin_json` source).

**Done in schema (see README):** `stream.type` = `refresh_jpeg` | `mjpeg` | `hls` + `stream.url`.

**TODO:**

- [ ] Document `ip` / `host` shorthand in plugin README
- [ ] Proxy allowlist for private LAN URLs if ingesting from a trusted bridge (security review)
- [ ] UI: “Import cameras from JSON” file picker in dev mode
- [ ] Validate RTSP → HLS transcode path (ffmpeg sidecar) — out of scope until requested

Example entry:

```json
{
  "id": "warehouse-cam-1",
  "label": "Loading dock",
  "lat": 39.95,
  "lon": -75.16,
  "source": "plugin_json",
  "stream": { "type": "mjpeg", "url": "http://192.168.1.50/mjpg/video.mjpg" }
}
```

## Map UI

- [x] Pictographic icons per type (camera, bus, train, plane, helicopter, bike, metro L/B)
- [x] Floating `#entity-popup` on selection (not inside scrollable HUD)
- [x] Minimizable left HUD (`−` / `+` toggle)
- [x] MFL/BSL corridor polylines + SEPTA wayfinding colors
- [ ] AIS / boat layer (icon ready; needs maritime data source)
- [ ] User-toggle classic points vs icons
