/** SEPTA live-vehicle layer. Polls /api/septa/vehicles on an interval. */
import * as Cesium from "cesium";
import { animateTo, enableGlobeAnimation } from "./motion.js";

const POLL_INTERVAL_MS = 10_000;
const MOTION_SECONDS = 10;

function description(v) {
  const rows = [
    ["Mode", v.kind === "regional_rail" ? "Regional Rail" : "Bus/Trolley"],
    ["Route", v.route || "—"],
    ["Destination", v.destination || "—"],
  ];
  if (v.kind === "regional_rail") {
    rows.push(["Train #", v.id?.replace?.("septa_train_", "") || "—"]);
    rows.push(["Service", v.service || "—"]);
    rows.push(["Current stop", v.current_stop || "—"]);
    rows.push(["Next stop", v.next_stop || "—"]);
    rows.push(["Track", v.track || "—"]);
  } else {
    rows.push(["Direction", v.direction || "—"]);
    rows.push(["Next stop", v.next_stop || "—"]);
    rows.push(["Seats", v.seat_availability || "—"]);
  }
  rows.push(["Late (min)", v.late_min ?? "—"]);
  return `<table style="font:12px monospace">` +
    rows.map(([k, val]) =>
      `<tr><td style="padding-right:8px;color:#8b95a6">${k}</td><td>${val}</td></tr>`
    ).join("") + `</table>`;
}

export class TransitLayer {
  constructor(viewer) {
    this.viewer = viewer;
    this.dataSource = new Cesium.CustomDataSource("septa-transit");
    viewer.dataSources.add(this.dataSource);
    this.dataSource.show = false;
    this.dataSource.clustering.enabled = false;
    enableGlobeAnimation(viewer);
    this._index = new Map();
    this._timer = null;
    this._enabled = false;
  }

  setVisible(visible) {
    this.dataSource.show = visible;
  }

  async start() {
    if (this._enabled) {
      await this._refresh();
      return;
    }
    this._enabled = true;
    await this._refresh();
    this._timer = setInterval(() => this._refresh(), POLL_INTERVAL_MS);
  }

  async refresh() {
    await this._refresh();
  }

  stop() {
    this._enabled = false;
    if (this._timer) {
      clearInterval(this._timer);
      this._timer = null;
    }
  }

  async _refresh() {
    let payload;
    try {
      const r = await fetch("/api/septa/vehicles");
      if (!r.ok) return;
      payload = await r.json();
    } catch {
      return;
    }
    const sources = payload.sources || {};
    const failed = Object.values(sources).some((s) => s === "error");
    if (failed && !payload.vehicles?.length) return;

    const seen = new Set();
    const keepIfSourceDown = (kind) => {
      if (kind === "regional_rail" && sources.trainview === "error") return true;
      if (kind === "bus_trolley" && sources.transitview === "error") return true;
      return false;
    };
    for (const v of payload.vehicles || []) {
      seen.add(v.id);
      const pos = Cesium.Cartesian3.fromDegrees(v.lon, v.lat, 0);
      const isRail = v.kind === "regional_rail";
      const rec = this._index.get(v.id);
      if (rec) {
        animateTo(rec.entity, v.lon, v.lat, 0, MOTION_SECONDS);
        rec.entity.description = description(v);
        rec.entity.label.text = this._labelText(v);
        rec.entity.point.color = colorFor(v);
        rec.entity.point.pixelSize = isRail ? 12 : 9;
        rec.kind = v.kind;
      } else {
        const entity = this.dataSource.entities.add({
          name: this._labelText(v),
          description: description(v),
          position: pos,
          point: {
            pixelSize: isRail ? 12 : 9,
            color: colorFor(v),
            outlineColor: Cesium.Color.BLACK,
            outlineWidth: 2,
            disableDepthTestDistance: Number.POSITIVE_INFINITY,
            scaleByDistance: new Cesium.NearFarScalar(500, 1.4, 5e5, 0.7),
            heightReference: Cesium.HeightReference.CLAMP_TO_GROUND,
          },
          label: {
            text: this._labelText(v),
            font: "10px monospace",
            fillColor: Cesium.Color.WHITE,
            outlineColor: Cesium.Color.BLACK,
            outlineWidth: 2,
            style: Cesium.LabelStyle.FILL_AND_OUTLINE,
            pixelOffset: new Cesium.Cartesian2(8, 0),
            distanceDisplayCondition: new Cesium.DistanceDisplayCondition(0, 8e4),
            scaleByDistance: new Cesium.NearFarScalar(500, 1, 4e5, 0),
          },
          properties: v,
        });
        this._index.set(v.id, { entity, kind: v.kind });
      }
    }
    for (const [id, rec] of [...this._index]) {
      if (seen.has(id)) continue;
      if (keepIfSourceDown(rec.kind)) continue;
      this.dataSource.entities.remove(rec.entity);
      this._index.delete(id);
    }
  }

  _labelText(v) {
    return `${v.kind === "regional_rail" ? "🚆" : "🚌"} ${v.route}`;
  }

  count() {
    return this._index.size;
  }
}

function colorFor(v) {
  if (v.kind === "regional_rail") return Cesium.Color.fromCssColorString("#41a8ff");
  return Cesium.Color.fromCssColorString("#ff9c41");
}
