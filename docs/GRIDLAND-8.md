# GRIDLAND-8 — Contextual Layers Reference

Technical reference for photosphere layer (street view alternatives), contextual data streams (weather/emergency/transit/maritime/environmental/radio), and the layer composition architecture. Additive to GRIDLAND-5 through GRIDLAND-7.


## Table of Contents

1. [The Contextual Philosophy](#1-the-contextual-philosophy)
2. [Street View Equivalents & The Photosphere Layer](#2-street-view-equivalents--the-photosphere-layer)
3. [Weather & Atmospheric Layers](#3-weather--atmospheric-layers)
4. [Emergency Services & Public Safety](#4-emergency-services--public-safety)
5. [Public Transit Layer](#5-public-transit-layer)
6. [Maritime Layer — AIS](#6-maritime-layer--ais)
7. [Environmental & Scientific Layers](#7-environmental--scientific-layers)
8. [Wikipedia & Cultural Context](#8-wikipedia--cultural-context)
9. [APRS — The Wild Card Layer](#9-aprs--the-wild-card-layer)
10. [Aviation Weather — METARs, PIREPs, NOTAMs, TFRs](#10-aviation-weather--metars-pireps-notams-tfrs)
11. [Software Defined Radio Discovery](#11-software-defined-radio-discovery)
12. [Novel Dorking for Contextual Sources](#12-novel-dorking-for-contextual-sources)
13. [The Layer Management System](#13-the-layer-management-system)
14. [Feature Concepts](#14-feature-concepts)
15. [Full Contextual Layer Registry](#15-full-contextual-layer-registry)

---

## 1. Contextual Layer Categories

Categories included in this reference: weather/atmospheric, emergency/public-safety, transit, maritime (AIS), environmental/scientific, Wikipedia/cultural, APRS, aviation weather (METARs/PIREPs/NOTAMs/TFRs), SDR feeds, contextual dorking.

---

## 2. Street View Equivalents & The Photosphere Layer

### 2.1 The Open Alternatives to Google Street View

Google Street View is closed — embeddable via Maps API but expensive at scale and not truly public infrastructure. Three open alternatives exist, each with different coverage density and data licensing:

| Platform | Coverage | License | API | Operator |
|---|---|---|---|---|
| **Mapillary** | Best global coverage | CC BY-SA 4.0 (images) | Free (graph.mapillary.com) | Meta |
| **KartaView** | Strong in EU, growing | CC BY-SA 4.0 | Free (api.openstreetcam.org) | Grab |
| **Panoramax** | European focus, growing | Fully open | Free (api.panoramax.xyz) | French Gov / OSM community |

**Mapillary** is the choice for coverage. **Panoramax** is the choice for pure openness. In practice, layer them — query Mapillary first, fall back to KartaView, then Panoramax.

### 2.2 Mapillary API v4 — The Primary Street View Source

```python
import requests

MAPILLARY_TOKEN = "YOUR_TOKEN"
MAPILLARY_BASE  = "https://graph.mapillary.com"

def find_images_near(lat, lon, radius_m=100, limit=20):
    """Find street-level images near a coordinate."""
    r = requests.get(
        f"{MAPILLARY_BASE}/images",
        params={
            "access_token": MAPILLARY_TOKEN,
            "fields":       "id,captured_at,compass_angle,geometry,sequence_id,is_pano,thumb_2048_url",
            "closeto":      f"{lon},{lat}",   # GeoJSON order: lon,lat
            "radius":       radius_m,
            "limit":        limit,
            "is_pano":      True              # Only panoramic images
        }
    )
    return r.json().get('data', [])

def get_sequence_images(sequence_id, limit=100):
    """Get all images in a sequence — for navigation along a road."""
    r = requests.get(
        f"{MAPILLARY_BASE}/image_ids",
        params={
            "access_token": MAPILLARY_TOKEN,
            "sequence_id":  sequence_id,
            "limit":        limit
        }
    )
    return r.json().get('data', [])

def get_image_metadata(image_id):
    """Full metadata for a single image."""
    r = requests.get(
        f"{MAPILLARY_BASE}/{image_id}",
        params={
            "access_token": MAPILLARY_TOKEN,
            "fields": ("id,captured_at,compass_angle,geometry,sequence_id,"
                      "is_pano,thumb_original_url,thumb_2048_url,"
                      "altitude,camera_parameters")
        }
    )
    return r.json()
```

### 2.3 KartaView API

```python
KARTAVIEW_BASE = "https://api.openstreetcam.org"

def kartaview_near(lat, lon, radius_m=100, page=1):
    """Get street-level imagery sequences near a coordinate."""
    r = requests.get(
        f"{KARTAVIEW_BASE}/1.0/list/nearby-photos/",
        params={
            "lat":    lat,
            "lng":    lon,
            "radius": radius_m / 1000,   # KartaView uses km
            "page":   page,
            "ipp":    50
        }
    )
    data = r.json()
    return [
        {
            'id':         p['id'],
            'lat':        p['lat'],
            'lon':        p['lng'],
            'heading':    p['heading'],
            'sequence_id': p['sequence_id'],
            'image_url':  p['image_name'],
            'thumb_url':  p['th_name'],
            'shot_date':  p['shot_date']
        }
        for p in data.get('currentPageItems', [])
    ]
```

### 2.4 Panoramax API

```python
PANORAMAX_BASE = "https://api.panoramax.xyz"

def panoramax_search_bbox(west, south, east, north, limit=100):
    """Search Panoramax imagery in a bounding box."""
    r = requests.get(
        f"{PANORAMAX_BASE}/api/search/",
        params={
            "bbox":  f"{west},{south},{east},{north}",
            "limit": limit
        }
    )
    features = r.json().get('features', [])
    return [
        {
            'id':      f['id'],
            'lat':     f['geometry']['coordinates'][1],
            'lon':     f['geometry']['coordinates'][0],
            'heading': f['properties'].get('heading'),
            'url_hd':  f"{PANORAMAX_BASE}/api/pictures/{f['id']}/hd.jpg",
            'url_sd':  f"{PANORAMAX_BASE}/api/pictures/{f['id']}/sd.jpg",
            'url_thumb': f"{PANORAMAX_BASE}/api/pictures/{f['id']}/thumb.jpg"
        }
        for f in features
    ]
```

### 2.5 Panoramic Viewer Library Selection

Three JavaScript libraries render equirectangular panoramas in a browser:

| Library | Gzipped | npm Package | VR | Video | Best For |
|---|---|---|---|---|---|
| **Pannellum** | 21 KB | `pannellum` | No | No | Lightweight embeds |
| **Photo Sphere Viewer** | ~500 KB | `photo-sphere-viewer` | Yes | Yes | Feature-rich, markers |
| **Marzipano** | ~500 KB | `marzipano` | Yes | Yes | Professional tours |

**Recommendation: Photo Sphere Viewer** — it has the richest marker/plugin system, which GRIDLAND needs to overlay contextual data (camera icons, incident markers, transit stops) on top of the photosphere.

```bash
npm install photo-sphere-viewer @photo-sphere-viewer/markers-plugin
```

### 2.6 CesiumJS Native Panorama Support

CesiumJS has a built-in panoramic image display system — documented at `cesium.com/learn/cesiumjs-learn/display-panoramic-images/`. This is the cleanest integration path: rather than switching rendering engines, GRIDLAND can display the photosphere *within* the CesiumJS scene, positioned at ground level.

```javascript
// CesiumJS has direct support for equirectangular panoramas
// positioned in 3D space — no external viewer library required for basic display

async function enterStreetView(viewer, lat, lon) {
    // Find nearest Mapillary image
    const images = await fetch(
        `/api/streetview/near?lat=${lat}&lon=${lon}&radius=50`
    ).then(r => r.json());

    if (!images.length) return;
    const img = images[0];

    // Position the camera at ground level facing the image's compass angle
    viewer.camera.setView({
        destination: Cesium.Cartesian3.fromDegrees(img.lon, img.lat, 1.7), // eye height
        orientation: {
            heading: Cesium.Math.toRadians(img.compass_angle || 0),
            pitch:   0,
            roll:    0
        }
    });

    // Load panorama as a sphere entity surrounding the camera
    const panoramaSphere = viewer.entities.add({
        id: 'street_view_sphere',
        position: Cesium.Cartesian3.fromDegrees(img.lon, img.lat, 1.7),
        ellipsoid: {
            radii:             new Cesium.Cartesian3(10, 10, 10),
            material:          img.thumb_2048_url,
            backFaceCulling:   false,  // render inside of sphere
            shadows:           Cesium.ShadowMode.DISABLED
        }
    });

    // Restrict camera to rotation only (no translation)
    viewer.scene.screenSpaceCameraController.enableTranslate = false;
    viewer.scene.screenSpaceCameraController.enableZoom      = false;

    return panoramaSphere;
}

function exitStreetView(viewer, panoramaSphere) {
    viewer.entities.remove(panoramaSphere);
    viewer.scene.screenSpaceCameraController.enableTranslate = true;
    viewer.scene.screenSpaceCameraController.enableZoom      = true;
}
```

### 2.7 The Seamless Transition Architecture

```
ALTITUDE > 20m  →  CesiumJS 3D globe (all GRIDLAND layers active)
                        ↓ camera descends below 20m OR user clicks
                        "Enter Street View" button
ALTITUDE < 20m  →  Photo Sphere Viewer renders in overlay <div>
                   CesiumJS canvas fades to 10% opacity (still visible as mini-map)
                   GRIDLAND contextual HUD persists over photosphere
                        ↑ user clicks "Exit" or scrolls up
ALTITUDE > 20m  →  Photosphere fades out, CesiumJS returns to full opacity
```

```javascript
// DOM structure
// <div id="cesium-container">    ← CesiumJS renders here
// <div id="streetview-overlay">  ← Photo Sphere Viewer renders here
// <div id="gridland-hud">        ← Weather, incidents, transit always on top

class StreetViewManager {
    constructor(viewer) {
        this.viewer       = viewer;
        this.psv          = null;   // Photo Sphere Viewer instance
        this.currentImage = null;
        this._active      = false;
    }

    async enter(lat, lon) {
        const images = await this._findNearestPanorama(lat, lon);
        if (!images.length) {
            this._showNoPanoramaMessage();
            return;
        }
        this._active = true;
        this.currentImage = images[0];

        // Fade CesiumJS to background
        document.getElementById('cesium-container').style.opacity = '0.15';
        document.getElementById('streetview-overlay').style.display = 'block';

        // Initialize Photo Sphere Viewer
        const { Viewer } = await import('photo-sphere-viewer');
        const { MarkersPlugin } = await import('@photo-sphere-viewer/markers-plugin');

        this.psv = new Viewer({
            container:  document.getElementById('streetview-overlay'),
            panorama:   this.currentImage.thumb_2048_url,
            caption:    `${this.currentImage.captured_at} · Mapillary`,
            plugins:    [[MarkersPlugin, { markers: await this._buildMarkers(lat, lon) }]]
        });

        // Wire sequence navigation
        this.psv.on('click', ({ data }) => this._handleClick(data));
    }

    async _buildMarkers(lat, lon) {
        // Fetch contextual data and place as markers in the photosphere
        const [cameras, incidents, transit] = await Promise.all([
            fetch(`/api/cameras/near?lat=${lat}&lon=${lon}&r=200`).then(r => r.json()),
            fetch(`/api/incidents/near?lat=${lat}&lon=${lon}&r=500`).then(r => r.json()),
            fetch(`/api/transit/near?lat=${lat}&lon=${lon}&r=300`).then(r => r.json()),
        ]);

        const markers = [];

        // Place camera markers at their compass bearing from this point
        cameras.forEach(cam => {
            const bearing = this._bearingTo(lat, lon, cam.lat, cam.lon);
            markers.push({
                id:       `cam_${cam.id}`,
                position: { yaw: `${bearing}deg`, pitch: '-5deg' },
                html:     `<div class="pano-marker camera">📷</div>`,
                tooltip:  cam.label
            });
        });

        // Incident markers
        incidents.forEach(inc => {
            const bearing = this._bearingTo(lat, lon, inc.lat, inc.lon);
            markers.push({
                id:       `inc_${inc.id}`,
                position: { yaw: `${bearing}deg`, pitch: '-3deg' },
                html:     `<div class="pano-marker incident">🚨</div>`,
                tooltip:  inc.description
            });
        });

        return markers;
    }

    exit() {
        if (this.psv) { this.psv.destroy(); this.psv = null; }
        document.getElementById('cesium-container').style.opacity  = '1';
        document.getElementById('streetview-overlay').style.display = 'none';
        this._active = false;
    }

    _bearingTo(fromLat, fromLon, toLat, toLon) {
        const dLon = (toLon - fromLon) * Math.PI / 180;
        const lat1 = fromLat * Math.PI / 180;
        const lat2 = toLat  * Math.PI / 180;
        const y = Math.sin(dLon) * Math.cos(lat2);
        const x = Math.cos(lat1) * Math.sin(lat2) -
                  Math.sin(lat1) * Math.cos(lat2) * Math.cos(dLon);
        return ((Math.atan2(y, x) * 180 / Math.PI) + 360) % 360;
    }
}
```

**[FEATURE IDEA — Photosphere Navigator]:** When inside street view, arrow overlays on the photosphere show which direction the next connected Mapillary sequence images are. Clicking them advances through the sequence — you're "walking" the street. The GRIDLAND contextual HUD (weather, incidents, transit arrivals) updates in real-time as you navigate.

---

## 3. Weather & Atmospheric Layers

### 3.1 NEXRAD Radar — Iowa Environmental Mesonet

The single most important weather layer — composite NEXRAD radar covering the continental US, served as WMTS tiles that CesiumJS can load directly with no authentication.

```javascript
// Live NEXRAD composite radar — free WMTS from Iowa State
const nexradLayer = new Cesium.UrlTemplateImageryProvider({
    url:   'https://mesonet.agron.iastate.edu/cache/tile.py/1.0.0/nexrad-n0q-900913/{z}/{x}/{y}.png',
    credit: 'Iowa Environmental Mesonet / NEXRAD',
    minimumLevel: 2,
    maximumLevel: 12,
    // Tile updates every ~5 minutes with latest radar composite
});
viewer.imageryLayers.addImageryProvider(nexradLayer);

// Iowa State also serves individual NEXRAD station radar:
// https://mesonet.agron.iastate.edu/cache/tile.py/1.0.0/nexrad-n0r-{STATION}-900913/{z}/{x}/{y}.png
// Replace {STATION} with radar site ID (e.g., KDIX for Philadelphia-area)
```

### 3.2 Blitzortung — Real-Time Lightning

Blitzortung is a worldwide community lightning detection network. Real-time strike data is available via WebSocket. Note: their terms require third-party apps to serve data from their own relay server rather than connecting users directly to Blitzortung's WebSocket.

```javascript
// npm install @simonschick/blitzortungapi
import { BlitzortungApi } from '@simonschick/blitzortungapi';

class LightningLayer {
    constructor(viewer) {
        this.viewer  = viewer;
        this.strikes = [];
        this.api     = null;
    }

    start() {
        this.api = new BlitzortungApi();
        this.api.connect();

        this.api.on('strike', (strike) => {
            this._addStrike(strike.lat, strike.lon, strike.time);
        });
    }

    _addStrike(lat, lon, timestamp) {
        // Flash the strike point briefly, then fade
        const entity = this.viewer.entities.add({
            position: Cesium.Cartesian3.fromDegrees(lon, lat, 0),
            point: {
                pixelSize: 6,
                color:     Cesium.Color.YELLOW,
                outlineColor: Cesium.Color.WHITE,
                outlineWidth: 2
            }
        });

        // Remove after 30 seconds
        setTimeout(() => this.viewer.entities.remove(entity), 30000);
        this.strikes.push({ entity, timestamp });

        // Clean up strikes older than 2 minutes
        const cutoff = Date.now() - 120000;
        this.strikes = this.strikes.filter(s => {
            if (s.timestamp < cutoff) {
                this.viewer.entities.remove(s.entity);
                return false;
            }
            return true;
        });
    }

    stop() {
        this.api?.disconnect();
    }
}
```

**[FEATURE IDEA — Storm Compositing]:** When lightning density in an area exceeds a threshold, automatically composite: NEXRAD radar tile + Blitzortung strikes + APRS storm chaser positions + any NOAA severe weather alerts for that county. The storm becomes a multi-layer event object on the map rather than isolated data points.

### 3.3 OpenWeatherMap — Hyperlocal Point Weather

```python
import requests

OWM_KEY = "YOUR_KEY"

def get_weather_at(lat, lon):
    """Current weather conditions at a coordinate."""
    r = requests.get(
        "https://api.openweathermap.org/data/2.5/weather",
        params={
            "lat":   lat,
            "lon":   lon,
            "appid": OWM_KEY,
            "units": "imperial"
        }
    )
    d = r.json()
    return {
        'temp_f':      d['main']['temp'],
        'feels_like':  d['main']['feels_like'],
        'humidity':    d['main']['humidity'],
        'pressure_hpa': d['main']['pressure'],
        'wind_speed':  d['wind']['speed'],     # mph
        'wind_dir':    d['wind']['deg'],        # degrees
        'description': d['weather'][0]['description'],
        'visibility_m': d.get('visibility'),
        'clouds_pct':  d['clouds']['all'],
        'sunrise':     d['sys']['sunrise'],
        'sunset':      d['sys']['sunset']
    }

def get_hourly_forecast(lat, lon, hours=12):
    """Hourly forecast — useful for camera planning."""
    r = requests.get(
        "https://api.openweathermap.org/data/2.5/forecast",
        params={"lat": lat, "lon": lon, "appid": OWM_KEY, "units": "imperial", "cnt": hours}
    )
    return r.json()['list']
```

### 3.4 NWS Active Alerts

```python
def get_nws_alerts(lat, lon):
    """Active weather alerts from NWS for any US coordinate."""
    r = requests.get(
        f"https://api.weather.gov/alerts/active",
        params={"point": f"{lat},{lon}"},
        headers={"User-Agent": "GRIDLAND (contact@yourorg.com)"}
    )
    alerts = r.json().get('features', [])
    return [
        {
            'event':       a['properties']['event'],
            'headline':    a['properties']['headline'],
            'severity':    a['properties']['severity'],
            'urgency':     a['properties']['urgency'],
            'areas':       a['properties']['areaDesc'],
            'onset':       a['properties']['onset'],
            'expires':     a['properties']['expires'],
            'description': a['properties']['description'][:500]
        }
        for a in alerts
    ]
```

### 3.5 OpenAQ — Air Quality

```python
OPENAQ_BASE = "https://api.openaq.org/v3"

def get_air_quality_near(lat, lon, radius_m=25000):
    """
    Get air quality sensor readings near a coordinate.
    Max radius: 25,000m per OpenAQ API.
    """
    r = requests.get(
        f"{OPENAQ_BASE}/locations",
        params={
            "coordinates": f"{lat},{lon}",
            "radius":      min(radius_m, 25000),
            "limit":       20
        },
        headers={"X-API-Key": "YOUR_OPENAQ_KEY"}
    )
    locations = r.json().get('results', [])
    return [
        {
            'id':         loc['id'],
            'name':       loc['name'],
            'lat':        loc['coordinates']['latitude'],
            'lon':        loc['coordinates']['longitude'],
            'parameters': [p['displayName'] for p in loc['sensors']],
            'last_updated': loc.get('datetimeLast', {}).get('utc')
        }
        for loc in locations
    ]

def get_location_measurements(location_id, parameter='pm25', limit=1):
    """Get latest reading for a specific pollutant at a station."""
    r = requests.get(
        f"{OPENAQ_BASE}/locations/{location_id}/sensors",
        headers={"X-API-Key": "YOUR_OPENAQ_KEY"}
    )
    sensors = r.json().get('results', [])
    return [s for s in sensors if parameter in s.get('parameter', {}).get('name', '').lower()]
```

### 3.6 Weather Layer Summary

| Layer | Source | Update Rate | Auth | Notes |
|---|---|---|---|---|
| NEXRAD radar tiles | Iowa State / IEM | ~5 min | None | WMTS, CesiumJS-ready |
| Lightning strikes | Blitzortung | Real-time | None (relay required) | WebSocket |
| Current conditions | OpenWeatherMap | 10 min | Free key | Per-point |
| Severe alerts | NWS | Real-time | None | US only |
| Air quality | OpenAQ | Varies by station | Free key | Global |
| Satellite imagery | NASA GIBS / GOES | 5–10 min | None | GRIDLAND-7 |
| Weather balloon path | NOAA IGRA / APRS | Twice daily | None | See Section 9 |

---

## 4. Emergency Services & Public Safety

### 4.1 Broadcastify — Police, Fire, EMS Scanner Audio

Broadcastify hosts 6,700+ live scanner feeds from police, fire, and EMS agencies across the US and internationally. The API provides feed discovery by geography.

```python
BROADCASTIFY_KEY = "YOUR_KEY"  # Apply at broadcastify.com

def find_scanner_feeds_near(lat, lon, radius_km=50):
    """Find active scanner feeds covering a geographic area."""
    r = requests.get(
        "https://api.broadcastify.com/call/",
        params={
            "key":    BROADCASTIFY_KEY,
            "type":   "feed",
            "limit":  20,
            "geo":    f"{lat},{lon}",
            "radius": radius_km
        }
    )
    feeds = r.json().get('feed', [])
    return [
        {
            'id':          f['feedId'],
            'name':        f['feedName'],
            'county':      f['countyName'],
            'state':       f['stateName'],
            'category':    f['feedType'],   # Public Safety, Aircraft, Marine, etc.
            'listeners':   f.get('listeners', 0),
            'status':      f.get('status'),
            # Embed URL for audio player
            'embed_url':   f"https://www.broadcastify.com/listen/feed/{f['feedId']}",
            # Direct stream mount point (when available)
            'stream_url':  f.get('mount')
        }
        for f in feeds
    ]

def get_county_feeds(county_name, state_abbr):
    """Get all feeds for a specific county."""
    r = requests.get(
        "https://api.broadcastify.com/call/",
        params={
            "key":    BROADCASTIFY_KEY,
            "type":   "feed",
            "county": county_name,
            "state":  state_abbr
        }
    )
    return r.json().get('feed', [])
```

**[FEATURE IDEA — Scanner Auto-Surface]:** When GRIDLAND detects an active emergency incident (from any source — FEMA, USGS, NWS alert, Broadcastify listener spike), automatically surface the relevant Broadcastify feed in the audio panel. If a user is viewing a location in Philadelphia County and a major incident fires, the Philadelphia Police Radio feed appears in the corner.

### 4.2 OpenMHZ — Digital Radio Archives

Many agencies now use encrypted P25 digital radio (Broadcastify can't decode it). OpenMHZ archives decoded transmissions from agencies that haven't encrypted — giving both live and historical incident audio with talkgroup metadata.

```python
OPENMHZ_BASE = "https://api.openmhz.com"

def get_recent_calls(system_shortname, talkgroup_id=None, since_time=None):
    """
    Get recent radio calls for a system.
    system_shortname: e.g. 'pa-philadelphia' for Philadelphia
    talkgroup_id: specific talkgroup (e.g., fire dispatch)
    since_time: Unix timestamp in ms
    """
    params = {}
    if talkgroup_id:
        params['filter-type'] = 'talkgroup'
        params['filter-code'] = str(talkgroup_id)
    if since_time:
        params['time'] = str(since_time)

    r = requests.get(
        f"{OPENMHZ_BASE}/{system_shortname}/calls/newer",
        params=params
    )
    calls = r.json().get('calls', [])
    return [
        {
            'id':         c['_id'],
            'talkgroup':  c['talkgroupNum'],
            'description': c.get('talkgroupDescription'),
            'start_time': c['startTime'],
            'duration_s': c['len'],
            'audio_url':  c['url'],
            'freq_hz':    c.get('freq')
        }
        for c in calls
    ]

# Real-time via Socket.IO
# import socketio
# sio = socketio.Client()
# sio.connect('https://api.openmhz.com')
# sio.on('new_call', handler)
```

### 4.3 FEMA OpenFEMA — Active Disaster Declarations

```python
def get_active_disasters(state=None):
    """Get current federal disaster declarations (no auth required)."""
    params = {
        "$filter": "declarationDate gt '2025-01-01'",
        "$orderby": "declarationDate desc",
        "$top": 50
    }
    if state:
        params['$filter'] += f" and state eq '{state}'"

    r = requests.get(
        "https://www.fema.gov/api/open/v2/DisasterDeclarationsSummaries",
        params=params
    )
    disasters = r.json().get('DisasterDeclarationsSummaries', [])
    return [
        {
            'disaster_number': d['disasterNumber'],
            'state':           d['state'],
            'declaration_type': d['declarationType'],   # DR=Major, EM=Emergency
            'title':           d['declarationTitle'],
            'incident_type':   d['incidentType'],
            'date':            d['declarationDate'],
            'county':          d.get('designatedArea')
        }
        for d in disasters
    ]
```

### 4.4 USGS Earthquakes — Real-Time Seismic

```python
USGS_QUAKE_FEEDS = {
    'significant_day':   'https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/significant_day.geojson',
    'significant_week':  'https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/significant_week.geojson',
    'all_hour':          'https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_hour.geojson',
    'all_day':           'https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_day.geojson',
    'm25_week':          'https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/2.5_week.geojson',
}

def get_earthquakes(feed='all_hour'):
    r = requests.get(USGS_QUAKE_FEEDS[feed])
    features = r.json().get('features', [])
    return [
        {
            'id':        f['id'],
            'place':     f['properties']['place'],
            'magnitude': f['properties']['mag'],
            'time':      f['properties']['time'],   # Unix ms
            'depth_km':  f['geometry']['coordinates'][2],
            'lat':       f['geometry']['coordinates'][1],
            'lon':       f['geometry']['coordinates'][0],
            'url':       f['properties']['url'],
            'alert':     f['properties']['alert']   # green/yellow/orange/red
        }
        for f in features
        if f['geometry']
    ]
```

### 4.5 Emergency Incident Dorks

```
# Google: Publicly accessible CAD/dispatch dashboards
intitle:"Computer Aided Dispatch" inurl:"/cad/" site:*.gov
intitle:"Incident Viewer" inurl:"/incidents" site:*.gov
intitle:"Active Incidents" site:*.pa.gov
inurl:"/activeincidents" site:*.gov
intitle:"Fire Incidents" inurl:"/live" site:*.gov

# Shodan: Exposed dispatch systems
http.title:"Computer Aided Dispatch" has_screenshot:true
http.title:"CAD System" country:US
org:"Fire Department" has_screenshot:true
org:"Police Department" http.title:"dashboard" has_screenshot:true
```

---

## 5. Public Transit Layer

### 5.1 GTFS-RT — The Universal Transit Standard

GTFS-Realtime (General Transit Feed Specification Realtime) is the universal standard for real-time transit data, used by hundreds of agencies worldwide. It uses Protocol Buffers (binary) encoding and defines three feed types:

| Feed Type | Contents | Update Rate |
|---|---|---|
| **Vehicle Positions** | Current lat/lon, bearing, speed of each vehicle | Every 15–30 seconds |
| **Trip Updates** | Departure/arrival predictions, delays, cancellations | Every 30–60 seconds |
| **Service Alerts** | Stop closures, route changes, network events | As needed |

```python
from google.transit import gtfs_realtime_pb2
import requests

def fetch_vehicle_positions(feed_url, api_key=None):
    """Fetch and parse a GTFS-RT vehicle positions feed."""
    headers = {}
    if api_key:
        headers['x-api-key'] = api_key

    r = requests.get(feed_url, headers=headers, timeout=10)
    feed = gtfs_realtime_pb2.FeedMessage()
    feed.ParseFromString(r.content)

    vehicles = []
    for entity in feed.entity:
        if not entity.HasField('vehicle'):
            continue
        v = entity.vehicle
        pos = v.position
        vehicles.append({
            'vehicle_id':  v.vehicle.id,
            'label':       v.vehicle.label,
            'route_id':    v.trip.route_id,
            'trip_id':     v.trip.trip_id,
            'lat':         pos.latitude,
            'lon':         pos.longitude,
            'bearing':     pos.bearing,     # degrees, 0=north
            'speed_ms':    pos.speed,       # m/s
            'timestamp':   v.timestamp,
            'occupancy':   v.occupancy_status if v.HasField('occupancy_status') else None
        })
    return vehicles
```

### 5.2 Transitland — Global Transit Feed Discovery

Transitland aggregates GTFS and GTFS-RT feeds from ~2,500 transit agencies worldwide.

```python
TRANSITLAND_KEY = "YOUR_KEY"
TRANSITLAND_BASE = "https://api.transit.land/api/v2/rest"

def find_transit_feeds_near(lat, lon, radius_m=50000):
    """Find all transit operators and their GTFS-RT feeds near a coordinate."""
    r = requests.get(
        f"{TRANSITLAND_BASE}/feeds",
        params={
            "api_key": TRANSITLAND_KEY,
            "lon":     lon,
            "lat":     lat,
            "r":       radius_m,
            "spec":    "gtfs-rt",     # Only real-time feeds
            "limit":   20
        }
    )
    feeds = r.json().get('feeds', [])
    return [
        {
            'id':          f['id'],
            'name':        f['name'],
            'operator':    f.get('associated_operators', [{}])[0].get('name'),
            'feed_url':    f.get('urls', {}).get('realtime_vehicle_positions'),
            'trips_url':   f.get('urls', {}).get('realtime_trip_updates'),
            'alerts_url':  f.get('urls', {}).get('realtime_alerts'),
            'license':     f.get('license', {}).get('spdx_identifier')
        }
        for f in feeds
    ]

def find_operators_near(lat, lon, radius_m=50000):
    """Find transit agencies operating near a coordinate."""
    r = requests.get(
        f"{TRANSITLAND_BASE}/operators",
        params={
            "api_key": TRANSITLAND_KEY,
            "lon":     lon,
            "lat":     lat,
            "r":       radius_m
        }
    )
    return r.json().get('operators', [])
```

### 5.3 SEPTA (Philadelphia) — Agency-Specific API

```python
SEPTA_BASE = "https://www3.septa.org/api"

def get_septa_bus_positions(route=None):
    """All current bus/trolley positions, optionally filtered by route."""
    if route:
        url = f"{SEPTA_BASE}/TransitView/index.php?route={route}"
    else:
        url = f"{SEPTA_BASE}/TransitViewAll/index.php?req1=all"

    r = requests.get(url)
    data = r.json()

    vehicles = []
    for route_data in data.get('bus', []):
        for bus in route_data.values() if isinstance(route_data, dict) else [route_data]:
            if isinstance(bus, list):
                for b in bus:
                    vehicles.append({
                        'vehicle_id': b.get('VehicleID'),
                        'lat':        float(b.get('lat', 0)),
                        'lon':        float(b.get('lng', 0)),
                        'direction':  b.get('Direction'),
                        'destination': b.get('destination'),
                        'route':      b.get('route'),
                        'offset_min': b.get('Offset'),    # minutes late/early
                        'speed':      b.get('Speed')
                    })
    return vehicles

def get_septa_rail_positions():
    """Current regional rail train positions."""
    r = requests.get(f"{SEPTA_BASE}/TrainView/index.php")
    trains = r.json()
    return [
        {
            'train_number': t.get('trainno'),
            'lat':          float(t.get('lat', 0)),
            'lon':          float(t.get('lon', 0)),
            'line':         t.get('line'),
            'source':       t.get('source'),       # station
            'destination':  t.get('dest'),
            'service':      t.get('SERVICE'),
            'late_min':     t.get('late', 0),
            'status':       t.get('STATUS')
        }
        for t in trains
    ]

def get_septa_alerts():
    """Active service alerts."""
    r = requests.get(f"{SEPTA_BASE}/Alerts/index.php?req1=all")
    return r.json()
```

### 5.4 MTA New York — GTFS-RT Feeds

```python
MTA_FEEDS = {
    'subway':     'https://gtfsrt.prod.obanyc.com/tripUpdates',
    'subway_pos': 'https://gtfsrt.prod.obanyc.com/vehiclePositions',
    'bus':        'https://gtfsrt.prod.obanyc.com/vehiclePositions?key=YOUR_KEY',
    'alerts':     'https://gtfsrt.prod.obanyc.com/alerts'
}

def get_mta_vehicles(feed_type='subway_pos', api_key=None):
    url = MTA_FEEDS[feed_type]
    if api_key:
        url += f"?key={api_key}"
    return fetch_vehicle_positions(url, api_key)
```

### 5.5 GBFS — Bike & Scooter Share

```python
def fetch_gbfs_feed(discovery_url):
    """
    Fetch all feeds from a GBFS discovery endpoint.
    Returns station locations + real-time availability.
    """
    r = requests.get(discovery_url)
    feeds = {
        f['name']: f['url']
        for f in r.json()['data']['en']['feeds']
    }

    stations = {}

    # Static station info (locations, capacity)
    if 'station_information' in feeds:
        r = requests.get(feeds['station_information'])
        for s in r.json()['data']['stations']:
            stations[s['station_id']] = {
                'id':       s['station_id'],
                'name':     s['name'],
                'lat':      s['lat'],
                'lon':      s['lon'],
                'capacity': s.get('capacity', 0)
            }

    # Real-time availability
    if 'station_status' in feeds:
        r = requests.get(feeds['station_status'])
        for s in r.json()['data']['stations']:
            if s['station_id'] in stations:
                stations[s['station_id']].update({
                    'bikes_available':   s.get('num_bikes_available', 0),
                    'docks_available':   s.get('num_docks_available', 0),
                    'is_renting':        s.get('is_renting', False),
                    'last_reported':     s.get('last_reported')
                })

    return list(stations.values())

# Indego Philadelphia
philly_bikes = fetch_gbfs_feed(
    "https://www.rideindego.com/stations/json/"
)

# Citi Bike NYC
citibike = fetch_gbfs_feed(
    "https://gbfs.citibikenyc.com/gbfs/en/gbfs.json"
)
```

---

## 6. Maritime Layer — AIS

AIS (Automatic Identification System) is to ships exactly what ADS-B is to aircraft. Every vessel over 300 gross tons internationally and 65 feet in US waters is legally required to broadcast AIS. The data includes vessel identity, position, speed, heading, destination, and cargo type.

### 6.1 AISHub — Free Research Access

```python
AISHUB_KEY = "YOUR_KEY"  # Register at aishub.net

def get_vessels_in_bbox(latmin, latmax, lonmin, lonmax, format='json'):
    """Get all vessels currently in a bounding box."""
    r = requests.get(
        "https://data.aishub.net/rec.php",
        params={
            "username": AISHUB_KEY,
            "format":   1 if format == 'json' else 3,  # 1=JSON, 3=XML
            "output":   "extended",
            "compress": 0,
            "latmin":   latmin,
            "latmax":   latmax,
            "lonmin":   lonmin,
            "lonmax":   lonmax
        }
    )
    data = r.json()
    if not data or len(data) < 2:
        return []

    vessels = []
    for v in data[1]:   # data[0] is metadata
        vessels.append({
            'mmsi':        v.get('MMSI'),
            'name':        v.get('NAME', '').strip(),
            'callsign':    v.get('CALLSIGN', '').strip(),
            'ship_type':   v.get('TYPE_AND_CARGO'),
            'lat':         v.get('LATITUDE'),
            'lon':         v.get('LONGITUDE'),
            'speed_kts':   v.get('SOG'),   # Speed over ground
            'heading':     v.get('COG'),   # Course over ground
            'nav_status':  v.get('NAVIGATIONAL_STATUS'),
            'destination': v.get('DESTINATION', '').strip(),
            'draught_m':   v.get('DRAUGHT'),
            'length_m':    v.get('LENGTH'),
            'timestamp':   v.get('TIME')
        })
    return vessels

# Delaware River / Philadelphia area
philly_vessels = get_vessels_in_bbox(
    latmin=39.5, latmax=40.2,
    lonmin=-75.8, lonmax=-74.9
)
```

### 6.2 NOAA NDBC Buoys — Ocean & Weather

```python
NDBC_BASE = "https://www.ndbc.noaa.gov"

def get_buoy_data(station_id):
    """Get real-time readings from a NOAA buoy (last 45 days available)."""
    r = requests.get(
        f"{NDBC_BASE}/data/realtime2/{station_id}.txt",
        timeout=10
    )
    lines = r.text.strip().split('\n')

    # NDBC format: header lines start with #, data is space-delimited
    headers = lines[0].lstrip('#').split()
    units   = lines[1].lstrip('#').split()
    latest  = lines[2].split()   # Most recent observation

    data = dict(zip(headers, latest))
    return {
        'station':    station_id,
        'year':       data.get('YY'),
        'month':      data.get('MM'),
        'day':        data.get('DD'),
        'hour':       data.get('hh'),
        'wind_dir':   data.get('WDIR'),    # degrees
        'wind_spd':   data.get('WSPD'),    # m/s
        'gust':       data.get('GST'),     # m/s
        'wave_ht_m':  data.get('WVHT'),   # significant wave height
        'wave_period': data.get('DPD'),    # dominant wave period (s)
        'air_temp_c':  data.get('ATMP'),
        'water_temp_c': data.get('WTMP'),
        'pressure_hpa': data.get('PRES'),
        'visibility_nm': data.get('VIS')
    }

# Find buoys near a location using NDBC station locator:
# https://www.ndbc.noaa.gov/obs.shtml (interactive map)
# Or query by region:
REGIONAL_BUOYS = {
    'mid_atlantic': ['44025', '44009', '44065', '44017'],  # NJ offshore, Delaware Bay
    'chesapeake':   ['TPLM2', 'CHCM2', 'BISM2'],
    'gulf_of_maine': ['44013', '44018', '44027']
}
```

### 6.3 Vessel Type Classification

```python
AIS_SHIP_TYPES = {
    20: 'Wing in ground', 21: 'Wing in ground - hazmat A',
    30: 'Fishing', 31: 'Towing', 32: 'Towing (long)',
    33: 'Dredging/underwater ops', 34: 'Diving ops',
    35: 'Military ops', 36: 'Sailing', 37: 'Pleasure craft',
    40: 'High speed craft', 41: 'HSC hazmat A',
    50: 'Pilot vessel', 51: 'Search and rescue',
    52: 'Tug', 53: 'Port tender', 54: 'Anti-pollution',
    55: 'Law enforcement', 58: 'Medical transport',
    60: 'Passenger', 61: 'Passenger - hazmat A',
    70: 'Cargo', 71: 'Cargo - hazmat A',
    80: 'Tanker', 81: 'Tanker - hazmat A',
    90: 'Other'
}
```

**[FEATURE IDEA — Port Pulse]:** When viewing a major port (Philadelphia, Baltimore, New York), a dedicated maritime panel shows inbound/outbound vessel traffic, current buoy conditions, and any Coast Guard maritime broadcasts for the area. Port authority cameras (many are public) surface automatically.

---

## 7. Environmental & Scientific Layers

### 7.1 NASA FIRMS — Real-Time Wildfire Detection

VIIRS and MODIS satellites detect active fire hotspots globally. Updates within hours of detection.

```python
FIRMS_KEY = "YOUR_MAP_KEY"  # Free: firms.modaps.eosdis.nasa.gov/api/

def get_fire_detections(west, south, east, north, source='VIIRS_SNPP_NRT', days=1):
    """
    Get satellite fire detections in a bounding box.
    source: VIIRS_SNPP_NRT, VIIRS_NOAA20_NRT, MODIS_NRT
    """
    area = f"{west},{south},{east},{north}"
    r = requests.get(
        f"https://firms.modaps.eosdis.nasa.gov/api/area/csv/{FIRMS_KEY}/{source}/{area}/{days}",
        timeout=30
    )
    # Parse CSV response
    import csv, io
    reader = csv.DictReader(io.StringIO(r.text))
    return [
        {
            'lat':          float(row['latitude']),
            'lon':          float(row['longitude']),
            'brightness_k': float(row.get('bright_ti4', row.get('brightness', 0))),
            'confidence':   row.get('confidence'),    # low/nominal/high
            'frp_mw':       float(row.get('frp', 0)),  # Fire Radiative Power (MW)
            'acq_datetime': f"{row['acq_date']}T{row['acq_time']}Z",
            'satellite':    row.get('satellite'),
            'instrument':   row.get('instrument')
        }
        for row in reader
        if row.get('latitude')
    ]
```

### 7.2 EPA Envirofacts — What's Near You

```python
EPA_BASE = "https://enviro.epa.gov/enviro/efservice"

def get_epa_sites_near(zip_code, miles=5):
    """Get EPA-regulated facilities near a zip code."""
    # TRI = Toxic Release Inventory — industrial emission sites
    r = requests.get(
        f"{EPA_BASE}/TRI_FACILITY/ZIP_CODE/{zip_code}/JSON",
        timeout=15
    )
    facilities = r.json()
    return [
        {
            'name':     f.get('FAC_NAME'),
            'address':  f.get('FAC_STREET'),
            'city':     f.get('FAC_CITY'),
            'state':    f.get('FAC_STATE'),
            'lat':      f.get('FAC_LAT'),
            'lon':      f.get('FAC_LONG'),
            'industry': f.get('INDUSTRY_SECTOR_CODE'),
            'naics':    f.get('PRIMARY_NAICS')
        }
        for f in (facilities if isinstance(facilities, list) else [])
    ]
```

### 7.3 iNaturalist — Species at a Location

```python
def get_observations_near(lat, lon, radius_km=10, taxon=None, days_back=30):
    """Get species observations near a coordinate."""
    from datetime import datetime, timedelta

    params = {
        "lat":       lat,
        "lng":       lon,
        "radius":    radius_km,
        "d1":        (datetime.utcnow() - timedelta(days=days_back)).strftime('%Y-%m-%d'),
        "order":     "desc",
        "order_by":  "observed_on",
        "per_page":  50
    }
    if taxon:
        params['taxon_name'] = taxon

    r = requests.get("https://api.inaturalist.org/v1/observations", params=params)
    results = r.json().get('results', [])
    return [
        {
            'id':          obs['id'],
            'species':     obs.get('taxon', {}).get('name'),
            'common_name': obs.get('taxon', {}).get('preferred_common_name'),
            'lat':         obs.get('location', '0,0').split(',')[0],
            'lon':         obs.get('location', '0,0').split(',')[1],
            'observed_on': obs.get('observed_on'),
            'photo_url':   obs.get('photos', [{}])[0].get('url'),
            'quality':     obs.get('quality_grade')
        }
        for obs in results
        if obs.get('location')
    ]
```

---

## 8. Wikipedia & Cultural Context

This is one of the simplest APIs in this stack and one of the most valuable. As a user flies over any location, GRIDLAND can silently pull Wikipedia articles whose subjects are physically located at that coordinate — giving immediate historical, cultural, and architectural context to what they're seeing.

```python
def get_wikipedia_near(lat, lon, radius_m=2000, limit=10):
    """
    Get Wikipedia articles about things physically near a coordinate.
    Works for any location on Earth — buildings, landmarks, natural features, etc.
    """
    r = requests.get(
        "https://en.wikipedia.org/w/api.php",
        params={
            "action":   "query",
            "list":     "geosearch",
            "gscoord":  f"{lat}|{lon}",
            "gsradius": min(radius_m, 10000),   # API max 10km
            "gslimit":  limit,
            "format":   "json"
        },
        headers={"User-Agent": "GRIDLAND/1.0 (contact@yourorg.com)"}
    )
    results = r.json().get('query', {}).get('geosearch', [])
    return [
        {
            'pageid':    r['pageid'],
            'title':     r['title'],
            'lat':       r['lat'],
            'lon':       r['lon'],
            'dist_m':    r['dist'],
            'url':       f"https://en.wikipedia.org/wiki/{r['title'].replace(' ', '_')}"
        }
        for r in results
    ]

def get_article_summary(title):
    """Get the first paragraph of a Wikipedia article."""
    r = requests.get(
        f"https://en.wikipedia.org/api/rest_v1/page/summary/{title.replace(' ', '_')}",
        headers={"User-Agent": "GRIDLAND/1.0"}
    )
    d = r.json()
    return {
        'title':    d.get('title'),
        'summary':  d.get('extract'),
        'image':    d.get('thumbnail', {}).get('source'),
        'url':      d.get('content_urls', {}).get('desktop', {}).get('page')
    }
```

**[FEATURE IDEA — Context Halo]:** When a user hovers over any location for more than 2 seconds, a subtle halo appears around that point and the nearest Wikipedia articles populate in a side panel with their summaries and thumbnails. No click required. This makes the entire map feel encyclopedic without being intrusive.

---

## 9. APRS — The Wild Card Layer

APRS (Automatic Packet Reporting System) is an amateur radio protocol for real-time tracking and data sharing, operated by the global ham radio community. It is public, free, and contains data that exists nowhere else.

**Why APRS is special:**
- **Weather balloons are tracked in real-time by balloon chasers** who APRS-tag their payloads. `aprs.fi` shows live stratospheric balloon positions — filling the gap between the aviation and orbital layers in GRIDLAND-7.
- **Storm chasers APRS-tag their vehicles.** When there's severe weather, you can watch storm chasers converging on the storm in real-time on the APRS layer while the NEXRAD radar shows the same storm growing.
- **Emergency vehicles and amateur radio operators** carry APRS trackers. During disasters, the APRS layer becomes a real-time picture of emergency response assets.
- **Weather stations** broadcast current readings over APRS — a dense network of hyperlocal weather data.

```python
APRSFI_KEY = "YOUR_KEY"   # Free at aprs.fi
APRSFI_BASE = "https://api.aprs.fi/api/get"

def get_aprs_objects_near(lat, lon, radius_km=50):
    """Get all APRS-tracked objects near a coordinate."""
    # aprs.fi requires name-based queries; for area search use the web API
    r = requests.get(
        APRSFI_BASE,
        params={
            "what":    "loc",
            "apikey":  APRSFI_KEY,
            "lat":     lat,
            "lng":     lon,
            "distance": radius_km,
            "format":  "json"
        }
    )
    entries = r.json().get('entries', [])

    stations   = [e for e in entries if e.get('type') in ('l', 'i', 'o')]
    weather    = [e for e in entries if e.get('type') == 'w']
    balloons   = [e for e in entries if 'balloon' in e.get('name', '').lower()
                  or 'wb' in e.get('name', '').lower()
                  or float(e.get('altitude', 0) or 0) > 5000]

    return {
        'stations':   stations,
        'weather':    weather,
        'balloons':   balloons,
        'all':        entries
    }

def get_aprs_balloon_altitude(callsign):
    """Track a specific balloon by callsign."""
    r = requests.get(
        APRSFI_BASE,
        params={
            "what":   "loc",
            "name":   callsign,
            "apikey": APRSFI_KEY,
            "format": "json"
        }
    )
    entries = r.json().get('entries', [])
    if not entries:
        return None
    e = entries[0]
    return {
        'callsign':   e.get('name'),
        'lat':        float(e.get('lat', 0)),
        'lon':        float(e.get('lng', 0)),
        'altitude_m': float(e.get('altitude', 0) or 0),
        'speed_kmh':  float(e.get('speed', 0) or 0),
        'course':     float(e.get('course', 0) or 0),
        'comment':    e.get('comment'),
        'last_seen':  e.get('lasttime')
    }
```

**In GRIDLAND, APRS creates a bridge between the stratospheric and orbital layers.** A high-altitude balloon at 30,000m appears between the aviation layer and the ISS, exactly where it belongs in the altitude stack. Its APRS callsign links to its mission page (most balloon teams publish these), and the descent trajectory from the sounding data can be animated.

**[FEATURE IDEA — Balloon Chase Mode]:** When a weather balloon is detected at altitude via APRS, GRIDLAND activates "Balloon Chase Mode" — the view follows the balloon's position in CesiumJS, showing its altitude on the stack, the NOAA sounding data for its current position, and the predicted landing zone from standard descent rate calculations.

---

## 10. Aviation Weather — METARs, PIREPs, NOTAMs, TFRs

This layer is unique to GRIDLAND's altitude-stratified model. At the aviation layer zoom level (1,000–12,000m), GRIDLAND can overlay weather conditions that *actual pilots are experiencing at that altitude* — data types that no mapping product outside of flight planning tools currently visualizes this way.

### 10.1 METARs — Surface Aviation Weather

```python
AVWX_BASE = "https://aviationweather.gov/api/data"

def get_metar(station_id):
    """Get current METAR for an airport weather station."""
    r = requests.get(
        f"{AVWX_BASE}/metar",
        params={"ids": station_id, "format": "json"}
    )
    data = r.json()
    if not data:
        return None
    m = data[0]
    return {
        'station':      m.get('stationId'),
        'lat':          m.get('latitude'),
        'lon':          m.get('longitude'),
        'elevation_m':  m.get('elevationM'),
        'temp_c':       m.get('temp'),
        'dewpoint_c':   m.get('dewp'),
        'wind_dir':     m.get('wdir'),
        'wind_kt':      m.get('wspd'),
        'gust_kt':      m.get('wgst'),
        'visibility_sm': m.get('visib'),
        'clouds':       m.get('clouds'),
        'ceiling_ft':   m.get('ceil'),     # Cloud ceiling in feet AGL
        'flight_rules': m.get('fltcat'),   # VFR/MVFR/IFR/LIFR
        'raw':          m.get('rawOb'),
        'time':         m.get('obsTime')
    }

def get_metars_near(lat, lon, radius_nm=50):
    """Get all METAR stations within radius of a coordinate."""
    r = requests.get(
        f"{AVWX_BASE}/metar",
        params={
            "format": "json",
            "bbox":   f"{lat-radius_nm/60},{lon-radius_nm/60},"
                      f"{lat+radius_nm/60},{lon+radius_nm/60}"
        }
    )
    return r.json() or []
```

### 10.2 PIREPs — Real Pilot Reports at Altitude

PIREPs are reports filed by actual pilots describing weather conditions they're experiencing in flight. They include altitude, location, and the specific hazard (turbulence, icing, etc.).

```python
def get_pireps_near(lat, lon, radius_nm=100, hours_back=3):
    """
    Get recent pilot weather reports near a coordinate.
    These are observations from actual aircraft at altitude.
    """
    r = requests.get(
        f"{AVWX_BASE}/pirep",
        params={
            "format":    "json",
            "distance":  radius_nm,
            "lat":       lat,
            "lon":       lon,
            "age":       hours_back
        }
    )
    pireps = r.json() or []
    return [
        {
            'aircraft_type': p.get('acType'),
            'altitude_ft':   p.get('altitude', {}).get('repr'),
            'lat':           p.get('lat'),
            'lon':           p.get('lon'),
            'turbulence':    p.get('turbulence'),    # intensity, frequency, type
            'icing':         p.get('icing'),          # intensity, type
            'sky':           p.get('skyCondition'),
            'temp_c':        p.get('temperature'),
            'wind':          p.get('wind'),
            'raw':           p.get('raw'),
            'time':          p.get('observationTime')
        }
        for p in pireps
    ]
```

**[FEATURE IDEA — Altitude Weather Slice]:** At the aviation layer in GRIDLAND, a vertical cross-section panel shows current weather conditions at each altitude band in a column above the current map center — pulling METARs for the surface, PIREPs for the mid-levels, and NOAA upper air soundings for the stratosphere. A single glance tells you what the atmosphere is doing at every level simultaneously.

### 10.3 NOTAMs & TFRs — Restricted Airspace

```python
FAA_TFR_BASE = "https://tfr.faa.gov"

def get_active_tfrs():
    """
    Get all active Temporary Flight Restrictions.
    TFRs appear for: VIP movements, disasters, sporting events, wildfires, airshows.
    """
    r = requests.get(f"{FAA_TFR_BASE}/tfr_map_ims/html/ns/tfr_status_data.xml")
    # Parse XML response
    import xml.etree.ElementTree as ET
    root = ET.fromstring(r.text)

    tfrs = []
    for tfr in root.findall('.//TFRAreaGroup'):
        tfrs.append({
            'id':          tfr.findtext('NOTAM_ID'),
            'type':        tfr.findtext('TYPE'),        # e.g., VIP, DISASTER
            'facility':    tfr.findtext('FACILITY'),
            'state':       tfr.findtext('STATE'),
            'description': tfr.findtext('DESCRIPTION'),
            'floor_ft':    tfr.findtext('FLOOR_NAVAID'),
            'ceiling_ft':  tfr.findtext('CEILING_NAVAID'),
            'effective':   tfr.findtext('EFFECTIVE_DATE'),
            'expire':      tfr.findtext('EXPIRE_DATE')
        })
    return tfrs
```

**Why TFRs matter for GRIDLAND:** When there's a TFR over an area, it means something significant is happening. Presidential movement, natural disaster response, major sporting event, active wildfire. TFRs become a contextual signal — a geofenced zone on the map that says *"something important is here."*

---

## 11. Software Defined Radio Discovery

Software-defined radios (SDRs) allow any RF signal to be received and decoded in software. Several public SDR servers exist that allow anyone to tune in to local radio frequencies — police scanners, air traffic control, weather satellites, ship AIS, ham radio, everything — from anywhere in the world.

This creates a novel GRIDLAND feature: **tuning in to the airwaves of any location you're viewing.**

### 11.1 Public SDR Server Discovery

**Known server networks:**

| Network | Technology | How to Find | Coverage |
|---|---|---|---|
| **KiwiSDR** | KiwiSDR hardware | `kiwisdr.com/public/` | ~700 worldwide |
| **OpenWebRX** | Software, any SDR hardware | `sdr.hu` registry | Growing |
| **WebSDR** | Custom software | `websdr.org` | ~200 worldwide |
| **rx-tx.info** | Aggregator map | `rx-tx.info/map-sdr-points` | Multi-network |

**Google Dorks for SDR servers:**

```
# KiwiSDR servers (port 8073 default)
"KiwiSDR" "Port 8073"
intitle:"KiwiSDR" inurl:":8073"
"KiwiSDR" inurl:"/kiwi/"

# OpenWebRX servers
intitle:"OpenWebRX"
inurl:"/static/openwebrx" has_screenshot:true
"OpenWebRX" inurl:"/ws/"

# WebSDR
intitle:"WebSDR" inurl:"/websdr"
"WebSDR" site:*.websdr.org

# Generic SDR web interfaces
intitle:"Software Defined Radio" inurl:"/receiver"
```

**Shodan:**

```
# KiwiSDR on Shodan
http.title:"KiwiSDR" has_screenshot:true
port:8073 "KiwiSDR"
http.html:"kiwisdr" has_screenshot:true

# OpenWebRX
http.title:"OpenWebRX" has_screenshot:true
```

### 11.2 KiwiSDR API

KiwiSDR servers expose a simple API for checking their status and tuning parameters:

```python
def get_kiwisdr_status(host, port=8073):
    """Get status of a KiwiSDR server."""
    r = requests.get(f"http://{host}:{port}/status", timeout=5)
    # Parse the key=value status format
    status = {}
    for line in r.text.split('\n'):
        if '=' in line:
            k, v = line.split('=', 1)
            status[k.strip()] = v.strip()
    return {
        'users':       int(status.get('users', 0)),
        'users_max':   int(status.get('users_max', 4)),
        'gps_lat':     float(status.get('gps_lat', 0)),
        'gps_lon':     float(status.get('gps_lon', 0)),
        'freq_min':    status.get('freq_lo'),   # kHz
        'freq_max':    status.get('freq_hi'),   # kHz
        'adc_clk_nom': status.get('adc_clk_nom'),
        'url':         f"http://{host}:{port}/"
    }
```

**[FEATURE IDEA — Radio Window]:** When viewing any location in GRIDLAND, a "Radio Window" sidebar shows:
1. The nearest public KiwiSDR/OpenWebRX instance to that location with a clickable link
2. The active Broadcastify scanner feeds covering that county
3. Any recent OpenMHZ call audio from the past 30 minutes for that jurisdiction

Clicking any of these opens an embedded audio player — you're listening to the radio environment of the place you're looking at.

---

## 12. Novel Dorking for Contextual Sources

These dorks surface contextual data sources that aren't in any standard directory.

### Emergency & Dispatch

```
# Exposed CAD dashboards
intitle:"Computer Aided Dispatch" inurl:"/cad/" site:*.gov
intitle:"Active Incidents" inurl:"/incidents" site:*.gov
intitle:"Incident Viewer" site:*.pa.gov OR site:*.nj.gov
inurl:"/incident-map" site:*.gov has_screenshot:true

# Hospital status / ER wait times
intitle:"Emergency Department" inurl:"/status" site:*.org
intitle:"ER Wait Time" site:*.hospital
inurl:"/bed-status" site:*.gov

# Utility outage maps with exposed data
intitle:"Outage Map" inurl:"/outagemap"
"outage" inurl:"/api/v1/" site:*.utility
"customerOut" inurl:"/api/" site:*.com

# Water/wastewater monitoring
intitle:"SCADA" inurl:"/dashboard" site:*.gov
intitle:"Water Quality" inurl:"/realtime" site:*.gov
```

### Transit & Traffic

```
# Exposed transit vehicle tracking APIs
inurl:"/api/vehicles" inurl:"/positions" site:*.transit
intitle:"Transit Dashboard" site:*.gov has_screenshot:true
inurl:"/gtfs-rt/" site:*.gov

# Traffic signal timing systems
intitle:"ATMS" inurl:"/dashboard" site:*.gov
"InSync" inurl:"/signal" site:*.gov
intitle:"Traffic Management" site:*.city.*.us

# Construction permit cameras (often publicly accessible EarthCam embeds)
site:earthcam.com inurl:"/construction"
inurl:"/constructioncam/" site:*.com
intitle:"Construction Camera" inurl:"/live"
```

### Weather & Environment

```
# Public personal weather stations with live pages
"weatherlink" inurl:"/live" has_screenshot:true
"Weather Underground" inurl:"/personal-weather-station"
intitle:"Weather Station" inurl:"/wx/" has_screenshot:true
"wunderground" inurl:"/dashboard" site:*.edu

# Air quality monitors with public dashboards
intitle:"Air Quality Monitor" inurl:"/dashboard"
"PurpleAir" inurl:"/map" site:*.gov
intitle:"AQMD" inurl:"/monitoring"

# Stream gauge cameras (USGS)
site:waterdata.usgs.gov inurl:"cam"
inurl:"/streamcam" site:*.usgs.gov

# University research sensor networks (often publicly accessible)
intitle:"Sensor Network" site:*.edu has_screenshot:true
inurl:"/sensors/live" site:*.edu
```

### Maritime & Water

```
# Port authority cameras and data
intitle:"Port" inurl:"/camera" site:*.port.*
intitle:"Harbor" inurl:"/traffic" site:*.gov
"AIS" inurl:"/vessel-tracking" site:*.gov
inurl:"/vessel-monitor" has_screenshot:true

# Tide gauges and water level monitors
site:tidesandcurrents.noaa.gov inurl:"/sensors"
intitle:"Water Level" inurl:"/realtime" site:*.noaa.gov
```

### Smart City & IoT Infrastructure

```
# Shodan: Smart city IoT sensors
org:"City of Philadelphia" has_screenshot:true
org:"City of New York" has_screenshot:true
http.title:"Smart City" has_screenshot:true
http.title:"IoT Dashboard" has_screenshot:true

# Google: Municipal sensor dashboards
intitle:"City Dashboard" site:*.arcgis.com
intitle:"Smart City" inurl:"/dashboard" site:*.gov
"sensor" inurl:"/api/v1/data" site:*.city.*.us

# Parking availability
intitle:"Parking Availability" site:*.gov
inurl:"/parking/api/" site:*.gov
"parking garage" inurl:"/occupancy"
```

---

## 13. The Layer Management System

The user experience of GRIDLAND depends as much on what can be *hidden* as what can be *shown*. The layer management system must be powerful enough for expert users to build complex composites, and simple enough for casual users to turn everything off and look at one camera feed.

### 13.1 Layer Group Taxonomy

```javascript
const LAYER_GROUPS = {

    space_orbit: {
        label: 'Space & Orbit',
        icon:  '🛸',
        defaultOpen: false,
        visibleAtAltitudeMin: 100_000,
        layers: {
            iss:          { label: 'International Space Station', default: true },
            starlink:     { label: 'Starlink Constellation',       default: false },
            weather_sats: { label: 'Weather Satellites',           default: true },
            all_leo:      { label: 'All LEO Objects (slow)',        default: false },
            goes_imagery: { label: 'GOES Cloud/Weather Imagery',   default: true },
            epic_earth:   { label: 'DSCOVR Full Earth Disk',       default: true }
        }
    },

    aviation: {
        label: 'Aviation',
        icon:  '✈️',
        defaultOpen: false,
        visibleAtAltitudeMin: 200,
        visibleAtAltitudeMax: 50_000,
        layers: {
            commercial:   { label: 'Commercial Aircraft',    default: true },
            helicopters:  { label: 'Helicopters',            default: true },
            military:     { label: 'Military Aircraft',      default: false },
            tfrs:         { label: 'Flight Restrictions',    default: true },
            pireps:       { label: 'Pilot Weather Reports',  default: false },
            metars:       { label: 'Airport Weather (METARs)', default: false }
        }
    },

    maritime: {
        label: 'Maritime',
        icon:  '🚢',
        defaultOpen: false,
        layers: {
            ais_vessels:  { label: 'AIS Vessel Tracking',    default: true },
            vessel_types: { label: 'Color by Vessel Type',   default: false },
            noaa_buoys:   { label: 'NOAA Buoys',             default: false },
            port_cameras: { label: 'Port Cameras',           default: true }
        }
    },

    traffic_roads: {
        label: 'Traffic & Roads',
        icon:  '🚗',
        defaultOpen: true,
        layers: {
            traffic_cams:   { label: 'Traffic Cameras (511)', default: true },
            traffic_flow:   { label: 'Traffic Flow Layer',    default: false },
            incidents:      { label: 'Traffic Incidents',     default: true },
            construction:   { label: 'Construction Cameras',  default: false }
        }
    },

    transit: {
        label: 'Public Transit',
        icon:  '🚌',
        defaultOpen: false,
        layers: {
            buses:        { label: 'Bus Positions',           default: true },
            rail:         { label: 'Rail / Subway',           default: true },
            bike_share:   { label: 'Bike Share Stations',     default: false },
            alerts:       { label: 'Service Alerts',          default: true }
        }
    },

    cameras_surveillance: {
        label: 'Cameras',
        icon:  '📷',
        defaultOpen: true,
        layers: {
            cctv:           { label: 'Exposed CCTV/DVR',      default: false },
            osm_cameras:    { label: 'OSM Community Cameras', default: true },
            alpr:           { label: 'LPR / ALPR Cameras',    default: false },
            broadcast_infra:{ label: 'Broadcast Infrastructure', default: false }
        }
    },

    weather: {
        label: 'Weather',
        icon:  '🌩️',
        defaultOpen: false,
        layers: {
            radar:        { label: 'NEXRAD Radar',            default: true },
            lightning:    { label: 'Lightning (Blitzortung)', default: true },
            air_quality:  { label: 'Air Quality (OpenAQ)',    default: false },
            nws_alerts:   { label: 'Severe Weather Alerts',   default: true },
            wind:         { label: 'Wind Layer',              default: false },
            satellite_ir: { label: 'Infrared Satellite',      default: false }
        }
    },

    emergency: {
        label: 'Emergency & Incidents',
        icon:  '🚨',
        defaultOpen: false,
        layers: {
            fema_disasters: { label: 'Federal Disasters',     default: true },
            earthquakes:    { label: 'Earthquakes (USGS)',    default: true },
            wildfires:      { label: 'Active Fires (FIRMS)',  default: true },
            scanner_audio:  { label: 'Scanner Feeds (Broadcastify)', default: false },
            digital_radio:  { label: 'Radio Calls (OpenMHZ)', default: false }
        }
    },

    environment: {
        label: 'Environment',
        icon:  '🌿',
        defaultOpen: false,
        layers: {
            epa_sites:    { label: 'EPA Regulated Sites',     default: false },
            inaturalist:  { label: 'Species Observations',    default: false },
            water_quality:{ label: 'Water / Buoy Data',       default: false },
            noise:        { label: 'Noise Monitoring',        default: false }
        }
    },

    context_info: {
        label: 'Context & Information',
        icon:  'ℹ️',
        defaultOpen: true,
        layers: {
            wikipedia:    { label: 'Wikipedia Articles',      default: true },
            aprs:         { label: 'APRS (Ham Radio / Balloons)', default: false },
            sdr_servers:  { label: 'Public Radio Receivers',  default: false },
            historical_maps:{ label: 'Historical Maps',       default: false }
        }
    },

    infrastructure: {
        label: 'Infrastructure',
        icon:  '🏗️',
        defaultOpen: false,
        layers: {
            fcc_towers:   { label: 'Broadcast Towers (FCC ASR)', default: false },
            cell_towers:  { label: 'Cell Towers (OpenCelliD)',   default: false },
            power_outages:{ label: 'Utility Outages',            default: false },
            ev_charging:  { label: 'EV Charging Stations',       default: false }
        }
    },

    street_view: {
        label: 'Street Level',
        icon:  '👁️',
        defaultOpen: true,
        layers: {
            mapillary:    { label: 'Mapillary Street View',   default: true },
            kartaview:    { label: 'KartaView',               default: false },
            panoramax:    { label: 'Panoramax',               default: false }
        }
    }
};
```

### 13.2 Layer Control Component

```javascript
class LayerPanel {
    constructor(layerEngine) {
        this.engine = layerEngine;
        this.el     = document.getElementById('layer-panel');
        this._render();
        this._setupSearch();
    }

    _render() {
        this.el.innerHTML = `
            <div class="layer-panel-header">
                <span>Layers</span>
                <input id="layer-search" placeholder="Filter layers..." />
            </div>
            <div class="layer-groups">
                ${Object.entries(LAYER_GROUPS).map(([groupId, group]) =>
                    this._renderGroup(groupId, group)
                ).join('')}
            </div>
            <div class="layer-panel-footer">
                <button id="btn-preset-minimal">Minimal</button>
                <button id="btn-preset-traffic">Traffic</button>
                <button id="btn-preset-weather">Weather</button>
                <button id="btn-preset-incident">Incident</button>
                <button id="btn-preset-full">Full</button>
            </div>
        `;
        this._attachHandlers();
        this._setupPresets();
    }

    _renderGroup(groupId, group) {
        const layers = Object.entries(group.layers)
            .map(([layerId, layer]) => `
                <div class="layer-row" data-layer="${groupId}.${layerId}">
                    <label>
                        <input type="checkbox" ${layer.default ? 'checked' : ''}
                               data-group="${groupId}" data-layer="${layerId}" />
                        ${layer.label}
                    </label>
                    <input type="range" class="layer-opacity"
                           min="0" max="100" value="100"
                           data-group="${groupId}" data-layer="${layerId}" />
                </div>
            `).join('');

        return `
            <div class="layer-group ${group.defaultOpen ? 'open' : ''}" id="grp-${groupId}">
                <div class="layer-group-header" onclick="this.parentElement.classList.toggle('open')">
                    <span>${group.icon} ${group.label}</span>
                    <span class="layer-group-chevron">▾</span>
                </div>
                <div class="layer-group-body">${layers}</div>
            </div>
        `;
    }

    _setupPresets() {
        const PRESETS = {
            'minimal': {
                // Only traffic cameras and Wikipedia
                on:  ['traffic_roads.traffic_cams', 'context_info.wikipedia'],
                off: '*'
            },
            'traffic': {
                on:  ['traffic_roads.traffic_cams', 'traffic_roads.incidents',
                      'transit.buses', 'transit.rail', 'transit.alerts',
                      'weather.radar', 'weather.nws_alerts'],
                off: '*'
            },
            'weather': {
                on:  ['weather.radar', 'weather.lightning', 'weather.air_quality',
                      'weather.nws_alerts', 'weather.satellite_ir',
                      'space_orbit.goes_imagery', 'environment.water_quality',
                      'aprs', 'emergency.earthquakes'],
                off: '*'
            },
            'incident': {
                on:  ['emergency.fema_disasters', 'emergency.earthquakes',
                      'emergency.wildfires', 'emergency.scanner_audio',
                      'weather.radar', 'weather.nws_alerts',
                      'cameras_surveillance.cctv', 'traffic_roads.traffic_cams',
                      'aviation.tfrs'],
                off: '*'
            },
            'full': { on: '*', off: [] }
        };

        ['minimal', 'traffic', 'weather', 'incident', 'full'].forEach(preset => {
            document.getElementById(`btn-preset-${preset}`)
                .addEventListener('click', () => this._applyPreset(PRESETS[preset]));
        });
    }

    _setupSearch() {
        document.getElementById('layer-search').addEventListener('input', (e) => {
            const term = e.target.value.toLowerCase();
            document.querySelectorAll('.layer-row').forEach(row => {
                const label = row.textContent.toLowerCase();
                row.style.display = label.includes(term) ? '' : 'none';
            });
        });
    }
}
```

---

## 14. Feature Concepts

These are proposed features beyond what the existing data naturally produces. Each is technically achievable with the sources already documented.

---

**[FEATURE — Witness Mode]**
Click any point on the map. GRIDLAND computes:
1. Which cameras have this point in their field of view (using OSM `camera:direction` + FOV geometry from GRIDLAND-6)
2. The Broadcastify scanner feed for this jurisdiction
3. Active NWS weather alerts for this county
4. USGS earthquake activity in the past 24h within 50km
5. NASA FIRMS fire detections within 25km
6. Wikipedia articles about this location
7. Transit vehicles expected within 500m in the next 10 minutes

All displayed in a single "Witness Report" panel. *"What is everything happening at this point, right now."*

---

**[FEATURE — The Pulse]**
Data events create brief visual pulses on the map. Implemented as animated CSS rings emanating from the point:
- 🟡 Yellow: New Blitzortung lightning strike
- 🔴 Red: Emergency incident dispatched (Broadcastify spike or FEMA alert)
- 🟢 Green: New camera stream confirmed live
- 🔵 Blue: Transit vehicle arriving at stop
- ⚪ White: New APRS object detected
- 🟠 Orange: NASA FIRMS fire detection

The overall effect: the map *breathes* with activity. Dense urban areas pulse with transit and incident data. Storm cells pulse with lightning. Wildfire perimeters pulse with satellite detection updates.

---

**[FEATURE — Night Vision Mode]**
When the current view center is on the night side of the Earth (computed from solar angle), GRIDLAND optionally switches the globe texture to NASA's VIIRS Black Marble nighttime lights product (NASA GIBS layer: `VIIRS_SNPP_DayNightBand_ENCC`). City grids emerge as networks of light. Highways trace glowing threads between them. ADS-B aircraft blink their navigation lights overhead. The ISS crosses the dark hemisphere.

---

**[FEATURE — Chase Mode]**
Lock the camera to follow any moving object in GRIDLAND:
- Follow the ISS as it completes its 92-minute orbit (1x or 100x time multiplier)
- Follow a specific ADS-B aircraft callsign from departure to arrival
- Follow an AIS vessel from port to port
- Follow a news helicopter currently covering a breaking story

The view rotates to keep the object centered. Altitude tracks the object's altitude automatically. Every contextual layer updates for the object's current position.

---

**[FEATURE — Storm Compositing]**
When NEXRAD radar reflectivity in an area exceeds 55 dBZ (severe threshold) AND Blitzortung lightning density exceeds a threshold in the same cell:
1. Auto-activate: NOAA severe weather alert check for that county
2. Auto-activate: APRS layer filtered to known storm chaser callsigns moving toward the cell
3. Auto-activate: NASA FIRMS check (fire + storm = extreme fire weather flag)
4. Surface: Any traffic cameras or public webcams within 20km of the storm
5. Highlight: The Broadcastify NWS Weather Radio feed for the affected region

*The storm becomes a composed event object — not just a radar blob but a multi-source situation.*

---

**[FEATURE — Altitude Weather Slice]**
A vertical cross-section panel (appears at the aviation layer altitude) showing a column of current atmosphere above the map center:
- Surface: METAR from nearest airport
- 3,000 ft: PIREPs from past 3 hours
- 8,000–12,000 ft: PIREPs, wind barbs from upper air soundings
- 18,000–30,000 ft: Upper air sounding data (NOAA IGRA)
- 50,000+ ft: APRS balloon data if available

*You see the whole atmosphere at a glance, populated with real observations.*

---

**[FEATURE — Context Halo]**
Hover over any location for 2+ seconds. A soft radial halo appears. Wikipedia articles about nearby subjects populate a panel with thumbnails and opening sentences. No click needed. Works at any zoom level. As you fly over any city, the halo tells you what you're looking at as you pass over it.

---

**[FEATURE — Radio Window]**
A persistent corner panel showing:
1. Nearest public KiwiSDR or OpenWebRX server to the current map center (with embed link)
2. Top 3 Broadcastify feeds by listener count for the current county
3. Most recent OpenMHZ calls in the past 20 minutes for the current jurisdiction
4. A "Tune In" button that opens an embedded audio player

*You can hear the radio environment of any place you're viewing.*

---

## 15. Full Contextual Layer Registry

This extends the GRIDLAND-5/6 and GRIDLAND-7 data source matrices with all contextual layers.

| Layer | Source | Update Rate | Auth | Cost |
|---|---|---|---|---|
| NEXRAD radar tiles | Iowa State / IEM | 5 min | None | Free |
| Lightning strikes | Blitzortung | Real-time | None (relay) | Free |
| Weather conditions | OpenWeatherMap | 10 min | Free key | Free (limited) |
| NWS severe alerts | weather.gov | Real-time | None | Free |
| Air quality | OpenAQ | Varies | Free key | Free |
| METAR weather obs | aviationweather.gov | 30–60 min | None | Free |
| PIREPs (pilot reports) | aviationweather.gov | Continuous | None | Free |
| TFRs / NOTAMs | FAA | Real-time | None | Free |
| Police/fire scanner | Broadcastify | Real-time | API key (licensed) | Paid |
| Digital radio calls | OpenMHZ | Real-time | None | Free |
| Federal disasters | FEMA OpenFEMA | As declared | None | Free |
| Earthquakes | USGS | Minutes | None | Free |
| Active fires | NASA FIRMS | Hours (satellite pass) | Free key | Free |
| GTFS-RT vehicle pos. | Transitland / agencies | 15–30 sec | Free key | Free |
| SEPTA real-time | SEPTA API | ~30 sec | None | Free |
| MTA NYC real-time | MTA | ~30 sec | Free key | Free |
| Bike share status | GBFS | 5 min | None | Free |
| AIS vessel positions | AISHub | Real-time | API key | Free (research) |
| NOAA buoys | NDBC | 10–60 min | None | Free |
| NASA FIRMS (fire) | FIRMS API | Hours | Free key | Free |
| OpenAQ air quality | OpenAQ | Varies | Free key | Free |
| EPA regulated sites | Envirofacts | Static/annual | None | Free |
| iNaturalist species | iNaturalist API | As observed | None | Free |
| Wikipedia articles | Wikipedia API | As edited | None | Free |
| APRS positions | aprs.fi | Real-time | Free key | Free |
| APRS weather | aprs.fi | Real-time | Free key | Free |
| Storm chasers | APRS (filter) | Real-time | Free key | Free |
| Stratospheric balloons | APRS (filter) | Real-time | Free key | Free |
| KiwiSDR locations | kiwisdr.com | Static | None | Free |
| OpenWebRX servers | sdr.hu / Shodan | Static | None | Free |
| Street view (Mapillary) | Mapillary v4 | Updated by contributors | Free key | Free |
| Street view (KartaView) | KartaView | Updated by contributors | Free key | Free |
| Street view (Panoramax) | Panoramax | Updated by contributors | None | Free |

---

## Questions for Next Steps

Before writing GRIDLAND-9, input is needed on:

1. **Backend language preference** — Python (FastAPI/Flask) or Node (Express/Fastify)? This determines how the API aggregation layer gets built.

2. **Deployment target** — Self-hosted, cloud (AWS/GCP/Azure), or undecided?

3. **Real-time data pipeline** — Should vehicle positions (aircraft, buses, ships) push to clients via WebSocket/SSE, or is polling acceptable for now?

4. **The photosphere experience** — Is the transition to street view mode a priority feature for the first version, or is it a later-phase addition?

5. **The name "GRIDLAND"** — Is this the final product name? Asking because GRIDLAND-9 could cover branding, UI design language, and the public-facing architecture if this is heading toward a real launch.

---

*GRIDLAND-8 — Contextual Layers & Street-Level Experience — Compiled 2026-05-17*
*All sources referenced are publicly accessible APIs and open data.*
