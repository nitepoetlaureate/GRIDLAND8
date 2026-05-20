/** GRIDLAND frontend entry point. */
import * as Cesium from "cesium";
import {
  cameraState,
  createViewer,
  flyTo,
  flyToPreset,
  heightForScanRadius,
} from "./cesium/viewer.js";
import { CameraLayer } from "./entities/cameras.js";
import { AircraftLayer } from "./entities/aircraft.js";
import { SatelliteLayer } from "./entities/satellites.js";
import { TransitLayer } from "./entities/transit.js";
import { IndegoLayer } from "./entities/indego.js";
import { ContextPoiLayer } from "./entities/context-pois.js";
import { GibsLayers } from "./cesium/gibs.js";
import { discover, context, health, whatsHere } from "./api.js";
import { LiveSocket, liveUrl } from "./ws.js";
import { PhotosphereTransition } from "./photosphere/transition.js";
import { CameraFeedPanel } from "./entities/camera-feed.js";

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

function isPhillyArea(lat, lon) {
  return lat > 39.86 && lat < 40.14 && lon > -75.28 && lon < -74.95;
}

function setLayerCheckbox(key, on) {
  const el = document.querySelector(`input[data-layer="${key}"]`);
  if (el) el.checked = on;
}

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
  if (ctx.septa_detours?.length) {
    parts.push(`<h4>SEPTA bus detours</h4><ul>` +
      ctx.septa_detours.slice(0, 6).map(d =>
        `<li><b>${d.route_id ?? ""}</b> ${d.direction ?? ""}: ${d.message ?? d.reason ?? ""}</li>`,
      ).join("") + `</ul>`);
  }
  if (ctx.indego_stations?.length) {
    const bikes = ctx.indego_stations.reduce((n, s) => n + (s.bikes ?? 0), 0);
    parts.push(`<h4>Indego (nearby)</h4><div>${ctx.indego_stations.length} stations · ${bikes} bikes available</div>`);
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
  const odp = ctx.opendataphilly?.layers;
  if (odp) {
    if (odp.crime_incidents?.length) {
      parts.push(`<h4>Crime dispatches (7d, ODP)</h4><ul>` +
        odp.crime_incidents.slice(0, 6).map(c =>
          `<li>${c.type ?? ""} · ${c.block ?? ""}</li>`,
        ).join("") + `</ul>`);
    }
    if (odp.shootings?.length) {
      parts.push(`<h4>Shootings (1y, ODP)</h4><div>${odp.shootings.length} in area</div>`);
    }
    if (odp.snow_routes?.length) {
      parts.push(`<h4>Snow emergency routes</h4><div>${odp.snow_routes.length} city routes</div>`);
    }
    if (odp.parks?.length) {
      parts.push(`<h4>Parks (PPR)</h4><ul>` +
        odp.parks.slice(0, 4).map(p =>
          `<li>${p.name ?? ""}${p.address ? ` · ${p.address}` : ""}</li>`,
        ).join("") + `</ul>`);
    }
    if (odp.polling_places?.length) {
      parts.push(`<h4>Polling places</h4><div>${odp.polling_places.length} nearby</div>`);
    }
    if (odp.zoning_overlays?.length) {
      parts.push(`<h4>Zoning overlays</h4><div>${odp.zoning_overlays.length} in area</div>`);
    }
    if (odp.red_light_cameras?.length) {
      parts.push(`<h4>Red-light cameras (PPA)</h4><div>${odp.red_light_cameras.length} citywide sites</div>`);
    }
    if (odp.parcel_count != null && odp.parcel_count > 0) {
      parts.push(`<h4>Parcels in search area</h4><div>${odp.parcel_count} (count only)</div>`);
    }
    const pd = odp.police_district;
    if (pd && typeof pd === "object") {
      parts.push(`<h4>Police district</h4><div>${pd.name ?? ""} (#${pd.district_num ?? "?"})` +
        (pd.phone ? ` · ${pd.phone}` : "") + `</div>`);
    }
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

function wireLayerToggles({ cameras, aircraft, satellites, transit, indego, contextPois, gibs }) {
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
        case "context-pois":
          contextPois.setVisible(on);
          break;
        case "indego":
          if (on) {
            try {
              const lat = parseFloat($("lat").value);
              const lon = parseFloat($("lon").value);
              setStatus("loading Indego…", "warn");
              await indego.start(lat, lon, 15);
              indego.setVisible(true);
              setStatus(`Indego: ${indego.count()} stations`, "ok");
            } catch (e) {
              console.error(e);
              setStatus("Indego load failed", "error");
            }
          } else {
            indego.stop();
            indego.setVisible(false);
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

function wireEntitySelection(viewer, { cameras, cameraFeed, aircraft, transit }) {
  viewer.selectedEntityChanged.addEventListener(() => {
    const ent = viewer.selectedEntity;
    if (!ent) {
      cameraFeed.hide();
      return;
    }
    const id = ent.id ?? "";
    if (typeof id === "string" && id.startsWith("camera:")) {
      const props = ent.properties;
      const cam = props?.getValue
        ? (typeof props.getValue === "function" ? props.getValue(Cesium.JulianDate.now()) : props)
        : props;
      cameraFeed.show(cam);
      dbg("main.js:select", "camera selected", {
        id, source: cam?.source, hasThumb: !!cam?.thumbnail_url,
      }, "H-feed");
      return;
    }
    cameraFeed.hide();
    if (typeof id === "string" && id.startsWith("septa_")) {
      dbg("main.js:select", "transit selected", { id }, "H-motion");
    }
  });

}

function wireWhatsHereClick(viewer) {
  const handler = new Cesium.ScreenSpaceEventHandler(viewer.scene.canvas);
  handler.setInputAction(async (movement) => {
    const pickedEntity = viewer.scene.pick(movement.position);
    if (pickedEntity?.id) {
      viewer.selectedEntity = pickedEntity.id;
      return;
    }
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
  const viewer = await createViewer("cesium-container");
  const mapStack = viewer._gridlandMapStack ?? {};
  // #region agent log
  dbg("main.js:bootstrap", "viewer created", {
    infoBox: !!viewer.infoBox,
    selectionIndicator: !!viewer.selectionIndicator,
    imageryLayerCount: viewer.imageryLayers.length,
    imageryProvider: viewer.imageryLayers.get(0)?.imageryProvider?.constructor?.name ?? null,
    terrainProvider: viewer.terrainProvider?.constructor?.name ?? null,
    mapStack,
    camera: cameraState(viewer),
    cesiumVersion: Cesium.VERSION,
  }, "H1+H3+H6");
  // #endregion
  if (mapStack.buildings3d === "none") {
    setStatus("map: OSM 2D · no 3D buildings (add VITE_CESIUM_ION_ACCESS_TOKEN for terrain+buildings)", "warn");
  }
  const cameras = new CameraLayer(viewer);
  const aircraft = new AircraftLayer(viewer);
  const satellites = new SatelliteLayer(viewer);
  satellites.setVisible(false);
  const transit = new TransitLayer(viewer);
  const indego = new IndegoLayer(viewer);
  const contextPois = new ContextPoiLayer(viewer);
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
      if (frame.type === "aircraft") {
        aircraft.handleFrame(frame);
        if (frame.kind === "snapshot") {
          dbg("main.js:ws", "aircraft snapshot", {
            count: frame.count ?? frame.items?.length ?? 0,
          }, "H-motion");
        }
      }
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
  const cameraFeed = new CameraFeedPanel("camera-feed");

  wireLayerToggles({ cameras, aircraft, satellites, transit, indego, contextPois, gibs });
  wireEntitySelection(viewer, { cameras, cameraFeed, aircraft, transit });
  wireWhatsHereClick(viewer);

  function flyQuery(preset) {
    const lat = parseFloat($("lat").value);
    const lon = parseFloat($("lon").value);
    const done = (info) => {
      dbg("main.js:flyTo", "camera after fly", {
        preset: preset ?? "scan",
        ...info,
        camera: cameraState(viewer),
        mapStack: viewer._gridlandMapStack,
      }, "H6");
    };
    if (preset) {
      flyToPreset(viewer, lat, lon, preset, done);
    } else {
      const h = heightForScanRadius(parseFloat($("radius").value));
      flyTo(viewer, lat, lon, h, done);
    }
  }

  async function scan() {
    const lat = parseFloat($("lat").value);
    const lon = parseFloat($("lon").value);
    const radius = parseFloat($("radius").value);
    flyQuery(null);
    setStatus("scanning…", "warn");
    try {
      const [d, c] = await Promise.all([
        discover(lat, lon, radius),
        context(lat, lon),
      ]);
      cameras.setAll(d.results);
      contextPois.setFromContext(c);
      contextPois.setVisible(true);
      setLayerCheckbox("context-pois", true);
      renderCounts(d);
      renderContext(c);
      if (d.results?.length && radius <= 8) {
        cameras.flyToResults(viewer, { duration: 1.0 });
      }
      live.setSubscription({ lat, lon, distance_nm: Math.max(50, radius * 2) });
      if (isPhillyArea(lat, lon)) {
        setLayerCheckbox("transit", true);
        setLayerCheckbox("indego", true);
        try {
          await transit.start();
          transit.setVisible(true);
          await transit.refresh();
          await indego.start(lat, lon, Math.min(radius, 15));
          indego.setVisible(true);
        } catch (e) {
          console.warn("Philly live layers", e);
        }
      }
      // #region agent log
      dbg("main.js:scan", "scan response", {
        query: { lat, lon, radius },
        cameras_total: d.results?.length ?? 0,
        context_pois: contextPois.count(),
        counts_by_source: d.counts_by_source ?? {},
        philly_auto_layers: isPhillyArea(lat, lon),
        context_keys_with_data: Object.fromEntries(
          Object.entries(c || {}).map(([k, v]) => [
            k, Array.isArray(v) ? v.length : (v ? 1 : 0)
          ])
        ),
      }, "H2");
      // #endregion
      const poiN = contextPois.count();
      const indegoN = (c.indego_stations || []).length;
      setStatus(
        `scan ok · ${d.results.length} cameras · ${poiN} pins` +
        (isPhillyArea(lat, lon)
          ? ` · SEPTA ${transit.count()} · Indego ${indegoN || indego.count()}`
          : "") +
        ` · aircraft streaming`,
        "ok",
      );
    } catch (e) {
      console.error(e);
      setStatus("scan failed", "error");
    }
  }

  $("go").addEventListener("click", scan);
  for (const btn of document.querySelectorAll("[data-view]")) {
    btn.addEventListener("click", () => flyQuery(btn.dataset.view));
  }
  scan();
}

bootstrap().catch((e) => {
  console.error(e);
  setStatus("boot failed", "error");
});
