/** REST API client for /api/discover and /api/context. */

const BASE = "";

export async function discover(lat, lon, radius_km) {
  const url = new URL("/api/discover", window.location.origin);
  url.searchParams.set("lat", lat);
  url.searchParams.set("lon", lon);
  url.searchParams.set("radius_km", radius_km);
  const r = await fetch(url);
  if (!r.ok) throw new Error(`discover ${r.status}`);
  return r.json();
}

export async function context(lat, lon) {
  const url = new URL("/api/context", window.location.origin);
  url.searchParams.set("lat", lat);
  url.searchParams.set("lon", lon);
  const r = await fetch(url);
  if (!r.ok) throw new Error(`context ${r.status}`);
  return r.json();
}

export async function health() {
  const r = await fetch("/health");
  if (!r.ok) throw new Error(`health ${r.status}`);
  return r.json();
}
