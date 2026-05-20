# GRIDLAND-7 — Altitude Stack Reference

Technical reference for sources covering ~30 m altitude to the L1 Lagrange point. Additive to GRIDLAND-5 and GRIDLAND-6.

## Table of Contents

1. [The Altitude Band Reference](#1-the-altitude-band-reference)
2. [L1 Lagrange Point — DSCOVR / EPIC](#2-l1-lagrange-point--dscovr--epic)
3. [Geostationary Orbit (35,786 km) — GOES & Weather Sats](#3-geostationary-orbit-35786-km--goes--weather-sats)
4. [Low Earth Orbit (160–2,000 km) — ISS, Starlink, Observation Sats](#4-low-earth-orbit-1602000-km--iss-starlink-observation-sats)
5. [Satellite Tracking APIs](#5-satellite-tracking-apis)
6. [NASA Live Feed Inventory](#6-nasa-live-feed-inventory)
7. [NOAA GOES Imagery Pipeline](#7-noaa-goes-imagery-pipeline)
8. [Orbital Mechanics in JavaScript — satellite.js](#8-orbital-mechanics-in-javascript--satellitejs)
9. [Stratospheric Layer (12–50 km) — Balloons & HAPS](#9-stratospheric-layer-1250-km--balloons--haps)
10. [Aviation Layer (100 m–12,000 m) — ADS-B](#10-aviation-layer-100-m12000-m--ads-b)
11. [Sub-Aviation / Broadcast Layer (30–3,000 m)](#11-sub-aviation--broadcast-layer-303000-m)
12. [CesiumJS — Altitude-Driven Layer Architecture](#12-cesiumjs--altitude-driven-layer-architecture)
13. [The Full Zoom Stack — Integration Pattern](#13-the-full-zoom-stack--integration-pattern)

---

## 1. The Altitude Band Reference

Every row in this table represents a layer that GRIDLAND renders as you zoom.

| Altitude | Layer | Objects Present | Live Data Available? | Key Sources |
|---|---|---|---|---|
| 1.5M km | L1 Lagrange Point | DSCOVR satellite | Yes — EPIC full-disk Earth images every ~2h | NASA EPIC API |
| 35,786 km | Geostationary Orbit (GEO) | GOES-16/18, Himawari, Meteosat, GPS | Yes — satellite imagery every 5–15 min | AWS S3 (noaa-goes16/18) |
| 20,200 km | Medium Earth Orbit (MEO) | GPS constellation (31 satellites) | Position only (TLE) | Celestrak |
| 550–570 km | Starlink Shell 1 | ~3,500 Starlink sats | Position (TLE, propagated) | Celestrak, satellite.js |
| 408 km | ISS Orbit | International Space Station | Yes — NASA live video | Open Notify, NASA TV HLS |
| 340–560 km | Starlink Shells 2–5 | ~5,500 additional Starlink sats | Position (TLE, propagated) | Celestrak |
| 160–600 km | General LEO | ~9,000 active satellites total | Position (TLE) | Space-Track, Celestrak |
| 80–160 km | Mesosphere / Thermosphere edge | Meteor trails, aurora | No live feeds | — |
| 20–50 km | Stratosphere | Weather balloons, HAPS (Zephyr) | Balloon: sounding data; HAPS: experimental | NOAA IGRA |
| 10–20 km | Upper troposphere | Commercial aviation cruising | Yes — ADS-B (OpenSky, ADS-B Exchange) | OpenSky Network |
| 3–10 km | Mid troposphere | Commercial aviation climb/descent | Yes — ADS-B | OpenSky Network |
| 1–3 km | Low altitude aviation | News helicopters, police aviation, general aviation | ADS-B + live video (some) | OpenSky, Shodan (GRIDLAND-6) |
| 300–1,000 m | Broadcast tower height | TV towers, microwave links | Position (FCC ASR), some live feeds | FCC ASR database |
| 100–300 m | Rooftop / crane height | Construction cameras, building roof cams | Some | Shodan, Windy Webcams |
| 0–100 m | Street / ground level | Traffic cameras, CCTV, OSM-mapped cameras | Yes — all GRIDLAND-5/6 sources | 511 APIs, Shodan, OSM |

---

## 2. L1 Lagrange Point — DSCOVR / EPIC

The **Deep Space Climate Observatory (DSCOVR)** sits at the L1 Lagrange point — the gravitational balance point between Earth and the Sun, approximately 1.5 million kilometers from Earth. Its **EPIC (Earth Polychromatic Imaging Camera)** captures the most complete view of Earth available as a public data product: a full sunlit disk, updated approximately every 2 hours.

This is the maximum zoom-out view in GRIDLAND — the whole Earth, rotating, in near real-time.

### API

```python
import requests
from datetime import datetime, timezone

NASA_KEY = "YOUR_NASA_KEY"  # Free at api.nasa.gov
EPIC_BASE = "https://epic.gsfc.nasa.gov"

def get_latest_epic_image(color="natural"):
    """
    Get the most recent EPIC full-disk Earth image.
    color: "natural" (true color) or "enhanced" (false color, more vivid)
    """
    r = requests.get(
        f"https://api.nasa.gov/EPIC/api/{color}",
        params={"api_key": NASA_KEY}
    )
    images = r.json()
    if not images:
        return None

    # Most recent is last in list
    latest = images[-1]

    # Parse date components for image URL construction
    dt = datetime.strptime(latest['date'], "%Y-%m-%d %H:%M:%S")
    date_path = dt.strftime("%Y/%m/%d")

    return {
        'image_name':  latest['image'],
        'date':        latest['date'],
        'lat_centroid': latest['centroid_coordinates']['lat'],
        'lon_centroid': latest['centroid_coordinates']['lon'],

        # Full resolution PNG (~10MB)
        'url_png': f"{EPIC_BASE}/archive/{color}/{date_path}/png/{latest['image']}.png",

        # Half-resolution JPG (faster)
        'url_jpg': f"{EPIC_BASE}/archive/{color}/{date_path}/jpg/{latest['image']}.jpg",

        # Thumbnail (quick preview)
        'url_thumb': f"{EPIC_BASE}/archive/{color}/{date_path}/thumbs/{latest['image']}.jpg",

        # DSCOVR position at time of capture
        'dscovr_j2000': latest.get('dscovr_j2000'),
        'lunar_j2000':  latest.get('lunar_j2000'),
        'sun_j2000':    latest.get('sun_j2000'),
    }

def get_epic_images_for_date(date_str, color="natural"):
    """Get all EPIC images for a specific date. date_str: 'YYYY-MM-DD'"""
    r = requests.get(
        f"https://api.nasa.gov/EPIC/api/{color}/date/{date_str}",
        params={"api_key": NASA_KEY}
    )
    return r.json()
```

### CesiumJS Integration

At maximum zoom-out altitude in CesiumJS (>1M km), you can display the EPIC image as a billboard pinned to the Earth's center, updated every 2 hours. The effect: a photorealistic full-Earth disk replacing the default Blue Marble texture when zoomed far out.

```javascript
async function loadEpicLayer(viewer) {
    const meta = await fetch('/api/epic/latest').then(r => r.json());

    viewer.entities.add({
        id: 'epic_earth',
        position: Cesium.Cartesian3.ZERO,  // Earth center
        billboard: {
            image: meta.url_jpg,
            width:  1024,
            height: 1024,
            // Fade in when camera is very far out
            show: new Cesium.CallbackProperty(() =>
                viewer.camera.positionCartographic.height > 500000000, false
            )
        },
        description: `Full Earth disk — DSCOVR/EPIC — ${meta.date} UTC`
    });

    // Auto-refresh every 2 hours
    setInterval(() => loadEpicLayer(viewer), 7200000);
}
```

---

## 3. Geostationary Orbit (35,786 km) — GOES & Weather Sats

At GEO orbit, satellites rotate at the same rate as the Earth and appear stationary from the ground. The most important for GRIDLAND: **GOES-16** (GOES-East, covering Americas) and **GOES-18** (GOES-West), both operated by NOAA. Their full-disk Earth imagery is stored in a **public AWS S3 bucket with no authentication required** and updated every 10–15 minutes.

At this zoom level in CesiumJS, you're looking at a planet. The GOES imagery becomes the globe texture — a near-real-time cloud and weather layer draped over the terrain.

### GOES Satellite Positions (for rendering in orbit view)

| Satellite | NORAD ID | Longitude | AWS Bucket |
|---|---|---|---|
| GOES-16 | 41866 | 75.2° W | `noaa-goes16` |
| GOES-18 | 51850 | 137.2° W | `noaa-goes18` |
| Himawari-9 | 40932 | 140.7° E | `noaa-himawari8` |
| Meteosat-9 | 28912 | 0° (Prime) | EUMETSAT |
| Meteosat-10 | 38552 | 9.5° E | EUMETSAT |

### GOES Imagery Products

| Product Code | Description | Update Rate | Coverage |
|---|---|---|---|
| `ABI-L2-CMIPF` | Cloud and Moisture Imagery (Full Disk) | 10 min | Full Earth disk |
| `ABI-L2-CMIPC` | Cloud and Moisture Imagery (CONUS) | 5 min | Continental US |
| `ABI-L2-CMIPF` band 2 | Visible light (blue) | 10 min | Full disk |
| `ABI-L2-CMIPF` band 13 | Clean IR longwave (cloud tops) | 10 min | Full disk |
| `ABI-L2-SSTF` | Sea Surface Temperature | 60 min | Full disk |
| `ABI-L2-TPWF` | Total Precipitable Water | 10 min | Full disk |
| `GLM-L2-LCFA` | Lightning detection | 20 seconds | Full disk |

### GOES S3 Path Structure

```
s3://noaa-goes16/{product}/{year}/{day_of_year}/{hour}/OR_{product}-M6_{band}_G16_sYYYYDDDHHMMSSx_eYYYY...nc
```

Example:
```
s3://noaa-goes16/ABI-L2-CMIPF/2026/137/18/OR_ABI-L2-CMIPF-M6C02_G16_s20261371800208_e...nc
```

### Fetching Latest GOES Imagery

```python
import boto3
import io
import numpy as np
from botocore import UNSIGNED
from botocore.config import Config
from datetime import datetime, timezone, timedelta
from PIL import Image
import netCDF4 as nc

s3 = boto3.client(
    's3',
    region_name='us-east-1',
    config=Config(signature_version=UNSIGNED)
)

def get_latest_goes_key(product='ABI-L2-CMIPF', band='C02', satellite='noaa-goes16'):
    """Return the S3 key of the most recent GOES image for a given product/band."""
    now = datetime.now(timezone.utc)

    for delta_hours in range(0, 6):
        t = now - timedelta(hours=delta_hours)
        prefix = f"{product}/{t.year}/{t.timetuple().tm_yday:03d}/{t.hour:02d}/"

        try:
            response = s3.list_objects_v2(
                Bucket=satellite,
                Prefix=prefix
            )
            objects = [
                o for o in response.get('Contents', [])
                if f'C{band[-2:]}' in o['Key'] or band in o['Key']
            ]
            if objects:
                # Sort by last modified, return most recent
                return sorted(objects, key=lambda x: x['LastModified'])[-1]['Key']
        except Exception:
            continue

    return None

def goes_nc_to_png(bucket, key, output_path):
    """Convert a GOES netCDF4 file to a PNG for web serving."""
    obj = s3.get_object(Bucket=bucket, Key=key)
    data = nc.Dataset('inmemory.nc', memory=obj['Body'].read())

    # Read radiance/reflectance values
    variable = list(data.variables.keys())[0]
    values = data.variables[variable][:]

    # Normalize to 0-255
    vmin, vmax = np.nanpercentile(values, [2, 98])
    normalized = np.clip((values - vmin) / (vmax - vmin), 0, 1)
    img_array = (normalized * 255).astype(np.uint8)

    img = Image.fromarray(img_array)
    img.save(output_path)
    return output_path
```

### Using NASA GIBS as a WMTS Layer (Simpler Alternative)

For web rendering without the netCDF4 pipeline, NASA GIBS pre-processes satellite imagery into standard web map tiles (WMTS). This is the fastest path to getting GOES-quality imagery into CesiumJS:

```javascript
// True-color VIIRS satellite imagery (daily, near-real-time)
const viirsLayer = new Cesium.WebMapTileServiceImageryProvider({
    url: 'https://gibs.earthdata.nasa.gov/wmts/epsg4326/best/'
       + 'VIIRS_SNPP_CorrectedReflectance_TrueColor/default/'
       + '{Time}/GoogleMapsCompatible_Level8/{TileMatrix}/{TileRow}/{TileCol}.jpg',
    layer:           'VIIRS_SNPP_CorrectedReflectance_TrueColor',
    style:           'default',
    tileMatrixSetID: 'GoogleMapsCompatible_Level8',
    maximumLevel:    8,
    format:          'image/jpeg',
    credit:          'NASA GIBS / VIIRS'
});
viewer.imageryLayers.addImageryProvider(viirsLayer);

// GOES-East visible imagery (updated every 10 minutes on GIBS)
const goesLayer = new Cesium.WebMapTileServiceImageryProvider({
    url: 'https://gibs.earthdata.nasa.gov/wmts/epsg4326/best/'
       + 'GOES-East_ABI_Band2_Red_Visible_1km/default/'
       + '{Time}/GoogleMapsCompatible_Level8/{TileMatrix}/{TileRow}/{TileCol}.png',
    layer:           'GOES-East_ABI_Band2_Red_Visible_1km',
    style:           'default',
    tileMatrixSetID: 'GoogleMapsCompatible_Level8',
    maximumLevel:    8,
    format:          'image/png',
    credit:          'NASA GIBS / NOAA GOES'
});

// GOES Lightning (GLM) — overlay showing lightning strikes
const lightningLayer = new Cesium.WebMapTileServiceImageryProvider({
    url: 'https://gibs.earthdata.nasa.gov/wmts/epsg4326/best/'
       + 'GOES-East_GLM_Groups_Density_5min/default/'
       + '{Time}/GoogleMapsCompatible_Level6/{TileMatrix}/{TileRow}/{TileCol}.png',
    layer:           'GOES-East_GLM_Groups_Density_5min',
    style:           'default',
    tileMatrixSetID: 'GoogleMapsCompatible_Level6',
    maximumLevel:    6,
    credit:          'NASA GIBS / NOAA GOES GLM'
});
```

---

## 4. Low Earth Orbit (160–2,000 km) — ISS, Starlink, Observation Sats

### ISS — Live Video + Position

The ISS orbits at approximately 408 km altitude, completing one full orbit every 92 minutes. At this altitude in CesiumJS, the ISS is a single point moving visibly fast across the globe — crossing from horizon to horizon in about 10 minutes as seen from any ground observer.

**Current live video streams:**

| Stream | Format | Notes |
|---|---|---|
| NASA TV Public (Channel 1) | HLS | `https://ntv1.akamaized.net/hls/live/2014075/NASA-NTV1-HLS/master_2000.m3u8` |
| NASA TV Media (Channel 3) | HLS | `https://ntv3.akamaized.net/hls/live/2016416/NASA-NTV3-HLS/master.m3u8` |
| NASA+ App Stream | HLS | Available via NASA+ platform (free) |
| NASA Earth Observation | HLS | External HD camera feed when ISS on daylit side |
| YouTube Live (NASA) | HLS (via YT) | @NASA channel, 24/7 ISS view or NASA TV |

> **Day/Night behavior:** When the ISS is in Earth's shadow (~36 min of each 92-min orbit),
> the external camera feed goes dark. This is not a stream failure — it's orbital mechanics.
> The GRIDLAND UI should indicate orbital day/night status on the ISS marker.

**Himawari-9 rapid scan (30 second updates for some sectors) available on AWS.**

### The Full Satellite Catalog

At LEO altitude in GRIDLAND, rather than showing individual satellite dots (there are 9,000+), you can render:
- Constellation shells as translucent orbital bands
- Individual named objects (ISS, Hubble, major weather sats) as labeled points
- Zoom in on a cluster to expand to individual satellites

The catalog is freely available from multiple sources and updated multiple times daily.

---

## 5. Satellite Tracking APIs

### 5.1 Open Notify — ISS Position (Simplest)

No auth, no rate limit (be polite — poll every 5 seconds max).

```python
import requests
import time

def track_iss():
    r = requests.get("http://api.open-notify.org/iss-now.json", timeout=5)
    data = r.json()
    return {
        'lat':       float(data['iss_position']['latitude']),
        'lon':       float(data['iss_position']['longitude']),
        'timestamp': data['timestamp'],
        'altitude_km': 408.0  # approximately constant; use TLE for precise value
    }

# ISS pass prediction over a location
def get_iss_passes(lat, lon, n=5):
    r = requests.get(
        "http://api.open-notify.org/iss-pass.json",
        params={"lat": lat, "lon": lon, "n": n},
        timeout=5
    )
    return r.json()['response']  # list of {duration, risetime} dicts
```

### 5.2 N2YO — Any Satellite by NORAD ID

```python
N2YO_KEY = "YOUR_KEY"
N2YO_BASE = "https://api.n2yo.com/rest/v1/satellite"

def get_satellite_position(norad_id, observer_lat=0, observer_lon=0,
                            observer_alt=0, seconds=1):
    """Get current + predicted positions for any NORAD-cataloged satellite."""
    r = requests.get(
        f"{N2YO_BASE}/positions/{norad_id}/{observer_lat}/{observer_lon}"
        f"/{observer_alt}/{seconds}/",
        params={"apiKey": N2YO_KEY}
    )
    data = r.json()
    return {
        'name':      data['info']['satname'],
        'norad_id':  data['info']['satid'],
        'positions': [
            {
                'lat':       p['satlatitude'],
                'lon':       p['satlongitude'],
                'altitude':  p['sataltitude'],  # km
                'azimuth':   p['azimuth'],       # degrees from north
                'elevation': p['elevation'],     # degrees above horizon
                'timestamp': p['timestamp']
            }
            for p in data['positions']
        ]
    }

def get_satellites_above(lat, lon, alt_km, search_radius_deg, category_id=0):
    """
    Get all satellites currently above an observer.
    category_id: 0=all, 52=Starlink, 18=weather, 29=ISS...
    """
    r = requests.get(
        f"{N2YO_BASE}/above/{lat}/{lon}/{alt_km}/{search_radius_deg}/{category_id}/",
        params={"apiKey": N2YO_KEY}
    )
    return r.json()

# N2YO Category IDs relevant to GRIDLAND
N2YO_CATEGORIES = {
    0:   "All satellites",
    18:  "Weather",
    29:  "Space stations (ISS etc.)",
    52:  "Starlink",
    20:  "GPS operational",
    24:  "Geostationary",
    32:  "Iridium",
    48:  "OneWeb",
    53:  "Planet Labs",
}
```

### 5.3 Space-Track.org — Official NORAD Catalog

The authoritative source. ~40,000 tracked objects. Requires free account.

```python
import requests

SPACETRACK_BASE = "https://www.space-track.org"

class SpaceTrackClient:
    def __init__(self, username, password):
        self.session = requests.Session()
        self._login(username, password)

    def _login(self, username, password):
        self.session.post(
            f"{SPACETRACK_BASE}/ajaxauth/login",
            data={"identity": username, "password": password}
        )

    def get_tle(self, norad_id):
        """Get latest TLE for a single object."""
        r = self.session.get(
            f"{SPACETRACK_BASE}/basicspacedata/query/class/gp"
            f"/NORAD_CAT_ID/{norad_id}/orderby/EPOCH desc/limit/1/format/json"
        )
        return r.json()

    def get_group_tles(self, group_name):
        """
        Get TLEs for a named group.
        group_name: 'starlink', 'weather', 'stations', 'geo' etc.
        """
        r = self.session.get(
            f"{SPACETRACK_BASE}/basicspacedata/query/class/gp"
            f"/OBJECT_TYPE/PAYLOAD/CONSTELLATION/{group_name}/format/tle"
        )
        return r.text  # Raw TLE format

    def search_by_name(self, name_pattern):
        """Search satellites by name pattern."""
        r = self.session.get(
            f"{SPACETRACK_BASE}/basicspacedata/query/class/gp"
            f"/OBJECT_NAME/{name_pattern}~~OBJECT_TYPE/PAYLOAD/format/json"
        )
        return r.json()
```

### 5.4 Celestrak — Free TLE Downloads (No Auth)

Best for bulk constellation data. Cache locally, refresh every 2 hours.

```python
import requests
from datetime import datetime, timezone

CELESTRAK_BASE = "https://celestrak.org/NORAD/elements/gp.php"

CELESTRAK_GROUPS = {
    'stations':   'stations',      # ISS, CSS, etc.
    'active':     'active',        # All active satellites
    'starlink':   'starlink',      # SpaceX Starlink
    'weather':    'weather',       # NOAA, GOES, Himawari
    'goes':       'goes',          # GOES specifically
    'geo':        'geo',           # All GEO satellites
    'gps':        'gps-ops',       # GPS constellation
    'iridium':    'iridium',       # Iridium
    'oneweb':     'oneweb',        # OneWeb
    'planet':     'planet',        # Planet Labs
    'cubesat':    'cubesat',       # All CubeSats
    'last30':     'last-30-days',  # Recently launched
}

def fetch_tles(group, format='tle'):
    """
    Fetch TLE data for a satellite group from Celestrak.
    format: 'tle', 'json', 'xml', 'csv'
    """
    r = requests.get(
        CELESTRAK_BASE,
        params={"GROUP": group, "FORMAT": format},
        timeout=30
    )
    r.raise_for_status()
    return r.text if format == 'tle' else r.json()

def parse_tle_text(tle_text):
    """Parse raw TLE text into list of (name, line1, line2) tuples."""
    lines = [l.strip() for l in tle_text.strip().split('\n') if l.strip()]
    satellites = []
    for i in range(0, len(lines) - 2, 3):
        name  = lines[i]
        line1 = lines[i+1]
        line2 = lines[i+2]
        if line1.startswith('1 ') and line2.startswith('2 '):
            satellites.append({
                'name':    name,
                'tle1':    line1,
                'tle2':    line2,
                'norad_id': int(line1[2:7]),
                'epoch':   line1[18:32].strip()
            })
    return satellites

# Example: Download Starlink TLEs and parse
starlink_tles = parse_tle_text(fetch_tles('starlink'))
print(f"Loaded {len(starlink_tles)} Starlink satellites")
```

---

## 6. NASA Live Feed Inventory

| Feed | Format | URL / Access | Notes |
|---|---|---|---|
| NASA TV Public (NTV1) | HLS | `ntv1.akamaized.net/hls/live/2014075/NASA-NTV1-HLS/master_2000.m3u8` | 24/7 programming, mission coverage |
| NASA TV Media (NTV3) | HLS | `ntv3.akamaized.net/hls/live/2016416/NASA-NTV3-HLS/master.m3u8` | Uncut mission audio/video |
| ISS External HD Camera | HLS (via YT) | NASA YouTube Live — search "@NASA" live | Earth views when ISS on daylit side |
| NASA EPIC | REST API | `api.nasa.gov/EPIC/api/natural` | Full Earth disk, ~2h delay |
| NASA Earth Observatory | RSS/API | `earthobservatory.nasa.gov/feeds/natural-event-feed.rss` | Near real-time Earth events |
| NOAA GOES-16 (East) | AWS S3 | `s3://noaa-goes16/` (public, no auth) | 10-min full disk imagery |
| NOAA GOES-18 (West) | AWS S3 | `s3://noaa-goes18/` (public, no auth) | 10-min full disk imagery |
| Himawari-9 | AWS S3 | `s3://noaa-himawari8/` (public, no auth) | 10-min full disk, Asia-Pacific |
| NASA GIBS/WorldView | WMTS | `gibs.earthdata.nasa.gov/wmts/` | 100+ layers, CesiumJS-ready |
| Space Weather | REST | `services.swpc.noaa.gov/products/` | Solar wind, aurora forecasts |
| JPL Solar System | REST | `ssd.jpl.nasa.gov/api/` | Planet/body ephemeris |

### Structured Feed Object (for GRIDLAND's feed registry)

```python
NASA_FEEDS = {
    "nasa_tv_public": {
        "label":      "NASA TV",
        "url":        "https://ntv1.akamaized.net/hls/live/2014075/NASA-NTV1-HLS/master_2000.m3u8",
        "format":     "hls",
        "lat":        None,   # Not geo-anchored
        "lon":        None,
        "altitude_m": None,
        "type":       "broadcast",
        "live":       True,
        "update_s":   None    # Continuous
    },
    "iss_position": {
        "label":      "International Space Station",
        "position_api": "http://api.open-notify.org/iss-now.json",
        "video_url":  "https://ntv1.akamaized.net/hls/live/2014075/NASA-NTV1-HLS/master_2000.m3u8",
        "format":     "hls",
        "altitude_m": 408000,  # ~408 km
        "type":       "spacecraft",
        "live":       True,
        "update_s":   5
    },
    "epic_earth": {
        "label":      "DSCOVR / EPIC — Full Earth",
        "api_url":    "https://api.nasa.gov/EPIC/api/natural",
        "format":     "image",
        "altitude_m": 1500000000,  # 1.5M km
        "type":       "satellite_image",
        "live":       False,   # Updated every ~2h, not streaming
        "update_s":   7200
    }
}
```

---

## 7. NOAA GOES Imagery Pipeline

This pipeline fetches the latest full-disk Earth image from GOES-16 and makes it available as a web-servable JPEG for CesiumJS to use as a globe texture overlay.

```python
import boto3
import netCDF4 as nc
import numpy as np
from PIL import Image
from botocore import UNSIGNED
from botocore.config import Config
from datetime import datetime, timezone, timedelta
import io

s3 = boto3.client('s3', region_name='us-east-1',
                  config=Config(signature_version=UNSIGNED))

GOES_PRODUCTS = {
    'visible':    ('ABI-L2-CMIPF', 'C02'),   # Band 2 — red/visible
    'infrared':   ('ABI-L2-CMIPF', 'C13'),   # Band 13 — clean IR longwave
    'water_vapor':('ABI-L2-CMIPF', 'C09'),   # Band 9 — mid-level water vapor
    'lightning':  ('GLM-L2-LCFA',  None),    # Lightning flash data
}

def find_latest_goes_key(product, band=None, satellite='noaa-goes16',
                          max_lookback_hours=3):
    """Find the S3 key of the most recent GOES file for a product/band."""
    now = datetime.now(timezone.utc)
    for h in range(max_lookback_hours * 12):  # check in 5-min increments
        t = now - timedelta(minutes=h * 5)
        prefix = (f"{product}/{t.year}/{t.timetuple().tm_yday:03d}"
                  f"/{t.hour:02d}/")
        try:
            resp = s3.list_objects_v2(Bucket=satellite, Prefix=prefix)
            keys = [o['Key'] for o in resp.get('Contents', [])
                    if band is None or f'C{band[-2:]}' in o['Key']]
            if keys:
                return sorted(keys)[-1]  # Most recent filename
        except Exception:
            continue
    return None

def goes_band_to_jpeg(bucket, key, width=2048, jpeg_quality=85):
    """
    Fetch a GOES netCDF4 ABI file from S3 and return a JPEG bytes object
    suitable for serving to a web client.
    """
    obj = s3.get_object(Bucket=bucket, Key=key)
    nc_bytes = obj['Body'].read()

    dataset = nc.Dataset('inmemory', memory=nc_bytes)

    # The primary variable in ABI-L2 CMIP files is 'CMI' (cloud moisture index)
    cmi = dataset.variables['CMI'][:]

    # Normalize to 8-bit
    vmin = np.nanpercentile(cmi, 1)
    vmax = np.nanpercentile(cmi, 99)
    normalized = np.clip((cmi - vmin) / (vmax - vmin), 0, 1)
    img_array = (normalized * 255).astype(np.uint8)

    # GOES full disk is 5424x5424 — resize for web
    img = Image.fromarray(img_array, mode='L').convert('RGB')
    img = img.resize((width, width), Image.LANCZOS)

    buf = io.BytesIO()
    img.save(buf, format='JPEG', quality=jpeg_quality)
    buf.seek(0)
    return buf.read()

# Flask endpoint example
from flask import Flask, send_file
import io

app = Flask(__name__)

@app.route('/api/goes/latest/<product>')
def serve_goes_image(product):
    prod_code, band = GOES_PRODUCTS.get(product, GOES_PRODUCTS['visible'])
    key = find_latest_goes_key(prod_code, band)
    if not key:
        return "No data available", 503

    jpeg_bytes = goes_band_to_jpeg('noaa-goes16', key)
    return send_file(io.BytesIO(jpeg_bytes), mimetype='image/jpeg',
                     max_age=300,  # cache 5 minutes
                     as_attachment=False)
```

### GOES as a CesiumJS Globe Texture

```javascript
// Poll for fresh GOES imagery and swap it as globe texture
async function setupGoesTexture(viewer) {
    async function refreshGoes() {
        const timestamp = Date.now();
        const goesLayer = new Cesium.SingleTileImageryProvider({
            url: `/api/goes/latest/visible?t=${timestamp}`,
            rectangle: Cesium.Rectangle.fromDegrees(-180, -90, 180, 90)
        });

        // Remove old layer, add fresh one
        if (viewer._goesLayerRef) {
            viewer.imageryLayers.remove(viewer._goesLayerRef);
        }
        viewer._goesLayerRef = viewer.imageryLayers.addImageryProvider(goesLayer);
        viewer._goesLayerRef.alpha = 0.75;  // Overlay over base terrain
    }

    await refreshGoes();
    setInterval(refreshGoes, 600000);  // Refresh every 10 minutes
}
```

---

## 8. Orbital Mechanics in JavaScript — satellite.js

To render satellite positions in real-time in CesiumJS without continuous API calls, propagate orbits locally using TLE data and the SGP4 algorithm. **satellite.js** is the standard JavaScript library for this.

```bash
npm install satellite.js
```

### Basic Propagation

```javascript
import * as satellite from 'satellite.js';

function createSatelliteEntity(viewer, name, tle1, tle2) {
    const satrec = satellite.twoline2satrec(tle1, tle2);

    // Create a Cesium SampledPositionProperty for smooth interpolation
    const positionProperty = new Cesium.SampledPositionProperty();

    // Pre-compute positions for the next 2 hours at 30-second intervals
    const now = new Date();
    for (let i = 0; i < 240; i++) {
        const t = new Date(now.getTime() + i * 30 * 1000);
        const { position } = satellite.propagate(satrec, t);
        if (!position) continue;

        const gmst = satellite.gstime(t);
        const geo  = satellite.eciToGeodetic(position, gmst);

        const cartesian = Cesium.Cartesian3.fromRadians(
            geo.longitude,
            geo.latitude,
            geo.height * 1000  // satellite.js returns km, Cesium wants meters
        );

        positionProperty.addSample(
            Cesium.JulianDate.fromDate(t),
            cartesian
        );
    }

    positionProperty.setInterpolationOptions({
        interpolationDegree:  5,
        interpolationAlgorithm: Cesium.LagrangePolynomialApproximation
    });

    // Add entity
    return viewer.entities.add({
        id:       `sat_${satrec.satnum}`,
        name:     name,
        position: positionProperty,
        point: {
            pixelSize:  4,
            color:      Cesium.Color.YELLOW,
            outlineColor: Cesium.Color.BLACK,
            outlineWidth: 1,
            // Only show when camera is in orbital altitude range
            show: new Cesium.CallbackProperty(() =>
                viewer.camera.positionCartographic.height > 100000, false
            )
        },
        label: {
            text:          name,
            font:          '10px sans-serif',
            fillColor:     Cesium.Color.WHITE,
            outlineColor:  Cesium.Color.BLACK,
            outlineWidth:  2,
            style:         Cesium.LabelStyle.FILL_AND_OUTLINE,
            pixelOffset:   new Cesium.Cartesian2(0, -15),
            show: new Cesium.CallbackProperty(() =>
                viewer.camera.positionCartographic.height < 5000000 &&
                viewer.camera.positionCartographic.height > 100000, false
            )
        }
    });
}
```

### Loading a Full Constellation

```javascript
async function loadConstellation(viewer, group = 'starlink') {
    // Fetch TLE data from your backend (which fetched from Celestrak)
    const tleData = await fetch(`/api/tles/${group}`).then(r => r.text());

    const lines = tleData.trim().split('\n');
    const entities = [];

    for (let i = 0; i < lines.length - 2; i += 3) {
        const name = lines[i].trim();
        const tle1 = lines[i + 1].trim();
        const tle2 = lines[i + 2].trim();

        if (!tle1.startsWith('1 ') || !tle2.startsWith('2 ')) continue;

        try {
            const entity = createSatelliteEntity(viewer, name, tle1, tle2);
            entities.push(entity);
        } catch (e) {
            console.warn(`Failed to create entity for ${name}:`, e);
        }
    }

    console.log(`Loaded ${entities.length} satellites in ${group} constellation`);
    return entities;
}
```

### Real-Time Position Update

```javascript
// Clock-driven position — CesiumJS clock drives all satellite positions
// automatically when using SampledPositionProperty with the viewer clock
viewer.clock.shouldAnimate = true;
viewer.clock.multiplier = 1;  // Real-time (increase for time-lapse)

// To refresh TLE data and recompute positions every 2 hours:
setInterval(async () => {
    // Remove old entities
    constellationEntities.forEach(e => viewer.entities.remove(e));

    // Reload with fresh TLEs
    constellationEntities = await loadConstellation(viewer, 'starlink');
}, 7200000);
```

### ISS Orbit Path (Ground Track)

```javascript
function addISSGroundTrack(viewer, satrec) {
    const path_positions = [];
    const now = new Date();

    // Compute one full orbit (92 minutes)
    for (let i = 0; i <= 92 * 60; i += 30) {
        const t = new Date(now.getTime() + i * 1000);
        const { position } = satellite.propagate(satrec, t);
        if (!position) continue;

        const gmst = satellite.gstime(t);
        const geo  = satellite.eciToGeodetic(position, gmst);

        // Ground track at 0 altitude
        path_positions.push(Cesium.Cartesian3.fromRadians(
            geo.longitude, geo.latitude, 0
        ));
    }

    viewer.entities.add({
        polyline: {
            positions: path_positions,
            width: 1,
            material: new Cesium.PolylineDashMaterialProperty({
                color: Cesium.Color.YELLOW.withAlpha(0.5)
            }),
            clampToGround: true
        }
    });
}
```

---

## 9. Stratospheric Layer (12–50 km) — Balloons & HAPS

### NOAA Weather Balloon Data

NOAA launches radiosondes twice daily from ~92 US stations (00Z and 12Z UTC). While live in-flight tracking of individual balloons isn't publicly available in real-time, the sounding data provides position, altitude, and atmospheric measurements that can be used to reconstruct the balloon's path.

```python
import requests

def get_latest_soundings(station_id, n=5):
    """
    Fetch recent radiosonde sounding data from the University of Wyoming archive.
    This is the most accessible public sounding data endpoint.
    station_id: WMO station number (e.g. 72520 for Philadelphia)
    """
    from datetime import datetime
    now = datetime.utcnow()
    r = requests.get(
        "http://weather.uwyo.edu/cgi-bin/bufrraob.py",
        params={
            "station": station_id,
            "year":    now.year,
            "month":   now.month,
            "from":    now.strftime("%d%H"),
            "to":      now.strftime("%d%H"),
            "type":    "TEXT:BUFROBS"
        }
    )
    return r.text

# US radiosonde station IDs near Philadelphia:
# 72520 = Philadelphia IAP (Coyle, PA)
# 72501 = Albany, NY
# 72519 = Wallops Island, VA

# IGRA (Integrated Global Radiosonde Archive) — NOAA
def get_igra_recent(station_id):
    """IGRA provides near-real-time sounding data via NOAA's FTP."""
    r = requests.get(
        f"https://www.ncei.noaa.gov/data/integrated-global-radiosonde-archive"
        f"/access/derived-por/{station_id}-drvd.txt.zip"
    )
    return r.content  # Zipped text data
```

### Rendering Balloon Ascents in CesiumJS

While real-time individual balloon tracking isn't public, you can animate the ascent profile from sounding data — a balloon rising at ~5 m/s from a known launch site, following a wind profile at each altitude level.

```javascript
function animateBalloonAscent(viewer, launchLat, launchLon, soundingProfile) {
    // soundingProfile: array of {altitude_m, wind_speed_ms, wind_dir_deg, lat, lon}
    const positions = soundingProfile.map(level =>
        Cesium.Cartesian3.fromDegrees(level.lon, level.lat, level.altitude_m)
    );

    const launchTime = Cesium.JulianDate.now();

    viewer.entities.add({
        name: 'Weather Balloon',
        position: new Cesium.SampledPositionProperty(),
        billboard: {
            image: '/icons/balloon.png',
            width: 24,
            height: 24,
            verticalOrigin: Cesium.VerticalOrigin.BOTTOM
        },
        path: {
            show: true,
            leadTime: 0,
            trailTime: 3600,
            width: 1,
            material: new Cesium.ColorMaterialProperty(
                Cesium.Color.WHITE.withAlpha(0.6)
            )
        }
    });
}
```

---

## 10. Aviation Layer (100 m–12,000 m) — ADS-B

### OpenSky Network

The most accessible free ADS-B source. Returns all tracked aircraft globally.

```python
import requests
from datetime import datetime

OPENSKY_BASE = "https://opensky-network.org/api"

def get_aircraft_in_bbox(lamin, lomin, lamax, lomax,
                          username=None, password=None):
    """
    Get all aircraft currently in a bounding box.
    Returns list of state vectors.
    Anonymous: 10 sec refresh, rate limited.
    Authenticated: higher limits.
    """
    params = {
        "lamin": lamin,
        "lamax": lamax,
        "lomin": lomin,
        "lomax": lomax
    }
    auth = (username, password) if username else None

    r = requests.get(
        f"{OPENSKY_BASE}/states/all",
        params=params,
        auth=auth,
        timeout=15
    )
    data = r.json()

    if not data.get('states'):
        return []

    # State vector field indices (per OpenSky docs)
    FIELDS = [
        'icao24', 'callsign', 'origin_country', 'time_position',
        'last_contact', 'longitude', 'latitude', 'baro_altitude',
        'on_ground', 'velocity', 'true_track', 'vertical_rate',
        'sensors', 'geo_altitude', 'squawk', 'spi', 'position_source'
    ]

    aircraft = []
    for state in data['states']:
        a = dict(zip(FIELDS, state))
        if a.get('latitude') and a.get('longitude'):
            aircraft.append({
                'icao24':      a['icao24'],
                'callsign':    (a['callsign'] or '').strip(),
                'lat':         a['latitude'],
                'lon':         a['longitude'],
                'altitude_m':  a['baro_altitude'],   # meters
                'velocity_ms': a['velocity'],         # m/s
                'heading':     a['true_track'],       # degrees
                'climb_ms':    a['vertical_rate'],    # m/s
                'on_ground':   a['on_ground'],
                'squawk':      a['squawk'],
                'country':     a['origin_country'],
                'last_seen':   a['last_contact']
            })
    return aircraft

# Philadelphia area (50km radius approximated as bbox)
philly_aircraft = get_aircraft_in_bbox(
    lamin=39.5, lomin=-75.7,
    lamax=40.4, lomax=-74.6
)
```

### ADSB.fi (Radius Query — More Convenient)

```python
def get_aircraft_near(lat, lon, radius_km):
    """ADSB.fi radius query — simpler than OpenSky bbox."""
    r = requests.get(
        f"https://opendata.adsb.fi/api/v3/lat/{lat}/lon/{lon}/dist/{radius_km}",
        headers={"User-Agent": "GRIDLAND Research Tool"}
    )
    data = r.json()
    aircraft = []
    for ac in data.get('aircraft', []):
        if 'lat' not in ac or 'lon' not in ac:
            continue
        aircraft.append({
            'icao24':   ac.get('hex'),
            'callsign': ac.get('flight', '').strip(),
            'lat':      ac['lat'],
            'lon':      ac['lon'],
            'altitude_m': (ac.get('alt_baro', 0) or 0) * 0.3048,  # ft → m
            'velocity_ms': (ac.get('gs', 0) or 0) * 0.514444,     # kt → m/s
            'heading':  ac.get('track'),
            'climb_ms': (ac.get('baro_rate', 0) or 0) * 0.00508,  # fpm → m/s
            'on_ground': ac.get('alt_baro') == 'ground',
            'aircraft_type': ac.get('t'),
            'registration': ac.get('r'),
        })
    return aircraft
```

### CesiumJS Aircraft Layer

```javascript
const aircraftSource = new Cesium.CustomDataSource('aircraft');
viewer.dataSources.add(aircraftSource);

// Aircraft icon (replace with actual aircraft icon)
const AIRCRAFT_ICON = '/icons/aircraft.png';

async function updateAircraftLayer() {
    const altitude = viewer.camera.positionCartographic.height;
    if (altitude > 100000 || altitude < 50) {
        // Don't show aircraft at orbital or street level
        aircraftSource.show = false;
        return;
    }
    aircraftSource.show = true;

    const center = viewer.camera.positionCartographic;
    const lat = Cesium.Math.toDegrees(center.latitude);
    const lon = Cesium.Math.toDegrees(center.longitude);

    const aircraft = await fetch(
        `/api/aircraft/near?lat=${lat}&lon=${lon}&km=200`
    ).then(r => r.json());

    aircraftSource.entities.removeAll();

    for (const ac of aircraft) {
        if (!ac.lat || !ac.lon) continue;

        const isHelicopter = ['H60', 'R44', 'EC35', 'B407', 'S76']
            .includes(ac.aircraft_type);
        const isNewsChopper = isHelicopter &&
            (ac.callsign?.includes('SKY') || ac.callsign?.includes('AIR'));

        aircraftSource.entities.add({
            id:       `ac_${ac.icao24}`,
            position: Cesium.Cartesian3.fromDegrees(
                ac.lon, ac.lat, ac.altitude_m || 1000
            ),
            billboard: {
                image:           AIRCRAFT_ICON,
                width:           isNewsChopper ? 32 : 20,
                height:          isNewsChopper ? 32 : 20,
                rotation:        Cesium.Math.toRadians(-(ac.heading || 0)),
                alignedAxis:     Cesium.Cartesian3.UNIT_Z,
                color:           isNewsChopper
                                    ? Cesium.Color.YELLOW
                                    : Cesium.Color.WHITE,
                sizeInMeters:    false
            },
            description: `
                <b>${ac.callsign || ac.icao24}</b><br/>
                Altitude: ${Math.round(ac.altitude_m)} m<br/>
                Speed: ${Math.round(ac.velocity_ms * 1.944)} kts<br/>
                Type: ${ac.aircraft_type || 'Unknown'}<br/>
                ${isNewsChopper ? '<b>⚡ News Helicopter</b>' : ''}
            `
        });
    }
}

setInterval(updateAircraftLayer, 10000);
```

---

## 11. Sub-Aviation / Broadcast Layer (30–3,000 m)

Between the ground-level cameras (GRIDLAND-5/6) and commercial aviation, there is a rich mid-altitude zone containing:

- **News helicopters** at 300–1,500 m (ADS-B tracked + live video, see GRIDLAND-5/6)
- **Police/law enforcement aviation** at 300–1,500 m (ADS-B tracked)
- **General aviation** at all altitudes
- **Broadcast towers** at 30–600 m (FCC ASR database, see GRIDLAND-6)
- **Construction cameras** and **building roof cams** at 50–300 m

### Identifying News Helicopters in ADS-B Data

News helicopters fly specific patterns (orbiting a scene) and often have callsigns that follow station naming conventions:

```python
# Known news helicopter ICAO patterns and callsigns
NEWS_HELICOPTER_PATTERNS = {
    # Callsign prefixes (station designations)
    'callsigns': [
        'SKY', 'AIR', 'EAGLE', 'CHOPPER', 'NEWS',
        'WPVI', 'NBC10', 'CBS3', 'FOX29',
        # Add market-specific callsigns
    ],
    # Aircraft types that are commonly used as news helicopters
    'types': ['AS50', 'EC35', 'B407', 'H500', 'R66', 'S76', 'A109'],
    # Low altitude + orbiting pattern = likely news coverage
    'altitude_range_m': (100, 1500),
}

def classify_helicopter(aircraft):
    callsign = (aircraft.get('callsign') or '').upper().strip()
    ac_type  = (aircraft.get('aircraft_type') or '').upper()
    altitude = aircraft.get('altitude_m', 0) or 0

    is_news = (
        any(p in callsign for p in NEWS_HELICOPTER_PATTERNS['callsigns'])
        or (
            ac_type in NEWS_HELICOPTER_PATTERNS['types']
            and NEWS_HELICOPTER_PATTERNS['altitude_range_m'][0]
            < altitude
            < NEWS_HELICOPTER_PATTERNS['altitude_range_m'][1]
        )
    )
    return 'news_helicopter' if is_news else 'helicopter'
```

### Linking ADS-B Helicopters to GRIDLAND-6 Stream Data

When a news helicopter's ICAO24 or callsign is identified via ADS-B, cross-reference with:
1. Station ASN data (ARIN RDAP) to find the broadcaster's IP space
2. Shodan Teradek/LiveU results on that ASN
3. crt.sh subdomain enumeration for streaming infrastructure

This creates the complete picture: **real-time position + real-time video feed**.

---

## 12. CesiumJS — Altitude-Driven Layer Architecture

This is the core system that makes GRIDLAND seamless. A single event listener on the camera altitude drives which data sources are active, which layers are visible, and which UI panels are shown.

### Altitude Zone Definitions

```javascript
const ALTITUDE_ZONES = {
    DEEP_SPACE: {
        id: 'deep_space',
        min: 1_000_000_000,     // 1M km (Lagrange / deep space)
        max: Infinity,
        label: 'Deep Space',
        imageryLayer: 'starfield',
        dataSources: [],
        uiMode: 'space'
    },
    GEO_ORBIT: {
        id: 'geo_orbit',
        min: 30_000_000,        // 30,000 km
        max: 1_000_000_000,
        label: 'Geostationary Orbit',
        imageryLayer: 'epic_earth',      // DSCOVR/EPIC full disk
        dataSources: ['geo_satellites'],
        uiMode: 'geo'
    },
    MEO_ORBIT: {
        id: 'meo_orbit',
        min: 5_000_000,         // 5,000 km
        max: 30_000_000,
        label: 'Medium Earth Orbit',
        imageryLayer: 'goes_full_disk',  // GOES imagery as globe texture
        dataSources: ['geo_satellites', 'gps_constellation'],
        uiMode: 'orbital'
    },
    LEO_ORBIT: {
        id: 'leo_orbit',
        min: 100_000,           // 100 km
        max: 5_000_000,
        label: 'Low Earth Orbit',
        imageryLayer: 'goes_full_disk',
        dataSources: ['iss', 'starlink', 'leo_satellites', 'weather_sats'],
        uiMode: 'orbital'
    },
    HIGH_ATMOSPHERE: {
        id: 'high_atmosphere',
        min: 12_000,            // 12 km
        max: 100_000,
        label: 'Upper Atmosphere',
        imageryLayer: 'satellite_truecolor',  // NASA GIBS VIIRS
        dataSources: [],
        uiMode: 'atmosphere'
    },
    AVIATION: {
        id: 'aviation',
        min: 1_000,             // 1 km
        max: 12_000,
        label: 'Aviation',
        imageryLayer: 'satellite_truecolor',
        dataSources: ['aircraft', 'aircraft_trails'],
        uiMode: 'aviation'
    },
    LOW_AVIATION: {
        id: 'low_aviation',
        min: 100,               // 100 m
        max: 1_000,
        label: 'Low Aviation / Helicopter',
        imageryLayer: 'high_res_sat',    // Higher resolution imagery
        dataSources: ['aircraft', 'helicopters', 'broadcast_towers'],
        uiMode: 'aviation'
    },
    GROUND: {
        id: 'ground',
        min: 0,
        max: 100,               // 0–100 m
        label: 'Ground Level',
        imageryLayer: 'photorealistic_3d', // Google 3D Tiles
        dataSources: ['traffic_cameras', 'cctv', 'osm_cameras', '511'],
        uiMode: 'ground'
    }
};
```

### Layer Switching Engine

```javascript
class GridlandLayerEngine {
    constructor(viewer) {
        this.viewer = viewer;
        this.currentZone = null;
        this.activeSources = new Map();
        this.imageryLayers = new Map();

        this._setupImageryLayers();
        this._startAltitudeWatch();
    }

    _startAltitudeWatch() {
        this.viewer.scene.preRender.addEventListener(() => {
            const height = this.viewer.camera.positionCartographic.height;
            const zone = this._getZone(height);
            if (zone?.id !== this.currentZone?.id) {
                this._transition(this.currentZone, zone);
                this.currentZone = zone;
            }
        });
    }

    _getZone(altitude) {
        return Object.values(ALTITUDE_ZONES)
            .find(z => altitude >= z.min && altitude < z.max);
    }

    _transition(from, to) {
        if (!to) return;
        console.log(`Altitude transition: ${from?.label} → ${to.label}`);

        // Swap imagery layer
        this._setImageryLayer(to.imageryLayer);

        // Deactivate old data sources
        if (from) {
            const removing = from.dataSources.filter(
                s => !to.dataSources.includes(s)
            );
            removing.forEach(s => this._deactivateSource(s));
        }

        // Activate new data sources
        const adding = to.dataSources.filter(
            s => !from?.dataSources.includes(s)
        );
        adding.forEach(s => this._activateSource(s));

        // Update UI mode
        document.body.setAttribute('data-ui-mode', to.uiMode);

        // Dispatch event for external listeners
        window.dispatchEvent(new CustomEvent('gridland:zone-change', {
            detail: { from: from?.id, to: to.id, label: to.label }
        }));
    }

    _activateSource(sourceId) {
        const source = DATA_SOURCES[sourceId];
        if (!source || this.activeSources.has(sourceId)) return;

        const interval = setInterval(
            () => source.update(this.viewer),
            source.updateIntervalMs
        );
        source.update(this.viewer); // Immediate first fetch
        this.activeSources.set(sourceId, interval);
    }

    _deactivateSource(sourceId) {
        const interval = this.activeSources.get(sourceId);
        if (interval) {
            clearInterval(interval);
            this.activeSources.delete(sourceId);
        }
        DATA_SOURCES[sourceId]?.cleanup?.(this.viewer);
    }

    _setImageryLayer(layerId) {
        // Show/hide pre-loaded imagery layers based on altitude zone
        for (const [id, layer] of this.imageryLayers) {
            layer.show = (id === layerId);
        }
    }
}
```

### Data Source Registry

```javascript
const DATA_SOURCES = {

    iss: {
        updateIntervalMs: 5000,
        async update(viewer) {
            const pos = await fetch('/api/iss/position').then(r => r.json());
            const entity = viewer.entities.getById('iss') ||
                viewer.entities.add({ id: 'iss' });
            entity.position = Cesium.Cartesian3.fromDegrees(
                pos.lon, pos.lat, 408000
            );
            entity.description = `
                <b>International Space Station</b><br/>
                <video src="${NASA_TV_HLS}" controls width="320" autoplay muted></video>
            `;
        },
        cleanup(viewer) { /* leave entity, just stop updating */ }
    },

    starlink: {
        updateIntervalMs: 30000,
        _entities: [],
        async update(viewer) {
            const tles = await fetch('/api/tles/starlink').then(r => r.text());
            // Propagate and render (see Section 8)
            this._entities = await loadConstellation(viewer, tles);
        },
        cleanup(viewer) {
            this._entities.forEach(e => viewer.entities.remove(e));
            this._entities = [];
        }
    },

    aircraft: {
        updateIntervalMs: 10000,
        _source: null,
        async update(viewer) {
            if (!this._source) {
                this._source = new Cesium.CustomDataSource('aircraft');
                viewer.dataSources.add(this._source);
            }
            await updateAircraftLayer(viewer, this._source);
        },
        cleanup(viewer) {
            if (this._source) viewer.dataSources.remove(this._source);
            this._source = null;
        }
    },

    traffic_cameras: {
        updateIntervalMs: 300000,  // 5 min (camera positions don't move)
        async update(viewer) {
            const cameras = await fetch('/api/cameras/511').then(r => r.json());
            cameras.forEach(cam => {
                viewer.entities.getOrCreateEntity(`cam_${cam.id}`, {
                    position: Cesium.Cartesian3.fromDegrees(
                        cam.lon, cam.lat, 5
                    ),
                    billboard: {
                        image: '/icons/traffic-camera.png',
                        width: 20, height: 20
                    },
                    description: cam.video_url
                        ? `<video src="${cam.video_url}" controls width="320"></video>`
                        : cam.name
                });
            });
        },
        cleanup(viewer) { /* cameras persist across altitude changes */ }
    }
};
```

### Visual Transitions — Atmosphere, Stars, Lighting

```javascript
function setupAtmosphericTransitions(viewer) {
    viewer.scene.skyBox = new Cesium.SkyBox({
        sources: {
            positiveX: '/skybox/px.jpg', negativeX: '/skybox/nx.jpg',
            positiveY: '/skybox/py.jpg', negativeY: '/skybox/ny.jpg',
            positiveZ: '/skybox/pz.jpg', negativeZ: '/skybox/nz.jpg',
        }
    });
    viewer.scene.sun   = new Cesium.Sun();
    viewer.scene.moon  = new Cesium.Moon();
    viewer.scene.skyAtmosphere = new Cesium.SkyAtmosphere();

    viewer.scene.preRender.addEventListener(() => {
        const h = viewer.camera.positionCartographic.height;

        // Stars: visible from space, fade out as you descend into atmosphere
        viewer.scene.skyBox.show = h > 200_000;

        // Atmosphere glow: peak around 100km, fade above and below
        const atmoAlpha = h > 10_000_000
            ? 0
            : h > 500_000
                ? Math.max(0, 1 - (h - 500_000) / 9_500_000)
                : h > 10_000
                    ? 1.0
                    : Math.max(0, h / 10_000);

        viewer.scene.skyAtmosphere.show  = atmoAlpha > 0;

        // Ground fog / haze at low altitude
        viewer.scene.fog.enabled   = h < 5_000;
        viewer.scene.fog.density   = h < 1_000 ? 0.0002 : 0.00005;
        viewer.scene.fog.minimumBrightness = 0.1;
    });
}
```

---

## 13. The Full Zoom Stack — Integration Pattern

This is the complete layer mapping from deep space to street level, fully integrated.

```
ALTITUDE            LAYER                   LIVE FEEDS                          APIs
─────────────────────────────────────────────────────────────────────────────────────
1.5M km         L1 Lagrange            DSCOVR/EPIC full Earth disk          NASA EPIC
                                        (~2h delay, free)
─────────────────────────────────────────────────────────────────────────────────────
35,786 km       Geostationary Orbit    GOES-16/18 full disk (10min)         AWS S3 noaa-goes16/18
                                        Himawari-9 (10min, Asia)             AWS S3 noaa-himawari8
                                        Meteosat (EU)                        EUMETSAT
─────────────────────────────────────────────────────────────────────────────────────
20,200 km       MEO / GPS              Position only                        Celestrak TLE
─────────────────────────────────────────────────────────────────────────────────────
340–570 km      Starlink Constellation ~9,000 satellites, position           Celestrak, satellite.js
─────────────────────────────────────────────────────────────────────────────────────
408 km          ISS                    NASA External HD Camera (live)        Open Notify (position)
                                        NASA TV HLS (ntv1.akamaized.net)     N2YO (precision)
─────────────────────────────────────────────────────────────────────────────────────
~500–600 km     Earth Observation Sats  Planet Labs, Sentinel (imagery)      Copernicus API (free)
─────────────────────────────────────────────────────────────────────────────────────
12–50 km        Stratosphere            Weather balloon sounding data         NOAA IGRA
                                        HAPS (experimental, limited)
─────────────────────────────────────────────────────────────────────────────────────
10–12 km        Commercial Cruise       ADS-B position + callsign            OpenSky Network
─────────────────────────────────────────────────────────────────────────────────────
3–10 km         Aviation               ADS-B all aircraft                   OpenSky, ADSB.fi
─────────────────────────────────────────────────────────────────────────────────────
1–3 km          Low Aviation/Heli       ADS-B + news chopper live video      OpenSky + Shodan/6
─────────────────────────────────────────────────────────────────────────────────────
300–600 m       Broadcast Towers        FCC ASR coordinates                  FCC ASR API
                                        Some tower cam feeds                  Shodan (GRIDLAND-6)
─────────────────────────────────────────────────────────────────────────────────────
30–100 m        Rooftop / Elevated      Construction cams, building cams     Shodan, Windy
─────────────────────────────────────────────────────────────────────────────────────
0–30 m          Ground Level            Traffic cameras (511 APIs)           511 PA/NY/NJ/CA
                                        CCTV/DVR (Shodan)                    Shodan, Censys
                                        Community-mapped cameras (OSM)        Overpass API
                                        Mapillary visual detections           Mapillary v4
                                        Municipal open data                  NYC/PHL open data
═════════════════════════════════════════════════════════════════════════════════════
```

### One-Gesture Experience

When a user zooms out from street level in CesiumJS:

1. At **30m** → street cameras, traffic cams, OSM-mapped surveillance cameras
2. At **300m** → broadcast towers appear (FCC ASR), building roof cams
3. At **1,000m** → helicopter layer activates, news choppers appear with live video links
4. At **3,000m** → commercial aviation populates, ADS-B aircraft appear
5. At **12,000m** → aviation layer stays, atmosphere becomes visible
6. At **100,000m** → atmosphere glows fully, ground detail fades, orbital layer begins
7. At **408,000m** → ISS marker appears with its live feed attached, orbital path traces
8. At **550,000m** → Starlink constellation renders as a shell of points
9. At **35,786,000m** → GOES-16/18 appear at fixed GEO positions, their imagery tiles the globe
10. At **1,500,000,000m** → DSCOVR appears at L1, EPIC full-disk Earth replaces the globe

Every transition is driven by a single altitude value from `viewer.camera.positionCartographic.height`.

---

*GRIDLAND-7 — The Altitude Stack — Compiled 2026-05-17*
*All APIs, feeds, and sources referenced herein are publicly accessible.*
*Orbital TLE data: Celestrak / Space-Track. Aircraft: OpenSky Network / ADSB.fi.*
*Satellite imagery: NASA GIBS, NOAA GOES on AWS. ISS video: NASA TV.*
