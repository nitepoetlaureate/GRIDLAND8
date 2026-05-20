/** Aircraft entity collection. Handles snapshot + diff frames from /ws/live. */
import * as Cesium from "cesium";
import { animateTo, enableGlobeAnimation } from "./motion.js";

const MOTION_SECONDS = 10;

const STALE_MS = 60_000;

function aircraftDescription(ac) {
  const rows = [
    ["ICAO24", ac.icao24],
    ["Callsign", ac.callsign?.trim() || "—"],
    ["Lat/Lon", `${ac.lat?.toFixed?.(5)}, ${ac.lon?.toFixed?.(5)}`],
    ["Altitude", ac.alt_m != null ? `${Math.round(ac.alt_m)} m / ${Math.round(ac.alt_m * 3.281)} ft` : "—"],
    ["Speed", ac.velocity_ms != null
      ? `${Math.round(ac.velocity_ms / 0.514444)} kt` : "—"],
    ["Heading", ac.track_deg != null ? `${Math.round(ac.track_deg)}°` : "—"],
    ["On ground", ac.on_ground ? "yes" : "no"],
    ["Country", ac.origin_country || "—"],
  ];
  return `<table style="font:12px monospace">` +
    rows.map(([k, v]) =>
      `<tr><td style="padding-right:8px;color:#8b95a6">${k}</td><td>${v}</td></tr>`
    ).join("") +
    `</table>`;
}

export class AircraftLayer {
  constructor(viewer) {
    this.viewer = viewer;
    this.collection = new Cesium.CustomDataSource("aircraft");
    viewer.dataSources.add(this.collection);
    this._index = new Map();
    enableGlobeAnimation(viewer);
  }

  handleFrame(frame) {
    const now = Date.now();
    if (frame.kind === "snapshot") this._applySnapshot(frame, now);
    else if (frame.kind === "diff") this._applyDiff(frame, now);
    // Refresh lastSeen for all tracked aircraft on every frame (diffs often empty).
    for (const rec of this._index.values()) rec.lastSeen = now;
    this._expireStale();
  }

  _applySnapshot(frame, now) {
    this.collection.entities.removeAll();
    this._index.clear();
    for (const ac of frame.items || []) {
      this._index.set(ac.icao24, { entity: this._add(ac), lastSeen: now });
    }
  }

  _applyDiff(frame, now) {
    for (const ac of frame.added ?? []) {
      const rec = this._index.get(ac.icao24);
      if (rec) {
        this._update(rec.entity, ac);
        rec.lastSeen = now;
      } else {
        this._index.set(ac.icao24, { entity: this._add(ac), lastSeen: now });
      }
    }
    for (const ac of frame.updated ?? []) {
      const rec = this._index.get(ac.icao24);
      if (rec) {
        this._update(rec.entity, ac);
        rec.lastSeen = now;
      } else {
        this._index.set(ac.icao24, { entity: this._add(ac), lastSeen: now });
      }
    }
    for (const icao24 of frame.removed ?? []) {
      const rec = this._index.get(icao24);
      if (rec) {
        this.collection.entities.remove(rec.entity);
        this._index.delete(icao24);
      }
    }
  }

  _expireStale() {
    const cutoff = Date.now() - STALE_MS;
    for (const [k, r] of this._index) {
      if (r.lastSeen < cutoff) {
        this.collection.entities.remove(r.entity);
        this._index.delete(k);
      }
    }
  }

  _add(ac) {
    return this.collection.entities.add({
      name: this._labelText(ac),
      description: aircraftDescription(ac),
      position: Cesium.Cartesian3.fromDegrees(ac.lon, ac.lat, ac.alt_m ?? 0),
      point: {
        pixelSize: ac.on_ground ? 7 : 9,
        color: ac.on_ground
          ? Cesium.Color.fromCssColorString("#8b95a6")
          : Cesium.Color.fromCssColorString("#41d692"),
        outlineColor: Cesium.Color.BLACK,
        outlineWidth: 2,
        disableDepthTestDistance: Number.POSITIVE_INFINITY,
        scaleByDistance: new Cesium.NearFarScalar(2e3, 1.5, 3e6, 0.6),
      },
      label: {
        text: this._labelText(ac),
        font: "11px monospace",
        fillColor: Cesium.Color.WHITE,
        outlineColor: Cesium.Color.BLACK,
        outlineWidth: 2,
        style: Cesium.LabelStyle.FILL_AND_OUTLINE,
        pixelOffset: new Cesium.Cartesian2(8, -8),
        distanceDisplayCondition: new Cesium.DistanceDisplayCondition(0, 5e5),
      },
      properties: ac,
    });
  }

  _update(entity, ac) {
    animateTo(entity, ac.lon, ac.lat, ac.alt_m ?? 0, MOTION_SECONDS);
    entity.label.text = this._labelText(ac);
    entity.name = this._labelText(ac);
    entity.description = aircraftDescription(ac);
    entity.point.color = ac.on_ground
      ? Cesium.Color.fromCssColorString("#8b95a6")
      : Cesium.Color.fromCssColorString("#41d692");
  }

  _labelText(ac) {
    return ac.callsign?.trim() || ac.icao24.toUpperCase();
  }

  setVisible(visible) {
    this.collection.show = visible;
  }
}
