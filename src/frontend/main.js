/** GRIDLAND frontend entry point. */
import * as Cesium from "cesium";
import {
  createViewer,
  flyTo,
  flyToPreset,
  heightForScanRadius,
} from "./cesium/viewer.js";
import { CameraLayer } from "./entities/cameras.js";
import { AircraftLayer } from "./entities/aircraft.js";
import { SatelliteLayer } from "./entities/satellites.js";
import { TransitLayer } from "./entities/transit.js";
import { SeptaMetroLayer } from "./entities/septa-metro.js";
import { IndegoLayer } from "./entities/indego.js";
import { ContextPoiLayer } from "./entities/context-pois.js";
import { ContextLivePoiLayer } from "./entities/context-live-pois.js";
import { GibsLayers } from "./cesium/gibs.js";
import { discover, context, health, whatsHere } from "./api.js";
import { LiveSocket, liveUrl } from "./ws.js";
import { PhotosphereTransition } from "./photosphere/transition.js";
import { EntityDetailPanel } from "./entities/entity-detail.js";
import { applyEntitySelection } from "./entities/entity-selection.js";
import { readEntityData } from "./entities/entity-data.js";
import { ViewportSubscriptionManager, isPhillyArea } from "./viewport.js";
import { LiveTickScheduler } from "./live-scheduler.js";
import { LAYER_LEGEND } from "./entities/layer-glyphs.js";
import { iconDataUrl } from "./entities/layer-icons.js";

const $ = (id) => document.getElementById(id);

function renderLayerLegend() {
  const el = $("layer-legend");
  if (!el) return;
  el.innerHTML = LAYER_LEGEND.map((row) => {
    const src = iconDataUrl(row.icon, row.color, { badge: row.badge });
    return `<div class="layer-legend-item">` +
      `<img src="${src}" alt="" width="18" height="18" />` +
      `<span>${row.label}</span></div>`;
  }).join("");
}

function wireHudToggle() {
  const hud = $("hud");
  const btn = $("hud-toggle");
  if (!hud || !btn) return;
  btn.addEventListener("click", () => {
    const collapsed = hud.classList.toggle("hud--collapsed");
    btn.textContent = collapsed ? "+" : "−";
    btn.setAttribute("aria-expanded", collapsed ? "false" : "true");
    btn.title = collapsed ? "Expand controls" : "Minimize controls";
  });
}

async function enablePhillyLayers(transit, indego, septaMetro) {
  const lat = parseFloat($("lat").value);
  const lon = parseFloat($("lon").value);
  const radius = parseFloat($("radius").value);
  if (!isPhillyArea(lat, lon)) return;
  setLayerCheckbox("transit", true);
  setLayerCheckbox("septa-metro", true);
  setLayerCheckbox("indego", true);
  try {
    await transit.start();
    transit.setVisible(true);
    await indego.start(lat, lon, Math.min(radius, 15));
    indego.setVisible(true);
    await septaMetro.refresh(lat, lon, Math.min(radius, 25));
    septaMetro.setVisible(true);
  } catch (e) {
    console.warn("Philly layers", e);
  }
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

function updateLiveHud(transit, aircraft, indego, septaMetro) {
  const parts = ["live"];
  if (septaMetro?.dataSource?.show) {
    parts.push(`Metro ${septaMetro.count()}`);
  }
  if (transit.dataSource.show) {
    const src = transit.sourceStatus();
    const { bus, rail } = transit.countByKind();
    const tv = src.transitview === "ok" ? "" : ` tv:${src.transitview || "?"}`;
    const tr = src.trainview === "ok" ? "" : ` rail-api:${src.trainview || "?"}`;
    const counts = rail > 0 ? `${bus} buses · ${rail} rail` : `${transit.count()}`;
    parts.push(`SEPTA ${counts}${tv}${tr}`);
  }
  parts.push(`aircraft ${aircraft.count()}`);
  if (indego.dataSource.show) parts.push(`Indego ${indego.count()}`);
  setStatus(parts.join(" · "), "ok");
}

function renderMapStackNote(mapStack) {
  const el = $("map-stack");
  if (!el) return;
  const terrain = mapStack?.terrain === "cesium-world-terrain";
  const buildings = mapStack?.buildings3d === "cesium-osm-buildings";
  if (terrain && buildings) {
    el.className = "map-stack-note ok";
    el.innerHTML =
      "<strong>3D map active</strong> — Cesium World Terrain + OSM 3D Buildings. " +
      "Street view is Mapillary panoramas (not Google); use the chip at low altitude.";
    return;
  }
  el.className = "map-stack-note";
  el.innerHTML =
    "<strong>2D basemap only</strong> — flat terrain, no building meshes. " +
    "Add <code>VITE_CESIUM_ION_ACCESS_TOKEN</code> to <code>.env</code> " +
    "(free at <a href=\"https://ion.cesium.com/\" target=\"_blank\" rel=\"noopener\">cesium.com/ion</a>) " +
    "and restart <code>npm run dev</code>. " +
    "Live layers (cameras, transit, aircraft) still work; street view uses Mapillary when enabled.";
}

function renderCounts(resp) {
  const counts = resp?.counts_by_source ?? {};
  const sources = resp?.sources ?? {};
  const items = Object.entries(counts).map(([src, n]) => {
    const st = sources[src];
    const flag = st?.status && st.status !== "ok" ? ` (${st.status})` : "";
    return `<span>${src}: ${n}${flag}</span>`;
  });
  for (const [src, st] of Object.entries(sources)) {
    if (counts[src] != null) continue;
    if (st?.status === "error") {
      items.push(`<span class="warn">${src}: error</span>`);
    }
  }
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
  if (ctx.errors && Object.keys(ctx.errors).length) {
    parts.push(`<h4 class="warn">Context source errors</h4><ul>` +
      Object.entries(ctx.errors).map(([k, v]) =>
        `<li>${k}: ${v}</li>`).join("") + `</ul>`);
  }
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
    parts.push(`<h4>Indego (context snapshot)</h4><div>${ctx.indego_stations.length} stations · ${bikes} bikes (use Indego layer for live)</div>`);
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
    if (odp.errors && Object.keys(odp.errors).length) {
      parts.push(`<h4 class="warn">OpenDataPhilly errors</h4><ul>` +
        Object.entries(odp.errors).map(([k, v]) => `<li>${k}: ${v}</li>`).join("") +
        `</ul>`);
    }
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
  if (payload.errors && Object.keys(payload.errors).length) {
    parts.push(`<ul class="warn">` +
      Object.entries(payload.errors).map(([k, v]) => `<li>${k}: ${v}</li>`).join("") +
      `</ul>`);
  }
  if (cams.length) {
    parts.push(`<ul>` + cams.slice(0, 5).map(c =>
      `<li>${c.source}: ${c.label ?? c.id}</li>`).join("") + `</ul>`);
  }
  if (ctx?.weather?.now) {
    parts.push(`<div>Weather: ${ctx.weather.now}</div>`);
  }
  target.innerHTML = parts.join("");
  target.hidden = false;
}

function wireLayerToggles({
  cameras, aircraft, satellites, transit, septaMetro, indego, contextPois,
  contextLivePois, gibs, photosphere, onSatelliteGroup,
}) {
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
            } catch (e) {
              console.error(e);
              setStatus("SEPTA load failed", "error");
            }
          } else {
            transit.stop();
            transit.setVisible(false);
          }
          break;
        case "septa-metro":
          if (on) {
            try {
              const lat = parseFloat($("lat").value);
              const lon = parseFloat($("lon").value);
              const radius = parseFloat($("radius").value);
              setStatus("loading SEPTA Metro…", "warn");
              await septaMetro.refresh(lat, lon, Math.min(radius, 25));
              septaMetro.setVisible(true);
              setStatus(`Metro MFL/BSL: ${septaMetro.count()} pins`, "ok");
            } catch (e) {
              console.error(e);
              setStatus("SEPTA Metro load failed", "error");
            }
          } else {
            septaMetro.setVisible(false);
          }
          break;
        case "context-pois":
          contextPois.setVisible(on);
          break;
        case "context-live-pois":
          contextLivePois.setVisible(on);
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
        case "photosphere":
          photosphere.setEnabled(on);
          if (on) photosphere.start();
          else photosphere.stop();
          break;
        case "satellites":
          if (on) {
            try {
              setStatus("loading satellites…", "warn");
              const group = onSatelliteGroup?.() ?? "stations";
              await satellites.load(group);
              satellites.start();
              satellites.setVisible(true);
              setStatus(`satellites: ${satellites.count()}`, "ok");
            } catch (e) {
              console.error(e);
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
            } catch (e) {
              console.error(e);
            }
          }
          break;
      }
    });
  });
}

function wireEntitySelection(viewer, ctx) {
  viewer.selectedEntityChanged.addEventListener(() => {
    const ent = viewer.selectedEntity;
    if (!ent) {
      ctx.entityDetail?.hide?.();
      return;
    }
    applyEntitySelection(ent, { viewer, ...ctx });
  });
}

function wireWhatsHereClick(viewer) {
  const handler = new Cesium.ScreenSpaceEventHandler(viewer.scene.canvas);
  handler.setInputAction(async (movement) => {
    const picked = viewer.scene.pick(movement.position);
    if (picked?.id instanceof Cesium.Entity) {
      viewer.selectedEntity = picked.id;
      applyEntitySelection(picked.id, viewer._gridlandSelectionCtx);
      return;
    }
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
  renderMapStackNote(mapStack);
  if (mapStack.buildings3d === "none") {
    setStatus("map: OSM 2D · add VITE_CESIUM_ION_ACCESS_TOKEN for 3D", "warn");
  } else {
    setStatus("map: 3D terrain + buildings", "ok");
  }
  const cameras = new CameraLayer(viewer);
  const aircraft = new AircraftLayer(viewer);
  const satellites = new SatelliteLayer(viewer);
  satellites.setVisible(false);
  const transit = new TransitLayer(viewer);
  const septaMetro = new SeptaMetroLayer(viewer);
  const indego = new IndegoLayer(viewer);
  const contextPois = new ContextPoiLayer(viewer);
  const contextLivePois = new ContextLivePoiLayer(viewer);
  const gibs = new GibsLayers(viewer);

  try {
    await health();
    setStatus("backend ok", "ok");
  } catch {
    setStatus("backend unreachable", "error");
  }

  let lastContext = null;

  const live = new LiveSocket({
    url: liveUrl("/ws/live"),
    subscription: {
      lat: parseFloat($("lat").value),
      lon: parseFloat($("lon").value),
      distance_nm: 250,
      transit: isPhillyArea(parseFloat($("lat").value), parseFloat($("lon").value)),
    },
    onMessage: (frame) => {
      if (frame.type === "aircraft") {
        aircraft.handleFrame(frame);
      } else if (frame.type === "transit") {
        transit.handleFrame(frame);
      }
    },
    onStatus: (s) => {
      const map = { connecting: "live: connecting", open: "live: streaming",
                    closed: "live: reconnecting", error: "live: error" };
      const kindMap = { open: "ok", connecting: "warn", closed: "warn", error: "error" };
      if (s === "open") {
        updateLiveHud(transit, aircraft, indego, septaMetro);
      } else {
        setStatus(map[s] ?? s, kindMap[s] ?? "");
      }
    },
  });
  live.connect();

  const photosphere = new PhotosphereTransition(viewer);
  photosphere.start();
  const entityDetail = new EntityDetailPanel("entity-popup");
  entityDetail.attachViewer(viewer);
  const selectionCtx = {
    entityDetail, transit, aircraft, indego, cameras, septaMetro, viewport: null,
    cameraFeedHooks: {},
    onSelectCameraId(cameraEntityId) {
      const ent = cameras.collection.entities.getById(cameraEntityId);
      if (!ent) return;
      viewer.selectedEntity = ent;
      applyEntitySelection(ent, viewer._gridlandSelectionCtx);
    },
  };
  viewer._gridlandSelectionCtx = { viewer, ...selectionCtx };

  const scheduler = new LiveTickScheduler({
    onTick: async () => {
      if (transit.dataSource.show && transit._enabled) {
        await transit.refresh();
      }
      if (indego.dataSource.show && indego._enabled) {
        await indego.refresh();
      }
      if (septaMetro.dataSource.show) {
        const lat = parseFloat($("lat").value);
        const lon = parseFloat($("lon").value);
        const radius = parseFloat($("radius").value);
        await septaMetro.refresh(lat, lon, Math.min(radius, 25));
      }
      updateLiveHud(transit, aircraft, indego, septaMetro);
      viewer.scene.requestRender();
    },
  });
  scheduler.start();

  const viewport = new ViewportSubscriptionManager(viewer, (vp) => {
    const sub = viewport.subscriptionPayload(vp);
    if (sub) live.setSubscription(sub);
    transit.setBbox(vp.bbox);
    if (indego._enabled) {
      indego.setViewport(vp.lat, vp.lon, Math.min(vp.radiusKm, 15), vp.bbox);
    }
    if (vp.philly) {
      if (transit.dataSource.show && !transit._enabled) void transit.start();
      if (indego.dataSource.show && !indego._enabled) {
        void indego.start(vp.lat, vp.lon, Math.min(vp.radiusKm, 15));
      }
    } else if (transit.dataSource.show || indego.dataSource.show) {
      setStatus("live layers: outside Philly — SEPTA/Indego paused", "warn");
    }
    updateLiveHud(transit, aircraft, indego, septaMetro);
  });

  selectionCtx.viewport = viewport;
  viewer._gridlandSelectionCtx = { viewer, ...selectionCtx };

  wireLayerToggles({
    cameras, aircraft, satellites, transit, septaMetro, indego, contextPois,
    contextLivePois, gibs, photosphere,
    onSatelliteGroup: () => $("sat-group")?.value || "stations",
  });
  wireEntitySelection(viewer, selectionCtx);
  wireWhatsHereClick(viewer);
  wireHudToggle();
  renderLayerLegend();
  void enablePhillyLayers(transit, indego, septaMetro);

  if (import.meta.env.DEV) {
    window.__gridlandTest = {
      viewer,
      selectionCtx,
      async runWhatsHere(lat, lon, radiusKm = 1) {
        const payload = await whatsHere(lat, lon, radiusKm);
        renderWhatsHere(payload);
        return payload;
      },
      selectFirstEntity(dataSourceName) {
        for (let i = 0; i < viewer.dataSources.length; i++) {
          const ds = viewer.dataSources.get(i);
          if (ds.name !== dataSourceName) continue;
          const vals = ds.entities.values;
          if (!vals.length) return null;
          const ent = vals[0];
          viewer.selectedEntity = ent;
          applyEntitySelection(ent, { viewer, ...selectionCtx });
          const data = readEntityData(ent);
          return {
            id: ent.id,
            name: ent.name,
            data,
            panelHidden: document.getElementById("entity-popup")?.hidden ?? true,
            panelText: document.getElementById("entity-popup")?.textContent?.slice(0, 200),
          };
        }
        return null;
      },
    };
  }

  function flyQuery(preset) {
    const lat = parseFloat($("lat").value);
    const lon = parseFloat($("lon").value);
    if (preset) {
      flyToPreset(viewer, lat, lon, preset, () => viewport.refresh());
    } else {
      const h = heightForScanRadius(parseFloat($("radius").value));
      flyTo(viewer, lat, lon, h, () => viewport.refresh());
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
      lastContext = c;
      cameras.setAll(d.results);
      contextPois.setFromContext(c);
      contextLivePois.setFromContext(c);
      contextPois.setVisible(true);
      setLayerCheckbox("context-pois", true);
      renderCounts(d);
      renderContext(c);
      if (d.results?.length && radius <= 8) {
        cameras.flyToResults(viewer, { duration: 1.0 });
      }
      const sub = {
        lat, lon,
        distance_nm: Math.max(250, radius * 2),
        transit: isPhillyArea(lat, lon),
      };
      live.setSubscription(sub);
      if (isPhillyArea(lat, lon)) {
        setLayerCheckbox("transit", true);
        setLayerCheckbox("indego", true);
        setLayerCheckbox("septa-metro", true);
        try {
          await transit.start();
          transit.setVisible(true);
          await indego.start(lat, lon, Math.min(radius, 15));
          indego.setVisible(true);
          await septaMetro.refresh(lat, lon, Math.min(radius, 25));
          septaMetro.setVisible(true);
        } catch (e) {
          console.warn("Philly live layers", e);
        }
      }
      viewport.refresh();
      const poiN = contextPois.count();
      setStatus(
        `scan ok · ${d.results.length} cameras · ${poiN} pins` +
        (isPhillyArea(lat, lon)
          ? ` · SEPTA ${transit.count()} · Metro ${septaMetro.count()} · Indego ${indego.count()}`
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
