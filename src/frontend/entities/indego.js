/** Indego bike-share stations — GBFS via /api/indego/stations */
import * as Cesium from "cesium";

const POLL_INTERVAL_MS = 60_000;

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
    this._timer = null;
    this._enabled = false;
  }

  setVisible(visible) {
    this.dataSource.show = visible;
  }

  async start(lat, lon, radiusKm = 15) {
    this._lat = lat;
    this._lon = lon;
    this._radiusKm = radiusKm;
    if (this._enabled) {
      await this._refresh();
      return;
    }
    this._enabled = true;
    await this._refresh();
    this._timer = setInterval(() => this._refresh(), POLL_INTERVAL_MS);
  }

  stop() {
    this._enabled = false;
    if (this._timer) {
      clearInterval(this._timer);
      this._timer = null;
    }
  }

  async _refresh() {
    const q = new URLSearchParams({
      lat: String(this._lat),
      lon: String(this._lon),
      radius_km: String(this._radiusKm),
    });
    let payload;
    try {
      const r = await fetch(`/api/indego/stations?${q}`);
      if (!r.ok) return;
      payload = await r.json();
    } catch {
      return;
    }
    const seen = new Set();
    for (const s of payload.stations || []) {
      const id = s.station_id;
      seen.add(id);
      const pos = Cesium.Cartesian3.fromDegrees(s.lon, s.lat, 0);
      const bikes = s.bikes ?? 0;
      const color = bikes > 0
        ? Cesium.Color.fromCssColorString("#3dd68c")
        : Cesium.Color.fromCssColorString("#6b7280");
      const existing = this._index.get(id);
      if (existing) {
        existing.position = pos;
        existing.description = description(s);
        existing.point.color = color;
        existing.label.text = `🚲 ${bikes}`;
      } else {
        const entity = this.dataSource.entities.add({
          name: s.name,
          description: description(s),
          position: pos,
          point: {
            pixelSize: 7,
            color,
            outlineColor: Cesium.Color.BLACK,
            outlineWidth: 1,
            disableDepthTestDistance: Number.POSITIVE_INFINITY,
            scaleByDistance: new Cesium.NearFarScalar(400, 1.3, 4e5, 0.65),
            heightReference: Cesium.HeightReference.CLAMP_TO_GROUND,
          },
          label: {
            text: `🚲 ${bikes}`,
            font: "10px monospace",
            fillColor: Cesium.Color.WHITE,
            outlineColor: Cesium.Color.BLACK,
            outlineWidth: 2,
            style: Cesium.LabelStyle.FILL_AND_OUTLINE,
            pixelOffset: new Cesium.Cartesian2(8, 0),
            distanceDisplayCondition: new Cesium.DistanceDisplayCondition(0, 12_000),
          },
          properties: s,
        });
        this._index.set(id, entity);
      }
    }
    for (const [id, entity] of [...this._index]) {
      if (!seen.has(id)) {
        this.dataSource.entities.remove(entity);
        this._index.delete(id);
      }
    }
  }

  count() {
    return this._index.size;
  }
}
