# GRIDLAND-5
## Camera & Streaming Infrastructure Discovery — Research Reference

> **Scope:** Public-facing, internet-indexed cameras and streaming infrastructure only.
> Covers traffic cameras, exposed CCTV/DVR/NVR, broadcast/news infrastructure, and municipal feeds.
> No private devices (smart doorbells, residential IoT). No physical user location tracking.
> All data sources are publicly accessible APIs or indexed public data.

---

## Table of Contents

1. [Google Dorking Fundamentals](#1-google-dorking-fundamentals)
2. [Shodan Dork Reference](#2-shodan-dork-reference)
3. [Device Category Breakdown](#3-device-category-breakdown)
4. [Shodan API — Deep Dive](#4-shodan-api--deep-dive)
5. [Censys API v2](#5-censys-api-v2)
6. [511 Traffic Camera APIs](#6-511-traffic-camera-apis)
7. [ZoomEye API](#7-zoomeye-api)
8. [GreyNoise — Noise Filtering](#8-greynoise--noise-filtering)
9. [ARIN RDAP — ASN/Org Classification](#9-arin-rdap--asnorg-classification)
10. [Unified Query Architecture](#10-unified-query-architecture)
11. [Compliance & Operational Guardrails](#11-compliance--operational-guardrails)
12. [Data Source Comparison Matrix](#12-data-source-comparison-matrix)

---

## 1. Google Dorking Fundamentals

### Core Operators

| Operator | Function | Example |
|---|---|---|
| `site:` | Limit to domain | `site:*.state.pa.us` |
| `filetype:` | File type filter | `filetype:m3u8` |
| `intitle:` | Match page title | `intitle:"Network Camera"` |
| `inurl:` | Match URL path | `inurl:"/axis-cgi/"` |
| `intext:` | Match page body | `intext:"rtsp://"` |
| `"..."` | Exact phrase | `"index of" "stream"` |
| `-` | Exclude term | `site:example.com -www` |
| `OR` | Boolean OR | `intitle:"DVR" OR intitle:"NVR"` |

### Streaming Endpoint Dorks

**HLS / m3u8**
```
inurl:.m3u8
inurl:playlist.m3u8
intitle:"index of" ".m3u8"
inurl:"/hls/" intitle:"index of"
```

**RTSP References**
```
intext:"rtsp://" filetype:html
inurl:"/live/stream"
```

**Exposed Streaming Server Admin Panels**
```
intitle:"Wowza Streaming Engine"
intitle:"Icecast Streaming Media Server"
intitle:"nginx-rtmp" inurl:stat
intitle:"Nimble Streamer"
```

**Traffic Camera Systems**
```
site:*.state.pa.us inurl:camera
site:*.state.nj.us inurl:camera
intitle:"Traffic Camera" inurl:stream
inurl:"/cwwp2/"
intitle:"traffic" inurl:stream
```

**News / Broadcast Infrastructure**
```
intitle:"live helicopter" site:*.com
inurl:"/helicopter/" inurl:stream
inurl:"/chopper/" inurl:live
intitle:"SKY" OR intitle:"Chopper" inurl:stream site:*.com
intitle:"LiveU" inurl:"/status"
intitle:"Haivision" inurl:login
```

**Broadcast Archives**
```
site:archive.org "broadcast" "news" filetype:mp4
intitle:"television archive" site:*.edu
inurl:"/tvnews/" OR inurl:"/broadcast-archive/"
```

---

## 2. Shodan Dork Reference

### Geo Filters

```
geo:39.9526,-75.1652,50        # lat, lon, radius in km
city:"Philadelphia"
region:"Pennsylvania"
country:US
postal:"19103"
asn:AS7922                     # specific ASN (e.g. Comcast)
org:"City of Philadelphia"
org:"PennDOT"
net:203.0.113.0/24             # CIDR block
```

> **Note:** Geo filters require Freelancer tier or above.

### Useful Global Filters

```
has_screenshot:true            # Shodan has captured a screenshot
port:554                       # RTSP default port
port:1935                      # RTMP ingest
port:8088                      # Wowza management default
port:8000                      # Icecast/Shoutcast default
product:"Axis network camera"
```

### IP CCTV / DVR Dorks

**Hikvision**
```
http.title:"Hikvision" has_screenshot:true
"Server: webserver" port:80 has_screenshot:true
http.html:"DNVRS-Webs"
```

**Dahua**
```
http.title:"Login - Dahua"
"Server: Dahua" has_screenshot:true
http.html:"DahuaHttp"
```

**Axis**
```
"WWW-Authenticate: Digest realm=\"AXIS" has_screenshot:true
http.title:"AXIS" product:"Axis network camera"
```

**Amcrest / Reolink / Foscam**
```
http.title:"Amcrest" has_screenshot:true
http.title:"Reolink" has_screenshot:true
http.title:"Foscam" has_screenshot:true
http.html:"webclient" http.title:"IPCamera"
```

**DVR / NVR Panels**
```
http.title:"DVR Web Client" has_screenshot:true
http.title:"XVR Login" has_screenshot:true
http.title:"NVR" has_screenshot:true
"Cross Web Server" port:81
http.title:"H.264 DVR"
```

**Generic**
```
http.title:"Network Camera" has_screenshot:true
http.html:"webclient" http.title:"IPCamera"
```

### Traffic & Municipal Camera Dorks

```
http.title:"traffic" has_screenshot:true country:US
org:"PENNDOT" has_screenshot:true
org:"NJDOT" has_screenshot:true
http.title:"Traffic Management" country:US
org:"DOT" http.title:"camera" has_screenshot:true
```

### Broadcast Infrastructure Dorks

**Wowza**
```
http.title:"Wowza Streaming Engine Manager"
http.title:"Wowza" has_screenshot:true
port:8088 http.title:"Wowza"
port:1935
"Wowza Streaming Engine" country:US
```

**Haivision (Makito encoder — news trucks, stadiums)**
```
http.title:"Haivision"
http.product:"Haivision"
"Server: Makito" has_screenshot:true
```

**LiveU (dominant bonded cellular ENG encoder)**
```
http.title:"LiveU" has_screenshot:true
"LiveU" port:443 has_screenshot:true
```

**Teradek (helicopters, sports, ENG)**
```
http.title:"Teradek" has_screenshot:true
http.html:"Teradek" port:80
```

**Dejero (bonded cellular, Canadian/US broadcast)**
```
http.title:"Dejero"
"Dejero" has_screenshot:true
```

**AWS Elemental / Elemental Live (large station encoders)**
```
http.title:"Elemental Live"
http.title:"AWS Elemental"
```

**Nimble Streamer**
```
http.title:"Nimble Streamer"
http.title:"WMSPanel"
```

**Icecast / Shoutcast**
```
http.title:"Icecast Streaming Media Server"
port:8000 "icy-name" country:US
```

### Geo + Device Type Compound Examples

```
# Hikvision cameras in Philadelphia metro (50km radius)
http.title:"Hikvision" has_screenshot:true geo:39.9526,-75.1652,50

# DVR panels in Pennsylvania
http.title:"DVR Web Client" region:"Pennsylvania" has_screenshot:true

# Any RTSP-exposed device in 25km radius
port:554 geo:39.9526,-75.1652,25

# Wowza servers on US broadcast station ASNs
http.title:"Wowza" org:"NBC" OR org:"CBS" OR org:"ABC" country:US

# Teradek encoders on Philadelphia station infrastructure
"Teradek" asn:<station_ASN>
```

---

## 3. Device Category Breakdown

### Technical Signature Comparison

| Category | Protocol | Typical Ports | Indexable? | Intentionally Public? |
|---|---|---|---|---|
| News van / SNG uplink | Bonded cellular / satellite | N/A | Rarely | Yes (but private network) |
| Helicopter / ENG feed | Teradek / LiveU | 443, 80 | Occasionally | Yes (but private) |
| Broadcast archive (e.g. Vanderbilt) | HTTP / HLS | 80, 443 | Yes | Yes |
| IP CCTV camera | RTSP / HTTP MJPEG | 554, 80, 8080 | Often (misconfigured) | Usually not |
| DVR / NVR | HTTP / RTSP | 80, 81, 554, 8554 | Often (misconfigured) | Usually not |
| Traffic camera | HTTP / MPEG-DASH / HLS | 80, 443 | Often | Sometimes intentional |
| PTZ camera (public venues) | HTTP / RTSP | 80, 554 | Yes | Often intentional |
| Wowza / streaming server | RTMP / HLS / HTTP | 1935, 8088, 80 | Often | Varies |
| Smart doorbell | Cloud-proxied | N/A | No | No — out of scope |

### News / Broadcast ENG — Notes

- **SNG (Satellite News Gathering)** and bonded cellular units (LiveU, Dejero, Teradek) transmit over private networks back to master control — the ingest endpoint is rarely internet-exposed directly
- **Receiving/ingest servers** at broadcast stations are more commonly findable (Wowza, Haivision, Elemental on station ASNs)
- Local stations periodically publicize chopper stream URLs; these follow predictable patterns per market and can be found via Google + station ASN lookups on Shodan
- Common chopper stream URL patterns:
  ```
  https://<station>.com/live/chopper<N>/playlist.m3u8
  https://stream.<station-domain>/sky<N>/index.m3u8
  rtmp://<ingest-ip>/live/helicopter
  ```

### Common Stream URL Patterns (511 / Traffic Systems)

```
https://video.dot.state.XX.us/cameras/{id}/stream.m3u8
https://cameras.XXX.gov/stream/{camera_id}/playlist.m3u8
https://511XX.org/media/cameras/{id}.jpg        # static snapshot
rtsp://traffic.XXX.gov:554/camera/{id}          # rarer in modern systems
```

---

## 4. Shodan API — Deep Dive

### Tiers & Credits

| Tier | Cost | Credits | Key Features |
|---|---|---|---|
| Free | $0 | 1 credit | No filters, 100 results max |
| Freelancer | $59/mo | 1M query credits | Filters, exports, geo |
| Small Business | $299/mo | 10M credits | Streaming API, historical data |
| Enterprise | Custom | Unlimited | Bulk exports, dedicated |

Credits are consumed per search query, not per result.

### Core Endpoints

```
GET  https://api.shodan.io/shodan/host/search      # main search
GET  https://api.shodan.io/shodan/host/{ip}         # single IP full detail
GET  https://api.shodan.io/shodan/host/count        # result count only (cheap)
GET  https://api.shodan.io/shodan/query/tags        # tag browser
POST https://stream.shodan.io/shodan/banners        # real-time stream (Small Biz+)
```

### Search — Full Parameter Reference

```python
import shodan

api = shodan.Shodan("YOUR_KEY")

results = api.search(
    query='http.title:"Hikvision" has_screenshot:true country:US',
    page=1,           # 100 results per page
    limit=100,
    offset=0,
    facets=[          # aggregate counts by field
        'country',
        'org',
        'port',
        'city:20',    # top 20 cities
    ],
    minify=False      # False = full banner data
)

print(f"Total results: {results['total']}")

for match in results['matches']:
    print({
        'ip':        match['ip_str'],
        'port':      match['port'],
        'org':       match.get('org'),
        'city':      match['location']['city'],
        'country':   match['location']['country_code'],
        'lat':       match['location']['latitude'],
        'lon':       match['location']['longitude'],
        'timestamp': match['timestamp'],
        'screenshot': match.get('opts', {}).get('screenshot'),  # base64 PNG
        'hostnames': match.get('hostnames', []),
        'domains':   match.get('domains', []),
        'transport': match.get('transport'),   # tcp / udp
        'banner':    match.get('data'),
        'product':   match.get('product'),
        'version':   match.get('version'),
        'cpe':       match.get('cpe', [])
    })
```

### Host Lookup — Single IP Full Detail

```python
host = api.host('203.0.113.42')

# Returns all open ports, all service banners, all historical snapshots
for item in host['data']:
    print(item['port'], item['transport'], item.get('product'), item.get('version'))

# Location
print(host['country_name'], host['city'], host['latitude'], host['longitude'])

# Organization
print(host['org'], host['isp'], host['asn'])
```

### Facets — Geographic Density / Dashboard Data

```python
# Returns aggregate counts, not individual results — very cheap on credits
result = api.search(
    'http.title:"Network Camera" has_screenshot:true country:US',
    facets=['city:20', 'org:10', 'port:5']
)

# Use for heatmaps, charts
for facet in result['facets']['city']:
    print(facet['value'], facet['count'])
# → Philadelphia 847, New York 2341, Los Angeles 1876 ...

for facet in result['facets']['port']:
    print(facet['value'], facet['count'])
```

### Count-Only Query (Minimal Credit Cost)

```python
# Use this to preview result size before spending credits on full search
count = api.count('http.title:"Hikvision" geo:39.9526,-75.1652,50')
print(count['total'])
```

### Streaming API — Real-Time Banner Feed

Requires Small Business tier. Receives banners as Shodan crawlers find them.

```python
import shodan

api = shodan.Shodan("YOUR_KEY")

# Stream all new banners on port 554 globally
for banner in api.stream.banners(filters={'port': 554}):
    print(banner['ip_str'], banner.get('data', '')[:100])

# Filter to a specific query (requires alert/monitor setup)
for banner in api.stream.alert(aid="YOUR_ALERT_ID"):
    print(banner)
```

### Shodan Monitor / Alerts (Pro Feature)

```python
# Create a persistent monitor — triggers webhook when new results appear
alert = api.create_alert(
    name="Camera Watch - Philadelphia",
    ip="203.0.113.0/24"    # CIDR of interest
)
print(alert['id'])

# List active alerts
for alert in api.alerts():
    print(alert['id'], alert['name'])
```

---

## 5. Censys API v2

Censys has broader TLS/certificate coverage than Shodan — better for finding streaming infrastructure by certificate CN or organization than by HTTP banner alone.

### Authentication

```python
from censys.search import CensysHosts, CensysCertificates

c = CensysHosts(
    api_id="YOUR_API_ID",
    api_secret="YOUR_API_SECRET"
)
```

### Censys Query Language (CQL) vs. Shodan

| Concept | Shodan | Censys CQL |
|---|---|---|
| Page title | `http.title:"X"` | `services.http.response.html_title: "X"` |
| Port | `port:554` | `services.port: 554` |
| Country | `country:US` | `location.country_code: US` |
| City | `city:"Philadelphia"` | `location.city: "Philadelphia"` |
| ASN | `asn:AS7922` | `autonomous_system.asn: 7922` |
| Org | `org:"Comcast"` | `autonomous_system.name: "Comcast"` |
| Certificate CN | (limited) | `services.tls.certificate.parsed.subject.common_name: "*.hikvision.com"` |
| Has screenshot | `has_screenshot:true` | (not available) |

### Hosts Search

```python
# Returns lazy iterator — handles pagination automatically
for host in c.search(
    'services.http.response.html_title: "Network Camera" and location.country_code: "US"',
    fields=[
        "ip",
        "location.city",
        "location.coordinates",
        "autonomous_system.name",
        "autonomous_system.asn",
        "services.port",
        "services.transport_protocol",
        "services.http.response.html_title",
        "services.tls.certificate.parsed.subject.common_name"
    ]
):
    print(host)
```

### Certificate Search — Broadcast Infrastructure Discovery

Censys's killer feature — find infrastructure by who issued the TLS cert.

```python
c_certs = CensysCertificates()

# Find certs issued to known broadcast/streaming companies
for cert in c_certs.search(
    'parsed.subject.organization: "Haivision" '
    'OR parsed.subject.organization: "Wowza Media Systems" '
    'OR parsed.subject.organization: "Teradek"'
):
    print(
        cert['parsed.subject.common_name'],
        cert.get('parsed.names'),
        cert.get('parsed.subject.organization')
    )
```

### Rate Limits

| Tier | Queries/Month | Results/Query |
|---|---|---|
| Free | 250 | 100 |
| Researcher (apply) | Expanded | Expanded |
| Paid | Contact sales | Contact sales |

> **Tip:** Apply for researcher access at censys.io — free expanded access is available for academic/security research with a brief application.

---

## 6. 511 Traffic Camera APIs

The cleanest data source — official government APIs, publicly documented, zero legal ambiguity. These are the recommended foundation layer.

### 511PA — Pennsylvania

```python
import requests

r = requests.get(
    "https://www.511pa.com/api/v1/cameras",
    params={"format": "json"}
)
cameras = r.json()

for cam in cameras:
    print({
        'id':      cam['ID'],
        'name':    cam['RoadwayName'],
        'lat':     cam['Latitude'],
        'lon':     cam['Longitude'],
        'url':     cam['VideoUrl'],     # direct HLS stream URL
        'image':   cam['ImageUrl'],     # static JPEG snapshot
        'status':  cam['Status']
    })
```

### 511NY — New York

Requires free API key registration at 511ny.org.

```python
r = requests.get(
    "https://511ny.org/api/getitems/cameras",
    params={
        "key":    "YOUR_511NY_KEY",
        "format": "json"
    }
)
cameras = r.json()
```

### 511NJ — New Jersey

NJ uses RITIS/INRIX-based vendor infrastructure. Camera data is available via their GeoJSON map feed:

```python
r = requests.get("https://www.511nj.org/map/cameras.geojson")
geojson = r.json()

for feature in geojson['features']:
    props = feature['properties']
    coords = feature['geometry']['coordinates']
    print({
        'id':    props.get('id'),
        'name':  props.get('name'),
        'url':   props.get('streamUrl'),
        'lon':   coords[0],
        'lat':   coords[1]
    })
```

### 511 California / Statewide

```python
r = requests.get(
    "https://api.511.org/traffic/cameras",
    params={
        "api_key": "YOUR_511_KEY",
        "format":  "JSON",
        "agency":  "Caltrans"    # or specific regional agency
    }
)
```

### Other State 511 Systems

| State | Base URL | Auth Required |
|---|---|---|
| Pennsylvania | 511pa.com/api/v1 | No |
| New York | 511ny.org/api | Yes (free key) |
| New Jersey | 511nj.org | No (GeoJSON) |
| California | api.511.org/traffic | Yes (free key) |
| Virginia | 511virginia.org | Yes (free key) |
| Maryland | chart.maryland.gov | No |
| Florida | fl511.com | Yes (free key) |
| Texas | drivetexas.org | No |

### Vendor Platforms

Most 511 implementations run on one of these vendor stacks:
- **RITIS** (Regional Integrated Transportation Information System) — university-hosted, covers Mid-Atlantic
- **ATMS Now** — common in Southeast/Midwest
- **KOVA** — common in Northeast
- **Iteris** — Western states

Camera URL patterns are consistent within each vendor:
```
# RITIS-based
https://data.ritis.org/cameras/{camera_id}/feed

# ATMS Now
https://atms.{state}.gov/cameras/{id}/stream.m3u8

# Generic DOT patterns
https://video.dot.state.XX.us/cameras/{id}/stream.m3u8
https://511XX.org/media/cameras/{id}.jpg
rtsp://traffic.XXX.gov:554/camera/{id}
```

---

## 7. ZoomEye API

Chinese-hosted (Knownsec). Covers Asian and Eastern European infrastructure that Shodan frequently misses. Useful as a supplemental source for global research.

### Authentication & SDK

```python
from zoomeye.sdk import ZoomEye

zm = ZoomEye(api_key="YOUR_KEY")
```

### Query Syntax

ZoomEye syntax is similar to Shodan but uses `app:` instead of `product:` and `+` for AND.

```python
# Host search
result = zm.dork_search(
    'app:"Hikvision" +country:"United States"',
    page=1,
    resource="host"     # "host" or "web"
)

for match in result['matches']:
    print({
        'ip':      match['ip'],
        'port':    match['portinfo']['port'],
        'city':    match['geoinfo']['city']['names']['en'],
        'country': match['geoinfo']['country']['names']['en'],
        'org':     match['geoinfo']['organization']
    })
```

### Useful ZoomEye Dorks

```
app:"Hikvision IP Camera" +country:"United States"
app:"Dahua Network Video Recorder" +country:"United States"
app:"Axis Network Camera"
app:"Wowza Streaming Engine"
app:"Icecast" +country:"United States"
service:rtsp +country:"United States"
```

### Rate Limits

| Tier | Queries/Day | Results/Query |
|---|---|---|
| Free | 10 | 20 |
| VIP (~$35/mo) | 100 | 100 |
| Pro | Custom | Custom |

---

## 8. GreyNoise — Noise Filtering

GreyNoise classifies IP addresses by behavior — scanners, crawlers, benign services, and malicious actors. Essential for removing false positives from Shodan/Censys results (e.g., Shodan's own crawlers appearing in results).

### Single IP Lookup

```python
import greynoise

gn = greynoise.GreyNoise(api_key="YOUR_KEY")

result = gn.ip("203.0.113.42")
print({
    'seen':           result['seen'],           # True if GreyNoise has observed it
    'classification': result['classification'], # "benign", "malicious", "unknown"
    'name':           result.get('name'),        # e.g. "Shodan.io", "Censys"
    'bot':            result.get('bot'),         # True if known bot/crawler
    'tags':           result.get('tags', []),    # e.g. ["RTSP Scanner", "Mirai"]
    'last_seen':      result.get('last_seen')
})
```

### Batch Filter for Shodan Results

```python
def greynoise_filter(shodan_matches, gn_client, drop_scanners=True):
    clean = []
    for match in shodan_matches:
        ip = match['ip_str']
        try:
            gn_data = gn_client.ip(ip)
            if drop_scanners and gn_data.get('seen'):
                # Drop known crawlers/scanners (Shodan, Censys, etc.)
                if gn_data.get('name') in ('Shodan.io', 'Censys', 'ZoomEye'):
                    continue
                # Drop Mirai and known exploit scanners
                if 'Mirai' in gn_data.get('tags', []):
                    continue
            match['_greynoise'] = gn_data
            clean.append(match)
        except greynoise.exceptions.RequestFailure:
            # IP not in GreyNoise — include it
            clean.append(match)
    return clean
```

### GNQL — GreyNoise Query Language

```python
# Find all IPs actively scanning for RTSP in the last 24 hours
results = gn.query('tags:RTSP last_seen:1d')

# Malicious actors scanning for Hikvision
results = gn.query('tags:"Hikvision" classification:malicious')

# All benign crawlers (to build an exclusion list)
results = gn.query('classification:benign')
```

### Rate Limits

| Tier | Cost | IP Lookups/Day |
|---|---|---|
| Community (free) | $0 | 50 |
| Researcher | Apply | Expanded |
| Pro | $299/mo | Unlimited |

---

## 9. ARIN RDAP — ASN/Org Classification

ARIN's RDAP API maps IP addresses to organizations and network blocks. Use this to classify whether a discovered device belongs to a municipality, broadcaster, ISP, or private business — critical for labeling results compliantly.

### Endpoints

```
https://rdap.arin.net/registry/ip/{ip}
https://rdap.arin.net/registry/autnum/{asn}
https://rdap.arin.net/registry/entity/{handle}
```

### IP to Org Lookup

```python
import requests

def classify_ip(ip):
    r = requests.get(
        f"https://rdap.arin.net/registry/ip/{ip}",
        headers={"Accept": "application/json"}
    )
    data = r.json()

    org_name = None
    for entity in data.get('entities', []):
        for role in entity.get('roles', []):
            if role in ('registrant', 'administrative'):
                vcard = entity.get('vcardArray', [])
                for field in vcard[1] if len(vcard) > 1 else []:
                    if field[0] == 'fn':
                        org_name = field[3]

    return {
        'ip':         ip,
        'network':    data.get('name'),
        'cidr':       data.get('cidr0_cidrs', [{}])[0].get('v4prefix'),
        'org':        org_name,
        'start_addr': data.get('startAddress'),
        'end_addr':   data.get('endAddress'),
        'country':    data.get('country')
    }
```

### Classification Heuristics

```python
MUNICIPAL_KEYWORDS = ['DOT', 'Department of Transportation', 'City of', 'County of',
                      'Township', 'Borough', 'Municipality', 'Port Authority']

BROADCAST_KEYWORDS = ['Broadcasting', 'Television', 'NBC', 'CBS', 'ABC', 'FOX',
                      'Radio', 'Media', 'Communications', 'WIRED', 'WPVI', 'KYW']

ISP_KEYWORDS = ['Comcast', 'Verizon', 'AT&T', 'Charter', 'Cox', 'Spectrum',
                'RCN', 'Optimum', 'Frontier']

def label_org(org_name):
    if not org_name:
        return "unknown"
    org_upper = org_name.upper()
    if any(k.upper() in org_upper for k in MUNICIPAL_KEYWORDS):
        return "municipal"
    if any(k.upper() in org_upper for k in BROADCAST_KEYWORDS):
        return "broadcast"
    if any(k.upper() in org_upper for k in ISP_KEYWORDS):
        return "isp"
    return "commercial"
```

---

## 10. Unified Query Architecture

### Device Query Registry

```python
DEVICE_QUERIES = {
    "hikvision": {
        "shodan":  'http.title:"Hikvision" has_screenshot:true',
        "censys":  'services.http.response.html_title: "Hikvision"',
        "zoomeye": 'app:"Hikvision IP Camera"',
        "label":   "Hikvision IP Camera",
        "category": "cctv"
    },
    "dahua": {
        "shodan":  'http.title:"Login - Dahua" has_screenshot:true',
        "censys":  'services.http.response.html_title: "Dahua"',
        "zoomeye": 'app:"Dahua Network Video Recorder"',
        "label":   "Dahua Camera/NVR",
        "category": "cctv"
    },
    "axis": {
        "shodan":  'product:"Axis network camera" has_screenshot:true',
        "censys":  'services.http.response.html_title: "AXIS"',
        "zoomeye": 'app:"Axis Network Camera"',
        "label":   "Axis Network Camera",
        "category": "cctv"
    },
    "dvr_generic": {
        "shodan":  'http.title:"DVR Web Client" has_screenshot:true',
        "censys":  'services.http.response.html_title: "DVR Web Client"',
        "zoomeye": 'app:"DVR Web Client"',
        "label":   "Generic DVR",
        "category": "dvr"
    },
    "traffic": {
        "shodan":  'org:"DOT" http.title:"camera" has_screenshot:true',
        "censys":  'services.http.response.html_title: "Traffic Camera"',
        "zoomeye": 'app:"traffic camera"',
        "label":   "Traffic / Municipal Camera",
        "category": "traffic"
    },
    "wowza": {
        "shodan":  'http.title:"Wowza Streaming Engine"',
        "censys":  'services.http.response.html_title: "Wowza Streaming Engine"',
        "zoomeye": 'app:"Wowza Streaming Engine"',
        "label":   "Wowza Streaming Server",
        "category": "broadcast"
    },
    "haivision": {
        "shodan":  '"Server: Makito" has_screenshot:true',
        "censys":  'autonomous_system.name: "Haivision"',
        "zoomeye": 'app:"Haivision"',
        "label":   "Haivision Encoder",
        "category": "broadcast"
    },
    "liveu": {
        "shodan":  'http.title:"LiveU" has_screenshot:true',
        "censys":  'services.http.response.html_title: "LiveU"',
        "zoomeye": 'app:"LiveU"',
        "label":   "LiveU ENG Encoder",
        "category": "broadcast"
    },
    "teradek": {
        "shodan":  'http.title:"Teradek" has_screenshot:true',
        "censys":  'services.http.response.html_title: "Teradek"',
        "zoomeye": 'app:"Teradek"',
        "label":   "Teradek Encoder",
        "category": "broadcast"
    }
}
```

### Core Discovery Class

```python
import shodan
import greynoise
import requests
from censys.search import CensysHosts
from zoomeye.sdk import ZoomEye

CENSYS_FIELDS = [
    "ip", "location.city", "location.coordinates",
    "autonomous_system.name", "autonomous_system.asn",
    "services.port", "services.transport_protocol",
    "services.http.response.html_title",
    "services.tls.certificate.parsed.subject.common_name"
]

class GridlandDiscovery:
    def __init__(self, shodan_key, censys_id, censys_secret,
                 greynoise_key, zoomeye_key=None):
        self.shodan  = shodan.Shodan(shodan_key)
        self.censys  = CensysHosts(censys_id, censys_secret)
        self.gn      = greynoise.GreyNoise(api_key=greynoise_key)
        self.zoomeye = ZoomEye(api_key=zoomeye_key) if zoomeye_key else None

    def search_geo(self, lat, lon, radius_km, device_types=None):
        if device_types is None:
            device_types = list(DEVICE_QUERIES.keys())

        results = []

        for dtype in device_types:
            q = DEVICE_QUERIES[dtype]

            # --- Shodan ---
            try:
                raw = self.shodan.search(
                    f'{q["shodan"]} geo:{lat},{lon},{radius_km}'
                )
                for m in raw['matches']:
                    results.append(self._normalize_shodan(m, dtype))
            except shodan.APIError as e:
                print(f"Shodan error ({dtype}): {e}")

            # --- Censys (filter by city post-hoc; no native geo) ---
            try:
                for host in self.censys.search(q["censys"], fields=CENSYS_FIELDS):
                    results.append(self._normalize_censys(host, dtype))
            except Exception as e:
                print(f"Censys error ({dtype}): {e}")

        # Deduplicate by IP
        seen = set()
        unique = []
        for r in results:
            if r['ip'] not in seen:
                seen.add(r['ip'])
                unique.append(r)

        # GreyNoise filter pass
        return self._greynoise_filter(unique)

    def _normalize_shodan(self, match, dtype):
        return {
            'ip':        match['ip_str'],
            'port':      match['port'],
            'org':       match.get('org'),
            'city':      match['location'].get('city'),
            'country':   match['location'].get('country_code'),
            'lat':       match['location'].get('latitude'),
            'lon':       match['location'].get('longitude'),
            'timestamp': match.get('timestamp'),
            'screenshot': match.get('opts', {}).get('screenshot'),
            'hostnames': match.get('hostnames', []),
            'label':     DEVICE_QUERIES[dtype]['label'],
            'category':  DEVICE_QUERIES[dtype]['category'],
            'source':    'shodan'
        }

    def _normalize_censys(self, host, dtype):
        coords = host.get('location.coordinates', {})
        return {
            'ip':        host.get('ip'),
            'port':      None,
            'org':       host.get('autonomous_system.name'),
            'city':      host.get('location.city'),
            'country':   None,
            'lat':       coords.get('latitude'),
            'lon':       coords.get('longitude'),
            'timestamp': None,
            'screenshot': None,
            'hostnames': [],
            'label':     DEVICE_QUERIES[dtype]['label'],
            'category':  DEVICE_QUERIES[dtype]['category'],
            'source':    'censys'
        }

    def _greynoise_filter(self, results, drop_crawlers=True):
        KNOWN_CRAWLERS = {'Shodan.io', 'Censys', 'ZoomEye', 'BinaryEdge'}
        clean = []
        for r in results:
            try:
                gn = self.gn.ip(r['ip'])
                if drop_crawlers and gn.get('name') in KNOWN_CRAWLERS:
                    continue
                r['_greynoise'] = {
                    'classification': gn.get('classification'),
                    'tags': gn.get('tags', []),
                    'bot':  gn.get('bot')
                }
            except Exception:
                pass
            clean.append(r)
        return clean
```

### 511 Integration Layer

```python
FEED_511 = {
    'PA': {
        'url':    'https://www.511pa.com/api/v1/cameras',
        'params': {'format': 'json'},
        'map':    lambda c: {
            'id':    c['ID'],
            'name':  c['RoadwayName'],
            'lat':   c['Latitude'],
            'lon':   c['Longitude'],
            'video': c['VideoUrl'],
            'image': c['ImageUrl'],
            'state': 'PA',
            'source': '511'
        }
    },
    'NY': {
        'url':    'https://511ny.org/api/getitems/cameras',
        'params': {'key': 'YOUR_511NY_KEY', 'format': 'json'},
        'map':    lambda c: {
            'id':    c.get('ID'),
            'name':  c.get('Name'),
            'lat':   c.get('Latitude'),
            'lon':   c.get('Longitude'),
            'video': c.get('VideoUrl'),
            'image': c.get('ImageUrl'),
            'state': 'NY',
            'source': '511'
        }
    }
    # Add additional states following same pattern
}

def fetch_511_cameras(states=None):
    if states is None:
        states = list(FEED_511.keys())
    cameras = []
    for state in states:
        cfg = FEED_511[state]
        try:
            r = requests.get(cfg['url'], params=cfg['params'], timeout=10)
            r.raise_for_status()
            for item in r.json():
                cameras.append(cfg['map'](item))
        except Exception as e:
            print(f"511 {state} error: {e}")
    return cameras
```

---

## 11. Compliance & Operational Guardrails

### Data Handling

- **Label data age:** Shodan results can be days to months old. Always surface the `timestamp` field to users. Never imply feeds are live unless confirmed.
- **Screenshot handling:** Shodan returns base64 PNG screenshots. Strip or blur any screenshots showing interior spaces, identifiable individuals, or private property before display.
- **Residential IP detection:** Cross-reference discovered IPs against ARIN RDAP. Flag or exclude results on residential ISP IP blocks (Comcast residential, Verizon FIOS, etc.) where cameras are almost certainly private.

### What to Display vs. What to Withhold

| Data Point | Display | Rationale |
|---|---|---|
| IP address | Yes | Public, already indexed |
| GPS coordinates | Yes (coarse) | Public infrastructure |
| Stream URL | Yes (for public feeds) | Already public |
| Screenshot of public infrastructure | Yes | Publicly accessible |
| Screenshot of interior / private space | No — blur/omit | Privacy |
| Login credentials (found in banners) | No — never | Out of scope |
| Authentication bypass paths | No | Out of scope |

### API Rate Limiting Strategy

```python
import time
from functools import wraps

def rate_limit(calls_per_second=1):
    min_interval = 1.0 / calls_per_second
    last_called = [0.0]

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            elapsed = time.time() - last_called[0]
            wait = min_interval - elapsed
            if wait > 0:
                time.sleep(wait)
            result = fn(*args, **kwargs)
            last_called[0] = time.time()
            return result
        return wrapper
    return decorator

# Apply to API calls
@rate_limit(calls_per_second=0.5)   # 1 call per 2 seconds for Shodan
def shodan_search(api, query, **kwargs):
    return api.search(query, **kwargs)
```

### ToS Summary by Source

| Source | Key Restrictions |
|---|---|
| Shodan | No automated scraping beyond API; no reselling raw data without agreement |
| Censys | Attribution required for published research; no commercial resale of raw data |
| 511 APIs | Generally public domain; check individual state ToS |
| ZoomEye | No automated bulk crawling; no commercial redistribution |
| GreyNoise | Attribution required; no resale |
| ARIN RDAP | Fully public; no restrictions |

---

## 12. Data Source Comparison Matrix

| Dimension | Shodan | Censys | 511 APIs | ZoomEye | GreyNoise |
|---|---|---|---|---|---|
| Primary strength | Banner/screenshot indexing | TLS certs, broad coverage | Official traffic cameras | Asian/EU coverage | Noise classification |
| Geo filter | Native (`geo:`) | Post-hoc (city/country) | Native (lat/lon in response) | Country-level | Country-level |
| Screenshot support | Yes | No | Yes (JPEG snapshot URL) | No | No |
| Real-time feed | Small Biz+ | No | Yes (refresh interval) | No | Yes (GNQL) |
| Free tier | Very limited | 250 q/mo | Yes (most states) | 10 q/day | 50 lookups/day |
| Best for | CCTV, DVR, broadcast panels | Broadcast TLS infra | Traffic cameras (authoritative) | Supplemental global | Filtering results |
| Legal clarity | Gray (public data) | Gray (public data) | Clear (government API) | Gray (public data) | Clear (threat intel) |

### Recommended Source Priority

1. **511 State APIs** — foundation layer, authoritative, zero ambiguity
2. **Shodan** (geo + facets) — broadest camera/DVR discovery, screenshots
3. **ARIN RDAP** — classify every result by org type
4. **GreyNoise** — filter pass to remove scanners and crawlers
5. **Censys** — supplement for broadcast infrastructure via cert search
6. **ZoomEye** — optional, for global coverage gaps

---

*Document compiled from GRIDLAND-5 research session — 2026-05-17*
