/** HUD panel for selected map entity — all live layers route here. */
import { resolveCameraFeedUrl } from "./camera-feed.js";
import { readEntityDescriptionHtml } from "./entity-data.js";
import { metroCameraListHtml, metroDetailRows } from "./entity-detail-metro.js";
import { metroLineBadge } from "./septa-colors.js";
import { aircraftDetailRows } from "./aircraft-detail-rows.js";
import { transitDetailRows } from "./entity-detail-rows.js";

function esc(s) {
  return String(s ?? "").replace(/[&<>"']/g, (c) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  })[c]);
}

function tableHtml(rows) {
  if (!rows.length) {
    return `<p class="entity-detail-empty">No detail fields for this pin.</p>`;
  }
  const body = rows
    .map(([k, v]) =>
      `<tr><td style="padding-right:8px;color:#8b95a6;white-space:nowrap">${esc(k)}</td>` +
      `<td>${esc(v)}</td></tr>`)
    .join("");
  return `<table class="entity-detail-table">${body}</table>`;
}

function reveal(el) {
  if (!el) return;
  el.hidden = false;
}

export class EntityDetailPanel {
  constructor(rootId = "entity-popup") {
    this.el = document.getElementById(rootId);
    if (!this.el) {
      this.el = document.createElement("div");
      this.el.id = rootId;
      this.el.className = "entity-popup";
      this.el.hidden = true;
      document.body.appendChild(this.el);
    }
    this._feedTimer = null;
    this._feedUrl = null;
  }

  hide() {
    this._stopFeedRefresh();
    if (!this.el) return;
    this.el.hidden = true;
    this.el.innerHTML = "";
  }

  _render(title, bodyHtml, meta = "") {
    if (!this.el) return;
    this.el.innerHTML =
      `<button type="button" class="entity-popup-close" aria-label="Close">×</button>` +
      `<h4 class="entity-popup-title">${esc(title)}</h4>` +
      bodyHtml +
      (meta ? `<p class="entity-popup-meta">${meta}</p>` : "");
    this.el.querySelector(".entity-popup-close")?.addEventListener("click", () => {
      this.hide();
      if (this._viewer) this._viewer.selectedEntity = undefined;
    });
    reveal(this.el);
  }

  attachViewer(viewer) {
    this._viewer = viewer;
  }

  showTransit(v) {
    if (!this.el || !v) return;
    const isRail = v.kind === "regional_rail";
    const icon = isRail ? "🚆" : "🚌";
    const title = `${icon} ${v.route || "SEPTA"}${v.destination ? ` → ${v.destination}` : ""}`;
    const link = isRail
      ? "https://www3.septa.org/api/TrainView/index.php"
      : "https://www3.septa.org/hackathon/TransitViewAll/";
    this._render(
      title,
      tableHtml(transitDetailRows(v)),
      `Live SEPTA · <a href="${link}" target="_blank" rel="noopener">API</a>`,
    );
  }

  showAircraft(ac) {
    if (!this.el || !ac) return;
    const title = ac.type_desc || ac.callsign?.trim() || ac.icao24?.toUpperCase?.() || "Aircraft";
    const meta = "Live ADS-B · adsb.fi — route airports need flight-plan API (see docs/TODO.md)";
    const note = (!ac.origin_airport && !ac.destination_airport)
      ? `<p class="entity-detail-empty">Origin/destination airports are not in the ADS-B feed. FlightRadar or similar route API is optional; see <code>docs/TODO.md</code>.</p>`
      : "";
    this._render(title, tableHtml(aircraftDetailRows(ac)) + note, meta);
  }

  showCamera(cam, hooks = {}) {
    if (!this.el || !cam) return;
    void this._showCameraAsync(cam, hooks);
  }

  async _showCameraAsync(cam, hooks) {
    const label = cam.label || cam.name || cam.id || "Camera";
    const rows = [
      ["Source", cam.source || "—"],
      ["Status", cam.publication_status || "—"],
      ["Coordinates", `${Number(cam.lat).toFixed(5)}, ${Number(cam.lon).toFixed(5)}`],
    ];
    if (cam.operator) rows.push(["Operator", cam.operator]);
    if (cam.tags && typeof cam.tags === "object") {
      for (const [k, v] of Object.entries(cam.tags).slice(0, 12)) {
        rows.push([k, String(v)]);
      }
    }

    const pageUrl = cam.url || "";
    const penndotPage = cam.source === "penndot" && pageUrl;
    let extra = `<div class="feed-hint" id="entity-detail-feed-status">Loading feed…</div>`;
    this._render(label, tableHtml(rows) + extra, esc(cam.source));

    const imgUrl = await resolveCameraFeedUrl(cam, hooks);
    const statusEl = document.getElementById("entity-detail-feed-status");
    if (imgUrl) {
      if (statusEl) statusEl.remove();
      const frame = document.createElement("div");
      frame.className = "feed-frame";
      frame.innerHTML = `<img id="entity-detail-feed-img" src="${esc(imgUrl)}" alt="live feed" />`;
      this.el.appendChild(frame);
      const hint = document.createElement("div");
      hint.className = "feed-hint";
      hint.textContent = "Live feed · refreshes every 8s when supported.";
      this.el.appendChild(hint);
      this._feedUrl = imgUrl;
      this._startFeedRefresh();
    } else {
      this._stopFeedRefresh();
      if (statusEl) {
        if (penndotPage) {
          statusEl.innerHTML =
            "No proxied JPEG yet — <code>N511PA_API_KEY</code> unlocks PennDOT stills. Preview page below.";
        } else {
          statusEl.textContent =
            "No public still-image URL for this pin — location metadata only.";
        }
      }
      if (penndotPage) {
        const frame = document.createElement("div");
        frame.className = "feed-frame feed-frame--page";
        frame.innerHTML =
          `<iframe src="${esc(pageUrl)}" title="511PA camera" loading="lazy"></iframe>`;
        this.el.appendChild(frame);
      }
    }
    if (pageUrl) {
      const link = document.createElement("div");
      link.innerHTML =
        `<a href="${esc(pageUrl)}" target="_blank" rel="noopener">Open operator page →</a>`;
      this.el.appendChild(link);
    }
    reveal(this.el);
  }

  showMetro(item, bundle, hooks = {}) {
    if (!this.el || !item) return;
    const badge = metroLineBadge(item.line);
    const title = item.kind === "metro_station"
      ? `${badge} ${item.name}`
      : `${badge} ${item.line} → ${item.destination || item.route || "run"}`;
    const rows = metroDetailRows(item, bundle);
    const camHtml = metroCameraListHtml(item.nearby_cameras);
    this._render(title, tableHtml(rows) + camHtml,
      "SEPTA Metro API · † = schedule-only position");
    this._wireMetroCameraLinks(hooks);
  }

  _wireMetroCameraLinks(hooks) {
    if (!this.el) return;
    this.el.querySelectorAll(".metro-cam-link").forEach((btn) => {
      btn.addEventListener("click", () => {
        const id = btn.getAttribute("data-camera-id");
        if (id && hooks.onSelectCameraId) hooks.onSelectCameraId(id);
      });
    });
  }

  showIndego(s) {
    if (!this.el || !s) return;
    const rows = [
      ["Station", s.name || "—"],
      ["Station ID", s.station_id || "—"],
      ["Bikes available", s.bikes ?? "—"],
      ["Docks available", s.docks ?? "—"],
      ["Renting", s.is_renting ? "yes" : "no"],
      ["Returning", s.is_returning ? "yes" : "no"],
      ["Position", `${Number(s.lat).toFixed(5)}, ${Number(s.lon).toFixed(5)}`],
    ];
    this._render(`🚲 ${s.name || "Indego"}`, tableHtml(rows), "Live GBFS · Indego");
  }

  /** Context POIs and anything with an HTML description string. */
  showFromEntity(entity) {
    if (!this.el || !entity) return;
    const html = readEntityDescriptionHtml(entity);
    const title = entity.name || String(entity.id ?? "Map item");
    if (html && html.includes("<table")) {
      this._render(title, html, "");
      return;
    }
    const rows = [["ID", String(entity.id ?? "—")]];
    if (html) rows.push(["Details", html.replace(/<[^>]+>/g, " ").trim().slice(0, 200)]);
    this._render(title, tableHtml(rows), "");
  }

  _startFeedRefresh() {
    this._stopFeedRefresh();
    if (!this._feedUrl) return;
    this._feedTimer = setInterval(() => {
      const img = document.getElementById("entity-detail-feed-img");
      if (!img) return;
      const sep = this._feedUrl.includes("?") ? "&" : "?";
      img.src = `${this._feedUrl}${sep}_t=${Date.now()}`;
    }, 8000);
  }

  _stopFeedRefresh() {
    if (this._feedTimer) {
      clearInterval(this._feedTimer);
      this._feedTimer = null;
    }
    this._feedUrl = null;
  }
}
