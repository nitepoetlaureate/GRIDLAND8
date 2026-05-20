/** GRIDLAND frontend entry point. */
import * as Cesium from "cesium";
import { createViewer, flyTo } from "./cesium/viewer.js";
import { CameraLayer } from "./entities/cameras.js";
import { AircraftLayer } from "./entities/aircraft.js";
import { SatelliteLayer } from "./entities/satellites.js";
import { TransitLayer } from "./entities/transit.js";
import { GibsLayers } from "./cesium/gibs.js";
import { discover, context, health, whatsHere } from "./api.js";
import { LiveSocket, liveUrl } from "./ws.js";
import { PhotosphereTransition } from "./photosphere/transition.js";

// #region agent log
function dbg(location, message, data, hypothesisId) {
  try {
    fetch("http://127.0.0.1:7253/ingest/0d443fcc-bf02-4ed0-bbab-47f404bdc834", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Debug-Session-Id": "716b73",
      },
      body: JSON.stringify({
        sessionId: "716b73",
        runId: "ui",
        hypothesisId,
        location,
        message,
        data,
        timestamp: Date.now(),
      }),
    }).catch(() => {});
  } catch {}
}
window.__gridland_dbg = dbg;
// #endregion

const $ = (id) => document.getElementById(id);

function setStatus(text, kind = "") {
  const el = $("status");
  el.textContent = text;
  el.className = "status " + kind;
}

function renderCounts(resp) {
  const counts = resp?.counts_by_source ?? {};
  const items = Object.entries(counts).map(
    ([src, n]) => `<span>${src}: ${n}</span>`,
  );
  $("counts").innerHTML = items.length
    ? `cameras → ${items.join(" ")}`
    : "cameras → 0";
}

function renderContext(ctx) {
  const target = $("context");
  if (!ctx) {
    target.innerHTML = "";
    return;
  }
  const parts = [];
  if (ctx.weather) {
    parts.push(`<h4>Weather</h4><div>${ctx.weather.now ?? "?"}` +
      (ctx.weather.temperature_f != null ? ` · ${ctx.weather.temperature_f}°F` : "") +
      (ctx.weather.wind ? ` · ${ctx.weather.wind}` : "") + `</div>`);
  }
  if (ctx.alerts?.length) {
    parts.push(`<h4>Alerts</h4><ul>` +
      ctx.alerts.map(a =>
        `<li class="alert">${a.event ?? ""} — ${a.headline ?? ""}</li>`,
      ).join("") + `</ul>`);
  }
  if (ctx.quakes?.length) {
    parts.push(`<h4>Earthquakes (7d)</h4><ul>` +
      ctx.quakes.slice(0, 5).map(q =>
        `<li>M${(q.mag ?? "?")} · ${q.place ?? ""}</li>`,
      ).join("") + `</ul>`);
  }
  if (ctx.fires?.length) {
    parts.push(`<h4>Active fires</h4><div>${ctx.fires.length} detections nearby</div>`);
  }
  if (ctx.air_quality?.length) {
    parts.push(`<h4>Air-quality stations</h4><ul>` +
      ctx.air_quality.slice(0, 4).map(a =>
        `<li>${a.name ?? a.id} · ${(a.sensors || []).join(", ")}</li>`,
      ).join("") + `</ul>`);
  }
  if (ctx.metars?.length) {
    parts.push(`<h4>METAR</h4><ul>` +
      ctx.metars.slice(0, 3).map(m =>
        `<li>${m.station} · ${m.flight_category ?? ""} · ${m.raw ?? ""}</li>`,
      ).join("") + `</ul>`);
  }
  if (ctx.transit_alerts?.length) {
    parts.push(`<h4>SEPTA alerts</h4><ul>` +
      ctx.transit_alerts.slice(0, 5).map(a =>
        `<li><b>${a.route_name ?? a.route_id ?? ""}</b>: ${a.current_message ?? a.advisory_message ?? a.detour_message ?? ""}</li>`,
      ).join("") + `</ul>`);
  }
  if (ctx.service_requests?.length) {
    const counts = {};
    for (const s of ctx.service_requests) {
      counts[s.service_name] = (counts[s.service_name] ?? 0) + 1;
    }
    const top = Object.entries(counts).sort((a, b) => b[1] - a[1]).slice(0, 5);
    parts.push(`<h4>Philly 311 (last 7d)</h4>` +
      `<div>${ctx.service_requests.length} recent · ` +
      top.map(([k, n]) => `${k}: ${n}`).join(" · ") + `</div>`);
  }
  if (ctx.water_gauges?.length) {
    parts.push(`<h4>USGS water gauges</h4><ul>` +
      ctx.water_gauges.slice(0, 4).map(g => {
        const d = g.measurements?.["00060"];
        const h = g.measurements?.["00065"];
        const bits = [];
        if (d?.value != null) bits.push(`${d.value} cfs`);
        if (h?.value != null) bits.push(`${h.value} ft`);
        return `<li>${g.name ?? g.site_code} — ${bits.join(", ")}</li>`;
      }).join("") + `</ul>`);
  }
  if (ctx.wikipedia?.length) {
    parts.push(`<h4>Nearby (Wikipedia)</h4><ul>` +
      ctx.wikipedia.slice(0, 6).map(w =>
        `<li><a href="${w.url}" target="_blank" rel="noopener">${w.title}</a> (${w.distance_m}m)</li>`,
      ).join("") + `</ul>`);
  }
  target.innerHTML = parts.join("");
}

function renderWhatsHere(payload) {
  const target = $("whats-here");
  if (!payload) { target.hidden = true; target.innerHTML = ""; return; }
  const { lat, lon } = payload.query;
  const cams = payload.cameras?.results ?? [];
  const ctx = payload.context;
  const panos = payload.photospheres ?? [];
  const parts = [
    `<h4>What's here? (${lat.toFixed(4)}, ${lon.toFixed(4)})</h4>`,
    `<div>${cams.length} cameras · ${panos.length} panos</div>`,
  ];
  if (cams.length) {
    parts.push(`<ul>` + cams.slice(0, 5).map(c =>
      `<li>${c.source}: ${c.name ?? c.id}</li>`).join("") + `</ul>`);
  }
  if (ctx?.weather?.now) {
    parts.push(`<div>Weather: ${ctx.weather.now}</div>`);
  }
  target.innerHTML = parts.join("");
  target.hidden = false;
}

function wireLayerToggles({ cameras, aircraft, satellites, transit, gibs }) {
  document.querySelectorAll('input[type="checkbox"][data-layer]').forEach((el) => {
    el.addEventListener("change", async () => {
      const key = el.dataset.layer;
      const on = el.checked;
      switch (key) {
        case "cameras":
          cameras.setVisible(on);
          break;
        case "aircraft":
          aircraft.setVisible(on);
          break;
        case "transit":
          if (on) {
            try {
              setStatus("loading SEPTA…", "warn");
              await transit.start();
              transit.setVisible(true);
              setStatus(`SEPTA: ${transit.count()} vehicles`, "ok");
              dbg("main.js:layers", "transit enabled",
                  { count: transit.count() }, "philly");
            } catch (e) {
              console.error(e);
              setStatus("SEPTA load failed", "error");
            }
          } else {
            transit.stop();
            transit.setVisible(false);
          }
          break;
        case "satellites":
          if (on) {
            try {
              setStatus("loading satellites…", "warn");
              await satellites.load("stations");
              satellites.start();
              satellites.setVisible(true);
              setStatus(`satellites: ${satellites.count()}`, "ok");
              dbg("main.js:layers", "satellites enabled",
                  { count: satellites.count() }, "H5");
            } catch (e) {
              console.error(e);
              dbg("main.js:layers", "satellite load failed",
                  { error: String(e) }, "H5");
              setStatus("satellite load failed", "error");
            }
          } else {
            satellites.stop();
            satellites.setVisible(false);
          }
          break;
        case "gibs-truecolor":
        case "gibs-fires":
        case "gibs-aerosol":
          { const k = key.replace("gibs-", "");
            try {
              gibs.setEnabled(k, on);
              dbg("main.js:layers", `gibs toggled ${k}`,
                  { on, enabled: gibs.isEnabled(k) }, "H5");
            } catch (e) {
              dbg("main.js:layers", `gibs failed ${k}`,
                  { error: String(e) }, "H5");
            }
          }
          break;
      }
    });
  });
}

function wireWhatsHereClick(viewer) {
  const handler = new Cesium.ScreenSpaceEventHandler(viewer.scene.canvas);
  handler.setInputAction(async (movement) => {
    const pickedEntity = viewer.scene.pick(movement.position);
    // #region agent log
    dbg("main.js:click", "globe clicked", {
      pickedEntityKind: pickedEntity?.id?.constructor?.name ?? null,
      pickedEntityName: pickedEntity?.id?.name ?? null,
      hasDescription: !!pickedEntity?.id?.description,
    }, "H1");
    // #endregion
    const ray = viewer.camera.getPickRay(movement.position);
    if (!ray) return;
    const cart = viewer.scene.globe.pick(ray, viewer.scene);
    if (!cart) return;
    const carto = Cesium.Cartographic.fromCartesian(cart);
    const lat = Cesium.Math.toDegrees(carto.latitude);
    const lon = Cesium.Math.toDegrees(carto.longitude);
    try {
      const payload = await whatsHere(lat, lon, 1.0);
      renderWhatsHere(payload);
    } catch (e) {
      console.error("whats_here failed", e);
    }
  }, Cesium.ScreenSpaceEventType.LEFT_CLICK);
}

async function bootstrap() {
  const viewer = createViewer("cesium-container");
  // #region agent log
  dbg("main.js:bootstrap", "viewer created", {
    infoBox: !!viewer.infoBox,
    selectionIndicator: !!viewer.selectionIndicator,
    imageryLayerCount: viewer.imageryLayers.length,
    imageryProvider: viewer.imageryLayers.get(0)?.imageryProvider?.constructor?.name ?? null,
    terrainProvider: viewer.terrainProvider?.constructor?.name ?? null,
    cesiumVersion: Cesium.VERSION,
  }, "H1+H3");
  // #endregion
  const cameras = new CameraLayer(viewer);
  const aircraft = new AircraftLayer(viewer);
  const satellites = new SatelliteLayer(viewer);
  satellites.setVisible(false);
  const transit = new TransitLayer(viewer);
  const gibs = new GibsLayers(viewer);

  try {
    await health();
    setStatus("backend ok", "ok");
  } catch {
    setStatus("backend unreachable", "error");
  }

  const live = new LiveSocket({
    url: liveUrl("/ws/live"),
    subscription: {
      lat: parseFloat($("lat").value),
      lon: parseFloat($("lon").value),
      distance_nm: 250,
    },
    onMessage: (frame) => {
      if (frame.type === "aircraft") aircraft.handleFrame(frame);
    },
    onStatus: (s) => {
      const map = { connecting: "live: connecting", open: "live: streaming",
                    closed: "live: reconnecting", error: "live: error" };
      const kindMap = { open: "ok", connecting: "warn", closed: "warn", error: "error" };
      setStatus(map[s] ?? s, kindMap[s] ?? "");
    },
  });
  live.connect();

  const photosphere = new PhotosphereTransition(viewer);
  photosphere.start();

  wireLayerToggles({ cameras, aircraft, satellites, transit, gibs });
  wireWhatsHereClick(viewer);

  async function scan() {
    const lat = parseFloat($("lat").value);
    const lon = parseFloat($("lon").value);
    const radius = parseFloat($("radius").value);
    flyTo(viewer, lat, lon, Math.max(15000, radius * 2000));
    setStatus("scanning…", "warn");
    try {
      const [d, c] = await Promise.all([
        discover(lat, lon, radius),
        context(lat, lon),
      ]);
      cameras.setAll(d.results);
      renderCounts(d);
      renderContext(c);
      // #region agent log
      dbg("main.js:scan", "scan response", {
        query: { lat, lon, radius },
        cameras_total: d.results?.length ?? 0,
        counts_by_source: d.counts_by_source ?? {},
        context_keys_with_data: Object.fromEntries(
          Object.entries(c || {}).map(([k, v]) => [
            k, Array.isArray(v) ? v.length : (v ? 1 : 0)
          ])
        ),
      }, "H2");
      // #endregion
      live.setSubscription({ lat, lon, distance_nm: Math.max(50, radius * 2) });
      setStatus(`live: streaming · ${d.results.length} cameras`, "ok");
    } catch (e) {
      console.error(e);
      setStatus("scan failed", "error");
    }
  }

  $("go").addEventListener("click", scan);
  scan();
}

bootstrap().catch((e) => {
  console.error(e);
  setStatus("boot failed", "error");
});
