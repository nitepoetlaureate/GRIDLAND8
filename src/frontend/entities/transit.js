/** SEPTA live-vehicle layer — WS snapshots + REST fallback with viewport bbox. */
import * as Cesium from "cesium";
import { bboxQueryParams } from "../geo.js";
import { transitDetailRows } from "./entity-detail-rows.js";
import { iconBillboard } from "./layer-icons.js";
import { busRouteColor, regionalRailColor } from "./septa-colors.js";
import { animateTo, enableGlobeAnimation, requestSceneRender } from "./motion.js";

const MOTION_SECONDS = 10;

function descriptionHtml(v) {
  const rows = transitDetailRows(v);
  return `<table style="font:12px monospace">` +
    rows.map(([k, val]) =>
      `<tr><td style="padding-right:8px;color:#8b95a6">${k}</td><td>${val}</td></tr>`
    ).join("") + `</table>`;
}

function descriptionProperty(v) {
  return new Cesium.ConstantProperty(descriptionHtml(v));
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
    this._enabled = false;
    this._bbox = null;
    this._lastSources = {};
  }

  setVisible(visible) {
    this.dataSource.show = visible;
  }

  setBbox(bbox) {
    this._bbox = bbox;
  }

  async start() {
    this._enabled = true;
    return this.refresh();
  }

  stop() {
    this._enabled = false;
  }

  handleFrame(frame) {
    if (frame?.type !== "transit") return;
    if (frame.kind === "snapshot") {
      this._applyPayload(frame.vehicles || [], frame.sources || {});
    }
  }

  async refresh() {
    if (!this._enabled) return this._index.size;
    let url = "/api/septa/vehicles?";
    url += bboxQueryParams(this._bbox).replace(/^&/, "");
    try {
      const r = await fetch(url.endsWith("?") ? url.slice(0, -1) : url);
      if (!r.ok) return this._index.size;
      const payload = await r.json();
      return this._applyPayload(payload.vehicles || [], payload.sources || {});
    } catch {
      return this._index.size;
    }
  }

  _applyPayload(vehicles, sources) {
    this._lastSources = sources;
    const failed = Object.values(sources).some((s) => s === "error");
    if (failed && !vehicles.length) return this._index.size;

    const seen = new Set();
    const keepIfSourceDown = (kind) => {
      if (kind === "regional_rail" && sources.trainview === "error") return true;
      if (kind === "bus_trolley" && sources.transitview === "error") return true;
      return false;
    };
    for (const v of vehicles) {
      if (!Number.isFinite(v.lat) || !Number.isFinite(v.lon)) continue;
      seen.add(v.id);
      const isRail = v.kind === "regional_rail";
      const rec = this._index.get(v.id);
      if (rec) {
        animateTo(rec.entity, v.lon, v.lat, 0, MOTION_SECONDS);
        rec.entity.description = descriptionProperty(v);
        rec.entity.properties = new Cesium.PropertyBag(v);
        rec.data = v;
        rec.entity.label.text = this._labelText(v);
        applyVehicleGlyph(rec.entity, v, this._labelText(v));
        rec.kind = v.kind;
      } else {
        const entity = this.dataSource.entities.add({
          id: v.id,
          name: this._labelText(v),
          description: descriptionProperty(v),
          position: Cesium.Cartesian3.fromDegrees(v.lon, v.lat, 0),
          ...vehicleGraphics(v),
          label: {
            text: this._labelText(v),
            font: "10px monospace",
            fillColor: Cesium.Color.WHITE,
            outlineColor: Cesium.Color.BLACK,
            outlineWidth: 2,
            style: Cesium.LabelStyle.FILL_AND_OUTLINE,
            pixelOffset: new Cesium.Cartesian2(8, 0),
            distanceDisplayCondition: new Cesium.DistanceDisplayCondition(
              0, isRail ? 800_000 : 250_000,
            ),
            scaleByDistance: new Cesium.NearFarScalar(500, 1, 4e5, 0),
          },
          properties: new Cesium.PropertyBag(v),
        });
        this._index.set(v.id, { entity, kind: v.kind, data: v });
      }
    }
    for (const [id, rec] of [...this._index]) {
      if (seen.has(id)) continue;
      if (keepIfSourceDown(rec.kind)) continue;
      this.dataSource.entities.remove(rec.entity);
      this._index.delete(id);
    }
    requestSceneRender(this.viewer);
    return this._index.size;
  }

  _labelText(v) {
    if (v.kind === "regional_rail") {
      const dest = v.destination ? ` → ${v.destination}` : "";
      return `${v.route || "Rail"}${dest}`;
    }
    return `Bus ${v.route || ""}`;
  }

  count() {
    return this._index.size;
  }

  getVehicle(id) {
    return this._index.get(id)?.data ?? null;
  }

  countByKind() {
    let bus = 0;
    let rail = 0;
    for (const rec of this._index.values()) {
      if (rec.kind === "regional_rail") rail += 1;
      else bus += 1;
    }
    return { bus, rail, total: bus + rail };
  }

  sourceStatus() {
    return this._lastSources;
  }
}

function colorCss(v) {
  if (v.kind === "regional_rail") return regionalRailColor(v.route);
  return busRouteColor(v.route);
}

function vehicleGraphics(v) {
  const isRail = v.kind === "regional_rail";
  const css = colorCss(v);
  const type = isRail ? "train" : "bus";
  return {
    billboard: iconBillboard(type, css, isRail ? 1.15 : 1.0),
  };
}

function applyVehicleGlyph(entity, v, labelText) {
  entity.billboard = vehicleGraphics(v).billboard;
  entity.point = undefined;
  entity.label.text = labelText;
  entity.label.show = true;
  entity.label.pixelOffset = new Cesium.Cartesian2(14, 0);
  entity.label.distanceDisplayCondition = new Cesium.DistanceDisplayCondition(
    0, v.kind === "regional_rail" ? 800_000 : 250_000,
  );
}
