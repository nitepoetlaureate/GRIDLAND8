/** GRIDLAND frontend entry point. */
import { createViewer, flyTo } from "./cesium/viewer.js";
import { CameraLayer } from "./entities/cameras.js";
import { AircraftLayer } from "./entities/aircraft.js";
import { discover, context, health } from "./api.js";
import { LiveSocket, liveUrl } from "./ws.js";
import { PhotosphereTransition } from "./photosphere/transition.js";

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
  if (ctx.wikipedia?.length) {
    parts.push(`<h4>Nearby</h4><ul>` +
      ctx.wikipedia.slice(0, 6).map(w =>
        `<li><a href="${w.url}" target="_blank" rel="noopener">${w.title}</a> (${w.distance_m}m)</li>`,
      ).join("") + `</ul>`);
  }
  target.innerHTML = parts.join("");
}

async function bootstrap() {
  const viewer = createViewer("cesium-container");
  const cameras = new CameraLayer(viewer);
  const aircraft = new AircraftLayer(viewer);

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
