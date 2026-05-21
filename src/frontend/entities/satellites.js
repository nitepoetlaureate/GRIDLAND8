/**
 * Satellite layer. Propagates orbital positions client-side using satellite.js
 * (SGP4) and renders them on the Cesium globe.
 */
import * as Cesium from "cesium";
import * as satellite from "satellite.js";

import { satellites as fetchCatalog } from "../api.js";

const UPDATE_INTERVAL_MS = 2000;

function satelliteDescription(item, satrec) {
  const catalog = satrec?.satnum ?? "—";
  const inclination = satrec?.inclo != null
    ? (satrec.inclo * 180 / Math.PI).toFixed(2) + "°" : "—";
  const eccentricity = satrec?.ecco?.toFixed?.(5) ?? "—";
  const period_min = satrec?.no != null
    ? (2 * Math.PI / satrec.no).toFixed(1) : "—";
  const rows = [
    ["Name", item.name],
    ["Catalog #", catalog],
    ["Inclination", inclination],
    ["Eccentricity", eccentricity],
    ["Period (min)", period_min],
    ["TLE line 1", `<code style="font:11px monospace">${item.line1}</code>`],
    ["TLE line 2", `<code style="font:11px monospace">${item.line2}</code>`],
  ];
  return `<table style="font:12px monospace">` +
    rows.map(([k, v]) =>
      `<tr><td style="padding-right:8px;color:#8b95a6;vertical-align:top">${k}</td><td>${v}</td></tr>`
    ).join("") +
    `</table>`;
}

export class SatelliteLayer {
  constructor(viewer) {
    this.viewer = viewer;
    this.dataSource = new Cesium.CustomDataSource("satellites");
    viewer.dataSources.add(this.dataSource);
    this.records = [];
    this._timer = null;
    this._enabled = false;
    this._currentGroup = null;
  }

  setVisible(visible) {
    this.dataSource.show = visible;
  }

  async load(group = "stations") {
    if (this._currentGroup === group && this.records.length) return;
    const payload = await fetchCatalog(group);
    this._currentGroup = group;
    this.records = [];
    this.dataSource.entities.removeAll();

    for (const item of payload.items || []) {
      let satrec;
      try {
        satrec = satellite.twoline2satrec(item.line1, item.line2);
      } catch {
        continue;
      }
      if (!satrec) continue;
      const entity = this.dataSource.entities.add({
        name: item.name,
        description: satelliteDescription(item, satrec),
        position: Cesium.Cartesian3.fromDegrees(0, 0, 0),
        point: {
          pixelSize: 4,
          color: Cesium.Color.YELLOW.withAlpha(0.9),
          outlineColor: Cesium.Color.BLACK,
          outlineWidth: 1,
        },
        label: {
          text: item.name,
          font: "11px sans-serif",
          fillColor: Cesium.Color.YELLOW,
          showBackground: true,
          backgroundColor: Cesium.Color.BLACK.withAlpha(0.5),
          pixelOffset: new Cesium.Cartesian2(0, -14),
          distanceDisplayCondition: new Cesium.DistanceDisplayCondition(0, 500_000),
        },
      });
      this.records.push({ satrec, entity });
    }
    this._tick();
  }

  start() {
    if (this._enabled) return;
    this._enabled = true;
    this._timer = setInterval(() => this._tick(), UPDATE_INTERVAL_MS);
  }

  stop() {
    this._enabled = false;
    if (this._timer) {
      clearInterval(this._timer);
      this._timer = null;
    }
  }

  _tick() {
    const now = new Date();
    const gmst = satellite.gstime(now);
    for (const { satrec, entity } of this.records) {
      let pv;
      try {
        pv = satellite.propagate(satrec, now);
      } catch {
        continue;
      }
      if (!pv || !pv.position) continue;
      const geo = satellite.eciToGeodetic(pv.position, gmst);
      const lat = satellite.degreesLat(geo.latitude);
      const lon = satellite.degreesLong(geo.longitude);
      const altKm = geo.height;
      if (!Number.isFinite(lat) || !Number.isFinite(lon) || !Number.isFinite(altKm)) {
        continue;
      }
      entity.position = Cesium.Cartesian3.fromDegrees(lon, lat, altKm * 1000);
    }
  }

  count() {
    return this.records.length;
  }
}
