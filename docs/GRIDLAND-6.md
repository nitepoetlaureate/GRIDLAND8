# GRIDLAND-6
## Camera & Streaming Infrastructure Discovery — Extended Research Reference

> **This document is a direct continuation of GRIDLAND-5.md.**
> It introduces no duplicate content. All APIs, dork techniques, device categories,
> and architectural guidance here are additive to GRIDLAND-5.
>
> New in this volume: advanced Shodan fingerprinting techniques, six additional internet
> scanners, four passive/historical discovery APIs, FCC broadcast infrastructure databases,
> OpenStreetMap community camera data, Mapillary street-level detection, municipal open data
> portals, LPR/ALPR camera networks, government environmental cameras, public stream
> aggregators, and a full architectural opinion on the 2D/3D visualization stack including
> OpenStreetMap and Google Maps 3D Tiles.

---

## Table of Contents

1. [Advanced Shodan Fingerprinting Techniques](#1-advanced-shodan-fingerprinting-techniques)
2. [Additional Internet Scanners](#2-additional-internet-scanners)
3. [Historical & Passive Discovery APIs](#3-historical--passive-discovery-apis)
4. [New Device Categories](#4-new-device-categories)
5. [FCC Database Integration](#5-fcc-database-integration)
6. [OpenStreetMap Overpass API — Community Camera Data](#6-openstreetmap-overpass-api--community-camera-data)
7. [Mapillary API v4 — Street-Level Camera Detection](#7-mapillary-api-v4--street-level-camera-detection)
8. [Municipal Open Data Portals](#8-municipal-open-data-portals)
9. [EFF Atlas of Surveillance](#9-eff-atlas-of-surveillance)
10. [Public Stream Aggregators](#10-public-stream-aggregators)
11. [Visualization Architecture — Full Opinion](#11-visualization-architecture--full-opinion)
12. [Multi-Layer Discovery Workflow](#12-multi-layer-discovery-workflow)
13. [Expanded Data Source Matrix](#13-expanded-data-source-matrix)

---

## 1. Advanced Shodan Fingerprinting Techniques

These techniques were not covered in GRIDLAND-5 and represent some of the most precise methods for identifying specific device types with minimal false positives.

---

### 1.1 Favicon Hash Fingerprinting

Every manufacturer ships their web UI with a characteristic `favicon.ico`. Because the same favicon is used across all firmware versions and device models within a product line, hashing it produces a stable, highly specific device fingerprint. This is often *more* precise than title-based queries because titles can be changed by administrators while favicons rarely are.

**How the hash is computed:**

```python
import requests
import mmh3          # pip install mmh3
import base64

def get_favicon_hash(url):
    """
    Fetch a favicon and return its Shodan-compatible MurmurHash3 value.
    url: full URL to the favicon, e.g. 'http://192.168.1.1/favicon.ico'
    """
    r = requests.get(url, timeout=5, verify=False)
    r.raise_for_status()
    # Shodan base64-encodes with newlines (encodebytes, not b64encode)
    favicon_b64 = base64.encodebytes(r.content)
    return mmh3.hash(favicon_b64)

# Example
print(get_favicon_hash("http://target-ip/favicon.ico"))
```

> **Critical detail:** Use `base64.encodebytes()` (which inserts `\n` every 76 chars),
> NOT `base64.b64encode()`. Using the wrong encoder produces a different hash that
> won't match Shodan's index.

**Known favicon hashes for camera/streaming brands:**

| Hash | Device / Brand | Notes |
|---|---|---|
| `-1290966513` | Hikvision IP camera | Most common worldwide |
| `999357577` | Dahua NVR/camera | Second most common |
| `1179309768` | Axis network camera | Enterprise/public sector |
| `-1604540064` | Amcrest camera | Prosumer |
| `-335242539` | Foscam | Consumer |
| `1871576669` | Reolink | Consumer/prosumer |
| `-1419365502` | Samsung Techwin / Hanwha | Enterprise |
| `-1115580227` | Wowza Streaming Engine | Broadcast server |
| `116323821` | Avigilon | Enterprise/gov cameras |

> **Note:** Hashes can change between major firmware revisions. If a brand releases a
> new UI, their hash changes. Always verify a hash against a known-good device before
> using it as a sole filter. Tools like https://favicon-hash.kmsec.uk/ can compute
> hashes from a URL without writing code.

**Shodan queries:**

```
# Single brand
http.favicon.hash:-1290966513

# Hikvision in Philadelphia metro
http.favicon.hash:-1290966513 geo:39.9526,-75.1652,50

# Dahua in Pennsylvania
http.favicon.hash:999357577 region:"Pennsylvania"

# Axis cameras on known broadcast ASNs
http.favicon.hash:1179309768 org:"NBC" OR org:"CBS" OR org:"ABC"

# Wowza streaming servers US-wide
http.favicon.hash:-1115580227 country:US
```

**Building a live hash library:**

```python
CAMERA_TARGETS = {
    "hikvision": "http://{ip}/favicon.ico",
    "dahua":     "http://{ip}/favicon.ico",
    "axis":      "http://{ip}/favicon.ico",
    "wowza":     "http://{ip}:8088/favicon.ico",
}

# When you discover a new camera type, compute its hash immediately
# and add it to your registry
def fingerprint_new_device(ip):
    for brand, url_template in CAMERA_TARGETS.items():
        url = url_template.format(ip=ip)
        try:
            h = get_favicon_hash(url)
            print(f"  {brand}: {h}")
        except Exception as e:
            print(f"  {brand}: failed ({e})")
```

---

### 1.2 JARM TLS Fingerprinting

JARM (developed by Salesforce) fingerprints TLS servers by sending 10 crafted Client Hello packets with varying cipher suites and extensions, then hashing the server's response patterns. The result is a 62-character string: the first 30 characters encode cipher + TLS version behavior, the last 32 are a truncated SHA-256 of the cumulative extension pattern.

JARM fingerprints are **stable across IP changes** — if a Wowza server moves to a different IP, its JARM fingerprint stays the same.

**Shodan query syntax:**

```
ssl.jarm:<62-char-fingerprint>
```

**Use case for GRIDLAND:** Identify streaming server software regardless of hostname, title, or port — useful for finding broadcast ingest servers that have been reconfigured to use non-standard ports or have custom titles.

**Computing JARM for a target:**

```bash
# Install JARM
pip install jarm

# Fingerprint a streaming server
python jarm.py stream.example.com 443
# → 2ad2ad0002ad2ad00042d42d00000069d641f34fe76acdc05c40262f8815e5
```

```python
# Then search Shodan for all servers with identical TLS behavior
# api.search('ssl.jarm:2ad2ad0002ad2ad00042d42d00000069d641f34fe76acdc05c40262f8815e5')
```

**Workflow:** Identify one confirmed Wowza/Haivision/Elemental server → compute its JARM → search Shodan for all servers with the same fingerprint globally. This surfaces hidden streaming infrastructure that doesn't expose any other identifying information.

---

### 1.3 HTTP Response Header Fingerprinting

Camera and streaming server brands leave distinctive fingerprints in their HTTP response headers. These are often more reliable than page titles (which admins customize) or favicons (which vary by firmware).

**Shodan header queries:**

```
# Hikvision — all variants
http.headers:"Server: App-webs/"
http.headers:"Server: DVRDVS-Webs"
http.headers:"Server: webserver"
http.headers:"X-Powered-By: HiEagle"

# Dahua
http.headers:"Server: Dahua"
http.headers:"X-Private-IP:"              # Dahua exposes internal IP in header

# Generic cheap camera firmware (Boa web server — embedded in millions of cameras)
http.headers:"Server: Boa/0.94.14rc21"
http.headers:"Server: Boa/0.94"
http.headers:"Server: GoAhead-Webs"      # GoAhead — another common embedded server

# Axis
http.headers:"Server: Axis"
http.headers:"WWW-Authenticate: Digest realm=\"AXIS"

# Motion MJPEG (open-source motion detection daemon)
http.headers:"Server: Motion"

# Wowza
http.headers:"Server: Wowza Streaming Engine"
http.headers:"X-Wowza-Session-Id:"

# Haivision Makito encoder
http.headers:"Server: Makito"

# Streaming generic
http.headers:"Content-Type: multipart/x-mixed-replace"   # MJPEG stream
http.headers:"Content-Type: application/x-mpegURL"       # HLS stream
```

**Header hash queries (when the full header string is long):**

```
http.headers_hash:<hash>
```

Compute the hash using `mmh3.hash()` on the normalized headers string — same approach as favicon hashing.

---

### 1.4 ONVIF Protocol Discovery

ONVIF (Open Network Video Interface Forum) is the industry-standard protocol for IP cameras. Virtually every professional and prosumer IP camera manufactured after 2010 supports ONVIF, regardless of brand. It uses WS-Discovery (Web Services Dynamic Discovery) over UDP multicast.

**Protocol details:**
- Port: 3702 (UDP)
- Multicast address: `239.255.255.250:3702`
- Message format: SOAP-over-UDP
- Device type announced: `dn:NetworkVideoTransmitter`

Shodan indexes ONVIF probe responses, which contain the device's service URL (often including the RTSP endpoint) and scope metadata.

**Shodan queries:**

```
port:3702
port:3702 "onvif"
port:3702 "NetworkVideoTransmitter"
port:3702 "NetworkVideoDisplay"
port:3702 "NetworkVideoStorage"
port:3702 country:US has_screenshot:true
port:3702 geo:39.9526,-75.1652,50

# ONVIF combined with RTSP
port:3702 port:554
```

**What the ONVIF banner reveals:**

```xml
<!-- Typical ONVIF WS-Discovery ProbeMatch response indexed by Shodan -->
<d:ProbeMatches>
  <d:ProbeMatch>
    <wsa:EndpointReference>
      <wsa:Address>urn:uuid:2419d68a-2dd2-21b2-a205-000c299a3a2f</wsa:Address>
    </wsa:EndpointReference>
    <d:Types>dn:NetworkVideoTransmitter</d:Types>
    <d:Scopes>
      onvif://www.onvif.org/location/country/china
      onvif://www.onvif.org/name/Hikvision
      onvif://www.onvif.org/hardware/DS-2CD2143G2-I
      onvif://www.onvif.org/Profile/Streaming
    </d:Scopes>
    <d:XAddrs>http://192.168.1.64/onvif/device_service</d:XAddrs>
  </d:ProbeMatch>
</d:ProbeMatches>
```

The `d:Scopes` field exposes brand, model, and sometimes location. The `d:XAddrs` field exposes the ONVIF service endpoint — which, combined with the public IP, can be used to construct the RTSP stream URL.

**Python ONVIF query:**

```python
from onvif import ONVIFCamera   # pip install onvif2

cam = ONVIFCamera('192.0.2.1', 80, 'admin', '')
media = cam.create_media_service()
profiles = media.GetProfiles()

for profile in profiles:
    stream_uri = media.GetStreamUri({
        'StreamSetup': {
            'Stream': 'RTP-Unicast',
            'Transport': {'Protocol': 'RTSP'}
        },
        'ProfileToken': profile.token
    })
    print(stream_uri.Uri)
    # → rtsp://192.0.2.1:554/Streaming/Channels/1
```

---

### 1.5 UPnP Exposure (Port 1900)

UPnP SSDP (Simple Service Discovery Protocol) runs on port 1900 UDP. Many cameras and DVRs that are behind NAT routers use UPnP to automatically open port-forwarding rules, inadvertently exposing their RTSP and HTTP streams to the internet. The UPnP description document (retrieved via HTTP from the URL in the SSDP announcement) often contains:

- Device model and manufacturer
- Internal IP address
- Open service ports including RTSP

**Shodan queries:**

```
port:1900 "urn:schemas-upnp-org:device:MediaServer"
port:1900 "urn:schemas-upnp-org:device:MediaRenderer"
port:1900 "camera" country:US
port:1900 "Hikvision"
port:1900 "RTSP"
upnp country:US has_screenshot:true
```

**UPnP description parsing:**

```python
import requests
from xml.etree import ElementTree as ET

def parse_upnp_device(ip, port=1900):
    # SSDP banners in Shodan often include the description URL
    # Once you have it, fetch the XML
    desc_url = f"http://{ip}:{port}/description.xml"   # common default path
    r = requests.get(desc_url, timeout=5)
    tree = ET.fromstring(r.content)
    ns = {'upnp': 'urn:schemas-upnp-org:device-1-0'}
    device = tree.find('.//upnp:device', ns)
    return {
        'manufacturer': device.findtext('upnp:manufacturer', namespaces=ns),
        'model':        device.findtext('upnp:modelName', namespaces=ns),
        'serial':       device.findtext('upnp:serialNumber', namespaces=ns),
        'friendly_name': device.findtext('upnp:friendlyName', namespaces=ns),
    }
```

---

### 1.6 Motion MJPEG Server Detection

`motion` is a widely-used open-source motion detection and video streaming daemon. It serves MJPEG streams over HTTP on port 8080 (default) and has a distinctive Server header. Unlike commercial camera systems, Motion is often self-hosted on Linux boxes connected to USB or CSI cameras — hobbyist surveillance, weather stations, maker spaces, small businesses.

**Shodan queries:**

```
"Server: Motion" -"WWW-Authenticate" -Apache "200 OK"
"Server: Motion/4" has_screenshot:true
"Server: Motion/3" has_screenshot:true
port:8080 "Server: Motion" country:US
port:8081 "Server: Motion"          # alternate common port
```

> The filter `-"WWW-Authenticate" -Apache` is important — it removes false positives where
> "Motion" appears in other contexts. Raw Motion servers serving unauthenticated streams
> are the target here (3,400+ indexed by Shodan).

**Direct stream paths for Motion:**

```
http://{ip}:8080/0/stream         # camera 0 MJPEG stream
http://{ip}:8080/0/feed           # alternative path
http://{ip}:8080/stream/feed.mjpg # alternate
```

---

### 1.7 SSL/TLS Certificate Subject Searching (Shodan)

```
# Find all devices with Hikvision in their TLS cert
ssl:"Hikvision"
ssl.cert.subject.cn:"hikvision"
ssl.cert.subject.cn:"dahua"
ssl.cert.subject.cn:"axis"
ssl.cert.subject.o:"Wowza Media Systems"
ssl.cert.subject.o:"Haivision"

# Find broadcast infrastructure by cert org
ssl.cert.subject.o:"NBCUniversal"
ssl.cert.subject.o:"CBS Broadcasting"
ssl.cert.subject.o:"Sinclair Broadcast"

# Expired certs on camera systems (often means unmaintained/forgotten infrastructure)
ssl.cert.expired:true http.title:"camera"
```

---

## 2. Additional Internet Scanners

GRIDLAND-5 covered Shodan, Censys, ZoomEye, and GreyNoise. The following are additive sources with distinct sensor networks, coverage regions, and query capabilities.

---

### 2.1 BinaryEdge

BinaryEdge operates independent scan sensors with different geographic distribution than Shodan — particularly stronger coverage in South America, Eastern Europe, and Southeast Asia. Its query language uses Elasticsearch-style syntax.

**Base URL:** `https://api.binaryedge.io/v2/`

**Query syntax:**

```
# Standard field queries
type:service port:554
type:service port:554 product:"RTSP"

# Boolean operators (must be UPPERCASE)
type:service port:554 AND country:US
type:service NOT _exists_:product

# Wildcard
product:Hikvis*

# Existence check
_exists_:product AND port:554

# Exact match
product.keyword:"Hikvision IP Camera"
```

**Python integration:**

```python
import requests

BINARYEDGE_KEY = "YOUR_KEY"

def binaryedge_search(query, page=1):
    r = requests.get(
        "https://api.binaryedge.io/v2/query/search",
        params={"query": query, "page": page},
        headers={"X-Key": BINARYEDGE_KEY}
    )
    r.raise_for_status()
    data = r.json()
    return {
        'total':   data['total'],
        'results': [
            {
                'ip':      e['target']['ip'],
                'port':    e['target']['port'],
                'proto':   e['target']['protocol'],
                'country': e.get('origin', {}).get('country'),
                'ts':      e.get('origin', {}).get('ts'),
                'result':  e.get('result', {})
            }
            for e in data.get('events', [])
        ]
    }

# Camera searches
results = binaryedge_search('type:service port:554 product:"RTSP" country:US')
results = binaryedge_search('type:service port:80 product:"Hikvision"')
```

**BinaryEdge-specific dataset types:**

| Dataset | Relevance |
|---|---|
| `type:service` | General service banners (equivalent to Shodan's main index) |
| `type:ssl` | TLS/SSL certificate data |
| `type:screenshot` | Web screenshots (similar to Shodan has_screenshot) |
| `type:vulns` | Vulnerability correlation data |
| `type:rdns` | Reverse DNS |

---

### 2.2 Netlas.io

Netlas performs continuous full-internet scanning and maintains a queryable database. Its free tier (50 requests/day) is useful for verification and spot-checks without Shodan credits.

**Python SDK:**

```python
import netlas   # pip install netlas

api = netlas.Netlas(api_key="YOUR_KEY")

# Search responses (HTTP banners, open ports)
response = api.query(
    query='http.title:"Hikvision" AND geo.city:"Philadelphia"',
    datatype="response",
    fields=["ip", "port", "http.title", "geo.city", "geo.country",
            "geo.location.lat", "geo.location.lon", "as.organization"]
)

for item in response['items']:
    print({
        'ip':    item['data']['ip'],
        'port':  item['data']['port'],
        'title': item['data'].get('http', {}).get('title'),
        'city':  item['data'].get('geo', {}).get('city'),
        'org':   item['data'].get('as', {}).get('organization'),
        'lat':   item['data'].get('geo', {}).get('location', {}).get('lat'),
        'lon':   item['data'].get('geo', {}).get('location', {}).get('lon'),
    })

# Count only (free operation)
count = api.count(
    query='http.title:"DVR" AND geo.country:"US"',
    datatype="response"
)
print(count['total'])
```

**Netlas query language examples:**

```
http.title:"Network Camera"
http.title:"Hikvision" AND geo.city:"Philadelphia"
port:554 AND geo.country_code:"US"
http.headers.server:"Boa"           # embedded camera firmware
http.title:"Wowza"
cert.subject.organization:"Haivision"
```

**Data types available:**

| Type | Contents |
|---|---|
| `response` | HTTP/HTTPS banners, titles, headers, bodies |
| `cert` | TLS certificate data |
| `domain` | Domain records |
| `whois-ip` | IP WHOIS data |
| `whois-domain` | Domain WHOIS data |

---

### 2.3 FOFA

FOFA (fofa.info) is a Chinese internet scanner with particularly strong coverage of Asian infrastructure and a different sensor refresh cycle than Shodan. Queries must be base64-encoded before submission.

**API endpoint:**

```
GET https://fofa.info/api/v1/search/all
    ?email=YOUR_EMAIL
    &key=YOUR_KEY
    &qbase64=BASE64_ENCODED_QUERY
    &fields=ip,host,port,title,country,city,latitude,longitude,as_organization
    &size=100
    &page=1
```

**Python integration:**

```python
import requests
import base64

FOFA_EMAIL = "your@email.com"
FOFA_KEY   = "YOUR_KEY"

def fofa_search(query, fields=None, size=100, page=1):
    if fields is None:
        fields = "ip,host,port,title,country,city,latitude,longitude,as_organization"

    qb64 = base64.b64encode(query.encode()).decode()

    r = requests.get(
        "https://fofa.info/api/v1/search/all",
        params={
            "email":   FOFA_EMAIL,
            "key":     FOFA_KEY,
            "qbase64": qb64,
            "fields":  fields,
            "size":    size,
            "page":    page
        }
    )
    data = r.json()
    if data.get('error'):
        raise Exception(data.get('errmsg'))

    # Results are a list of lists matching field order
    field_list = fields.split(',')
    return [dict(zip(field_list, row)) for row in data.get('results', [])]

# Camera searches
results = fofa_search('title="Hikvision" && country="US"')
results = fofa_search('title="DVR Web Client" && country="US"')
results = fofa_search('app="Wowza-Streaming-Engine"')
results = fofa_search('protocol="rtsp" && country="US"')
```

**FOFA query operators:**

```
=       exact match
!=      not equal
~=      regexp match (for string fields)
=~      contains match
&&      AND
||      OR
&&!     AND NOT

# Examples
title="Hikvision" && country="US"
title="Network Camera" && city="Philadelphia"
protocol="rtsp" && country="US"
app="Axis-Network-Camera"
banner="Server: Motion" && country="US"
```

---

### 2.4 LeakIX

LeakIX focuses on finding exposed services and data leaks rather than generic banners. It has purpose-built plugins for specific software — including camera management systems and streaming servers — which means its results are pre-classified and often higher signal than raw Shodan results.

**API endpoints:**

```
GET https://leakix.net/host/{ip}                # full host report
GET https://leakix.net/search?scope=service&q={query}   # service search
GET https://leakix.net/search?scope=leak&q={query}      # leak search
```

**Python integration:**

```python
import requests

LEAKIX_KEY = "YOUR_KEY"

def leakix_search(query, scope="service", page=0):
    r = requests.get(
        "https://leakix.net/search",
        params={"scope": scope, "q": query, "page": page},
        headers={
            "api-key":  LEAKIX_KEY,
            "Accept":   "application/json"
        }
    )
    return r.json()

# Camera-specific plugin queries
results = leakix_search('+plugin:"HikvisionPlugin"')
results = leakix_search('+plugin:"DahuaPlugin"')
results = leakix_search('+plugin:"RtspPlugin" +country:"US"')
results = leakix_search('+plugin:"WowzaPlugin"')

# By severity (useful for compliance filtering — show only 'info', not 'critical')
results = leakix_search('+plugin:"HikvisionPlugin" +severity:"info"')
```

**LeakIX plugin taxonomy relevant to GRIDLAND:**

| Plugin | Detects |
|---|---|
| `HikvisionPlugin` | Hikvision cameras and NVRs |
| `DahuaPlugin` | Dahua cameras |
| `RtspPlugin` | RTSP streams (brand-agnostic) |
| `WowzaPlugin` | Wowza streaming servers |
| `HttpNTLM` | Windows auth on management panels |
| `ElasticSearchExplorePlugin` | Elasticsearch (sometimes used for camera event logs) |

---

### 2.5 Criminal IP

Korean cybersecurity company. Particularly strong for identifying malicious actors scanning camera infrastructure, and for enriching results with threat scoring.

**Key endpoints:**

```python
import requests

CRIMINALIP_KEY = "YOUR_KEY"
HEADERS = {"x-api-key": CRIMINALIP_KEY}

# Banner / asset search (up to 10,000 results)
def criminalip_search(query, offset=0):
    r = requests.get(
        "https://api.criminalip.io/v1/banner/search",
        params={"query": query, "offset": offset},
        headers=HEADERS
    )
    return r.json()

# Full IP report (includes geolocation, WHOIS, blacklist, screenshot, open ports, CVEs)
def criminalip_ip_report(ip):
    r = requests.get(
        f"https://api.criminalip.io/v1/asset/ip/report",
        params={"ip": ip},
        headers=HEADERS
    )
    return r.json()

# Example
results = criminalip_search('title:"Hikvision" country:US')
results = criminalip_search('title:"Wowza Streaming Engine"')
```

**Unique Criminal IP features for GRIDLAND:**
- **Threat score** per IP (0-100): useful for flagging cameras that have been observed in attacks
- **CVE correlation**: surfaces known vulnerabilities on discovered devices
- **Screenshot**: captures web UI screenshots like Shodan
- **AI-powered scanning** with 24/7 refresh cycle — often has fresher data than Shodan for recently-exposed devices

---

### 2.6 Onyphe

French internet scanner operational since 2017. Distinct sensor locations (strong European coverage). Uses OQL (ONYPHE Query Language).

**API base:** `https://www.onyphe.io/api/v2/`

**OQL query examples:**

```
# Datascan category — general service banners
category:datascan app:"Hikvision" country:US
category:datascan app:"Wowza Streaming Engine"
category:datascan port:554 country:US

# Synscan — just open port detection
category:synscan port:554 country:US

# Threatlist — IPs on threat intel lists
category:threatlist tag:scanner ip:203.0.113.0/24
```

```python
import requests

ONYPHE_KEY = "YOUR_KEY"

def onyphe_search(oql, page=1):
    r = requests.get(
        "https://www.onyphe.io/api/v2/search",
        params={"q": oql, "page": page},
        headers={"Authorization": f"apikey {ONYPHE_KEY}"}
    )
    data = r.json()
    return data.get('results', [])

results = onyphe_search('category:datascan app:"Hikvision" country:US')
```

---

### 2.7 Rapid7 Project Sonar — Free Researcher Data

Rapid7 conducts ongoing internet-wide scans (Project Sonar) and publishes the raw data for free to qualified researchers. This is the highest-volume free alternative to Shodan — covering HTTP/HTTPS banners, TCP ports, DNS, SSL certificates, and UDP services globally.

**Access:** https://opendata.rapid7.com/

**Datasets most relevant to GRIDLAND:**

| Dataset | Description | Update Frequency |
|---|---|---|
| `sonar.http` | HTTP banner responses (all ports) | ~Weekly |
| `sonar.https` | HTTPS banner responses | ~Weekly |
| `sonar.tcp` | TCP port scan results | ~Weekly |
| `sonar.ssl` | SSL certificate data | ~Weekly |
| `sonar.fdns` | Forward DNS data | ~Weekly |
| `sonar.rdns` | Reverse DNS data | ~Weekly |
| `sonar.udp` | UDP service responses (inc. port 3702 ONVIF) | ~Monthly |

**Data format:** gzip-compressed JSONL (one JSON object per line)

```python
import gzip
import json
import requests

# Datasets are large (10GB-200GB compressed). Stream and filter rather than download fully.
def stream_sonar_http_for_cameras(sonar_http_url):
    """
    Stream Rapid7 sonar.http data and filter for camera-related titles.
    sonar_http_url: the presigned S3 URL from opendata.rapid7.com
    """
    CAMERA_KEYWORDS = ['hikvision', 'dahua', 'axis', 'dvr web client',
                       'network camera', 'wowza', 'nvr', 'ipcam']

    with requests.get(sonar_http_url, stream=True) as r:
        with gzip.GzipFile(fileobj=r.raw) as f:
            for line in f:
                try:
                    record = json.loads(line)
                    title = record.get('title', '').lower()
                    if any(kw in title for kw in CAMERA_KEYWORDS):
                        yield {
                            'ip':    record.get('ip'),
                            'port':  record.get('port'),
                            'vhost': record.get('vhost'),
                            'title': record.get('title'),
                        }
                except json.JSONDecodeError:
                    continue
```

> **Researcher access:** Email Rapid7 at research@rapid7.com with your use case. Access
> is granted freely for legitimate security research within a few business days.

---

## 3. Historical & Passive Discovery APIs

These sources don't scan the internet — they index what has already been publicly visible. They are invaluable for recovering stream URLs that were briefly exposed, finding infrastructure subdomains, and auditing historical exposure.

---

### 3.1 Certificate Transparency — crt.sh

Every public TLS certificate is logged to Certificate Transparency logs. `crt.sh` provides a free, unauthenticated API to search them. **This is the best way to enumerate subdomains of broadcast stations and streaming infrastructure companies** — stream.*, live.*, hls.*, ingest.*, and similar subdomains appear in TLS certs and often represent active streaming infrastructure.

**API endpoint:**

```
GET https://crt.sh/?q={query}&output=json
```

**Query syntax:**

```
%.example.com        → all subdomains of example.com
example.com          → exact domain only
%.wowza.com          → all Wowza subdomains
%.haivision.com      → Haivision infrastructure
%.wpvi.com           → Philly ABC station
%.nbcphiladelphia.com
```

**Python integration:**

```python
import requests

def crt_sh_search(domain_pattern):
    """
    Find all TLS certificate subjects matching a wildcard pattern.
    domain_pattern: e.g. '%.wpvi.com' for all wpvi.com subdomains
    """
    r = requests.get(
        "https://crt.sh/",
        params={"q": domain_pattern, "output": "json"},
        headers={"Accept": "application/json"},
        timeout=30
    )
    certs = r.json()

    subdomains = set()
    for cert in certs:
        name_value = cert.get('name_value', '')
        for name in name_value.split('\n'):
            name = name.strip()
            if name and not name.startswith('*'):
                subdomains.add(name)

    return sorted(subdomains)

# Discover streaming subdomains for major Philly broadcast stations
PHILLY_STATIONS = [
    '%.wpvi.com',         # 6ABC
    '%.cbsphiladelphia.com',
    '%.nbcphiladelphia.com',
    '%.fox29.com',
    '%.phillytrib.com',
    '%.whyy.org',
]

STREAMING_KEYWORDS = ['stream', 'live', 'hls', 'ingest', 'rtmp',
                       'video', 'media', 'cdn', 'broadcast', 'air']

for pattern in PHILLY_STATIONS:
    subdomains = crt_sh_search(pattern)
    stream_subdomains = [s for s in subdomains
                         if any(kw in s.lower() for kw in STREAMING_KEYWORDS)]
    print(f"\n{pattern}:")
    for s in stream_subdomains:
        print(f"  {s}")
```

**Also useful for broadcast infrastructure companies:**

```python
BROADCAST_INFRA = [
    '%.wowza.com',
    '%.haivision.com',
    '%.teradek.com',
    '%.dejero.com',
    '%.liveu.tv',
    '%.elemental.com',
    '%.nimblestreamer.com',
]
```

---

### 3.2 Wayback Machine CDX API

The Internet Archive indexes the web continuously. The CDX API lets you query its URL index — useful for finding `.m3u8` stream URLs, RTSP references, and camera login pages that were once publicly accessible and may still work.

**API endpoint:**

```
GET http://web.archive.org/cdx/search/cdx
```

**Parameters:**

| Parameter | Description | Example |
|---|---|---|
| `url` | URL pattern (required) | `*.wpvi.com/*.m3u8` |
| `output` | `json` or `text` | `json` |
| `fl` | Fields to return | `original,timestamp,statuscode,mimetype` |
| `match_type` | `exact`, `prefix`, `host`, `domain` | `prefix` |
| `filter` | Filter by field value | `statuscode:200` |
| `collapse` | Deduplicate by field | `urlkey` |
| `limit` | Max results | `500` |
| `from` | Start date (yyyyMMddhhmmss) | `20200101000000` |
| `to` | End date | `20241231235959` |

**Python integration:**

```python
import requests

def wayback_find_streams(domain_pattern):
    """
    Find historical HLS/RTSP stream URLs for a domain.
    domain_pattern: e.g. '*.wpvi.com' or '*.nbcphiladelphia.com'
    """
    r = requests.get(
        "http://web.archive.org/cdx/search/cdx",
        params={
            "url":        f"{domain_pattern}/*.m3u8",
            "output":     "json",
            "fl":         "original,timestamp,statuscode",
            "match_type": "prefix",
            "filter":     "statuscode:200",
            "collapse":   "urlkey",
            "limit":      500
        }
    )
    data = r.json()
    if not data or len(data) < 2:
        return []
    headers = data[0]
    return [dict(zip(headers, row)) for row in data[1:]]


def wayback_find_camera_pages(ip_or_domain):
    """Find historical camera login/view pages."""
    r = requests.get(
        "http://web.archive.org/cdx/search/cdx",
        params={
            "url":        ip_or_domain,
            "output":     "json",
            "fl":         "original,timestamp,statuscode,mimetype",
            "collapse":   "urlkey",
            "filter":     "mimetype:text/html",
            "limit":      200
        }
    )
    data = r.json()
    if not data or len(data) < 2:
        return []
    headers = data[0]
    return [dict(zip(headers, row)) for row in data[1:]]


# Find stream URLs for Philly news stations
stations = ['*.wpvi.com', '*.cbsphiladelphia.com', '*.nbcphiladelphia.com']
for station in stations:
    streams = wayback_find_streams(station)
    print(f"\n{station}: {len(streams)} historical stream URLs found")
    for s in streams[:10]:
        print(f"  [{s['timestamp']}] {s['original']}")
```

**Targeted search for news chopper stream URLs:**

```python
# Chopper/helicopter stream URLs often contain predictable path segments
CHOPPER_PATTERNS = [
    '*/chopper*',
    '*/helicopter*',
    '*/sky*',
    '*/air*',
    '*/live/chopper*',
]

for pattern in CHOPPER_PATTERNS:
    r = requests.get("http://web.archive.org/cdx/search/cdx", params={
        "url":      pattern,
        "output":   "json",
        "fl":       "original,timestamp",
        "collapse": "urlkey",
        "limit":    200,
        "filter":   "statuscode:200"
    })
    # ... process results
```

---

### 3.3 Common Crawl CDX API

Common Crawl crawls approximately 3 billion pages per month and makes its full URL index queryable. Unlike Wayback Machine (which focuses on archiving specific sites), Common Crawl is a broad web crawl — it captures pages that Wayback doesn't and vice versa.

**API endpoint:**

```
GET https://index.commoncrawl.org/{INDEX}-index
    ?url={pattern}
    &output=json
    &limit={n}
    &filter=status:200
```

**Finding the current index:**

```python
import requests

def get_current_crawl_index():
    r = requests.get("https://index.commoncrawl.org/collinfo.json")
    indexes = r.json()
    # Most recent crawl is first
    return indexes[0]['cdx-api']

def commoncrawl_search(url_pattern, limit=1000, index_api=None):
    if index_api is None:
        index_api = get_current_crawl_index()

    r = requests.get(
        index_api,
        params={
            "url":    url_pattern,
            "output": "json",
            "limit":  limit,
            "filter": "status:200"
        },
        stream=True
    )

    results = []
    for line in r.iter_lines():
        if line:
            try:
                results.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return results

# Find HLS stream URLs indexed in the current crawl
streams = commoncrawl_search("*.m3u8")

# RTSP references in HTML pages
rtsp_pages = commoncrawl_search("*rtsp://*")

# Wowza management pages
wowza_pages = commoncrawl_search("*/wowza/*")
```

---

### 3.4 PublicWWW — Source Code Search

PublicWWW indexes the source code of 200M+ websites and lets you search for exact strings within HTML, JavaScript, and other page source. Unlike Google/Bing (which search rendered content), PublicWWW sees everything in the raw source — including hidden stream URLs embedded in JavaScript players.

**Use cases for GRIDLAND:**
- Find pages with embedded `.m3u8` URLs in their JavaScript
- Find pages loading `rtsp://` streams
- Find pages loading known camera player libraries (Flowplayer, JW Player with RTSP config)
- Find pages embedding Wowza, Icecast, or Icecast2 player widgets

**API:**

```python
import requests

PUBLICWWW_KEY = "YOUR_KEY"

def publicwww_search(query, export_type="urls"):
    r = requests.get(
        f"https://publicwww.com/websites/{requests.utils.quote(query)}/",
        params={"export": export_type, "key": PUBLICWWW_KEY}
    )
    return r.text.strip().split('\n')

# Stream URL patterns embedded in page source
results = publicwww_search('".m3u8"')
results = publicwww_search('"rtsp://"')
results = publicwww_search('"wowza"')
results = publicwww_search('"icecast"')

# News station stream configs
results = publicwww_search('"chopper" ".m3u8"')
results = publicwww_search('"live" "stream" ".m3u8" "wpvi"')
```

> PublicWWW free tier returns limited results. Paid tiers unlock full export.
> The paid plan is inexpensive (~$49/mo) and includes API access.

---

## 4. New Device Categories

### 4.1 LPR / ALPR Cameras (License Plate Readers)

Automated License Plate Recognition cameras represent a distinct and rapidly growing category of public surveillance infrastructure. Major vendors:

- **Flock Safety** — deployed in thousands of US municipalities, HOAs, and campuses
- **Rekor Scout** — municipal and law enforcement LPR
- **Motorola Solutions (Vigilant)** — legacy enterprise LPR
- **OpenALPR** — open-source, self-hosted

**Rekor Scout API (for authorized access):**

```python
import requests

REKOR_KEY = "YOUR_KEY"

# Search for plate reads (requires agency account)
def rekor_search_plates(query, start_date, end_date):
    r = requests.get(
        "https://api.rekor.ai/v1/plates/search",
        params={
            "query":      query,
            "start_date": start_date,
            "end_date":   end_date
        },
        headers={"Authorization": f"Bearer {REKOR_KEY}"}
    )
    return r.json()

# Get camera locations (agency-specific)
def rekor_cameras():
    r = requests.get(
        "https://api.rekor.ai/v1/cameras",
        headers={"Authorization": f"Bearer {REKOR_KEY}"}
    )
    return r.json()
```

**Finding LPR cameras via Shodan:**

```
# Flock Safety cameras have distinctive web interfaces
http.title:"Flock Safety"
http.html:"flocksafety.com"

# OpenALPR self-hosted
http.title:"OpenALPR"
http.title:"Rekor Scout"
"openalpr" port:80 country:US

# Generic ALPR via ONVIF
port:3702 "ALPR" country:US
```

**OSM tag for LPR cameras:**
```
surveillance:type=ALPR
surveillance:type=ANPR          # UK/European terminology
```

---

### 4.2 Weather & Environmental Cameras

**NOAA / National Weather Service:**

NWS provides a well-documented REST API (no key required) covering weather stations, alerts, and observations. Weather cameras are linked from observation station records.

```python
import requests

NWS_BASE = "https://api.weather.gov"

def get_weather_stations(state="PA"):
    r = requests.get(
        f"{NWS_BASE}/stations",
        params={"state": state, "limit": 500},
        headers={"User-Agent": "GRIDLAND Research Tool (contact@yourorg.com)"}
    )
    return r.json().get('features', [])

def get_station_observations(station_id):
    r = requests.get(
        f"{NWS_BASE}/stations/{station_id}/observations/latest",
        headers={"User-Agent": "GRIDLAND Research Tool (contact@yourorg.com)"}
    )
    return r.json()

# NWS radar stations also have public camera feeds
# format: https://radar.weather.gov/station/{STATION_ID}/standard
RADAR_STATIONS_PA = ['KPBZ', 'KDIX', 'KCCX']  # Pittsburgh, Philadelphia-area, State College
```

**USGS StreamStats / StreamCam — Flood Monitoring:**

USGS operates stream gauge cameras at river monitoring stations that are publicly accessible:

```python
def get_usgs_streamcams(state_code="PA"):
    r = requests.get(
        "https://waterservices.usgs.gov/nwis/iv/",
        params={
            "format":       "json",
            "stateCd":      state_code,
            "parameterCd":  "00065",    # stream level
            "siteType":     "ST",       # streams
            "siteStatus":   "active"
        }
    )
    sites = r.json()['value']['timeSeries']
    return [
        {
            'site_id':   s['sourceInfo']['siteCode'][0]['value'],
            'name':      s['sourceInfo']['siteName'],
            'lat':       s['sourceInfo']['geoLocation']['geogLocation']['latitude'],
            'lon':       s['sourceInfo']['geoLocation']['geogLocation']['longitude'],
            # Camera URL follows a predictable pattern for many sites:
            'camera_url': f"https://waterdata.usgs.gov/nwisweb/get_image?site_no="
                         f"{s['sourceInfo']['siteCode'][0]['value']}&image_ht=480"
        }
        for s in sites
    ]
```

**NPS Webcam API:**

```python
NPS_KEY = "YOUR_NPS_KEY"  # Free at nps.gov/subjects/developer/get-started.htm

def get_nps_webcams(park_code=None):
    params = {
        "api_key": NPS_KEY,
        "limit":   500
    }
    if park_code:
        params["parkCode"] = park_code

    r = requests.get(
        "https://developer.nps.gov/api/v1/webcams",
        params=params
    )
    data = r.json()
    return [
        {
            'name':      cam['title'],
            'park':      cam.get('parkCode'),
            'lat':       cam.get('latitude'),
            'lon':       cam.get('longitude'),
            'url':       cam.get('url'),
            'status':    cam.get('status'),
            'images':    cam.get('images', [])
        }
        for cam in data.get('data', [])
    ]

# All NPS webcams
all_webcams = get_nps_webcams()

# Specific park (e.g., Delaware Water Gap)
dwg_cams = get_nps_webcams("dewa")
```

---

## 5. FCC Database Integration

The FCC maintains three public databases that are goldmines for broadcast infrastructure discovery. Together, they tell you where broadcast stations are licensed, where their towers are, and where their wireless links (microwave STL, SNG) operate.

---

### 5.1 FCC LMS — Broadcast Station Locations

The License Management System (LMS) replaced the legacy CDBS in October 2023. It contains the precise coordinates of every licensed broadcast transmitter in the US.

**Bulk download:** https://enterpriseefiling.fcc.gov/dataentry/public/tv/lmsDatabase.html

**Key tables:**

| File | Contents |
|---|---|
| `facility.txt` | All station facilities (callsign, type, state, city) |
| `antenna.txt` | Antenna coordinates (lat/lon, height, direction) |
| `app_auth_phase_act.txt` | Authorized construction permits + licenses |

```python
import csv
import io
import requests
import zipfile

def download_lms_facilities():
    """Download and parse FCC LMS facility database."""
    # LMS publishes full database as a ZIP
    r = requests.get(
        "https://enterpriseefiling.fcc.gov/dataentry/public/tv/lmsDatabase.html"
        # Actual ZIP URLs are on this page — fetch the current link dynamically
    )
    # Parse the page to find current ZIP download URL, then:
    # ...
    pass

# Alternatively, use the FCC's legacy bulk download that still works:
def get_fcc_tv_stations():
    r = requests.get(
        "https://data.fcc.gov/api/license-view/basicSearch/getLicenses",
        params={
            "searchValue": "",
            "licenseType": "TV",
            "format":      "json",
            "limit":       500,
            "offset":      0
        }
    )
    return r.json()

# FCC coverage contour API (FM/TV signal contours with lat/lon points)
def get_station_contour(facility_id, service="TV"):
    r = requests.get(
        f"https://geo.fcc.gov/api/contours/facilities/{facility_id}.json"
    )
    return r.json()
```

---

### 5.2 FCC ULS — Wireless Licenses (SNG Trucks, Microwave STL)

The Universal Licensing System covers wireless licenses. For broadcast, the key license category is **Part 74 — Broadcast Auxiliary Services**, which includes:

- **TP** — TV pickup (ENG, helicopter feeds)
- **TT** — TV translator relay
- **TB** — TV booster
- **MX** — TV microwave (studio-transmitter links)
- **TS** — TV studio transmitter links
- **CB** — Aural STL (audio studio-transmitter links)
- **AS** — Aural broadcast auxiliary

SNG trucks (satellite uplink vehicles) are licensed under these categories. The license records include:

- Licensee name (e.g., "WPVI-TV LLC")
- Service area
- Frequency
- Equipment type (often lists the encoder brand)
- Vehicle-mounted equipment flag

**ULS Search API:**

```python
def search_uls_broadcast_auxiliary(callsign_prefix=None, state=None):
    params = {
        "radioservice": "TB",      # TV booster/auxiliary
        "format":       "json",
        "limit":        500
    }
    if state:
        params["state"] = state
    if callsign_prefix:
        params["searchValue"] = callsign_prefix

    r = requests.get(
        "https://data.fcc.gov/api/license-view/basicSearch/getLicenses",
        params=params
    )
    return r.json()

# Find all TV broadcast auxiliary licenses in Pennsylvania
pa_aux = search_uls_broadcast_auxiliary(state="PA")

# Find licenses held by a specific station group
nbc_licenses = search_uls_broadcast_auxiliary(callsign_prefix="WCAU")  # NBC10 Philly
```

**Bulk ULS data download (pipe-delimited):**

```
https://wireless2.fcc.gov/UlsApp/UlsSearch/results.jsp?newSearch=Y&pas=&licKey=&radioservice=TB&...
```

ULS bulk downloads include an `EN.dat` (entity) file that maps license records to organization names, and an `HD.dat` (header) file with license details. Cross-referencing the entity file against known Philadelphia station call letters returns the full wireless license portfolio for each station — including which SNG trucks are licensed to operate.

---

### 5.3 FCC ASR — Broadcast Tower Locations

The Antenna Structure Registration database contains every broadcast tower registered with the FCC, with precise GPS coordinates, heights, and FAA lighting requirements. Broadcast towers are the physical locations where transmission equipment, microwave dishes, and sometimes camera systems are mounted.

**API / Search:**

```
GET https://wireless2.fcc.gov/UlsApp/AsrSearch/asrRegistrationSearch.jsp
    ?state=PA
    &county=Philadelphia
    &action=Search
    &format=json
```

**Radius search (find all towers within N km of a point):**

```
GET https://www.fcc.gov/media/radio/asrn-within-radius
    ?lat=39.9526
    &lon=-75.1652
    &dist=50          # kilometers
    &unit=km
```

```python
def get_towers_near(lat, lon, radius_km=50):
    r = requests.get(
        "https://www.fcc.gov/media/radio/asrn-within-radius",
        params={
            "lat":  lat,
            "lon":  lon,
            "dist": radius_km,
            "unit": "km"
        }
    )
    # Response is HTML table — parse with BeautifulSoup
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(r.text, 'html.parser')
    towers = []
    for row in soup.select('table tr')[1:]:
        cells = [td.get_text(strip=True) for td in row.find_all('td')]
        if cells:
            towers.append({
                'asrn':        cells[0],   # ASR number
                'lat':         cells[1],
                'lon':         cells[2],
                'height_agl':  cells[3],   # height above ground level (meters)
                'height_amsl': cells[4],   # height above mean sea level
                'registrant':  cells[5],
                'city':        cells[6],
                'state':       cells[7]
            })
    return towers
```

**Combined FCC + Shodan workflow:**

```
1. Query ASR for all towers within target area
2. For each tower registrant matching BROADCAST_KEYWORDS:
   a. Look up their FCC entity → get callsign/organization
   b. Query ARIN RDAP for their IP ranges
   c. Shodan search those IP ranges for Wowza/Haivision/LiveU panels
3. Cross-reference ULS Part 74 licenses for SNG truck equipment lists
```

---

## 6. OpenStreetMap Overpass API — Community Camera Data

This is the most underutilized source for this type of research. The OpenStreetMap community uses a well-developed tagging scheme to map physical surveillance cameras. Unlike Shodan (which finds cameras on the network) or 511 APIs (which expose official traffic cameras), OSM data represents cameras that community members have physically observed and documented.

**Overpass API endpoint:** `https://overpass-api.de/api/interpreter`

### 6.1 OSM Surveillance Tag Schema

| Tag | Values | Description |
|---|---|---|
| `surveillance` | `camera`, `webcam`, `guard` | Primary type |
| `surveillance:type` | `dome`, `fixed`, `panning`, `PTZ`, `ALPR`, `ANPR`, `mobile` | Camera mount/behavior type |
| `surveillance:zone` | `traffic`, `public`, `parking`, `retail`, `entrance`, `bank`, `atm`, `building` | What the camera monitors |
| `camera:direction` | `0`–`359` (compass bearing) | Direction camera faces |
| `camera:mount` | `pole`, `wall`, `ceiling`, `aerial`, `mast` | Physical mounting |
| `camera:type` | `colour`, `black_and_white`, `infrared`, `thermal` | Imaging type |
| `operator` | Free text | Who operates the camera |
| `operator:type` | `government`, `private`, `community` | Operator category |
| `indoor` | `yes`, `no` | Indoor or outdoor |
| `height` | Numeric (meters) | Mounting height |

### 6.2 Overpass QL Queries

```python
import requests

OVERPASS_URL = "https://overpass-api.de/api/interpreter"

def query_overpass(oql):
    r = requests.post(OVERPASS_URL, data={"data": oql}, timeout=60)
    r.raise_for_status()
    return r.json()

def get_surveillance_cameras_bbox(south, west, north, east):
    """Get all community-mapped surveillance cameras in a bounding box."""
    oql = f"""
    [out:json][timeout:60];
    (
      node["surveillance"~"camera|webcam"]({south},{west},{north},{east});
      node["man_made"="surveillance"]({south},{west},{north},{east});
    );
    out body;
    """
    data = query_overpass(oql)
    cameras = []
    for element in data.get('elements', []):
        tags = element.get('tags', {})
        cameras.append({
            'id':        element['id'],
            'lat':       element.get('lat'),
            'lon':       element.get('lon'),
            'type':      tags.get('surveillance'),
            'cam_type':  tags.get('surveillance:type'),
            'zone':      tags.get('surveillance:zone'),
            'direction': tags.get('camera:direction'),    # compass bearing
            'mount':     tags.get('camera:mount'),
            'operator':  tags.get('operator'),
            'op_type':   tags.get('operator:type'),
            'indoor':    tags.get('indoor', 'no') == 'yes',
            'height_m':  tags.get('height'),
            'camera_type': tags.get('camera:type'),
        })
    return cameras

# Philadelphia bounding box
philly_cams = get_surveillance_cameras_bbox(
    south=39.867, west=-75.280,
    north=40.138, east=-74.956
)

# Filter to traffic cameras only
traffic_cams = [c for c in philly_cams if c['zone'] == 'traffic']

# Filter to ALPR cameras
alpr_cams = [c for c in philly_cams if c['cam_type'] in ('ALPR', 'ANPR')]

# Cameras with known direction (useful for FOV visualization)
directed_cams = [c for c in philly_cams if c['direction'] is not None]
```

```python
def get_traffic_cameras_radius(lat, lon, radius_meters=5000):
    """Get traffic cameras within radius using Overpass around filter."""
    oql = f"""
    [out:json][timeout:60];
    (
      node["surveillance:zone"="traffic"](around:{radius_meters},{lat},{lon});
      node["surveillance:type"="ALPR"](around:{radius_meters},{lat},{lon});
    );
    out body;
    """
    return query_overpass(oql)
```

### 6.3 OSM Data as a Unique Layer

The OSM surveillance data layer brings something none of the network-discovery sources can: **physical ground truth with directional metadata**. When combined with `camera:direction`, you can render a field-of-view cone on the map. The combination of:

- **Shodan** → network-discoverable cameras (IP, port, screenshot)
- **OSM Overpass** → community-confirmed physical cameras (location, direction, type)
- **511 APIs** → official traffic cameras (authorized, live stream URLs)

...creates three independent validation layers. Cameras appearing in all three are confirmed with high confidence. Cameras appearing in only Shodan are unverified.

---

## 7. Mapillary API v4 — Street-Level Camera Detection

Mapillary is an open street-level photography platform (acquired by Meta but with a public API). Its computer vision pipeline analyzes every uploaded image for object detection, including `object--surveillance-camera`. This provides a visual, ground-truth detection of physical surveillance cameras in street imagery — the rarest data type in this stack.

**API base:** `https://graph.mapillary.com/`

**Authentication:** Bearer token (free account at mapillary.com)

### 7.1 Detected Objects — Surveillance Cameras

```python
import requests

MAPILLARY_TOKEN = "YOUR_TOKEN"
BASE = "https://graph.mapillary.com"

def get_camera_detections_bbox(west, south, east, north):
    """
    Get all street-level-detected surveillance cameras in a bounding box.
    Returns map features of type object--surveillance-camera.
    """
    r = requests.get(
        f"{BASE}/map_features",
        params={
            "access_token":  MAPILLARY_TOKEN,
            "fields":        "id,object_type,object_value,first_seen_at,last_seen_at,"
                            "geometry,images",
            "object_type":   "object--surveillance-camera",
            "bbox":          f"{west},{south},{east},{north}",
            "limit":         2000
        }
    )
    data = r.json()
    features = []
    for f in data.get('data', []):
        geom = f.get('geometry', {})
        features.append({
            'id':          f['id'],
            'object_type': f.get('object_type'),
            'object_value': f.get('object_value'),   # subtype if available
            'first_seen':  f.get('first_seen_at'),
            'last_seen':   f.get('last_seen_at'),
            'lon':         geom.get('coordinates', [None, None])[0],
            'lat':         geom.get('coordinates', [None, None])[1],
            'image_count': len(f.get('images', {}).get('data', []))
        })
    return features

# Philadelphia
philly_visual_cams = get_camera_detections_bbox(
    west=-75.280, south=39.867,
    east=-74.956, north=40.138
)
```

### 7.2 Street-Level Images in an Area

```python
def get_images_near(lat, lon, radius_m=200, limit=50):
    """Get Mapillary images near a coordinate — useful for visual verification."""
    r = requests.get(
        f"{BASE}/images",
        params={
            "access_token": MAPILLARY_TOKEN,
            "fields":       "id,captured_at,geometry,thumb_2048_url,creator",
            "closeto":      f"{lon},{lat}",
            "radius":       radius_m,
            "limit":        limit
        }
    )
    return r.json().get('data', [])

# After finding a camera in Shodan, visually verify its physical presence
# by finding Mapillary images taken near its geolocation
```

---

## 8. Municipal Open Data Portals

### 8.1 NYC Open Data

```python
# Speed camera locations (confirmed public dataset)
r = requests.get(
    "https://data.cityofnewyork.us/resource/hk4g-zwnh.json",
    params={"$limit": 5000}
)
speed_cameras = r.json()

# NYC DOT traffic camera feed URLs
r = requests.get("https://webcams.nyctmc.org/api/cameras/")
nyc_traffic_cams = r.json()

# NYC Open Data general camera search
r = requests.get(
    "https://data.cityofnewyork.us/api/views/metadata/v1",
    params={"q": "camera", "limit": 20}
)
```

### 8.2 OpenDataPhilly

```python
# OpenDataPhilly catalog search
r = requests.get(
    "https://www.opendataphilly.org/api/3/action/package_search",
    params={"q": "camera", "rows": 20}
)
datasets = r.json().get('result', {}).get('results', [])
for ds in datasets:
    print(ds['name'], ds.get('notes', '')[:100])

# Philadelphia PPA (Parking Authority) Camera Locations
# Check OpenDataPhilly for current endpoint
```

### 8.3 Data.gov — Federal Camera Datasets

```python
# Search Data.gov for camera datasets
r = requests.get(
    "https://catalog.data.gov/api/3/action/package_search",
    params={"q": "traffic camera location", "rows": 20, "fq": "res_format:JSON"}
)
datasets = r.json().get('result', {}).get('results', [])
```

### 8.4 State DOT Open Data Portals

| State | Portal | Camera Dataset |
|---|---|---|
| Pennsylvania | data.pa.gov | PennDOT traffic camera locations |
| New York | data.ny.gov | NYS DOT camera inventory |
| New Jersey | data.nj.gov | NJDOT traffic monitoring |
| California | data.ca.gov | Caltrans camera locations |
| Maryland | opendata.maryland.gov | SHA camera data |
| Virginia | data.virginia.gov | VDOT camera inventory |

---

## 9. EFF Atlas of Surveillance

The Electronic Frontier Foundation maintains the **Atlas of Surveillance** — a crowd-sourced, research-verified database of law enforcement surveillance technology deployments across the US. Unlike Shodan or OSM (which find cameras by network scanning or community mapping), the Atlas documents *who uses what* at the agency level.

**Website:** https://atlasofsurveillance.org

**Data available:**
- LPR/ALPR camera deployments by city/county
- Facial recognition programs
- Body cameras
- Drones
- Gunshot detection systems (ShotSpotter)
- Cell-site simulators (Stingrays)

**API access:** The Atlas publishes its data as downloadable CSV/JSON:

```python
def fetch_atlas_data():
    # EFF publishes the underlying dataset
    r = requests.get(
        "https://atlasofsurveillance.org/api/data",
        params={"format": "json"}
    )
    return r.json()

# Filter to LPR deployments in Pennsylvania
def get_alpr_deployments(state="Pennsylvania"):
    data = fetch_atlas_data()
    return [
        entry for entry in data
        if entry.get('state') == state
        and 'license plate' in entry.get('technology', '').lower()
    ]
```

**Integration note:** The Atlas data gives you the *agency* operating LPR cameras in a given area. Cross-reference this with OSM ALPR tags and Shodan results for IPs registered to municipal agencies to build a more complete picture.

---

## 10. Public Stream Aggregators

### 10.1 YouTube Live — Location-Tagged Streams

YouTube's Data API v3 can search for live streams tagged with a location. Many local news stations, traffic agencies, and public venues broadcast live on YouTube.

```python
from googleapiclient.discovery import build

youtube = build('youtube', 'v3', developerKey='YOUR_YT_KEY')

def search_live_streams(query, location=None, location_radius=None):
    params = {
        "part":       "snippet",
        "type":       "video",
        "eventType":  "live",          # only currently-live streams
        "q":          query,
        "maxResults": 50
    }
    if location:
        params["location"]       = location        # "lat,lon"
        params["locationRadius"] = location_radius  # e.g. "50km"

    r = youtube.search().list(**params).execute()
    return [
        {
            'video_id':      item['id']['videoId'],
            'title':         item['snippet']['title'],
            'channel':       item['snippet']['channelTitle'],
            'published':     item['snippet']['publishedAt'],
            'description':   item['snippet']['description'][:200],
            'thumbnail':     item['snippet']['thumbnails']['medium']['url'],
            'watch_url':     f"https://youtube.com/watch?v={item['id']['videoId']}"
        }
        for item in r.get('items', [])
    ]

# Traffic cameras, local news, public infrastructure
traffic_streams  = search_live_streams("traffic camera live")
news_streams     = search_live_streams("live news philadelphia", "39.9526,-75.1652", "50km")
chopper_streams  = search_live_streams("news helicopter live philadelphia")
weather_streams  = search_live_streams("weather camera live")
```

### 10.2 Earthcam and Webcam Aggregators

Several platforms aggregate publicly accessible webcams with location metadata:

| Platform | API? | Notes |
|---|---|---|
| Earthcam.com | Unofficial / scrape | Large catalog, US-heavy, location tagged |
| Webcamtaxi.com | Scrape | European-heavy, categorized |
| Insecam.org | Scrape | Indexes unsecured cameras — **use with caution, compliance review required** |
| Windy.com | Yes (weather cams) | Weather camera API, global |
| Roundshot.com | Yes | Panoramic webcam platform with embed URLs |

```python
# Windy Webcams API (weather cameras with location)
r = requests.get(
    "https://api.windy.com/api/webcams/v2/list/nearby/{lat},{lon},{radius}",
    params={
        "key":    "YOUR_WINDY_KEY",
        "fields": "id,title,location,image,player"
    }
)
webcams = r.json().get('result', {}).get('webcams', [])
```

---

## 11. Visualization Architecture — Full Opinion

### 11.1 The Case for OpenStreetMap as Base Layer

**Recommendation: YES, integrate OSM as the primary base map.**

Reasons:
1. **Free at any scale** — no per-tile costs, no API keys for basic tiles
2. **Community-maintained** — more accurate than Google Maps for infrastructure detail in many areas
3. **Overpass API integration** — you can query OSM surveillance tags in the same stack
4. **No vendor lock-in** — tile servers are interchangeable (switch from OSM.org to Mapbox Vector Tiles to self-hosted)
5. **Privacy** — no user request data goes to Google/Apple

**Tile providers for OSM base maps:**

| Provider | Cost | Notes |
|---|---|---|
| OpenStreetMap.org tiles | Free (with fair-use limits) | Dev/low-traffic only |
| Stadia Maps | Free tier generous | Good for production |
| MapTiler | Free tier + paid | Vector tiles, good quality |
| Protomaps | Self-hostable | Download planet, serve yourself |
| Mapbox (OSM-derived) | Free tier + paid | Best cartography, proprietary |

### 11.2 2D Mapping Library Recommendation

**Recommendation: MapLibre GL JS**

MapLibre is an open-source fork of Mapbox GL JS (before Mapbox went proprietary). It supports:
- WebGL-rendered vector tiles
- 3D terrain (via terrain exaggeration)
- 60fps animation
- Custom layer types (via deck.gl integration)
- Works with any tile source (OSM, Mapbox, MapTiler, self-hosted)

```javascript
import maplibregl from 'maplibre-gl';

const map = new maplibregl.Map({
    container: 'map',
    style: 'https://tiles.stadiamaps.com/styles/alidade_smooth_dark.json',
    center: [-75.1652, 39.9526],   // Philadelphia
    zoom: 12,
    pitch: 0,
    bearing: 0
});

// Add camera layer from your API
map.on('load', () => {
    map.addSource('cameras', {
        type: 'geojson',
        data: '/api/cameras/geojson'
    });

    map.addLayer({
        id: 'cameras-layer',
        type: 'circle',
        source: 'cameras',
        paint: {
            'circle-radius': 6,
            'circle-color': [
                'match', ['get', 'category'],
                'traffic',   '#00ff88',
                'cctv',      '#ff4444',
                'broadcast', '#4488ff',
                'alpr',      '#ffaa00',
                '#888888'
            ],
            'circle-stroke-width': 1,
            'circle-stroke-color': '#ffffff'
        }
    });
});
```

### 11.3 Google Maps 3D Tiles — Honest Opinion

**Recommendation: Powerful but use CesiumJS as the renderer rather than Google Maps JS API.**

The Google Photorealistic 3D Tiles are genuinely impressive — full photorealistic meshes of cities with real-world textures from aerial imagery. The key insight from the research: **Google 3D Tiles use the OGC standard 3D Tiles format (glTF)**, not a proprietary format. This means you can load them into **CesiumJS** (open-source) without using the Google Maps JavaScript API.

**Pricing reality:**
- Photorealistic 3D Tiles are billed per session (root tile request), not per tile
- One session covers ~3 hours of tile access
- Cost is reasonable for moderate use but unpredictable at scale

**The camera FOV use case** is where 3D truly earns its place. With a camera's position (lat/lon/height) and direction (compass bearing from OSM tags), you can render a frustum (view cone) in 3D space and see exactly what the camera sees — including which buildings occlude its view. This is not achievable in 2D.

### 11.4 3D Visualization Stack Recommendation

```
Layer 1 — Base 2D Map:     MapLibre GL JS + Stadia Maps tiles (free)
Layer 2 — 3D Mode:         CesiumJS + Google Photorealistic 3D Tiles
Layer 3 — Data Rendering:  deck.gl (integrates with both MapLibre and Cesium)
Layer 4 — FOV Cones:       Cesium FrustumGeometry OR deck.gl SolidPolygonLayer
Layer 5 — OSM Cameras:     Overpass API → GeoJSON → rendered as symbols
Layer 6 — Shodan Results:  Your API → GeoJSON → rendered with category colors
Layer 7 — 511 Traffic:     511 API → GeoJSON → distinct icon set
```

**CesiumJS + Google 3D Tiles setup:**

```javascript
import { Viewer, createGooglePhotorealistic3DTileset } from 'cesium';
import 'cesium/Build/Cesium/Widgets/widgets.css';

const viewer = new Viewer('cesiumContainer', {
    geocoder: false,
    baseLayerPicker: false,
    navigationHelpButton: false
});

// Load Google Photorealistic 3D Tiles
const tileset = await createGooglePhotorealistic3DTileset(
    'YOUR_GOOGLE_MAPS_API_KEY'
);
viewer.scene.primitives.add(tileset);

// Fly to Philadelphia
viewer.camera.flyTo({
    destination: Cesium.Cartesian3.fromDegrees(-75.1652, 39.9526, 500),
    orientation: { heading: 0, pitch: -0.5, roll: 0 }
});
```

**Rendering a camera FOV cone (frustum) in Cesium:**

```javascript
function addCameraFOV(lat, lon, heightM, bearingDeg, hFOVDeg=90, rangM=200) {
    const origin = Cesium.Cartesian3.fromDegrees(lon, lat, heightM);
    const bearingRad = Cesium.Math.toRadians(bearingDeg);
    const halfFOV = Cesium.Math.toRadians(hFOVDeg / 2);

    // Build frustum vertices
    const directions = [];
    for (let a = -halfFOV; a <= halfFOV; a += Cesium.Math.toRadians(5)) {
        const x = Math.sin(bearingRad + a);
        const y = Math.cos(bearingRad + a);
        directions.push(new Cesium.Cartesian3(x * rangM, y * rangM, 0));
    }

    // Add as translucent polygon
    viewer.entities.add({
        polygon: {
            hierarchy: new Cesium.PolygonHierarchy(
                [origin, ...directions.map(d =>
                    Cesium.Cartesian3.fromDegrees(lon + d.x/111000, lat + d.y/111000, heightM * 0.5)
                )]
            ),
            material: Cesium.Color.CYAN.withAlpha(0.3),
            outline: true,
            outlineColor: Cesium.Color.CYAN
        }
    });
}

// Add a camera with a known direction (from OSM data)
addCameraFOV(39.9526, -75.1652, 8, 270);  // West-facing camera at 8m height
```

**deck.gl FOV cone on MapLibre (2D alternative):**

```javascript
import { MapboxOverlay } from '@deck.gl/mapbox';
import { SolidPolygonLayer } from '@deck.gl/layers';

function buildFOVPolygon(lat, lon, bearingDeg, hFOVDeg = 90, rangeM = 150) {
    const points = [[lon, lat]];
    const halfFOV = hFOVDeg / 2;
    for (let a = -halfFOV; a <= halfFOV; a += 5) {
        const rad = ((bearingDeg + a) * Math.PI) / 180;
        points.push([
            lon + (Math.sin(rad) * rangeM) / 111320,
            lat + (Math.cos(rad) * rangeM) / 110540
        ]);
    }
    points.push([lon, lat]);
    return points;
}

const fovLayer = new SolidPolygonLayer({
    id: 'fov-cones',
    data: osmCamerasWithDirection,
    getPolygon: d => buildFOVPolygon(d.lat, d.lon, d.direction),
    getFillColor: [0, 200, 255, 60],
    extruded: false
});
```

### 11.5 Summary Recommendation Table

| Requirement | Recommended Tool | Alternative | Cost |
|---|---|---|---|
| 2D base map | MapLibre GL JS + Stadia | Leaflet + OSM tiles | Free |
| Vector tiles | Stadia Maps / MapTiler | Self-hosted Protomaps | Free–$ |
| 3D photorealistic | CesiumJS + Google 3D Tiles | CesiumJS + Cesium World Terrain | Free–$$ |
| FOV cones 2D | deck.gl SolidPolygonLayer | Turf.js + MapLibre | Free |
| FOV cones 3D | Cesium FrustumGeometry | Three.js custom layer | Free |
| OSM camera data | Overpass API | Overpass Turbo (UI) | Free |
| Clustering | MapLibre supercluster | deck.gl ScatterplotLayer | Free |
| Heatmap | deck.gl HeatmapLayer | MapLibre heatmap layer | Free |

---

## 12. Multi-Layer Discovery Workflow

This workflow combines all sources in a priority-ordered pipeline, from highest-trust to lowest-trust data.

```
┌─────────────────────────────────────────────────────────────────┐
│                    GRIDLAND DISCOVERY PIPELINE                   │
├──────────┬──────────────────────────────┬────────────────────────┤
│ Priority │ Source                       │ Trust Level            │
├──────────┼──────────────────────────────┼────────────────────────┤
│   1      │ 511 State APIs               │ Authoritative          │
│   2      │ FCC ASR (tower locations)    │ Authoritative          │
│   3      │ OSM Overpass (surveillance)  │ Community-verified     │
│   4      │ Mapillary object detection   │ CV-verified visual     │
│   5      │ NPS / NOAA / USGS APIs       │ Government-authoritative│
│   6      │ Municipal open data portals  │ Government-authoritative│
│   7      │ EFF Atlas of Surveillance    │ Research-verified      │
│   8      │ YouTube Live (location-tagged)│ Self-reported         │
│   9      │ Shodan (geo + device type)   │ Network-discovered     │
│  10      │ Censys (cert-based)          │ Network-discovered     │
│  11      │ BinaryEdge / Netlas          │ Network-discovered     │
│  12      │ FOFA / ZoomEye               │ Network-discovered     │
│  13      │ crt.sh (subdomain discovery) │ Infrastructure inferred│
│  14      │ Wayback CDX (historical)     │ Historical             │
│  15      │ Common Crawl (indexed URLs)  │ Historical             │
│  16      │ PublicWWW (source code)      │ Historical             │
└──────────┴──────────────────────────────┴────────────────────────┘
```

**Confidence scoring:**

```python
SOURCE_WEIGHTS = {
    '511':           1.0,   # Official government API
    'fcc_asr':       1.0,   # FCC registration
    'osm':           0.85,  # Community-verified, physical
    'mapillary':     0.80,  # Computer vision, physical
    'nps':           1.0,   # Government API
    'noaa':          1.0,   # Government API
    'open_data':     0.90,  # Government open data
    'eff_atlas':     0.85,  # Research-verified
    'youtube_live':  0.70,  # Self-reported
    'shodan':        0.65,  # Network discovery, may be stale
    'censys':        0.65,
    'binaryedge':    0.60,
    'netlas':        0.60,
    'fofa':          0.55,
    'zoomeye':       0.55,
    'crt_sh':        0.50,  # Infrastructure inferred
    'wayback':       0.40,  # Historical, may be dead
    'common_crawl':  0.40,
    'publicwww':     0.40,
}

def compute_confidence(camera_record):
    sources = camera_record.get('sources', [])
    if not sources:
        return 0.0
    # Confidence increases with corroboration across independent sources
    base = max(SOURCE_WEIGHTS.get(s, 0.3) for s in sources)
    corroboration_bonus = min(0.15 * (len(sources) - 1), 0.30)
    return min(base + corroboration_bonus, 1.0)
```

---

## 13. Expanded Data Source Matrix

This extends the GRIDLAND-5 matrix with all new sources.

| Source | Primary Strength | Geo Filter | Screenshots | Free Tier | Trust |
|---|---|---|---|---|---|
| **Shodan** | CCTV/DVR/broadcast panels, favicon hash | Native geo: | Yes | Very limited | Network |
| **Censys** | TLS cert coverage | City/country | No | 250q/mo | Network |
| **BinaryEdge** | South American / Asian sensors | Country | Yes | Limited | Network |
| **Netlas** | Fresh scans, low cost | City/country | No | 50 req/day | Network |
| **FOFA** | Chinese/Asian coverage | Country/city | No | 10q/day | Network |
| **LeakIX** | Pre-classified plugins | Country | No | Limited | Network |
| **Criminal IP** | Threat scoring, CVEs | Country/city | Yes | Limited | Network |
| **Onyphe** | French sensors, EU coverage | Country | No | Limited | Network |
| **ZoomEye** | Asian coverage | Country | No | 10q/day | Network |
| **GreyNoise** | Noise/scanner filtering | Country | No | 50 IPs/day | Intel |
| **Rapid7 Sonar** | Full internet, free for research | Post-process | No | Free (apply) | Network |
| **511 APIs** | Official traffic cameras | Native lat/lon | Snapshot URL | Free (most) | Official |
| **FCC ASR** | Broadcast tower locations | Radius search | No | Free | Official |
| **FCC ULS** | SNG/microwave licenses | State/county | No | Free | Official |
| **FCC LMS** | Station transmitter coords | Bulk download | No | Free | Official |
| **OSM Overpass** | Community camera mapping + direction | Bounding box | No | Free | Community |
| **Mapillary v4** | Visual camera detection | Bounding box | Street imagery | Free | Visual |
| **ARIN RDAP** | IP-to-org classification | N/A | No | Free | Authoritative |
| **crt.sh** | Streaming subdomain discovery | N/A | No | Free | Inferred |
| **Wayback CDX** | Historical stream URLs | N/A | No | Free | Historical |
| **Common Crawl** | Indexed stream URLs at scale | N/A | No | Free | Historical |
| **PublicWWW** | Source-code-embedded streams | Domain | No | Limited | Historical |
| **NPS API** | National park webcams | Park code | Photo URL | Free (key) | Official |
| **NOAA/NWS API** | Weather stations + observations | State | No | Free | Official |
| **USGS Streamcam** | River gauge cameras | State | Snapshot URL | Free | Official |
| **NYC Open Data** | NYC speed/traffic cameras | City | No | Free | Official |
| **EFF Atlas** | ALPR/surveillance deployments | City/county | No | Free | Research |
| **YouTube Data v3** | Location-tagged live streams | lat/lon + radius | Thumbnail | Free (quota) | Self-reported |
| **Windy Webcams** | Weather webcams globally | Radius | Yes | Free (key) | Aggregated |

---

*GRIDLAND-6 — Addendum to GRIDLAND-5 — Compiled 2026-05-17*
*All sources: public APIs, open government data, and publicly indexed internet data.*
