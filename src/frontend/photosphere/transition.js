/** Mapillary street view — opt-in docked panel (not fullscreen auto-hijack).
 *
 * When the camera is near ground level and a pano exists nearby, a small
 * entry chip appears. Opening shows Photo Sphere Viewer in a bottom dock
 * so the globe stays visible above. ESC / toolbar exits; cooldown prevents
 * immediate re-open loops.
 */
import * as Cesium from "cesium";
import { Viewer } from "@photo-sphere-viewer/core";
import "@photo-sphere-viewer/core/index.css";

const NEAR_GROUND_ALT_M = 400;
const PROMPT_ALT_M = 200;
const CHECK_INTERVAL_MS = 2000;
const EXIT_COOLDOWN_MS = 6000;

export class PhotosphereTransition {
  constructor(viewer) {
    this.viewer = viewer;
    this._psv = null;
    this._dock = null;
    this._viewport = null;
    this._chip = null;
    this._timer = null;
    this._lastCheckMs = 0;
    this._active = false;
    this._enabled = true;
    this._nearbyPano = null;
    this._dismissedUntil = 0;
    this._onKey = this._handleKey.bind(this);
  }

  start() {
    if (this._timer) return;
    this._ensureUi();
    this._timer = setInterval(() => this._tick(), CHECK_INTERVAL_MS);
  }

  stop() {
    if (this._timer) {
      clearInterval(this._timer);
      this._timer = null;
    }
    this._close();
    this._hideChip();
    this._dock?.remove();
    this._chip?.remove();
    this._dock = null;
    this._chip = null;
  }

  setEnabled(on) {
    this._enabled = !!on;
    if (!on) {
      this._close();
      this._hideChip();
      this._nearbyPano = null;
    }
  }

  _ensureUi() {
    if (this._dock) return;
    this._dock = document.createElement("div");
    this._dock.className = "psv-dock";
    this._dock.hidden = true;
    this._dock.setAttribute("role", "dialog");
    this._dock.setAttribute("aria-label", "Street view");
    this._dock.innerHTML = `
      <div class="psv-dock-toolbar">
        <button type="button" class="psv-dock-exit">← Back to map</button>
        <span class="psv-dock-hint">ESC to close</span>
        <a class="psv-dock-link" href="#" target="_blank" rel="noopener">Open in Mapillary ↗</a>
      </div>
      <div class="psv-dock-viewport"></div>
    `;
    document.body.appendChild(this._dock);
    this._viewport = this._dock.querySelector(".psv-dock-viewport");
    this._dock.querySelector(".psv-dock-exit")?.addEventListener("click", () => this._close());
    this._dock.querySelector(".psv-dock-link")?.addEventListener("click", (e) => {
      if (!this._nearbyPano?.viewer_url) e.preventDefault();
    });

    this._chip = document.createElement("button");
    this._chip.type = "button";
    this._chip.className = "psv-entry-chip";
    this._chip.hidden = true;
    this._chip.textContent = "Street view available";
    this._chip.addEventListener("click", () => {
      if (this._nearbyPano) this._open(this._nearbyPano);
    });
    document.body.appendChild(this._chip);
  }

  async _tick() {
    if (!this._enabled) return;
    this._ensureUi();
    if (this._active) return;
    if (Date.now() < this._dismissedUntil) {
      this._hideChip();
      return;
    }

    const cam = this.viewer.camera;
    const carto = cam.positionCartographic;
    if (!carto) return;
    const altM = carto.height;
    if (altM > NEAR_GROUND_ALT_M) {
      this._nearbyPano = null;
      this._hideChip();
      return;
    }

    const lat = (carto.latitude * 180) / Math.PI;
    const lon = (carto.longitude * 180) / Math.PI;
    const now = Date.now();
    if (now - this._lastCheckMs < CHECK_INTERVAL_MS) return;
    this._lastCheckMs = now;

    let panos = [];
    try {
      const url = new URL("/api/photospheres", window.location.origin);
      url.searchParams.set("lat", lat);
      url.searchParams.set("lon", lon);
      url.searchParams.set("radius_m", 80);
      url.searchParams.set("limit", 3);
      const r = await fetch(url);
      if (!r.ok) return;
      const body = await r.json();
      panos = body.items ?? [];
    } catch {
      return;
    }

    const pano = panos.find((p) => p.is_pano !== false && panoramaUrl(p));
    if (!pano) {
      this._nearbyPano = null;
      this._hideChip();
      return;
    }
    this._nearbyPano = pano;
    if (altM <= PROMPT_ALT_M) this._showChip(pano);
    else this._hideChip();
  }

  _showChip(pano) {
    if (!this._chip || this._active) return;
    const when = pano.captured_at
      ? new Date(pano.captured_at * 1000).toLocaleDateString()
      : "";
    this._chip.textContent = when
      ? `Open street view (${when})`
      : "Open street view";
    this._chip.hidden = false;
  }

  _hideChip() {
    if (this._chip) this._chip.hidden = true;
  }

  _open(pano) {
    if (this._active) return;
    const url = panoramaUrl(pano);
    if (!url) return;

    this._active = true;
    this._hideChip();
    this._dock.hidden = false;
    document.body.classList.add("psv-dock-open");

    const link = this._dock.querySelector(".psv-dock-link");
    if (link) {
      link.href = pano.viewer_url || "https://www.mapillary.com/";
      link.style.visibility = pano.viewer_url ? "visible" : "hidden";
    }

    if (this._psv) {
      this._psv.destroy();
      this._psv = null;
    }

    const yawDeg = Number(pano.compass_angle) || 0;
    this._psv = new Viewer({
      container: this._viewport,
      panorama: url,
      defaultYaw: `${yawDeg}deg`,
      defaultPitch: "0deg",
      defaultZoomLvl: 50,
      mousewheel: true,
      mousemove: true,
      touchmoveTwoFingers: true,
      navbar: ["zoom", "move", "fullscreen"],
      loadingTxt: "Loading street view…",
    });

    window.addEventListener("keydown", this._onKey);
    this.viewer.scene.requestRender();
  }

  _close() {
    if (!this._active && this._dock?.hidden !== false) return;
    window.removeEventListener("keydown", this._onKey);
    if (this._psv) {
      this._psv.destroy();
      this._psv = null;
    }
    if (this._dock) this._dock.hidden = true;
    document.body.classList.remove("psv-dock-open");
    this._active = false;
    this._dismissedUntil = Date.now() + EXIT_COOLDOWN_MS;
    this._hideChip();

    const carto = this.viewer.camera.positionCartographic;
    if (carto && carto.height < 120) {
      const lat = (carto.latitude * 180) / Math.PI;
      const lon = (carto.longitude * 180) / Math.PI;
      this.viewer.camera.flyTo({
        destination: Cesium.Cartesian3.fromDegrees(lon, lat, 280),
        duration: 0.8,
      });
    }
    this.viewer.scene.requestRender();
  }

  _handleKey(e) {
    if (e.key === "Escape") {
      e.preventDefault();
      this._close();
    }
  }
}

function panoramaUrl(pano) {
  return pano.pano_url || pano.thumb_original_url || pano.thumb_2048_url
    || pano.thumbnail_url || null;
}
