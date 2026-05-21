/** Indego bike-share stations — GBFS via /api/indego/stations */
import * as Cesium from "cesium";
import { bboxQueryParams } from "../geo.js";
import { iconBillboard } from "./layer-icons.js";
import { requestSceneRender } from "./motion.js";

function description(s) {
  return `<table style="font:12px monospace">` +
    [
      ["Station", s.name || "—"],
      ["Bikes", s.bikes ?? "—"],
      ["Docks", s.docks ?? "—"],
      ["Renting", s.is_renting ? "yes" : "no"],
      ["Returning", s.is_returning ? "yes" : "no"],
    ].map(([k, v]) =>
      `<tr><td style="padding-right:8px;color:#8b95a6">${k}</td><td>${v}</td></tr>`
    ).join("") + `</table>`;
}

export class IndegoLayer {
  constructor(viewer) {
    this.viewer = viewer;
    this.dataSource = new Cesium.CustomDataSource("indego");
    viewer.dataSources.add(this.dataSource);
    this.dataSource.show = false;
    this._index = new Map();
    this._enabled = false;
    this._lat = 39.9526;
    this._lon = -75.1652;
    this._radiusKm = 15;
    this._bbox = null;
  }

  setVisible(visible) {
    this.dataSource.show = visible;
  }

  setViewport(lat, lon, radiusKm, bbox) {
    this._lat = lat;
    this._lon = lon;
    this._radiusKm = radiusKm;
    this._bbox = bbox;
  }

  async start(lat, lon, radiusKm = 15) {
    this.setViewport(lat, lon, radiusKm, null);
    this._enabled = true;
    return this.refresh();
  }

  stop() {
    this._enabled = false;
  }

  async refresh() {
    if (!this._enabled) return this._index.size;
    const q = new URLSearchParams({
      lat: String(this._lat),
      lon: String(this._lon),
      radius_km: String(this._radiusKm),
    });
    const extra = bboxQueryParams(this._bbox);
    if (extra) {
      for (const [k, v] of new URLSearchParams(extra.slice(1))) {
        q.set(k, v);
      }
    }
    let payload;
    try {
      const r = await fetch(`/api/indego/stations?${q}`);
      if (!r.ok) return this._index.size;
      payload = await r.json();
    } catch {
      return this._index.size;
    }
    const seen = new Set();
    for (const s of payload.stations || []) {
      if (!Number.isFinite(s.lat) || !Number.isFinite(s.lon)) continue;
      const id = s.station_id;
      seen.add(id);
      const pos = Cesium.Cartesian3.fromDegrees(s.lon, s.lat, 0);
      const bikes = s.bikes ?? 0;
      const fill = bikes > 0 ? "#3dd68c" : "#6b7280";
      const existing = this._index.get(id);
      if (existing) {
        existing.entity.position = pos;
        existing.entity.description = description(s);
        existing.entity.billboard = iconBillboard("bike", fill, 0.95);
        existing.entity.point = undefined;
        existing.entity.label.text = String(bikes);
        existing.data = s;
      } else {
        const entity = this.dataSource.entities.add({
          id: `indego:${id}`,
          name: s.name,
          description: description(s),
          position: pos,
          billboard: iconBillboard("bike", fill, 0.95),
          label: {
            text: String(bikes),
            font: "10px monospace",
            fillColor: Cesium.Color.WHITE,
            outlineColor: Cesium.Color.BLACK,
            outlineWidth: 2,
            style: Cesium.LabelStyle.FILL_AND_OUTLINE,
            pixelOffset: new Cesium.Cartesian2(8, 0),
            distanceDisplayCondition: new Cesium.DistanceDisplayCondition(0, 80_000),
          },
          properties: new Cesium.PropertyBag(s),
        });
        this._index.set(id, { entity, data: s });
      }
    }
    for (const [id, rec] of [...this._index]) {
      if (!seen.has(id)) {
        this.dataSource.entities.remove(rec.entity);
        this._index.delete(id);
      }
    }
    requestSceneRender(this.viewer);
    return this._index.size;
  }

  getStation(stationId) {
    return this._index.get(stationId)?.data ?? null;
  }

  count() {
    return this._index.size;
  }
}
