/** Photosphere transition: when Cesium camera flies below the trigger
 *  altitude AND Mapillary returns nearby panos, swap the globe for a
 *  Photo Sphere Viewer fullscreen overlay. ESC or "back to globe" closes.
 */
import { Viewer } from "@photo-sphere-viewer/core";
import "@photo-sphere-viewer/core/index.css";

const TRIGGER_ALT_M = 80;
const CHECK_INTERVAL_MS = 1500;

export class PhotosphereTransition {
  constructor(viewer) {
    this.viewer = viewer;
    this._psv = null;
    this._overlay = null;
    this._timer = null;
    this._lastCheckMs = 0;
    this._active = false;
    this._enabled = true;
  }

  start() {
    if (this._timer) return;
    this._timer = setInterval(() => this._tick(), CHECK_INTERVAL_MS);
  }

  stop() {
    if (this._timer) {
      clearInterval(this._timer);
      this._timer = null;
    }
    this._close();
  }

  setEnabled(on) {
    this._enabled = !!on;
    if (!on) this._close();
  }

  async _tick() {
    if (!this._enabled || this._active) return;
    const cam = this.viewer.camera;
    const carto = cam.positionCartographic;
    if (!carto) return;
    const altM = carto.height;
    if (altM > TRIGGER_ALT_M) return;
    const lat = (carto.latitude * 180) / Math.PI;
    const lon = (carto.longitude * 180) / Math.PI;
    const now = Date.now();
    if (now - this._lastCheckMs < 2000) return;
    this._lastCheckMs = now;
    let panos = [];
    try {
      const url = new URL("/api/photospheres", window.location.origin);
      url.searchParams.set("lat", lat);
      url.searchParams.set("lon", lon);
      url.searchParams.set("radius_m", 250);
      url.searchParams.set("limit", 1);
      const r = await fetch(url);
      if (!r.ok) return;
      const body = await r.json();
      panos = body.items ?? [];
    } catch {
      return;
    }
    if (!panos.length) return;
    this._open(panos[0]);
  }

  _open(pano) {
    if (this._active) return;
    this._active = true;
    this._overlay = document.createElement("div");
    this._overlay.className = "psv-overlay";
    Object.assign(this._overlay.style, {
      position: "fixed", inset: "0", zIndex: "50",
      background: "#000",
    });
    const close = document.createElement("button");
    close.textContent = "↑ back to globe";
    Object.assign(close.style, {
      position: "absolute", top: "12px", right: "12px", zIndex: "60",
      padding: "6px 10px", borderRadius: "4px", border: "1px solid #1a2230",
      background: "#0d131c", color: "#e6edf3", cursor: "pointer",
      font: "12px monospace",
    });
    close.addEventListener("click", () => this._close());
    document.body.appendChild(this._overlay);
    this._overlay.appendChild(close);
    this._psv = new Viewer({
      container: this._overlay,
      panorama: pano.thumb_2048_url,
      defaultYaw: ((pano.compass_angle ?? 0) * Math.PI) / 180,
      navbar: ["zoom", "fullscreen"],
    });
    window.addEventListener("keydown", this._onKey);
  }

  _close = () => {
    if (!this._active) return;
    window.removeEventListener("keydown", this._onKey);
    if (this._psv) { this._psv.destroy(); this._psv = null; }
    if (this._overlay) { this._overlay.remove(); this._overlay = null; }
    this._active = false;
  };

  _onKey = (e) => {
    if (e.key === "Escape") this._close();
  };
}
