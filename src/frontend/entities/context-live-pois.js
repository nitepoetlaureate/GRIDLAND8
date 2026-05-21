/** Environmental / aviation POIs from context (fires, quakes, AQ, METAR, water). */
import * as Cesium from "cesium";

const COLORS = {
  fire: "#ff6b35",
  quake: "#fcc419",
  aq: "#94d82d",
  metar: "#74c0fc",
  water: "#4dabf7",
};

function esc(s) {
  return String(s ?? "").replace(/[&<>"']/g, (c) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  })[c]);
}

function tableHtml(rows) {
  return `<table style="font:12px monospace">` +
    rows.map(([k, v]) =>
      `<tr><td style="padding-right:8px;color:#8b95a6">${esc(k)}</td><td>${esc(v)}</td></tr>`
    ).join("") + `</table>`;
}

function addPoint(ds, { id, lat, lon, color, name, description, pixelSize = 8 }) {
  if (!Number.isFinite(lat) || !Number.isFinite(lon)) return;
  ds.entities.add({
    id,
    name,
    description,
    position: Cesium.Cartesian3.fromDegrees(lon, lat, 0),
    point: {
      pixelSize,
      color: Cesium.Color.fromCssColorString(color),
      outlineColor: Cesium.Color.BLACK,
      outlineWidth: 1,
      disableDepthTestDistance: Number.POSITIVE_INFINITY,
      scaleByDistance: new Cesium.NearFarScalar(800, 1.2, 6e5, 0.5),
      heightReference: Cesium.HeightReference.CLAMP_TO_GROUND,
    },
  });
}

export class ContextLivePoiLayer {
  constructor(viewer) {
    this.viewer = viewer;
    this.dataSource = new Cesium.CustomDataSource("context-live-pois");
    viewer.dataSources.add(this.dataSource);
    this.dataSource.show = false;
  }

  clear() {
    this.dataSource.entities.removeAll();
  }

  setFromContext(ctx) {
    this.clear();
    if (!ctx) return;
    for (const f of ctx.fires || []) {
      if (f.lat == null || f.lon == null) continue;
      addPoint(this.dataSource, {
        id: `fire:${f.id ?? `${f.lat},${f.lon}`}`,
        lat: f.lat, lon: f.lon,
        color: COLORS.fire,
        name: "Fire detection",
        description: tableHtml([
          ["Brightness", f.brightness], ["Confidence", f.confidence], ["At", f.acq_date],
        ]),
        pixelSize: 10,
      });
    }
    for (const q of ctx.quakes || []) {
      if (q.lat == null || q.lon == null) continue;
      addPoint(this.dataSource, {
        id: `quake:${q.id ?? q.time}`,
        lat: q.lat, lon: q.lon,
        color: COLORS.quake,
        name: `M${q.mag ?? "?"}`,
        description: tableHtml([["Place", q.place], ["Time", q.time], ["Mag", q.mag]]),
        pixelSize: 9,
      });
    }
    for (const a of ctx.air_quality || []) {
      if (a.lat == null || a.lon == null) continue;
      addPoint(this.dataSource, {
        id: `aq:${a.id}`,
        lat: a.lat, lon: a.lon,
        color: COLORS.aq,
        name: a.name || "Air quality",
        description: tableHtml([["Sensors", (a.sensors || []).join(", ")]]),
      });
    }
    for (const m of ctx.metars || []) {
      if (m.lat == null || m.lon == null) continue;
      addPoint(this.dataSource, {
        id: `metar:${m.station}`,
        lat: m.lat, lon: m.lon,
        color: COLORS.metar,
        name: `METAR ${m.station}`,
        description: tableHtml([
          ["Category", m.flight_category], ["Raw", m.raw],
        ]),
      });
    }
    for (const g of ctx.water_gauges || []) {
      if (g.lat == null || g.lon == null) continue;
      addPoint(this.dataSource, {
        id: `water:${g.site_code}`,
        lat: g.lat, lon: g.lon,
        color: COLORS.water,
        name: g.name || g.site_code,
        description: tableHtml([["Site", g.site_code]]),
      });
    }
  }

  setVisible(visible) {
    this.dataSource.show = visible;
  }

  count() {
    return this.dataSource.entities.values.length;
  }
}
