#!/usr/bin/env python3
"""Verify live/API data for each map layer type at Philly (click-equivalent payloads)."""
from __future__ import annotations

import asyncio
import json
import sys
from typing import Any

import httpx

BASE = "http://127.0.0.1:8000"
PHILLY = {"lat": 39.9526, "lon": -75.1652}
TIMEOUT = 45.0


def ok(label: str, detail: str) -> None:
    print(f"  OK   {label}: {detail}")


def fail(label: str, detail: str) -> None:
    print(f"  FAIL {label}: {detail}")


def warn(label: str, detail: str) -> None:
    print(f"  WARN {label}: {detail}")


async def get(client: httpx.AsyncClient, path: str, **params) -> dict[str, Any]:
    r = await client.get(f"{BASE}{path}", params=params, timeout=TIMEOUT)
    r.raise_for_status()
    return r.json()


async def main() -> int:
    errors = 0
    async with httpx.AsyncClient() as client:
        print("=== Health ===")
        h = await get(client, "/health")
        ok("health", h.get("status", ""))

        print("\n=== Discovery (camera pins) ===")
        d = await get(client, "/api/discover", lat=PHILLY["lat"], lon=PHILLY["lon"], radius_km=25)
        cams = d.get("results") or []
        if len(cams) < 100:
            fail("discover count", f"only {len(cams)} cameras")
            errors += 1
        else:
            ok("discover", f"{len(cams)} cameras")
        with_thumb = [c for c in cams if c.get("thumbnail_url")]
        ok("cameras with thumbnail", f"{len(with_thumb)} (feed-capable subset)")
        sample_cam = cams[0] if cams else {}
        if sample_cam.get("label") and sample_cam.get("lat"):
            ok("camera click payload", f"{sample_cam['source']} · {sample_cam['label'][:40]}")
        else:
            fail("camera click payload", "missing label/lat")
            errors += 1

        print("\n=== Context (sidebar + POI layers) ===")
        ctx = await get(client, "/api/context", lat=PHILLY["lat"], lon=PHILLY["lon"])
        for key in ("weather", "transit_alerts", "indego_stations", "opendataphilly"):
            val = ctx.get(key)
            if val:
                n = len(val) if isinstance(val, list) else (1 if isinstance(val, dict) else 0)
                ok(key, str(n))
            else:
                warn(key, "empty or null")
        odp = (ctx.get("opendataphilly") or {}).get("layers") or {}
        crime = odp.get("crime_incidents") or []
        if crime:
            c0 = crime[0]
            if c0.get("lat") and c0.get("type"):
                ok("crime POI click", f"{c0['type']} @ {c0['lat']:.4f}")
            else:
                fail("crime POI", "missing fields")
                errors += 1
        else:
            warn("crime POI", "no incidents in bundle")

        print("\n=== SEPTA live (transit layer) ===")
        septa = await get(client, "/api/septa/vehicles")
        vehicles = septa.get("vehicles") or []
        sources = septa.get("sources") or {}
        if vehicles:
            ok("septa vehicles", f"{len(vehicles)} · sources {sources}")
            v0 = vehicles[0]
            if v0.get("id") and v0.get("route") and v0.get("lat") is not None:
                ok("transit click payload", f"{v0['id']} route {v0['route']}")
            else:
                fail("transit payload", json.dumps(v0)[:120])
                errors += 1
        else:
            fail("septa vehicles", f"empty · sources {sources}")
            errors += 1

        print("\n=== Indego (bike layer) ===")
        indego = await get(
            client, "/api/indego/stations",
            lat=PHILLY["lat"], lon=PHILLY["lon"], radius_km=15,
        )
        stations = indego.get("stations") or []
        if stations:
            s0 = stations[0]
            ok("indego stations", f"{len(stations)} · sample {s0.get('name', s0.get('station_id'))}")
            if s0.get("lat") is not None and s0.get("bikes") is not None:
                ok("indego click payload", f"bikes={s0['bikes']} docks={s0.get('docks')}")
            else:
                fail("indego payload", json.dumps(s0)[:120])
                errors += 1
        else:
            fail("indego", "no stations")
            errors += 1

        print("\n=== Photospheres (street view) ===")
        ps = await get(
            client, "/api/photospheres",
            lat=PHILLY["lat"], lon=PHILLY["lon"], radius_m=50, limit=3,
        )
        items = ps.get("items") or []
        if items:
            p0 = items[0]
            ok("mapillary panos", f"{len(items)} · id={p0.get('id')}")
            if p0.get("thumb_2048_url"):
                ok("pano image url", "thumb present")
            else:
                warn("pano image url", "no thumb_2048_url")
        else:
            fail("photospheres", "empty — check MAPILLARY_API_KEY")
            errors += 1

        print("\n=== What's here (empty-map click) ===")
        wh = await get(
            client, "/api/whats_here",
            lat=PHILLY["lat"], lon=PHILLY["lon"], radius_km=1,
        )
        wh_cams = (wh.get("cameras") or {}).get("results") or []
        if wh_cams:
            w0 = wh_cams[0]
            label = w0.get("label") or w0.get("id")
            ok("whats_here cameras", f"{len(wh_cams)} · {w0.get('source')}: {label}")
        else:
            warn("whats_here cameras", "none in 1km")
        if wh.get("errors"):
            warn("whats_here errors", str(wh["errors"]))

        print("\n=== Live status ===")
        ls = await get(client, "/api/live/status")
        ok("live status", f"ws_clients={ls.get('ws_clients')} septa={ls.get('septa', {}).get('count')}")

        print("\n=== Camera frame proxy (if sample has thumb) ===")
        if with_thumb:
            thumb = with_thumb[0]["thumbnail_url"]
            try:
                r = await client.get(
                    f"{BASE}/api/cameras/frame",
                    params={"url": thumb},
                    timeout=TIMEOUT,
                )
                if r.status_code == 200 and "image" in (r.headers.get("content-type") or ""):
                    ok("camera proxy", f"{len(r.content)} bytes")
                else:
                    warn("camera proxy", f"status {r.status_code} type={r.headers.get('content-type')}")
            except httpx.HTTPError as e:
                warn("camera proxy", str(e))
        else:
            warn("camera proxy", "no thumbnail URL in discover sample")

        print("\n=== Environmental POIs (context-live layer) ===")
        for layer, key, latk, lonk in [
            ("fires", "fires", "lat", "lon"),
            ("quakes", "quakes", "lat", "lon"),
            ("air_quality", "air_quality", "lat", "lon"),
            ("metars", "metars", "lat", "lon"),
        ]:
            arr = ctx.get(key) or []
            if not arr:
                warn(layer, "empty")
                continue
            e0 = arr[0]
            if e0.get(latk) is not None and e0.get(lonk) is not None:
                ok(layer, f"{len(arr)} with coordinates")
            else:
                warn(layer, f"{len(arr)} but missing coords on first item")

    print("\n=== Summary ===")
    if errors:
        print(f"FAILED: {errors} critical check(s)")
        return 1
    print("All critical live-data checks passed (API layer).")
    print("UI: open http://localhost:5173 — scan Philly, click pins for Cesium info box + camera feed panel.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(asyncio.run(main()))
    except httpx.ConnectError:
        print("ERROR: backend not running at http://127.0.0.1:8000 — run: make backend")
        raise SystemExit(1)
