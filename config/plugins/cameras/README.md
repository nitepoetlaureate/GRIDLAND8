# Manual camera plugins (JSON)

Drop `*.json` files here. Each file is either:

- A JSON array of camera objects, or
- `{ "cameras": [ ... ] }`

## Schema

```json
{
  "id": "philly-demo-1",
  "label": "Demo intersection cam",
  "lat": 39.9526,
  "lon": -75.1652,
  "source": "plugin_json",
  "url": "https://example.com/camera-page",
  "thumbnail_url": "https://example.com/snapshot.jpg",
  "publication_status": "operator_published",
  "blur_required": false,
  "stream": {
    "type": "refresh_jpeg",
    "url": "https://example.com/snapshot.jpg"
  },
  "tags": {}
}
```

`stream.type`: `refresh_jpeg` | `mjpeg` | `hls`

For **manual IP cameras** on your network, set `stream.url` to the full HTTP MJPEG or snapshot URL
(e.g. `http://192.168.1.50/mjpg/video.mjpg`). GRIDLAND proxies allowed public hosts via
`/api/cameras/frame`; private IPs may require a future trusted-proxy setting (see `docs/TODO.md`).

Optional fields:

```json
"tags": { "notes": "loading dock", "vlan": "internal" }
```

After adding a file, run **scan** in GRIDLAND to merge pins into `/api/discover`.
