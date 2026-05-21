/** Aircraft entity collection. Handles snapshot + diff frames from /ws/live. */
import * as Cesium from "cesium";
import { aircraftDetailRows } from "./aircraft-detail-rows.js";
import { readEntityData } from "./entity-data.js";
import { aircraftIconType, iconBillboard } from "./layer-icons.js";
import { animateTo, enableGlobeAnimation, requestSceneRender } from "./motion.js";

const MOTION_SECONDS = 10;
const STALE_MS = 60_000;

function aircraftDescription(ac) {
  const rows = aircraftDetailRows(ac);
  return `<table class="entity-detail-table">` +
    rows.map(([k, v]) =>
      `<tr><td style="padding-right:8px;color:#8b95a6">${k}</td><td>${v}</td></tr>`
    ).join("") + `</table>`;
}

function colorForAircraft(ac) {
  const cat = (ac.category || "").toUpperCase();
  if (ac.on_ground) return "#8b95a6";
  if (cat.startsWith("H")) return "#74c0fc";
  if (cat.startsWith("B")) return "#ffa94d";
  return "#41d692";
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
    for (const rec of this._index.values()) rec.lastSeen = now;
    this._expireStale();
    requestSceneRender(this.viewer);
  }

  _applySnapshot(frame, now) {
    this.collection.entities.removeAll();
    this._index.clear();
    for (const ac of frame.items || []) {
      if (!Number.isFinite(ac.lat) || !Number.isFinite(ac.lon)) continue;
      const entity = this._add(ac);
      if (entity) this._index.set(ac.icao24, { entity, lastSeen: now, data: ac });
    }
  }

  _applyDiff(frame, now) {
    for (const ac of frame.added ?? []) {
      if (!Number.isFinite(ac.lat) || !Number.isFinite(ac.lon)) continue;
      const rec = this._index.get(ac.icao24);
      if (rec) {
        this._update(rec.entity, ac);
        rec.lastSeen = now;
      } else {
        const entity = this._add(ac);
        if (entity) this._index.set(ac.icao24, { entity, lastSeen: now, data: ac });
      }
    }
    for (const ac of frame.updated ?? []) {
      if (!Number.isFinite(ac.lat) || !Number.isFinite(ac.lon)) continue;
      const rec = this._index.get(ac.icao24);
      if (rec) {
        this._update(rec.entity, ac);
        rec.lastSeen = now;
      } else {
        const entity = this._add(ac);
        if (entity) this._index.set(ac.icao24, { entity, lastSeen: now, data: ac });
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
    if (!Number.isFinite(ac.lat) || !Number.isFinite(ac.lon)) return null;
    const css = colorForAircraft(ac);
    return this.collection.entities.add({
      id: `aircraft:${ac.icao24}`,
      name: this._labelText(ac),
      description: aircraftDescription(ac),
      position: Cesium.Cartesian3.fromDegrees(ac.lon, ac.lat, ac.alt_m ?? 0),
      billboard: iconBillboard(aircraftIconType(ac), css, ac.on_ground ? 0.85 : 1.0),
      label: {
        text: this._labelText(ac),
        font: "11px monospace",
        fillColor: Cesium.Color.WHITE,
        outlineColor: Cesium.Color.BLACK,
        outlineWidth: 2,
        style: Cesium.LabelStyle.FILL_AND_OUTLINE,
        pixelOffset: new Cesium.Cartesian2(12, -10),
        distanceDisplayCondition: new Cesium.DistanceDisplayCondition(0, 2e6),
      },
      properties: new Cesium.PropertyBag(ac),
    });
  }

  getByEntity(entity) {
    if (!entity) return null;
    for (const rec of this._index.values()) {
      if (rec.entity === entity) return rec.data;
    }
    return readEntityData(entity);
  }

  _update(entity, ac) {
    if (!Number.isFinite(ac.lat) || !Number.isFinite(ac.lon)) return;
    const rec = this._index.get(ac.icao24);
    if (rec) rec.data = ac;
    animateTo(entity, ac.lon, ac.lat, ac.alt_m ?? 0, MOTION_SECONDS);
    entity.label.text = this._labelText(ac);
    entity.name = this._labelText(ac);
    entity.description = aircraftDescription(ac);
    entity.properties = new Cesium.PropertyBag(ac);
    entity.billboard = iconBillboard(
      aircraftIconType(ac), colorForAircraft(ac), ac.on_ground ? 0.85 : 1.0,
    );
  }

  _labelText(ac) {
    const type = ac.aircraft_type || "";
    const cs = ac.callsign?.trim();
    if (cs && type) return `${cs} · ${type}`;
    if (cs) return cs;
    if (type) return type;
    return ac.icao24.toUpperCase();
  }

  setVisible(visible) {
    this.collection.show = visible;
  }

  count() {
    return this._index.size;
  }
}
