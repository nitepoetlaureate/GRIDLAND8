/** SEPTA Metro — Market-Frankford (L) & Broad Street (B): corridors, stations, vehicles. */
import * as Cesium from "cesium";
import { iconBillboard } from "./layer-icons.js";
import {
  metroLineBadge,
  metroLineColor,
  metroLineLabel,
} from "./septa-colors.js";
import { METRO_CORRIDORS } from "./septa-metro-corridors.js";
import { requestSceneRender } from "./motion.js";

function metroDescription(item) {
  const lineName = metroLineLabel(item.line);
  const rows = [
    ["Line", lineName],
    ["Type", item.kind === "metro_station" ? "Station" : "Train run"],
  ];
  if (item.kind === "metro_vehicle") {
    rows.push(["Route", item.route || "—"]);
    rows.push(["Destination", item.destination || "—"]);
    rows.push(["GPS", item.gps_live ? "live" : "schedule / approximate"]);
    if (item.late_min != null) rows.push(["Late (min)", String(item.late_min)]);
  }
  rows.push(["Position", `${Number(item.lat).toFixed(5)}, ${Number(item.lon).toFixed(5)}`]);
  const cams = item.nearby_cameras || [];
  if (cams.length) {
    rows.push(["Nearby cameras", cams.map((c) => c.label || c.id).join("; ")]);
  }
  return `<table class="entity-detail-table">` +
    rows.map(([k, v]) =>
      `<tr><td style="padding-right:8px;color:#8b95a6">${k}</td><td>${v}</td></tr>`).join("") +
    `</table>`;
}

function corridorPositions(line) {
  const pts = METRO_CORRIDORS[line];
  if (!pts?.length) return [];
  return pts.map(([lon, lat]) => Cesium.Cartesian3.fromDegrees(lon, lat, 0));
}

export class SeptaMetroLayer {
  constructor(viewer) {
    this.viewer = viewer;
    this.dataSource = new Cesium.CustomDataSource("septa-metro");
    viewer.dataSources.add(this.dataSource);
    this.dataSource.show = false;
    this._index = new Map();
    this._bundle = null;
    this._corridorIds = [];
  }

  setVisible(visible) {
    this.dataSource.show = visible;
  }

  getItem(id) {
    return this._index.get(id)?.data ?? null;
  }

  async refresh(lat, lon, radiusKm = 25) {
    const q = new URLSearchParams({
      lat: String(lat),
      lon: String(lon),
      radius_km: String(radiusKm),
    });
    try {
      const r = await fetch(`/api/septa/metro?${q}`);
      if (!r.ok) return 0;
      this._bundle = await r.json();
    } catch {
      return this._index.size;
    }
    return this._apply(this._bundle);
  }

  _clearCorridors() {
    for (const id of this._corridorIds) {
      const ent = this.dataSource.entities.getById(id);
      if (ent) this.dataSource.entities.remove(ent);
    }
    this._corridorIds = [];
  }

  _drawCorridors() {
    this._clearCorridors();
    for (const line of ["MFL", "BSL"]) {
      const positions = corridorPositions(line);
      if (positions.length < 2) continue;
      const color = Cesium.Color.fromCssColorString(metroLineColor(line));
      const id = `septa_metro_corridor_${line}`;
      this.dataSource.entities.add({
        id,
        name: metroLineLabel(line),
        polyline: {
          positions,
          width: 6,
          material: color.withAlpha(0.85),
          clampToGround: true,
        },
      });
      this._corridorIds.push(id);
      // Underlay glow for visibility on dark basemap
      this.dataSource.entities.add({
        id: `${id}_glow`,
        polyline: {
          positions,
          width: 12,
          material: color.withAlpha(0.25),
          clampToGround: true,
        },
      });
      this._corridorIds.push(`${id}_glow`);
    }
  }

  _apply(bundle) {
    this.dataSource.entities.removeAll();
    this._index.clear();
    this._corridorIds = [];
    this._drawCorridors();

    const items = [
      ...(bundle?.stations || []),
      ...(bundle?.vehicles || []),
    ];
    for (const item of items) {
      if (!Number.isFinite(item.lat) || !Number.isFinite(item.lon)) continue;
      const line = item.line || "MFL";
      const fill = metroLineColor(line);
      const badge = metroLineBadge(line);
      const isStation = item.kind === "metro_station";
      const iconType = isStation ? "metro-station" : "metro-train";
      const entity = this.dataSource.entities.add({
        id: item.id,
        name: isStation
          ? `${badge} ${item.name}`
          : `${badge} ${line} → ${item.destination || item.route}`,
        description: metroDescription(item),
        position: Cesium.Cartesian3.fromDegrees(item.lon, item.lat, 0),
        billboard: iconBillboard(iconType, fill, isStation ? 1.1 : 1.2, { badge }),
        label: {
          text: isStation
            ? `${badge} ${(item.name || "").slice(0, 18)}`
            : `${badge}${item.gps_live ? "" : "†"}`,
          font: "bold 11px system-ui,sans-serif",
          fillColor: Cesium.Color.fromCssColorString(fill),
          outlineColor: Cesium.Color.BLACK,
          outlineWidth: 3,
          style: Cesium.LabelStyle.FILL_AND_OUTLINE,
          pixelOffset: new Cesium.Cartesian2(0, -22),
          distanceDisplayCondition: new Cesium.DistanceDisplayCondition(0, 150_000),
        },
        properties: new Cesium.PropertyBag(item),
      });
      this._index.set(item.id, { entity, data: item });
    }
    requestSceneRender(this.viewer);
    return this._index.size;
  }

  count() {
    return this._index.size;
  }

  bundle() {
    return this._bundle;
  }
}
