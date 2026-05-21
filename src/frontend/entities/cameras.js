/** Camera entity collection. Each result is a billboard pinned to lat/lon. */
import * as Cesium from "cesium";
import { colorForCameraSource } from "./source-colors.js";
import { iconBillboard } from "./layer-icons.js";

function escape(s) {
  return String(s ?? "").replace(/[&<>"']/g, (c) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  })[c]);
}

function cameraDescription(r) {
  const rows = [
    ["Source", r.source],
    ["Publication", r.publication_status],
    ["Coordinates", `${r.lat?.toFixed?.(5)}, ${r.lon?.toFixed?.(5)}`],
  ];
  if (r.operator) rows.push(["Operator", r.operator]);
  if (r.tags && typeof r.tags === "object") {
    for (const [k, v] of Object.entries(r.tags)) {
      rows.push([escape(k), escape(v)]);
    }
  }
  const tableRows = rows.map(([k, v]) =>
    `<tr><td style="padding-right:8px;color:#8b95a6">${escape(k)}</td><td>${escape(v)}</td></tr>`
  ).join("");
  const thumb = r.thumbnail_url
    ? `<div style="margin-top:8px"><img src="${escape(r.thumbnail_url)}" alt="" style="max-width:100%;border:1px solid #1a2230" /></div>`
    : "";
  const link = r.url
    ? `<div style="margin-top:8px"><a href="${escape(r.url)}" target="_blank" rel="noopener">Open operator page →</a></div>`
    : "";
  return `<div><table style="font:12px monospace">${tableRows}</table>${thumb}${link}</div>`;
}

export class CameraLayer {
  constructor(viewer) {
    this.viewer = viewer;
    this._byId = new Map();
    this.collection = new Cesium.CustomDataSource("cameras");
    viewer.dataSources.add(this.collection);
    this.collection.clustering.enabled = true;
    this.collection.clustering.pixelRange = 30;
    this.collection.clustering.minimumClusterSize = 5;
  }

  clear() {
    this.collection.entities.removeAll();
    this._byId.clear();
  }

  get(id) {
    return this._byId.get(id) ?? null;
  }

  add(result) {
    const eid = `camera:${result.id}`;
    this._byId.set(eid, result);
    this.collection.entities.add({
      id: eid,
      name: result.label || result.id,
      description: cameraDescription(result),
      position: Cesium.Cartesian3.fromDegrees(result.lon, result.lat, 0),
      billboard: iconBillboard(
        "camera",
        colorForCameraSource(result.source).toCssColorString(),
        1.05,
      ),
      label: {
        text: (result.label || result.id || "").slice(0, 42),
        font: "11px monospace",
        fillColor: Cesium.Color.WHITE,
        outlineColor: Cesium.Color.BLACK,
        outlineWidth: 2,
        style: Cesium.LabelStyle.FILL_AND_OUTLINE,
        pixelOffset: new Cesium.Cartesian2(10, 0),
        distanceDisplayCondition: new Cesium.DistanceDisplayCondition(0, 1.2e5),
        scaleByDistance: new Cesium.NearFarScalar(800, 1, 8e5, 0),
      },
      properties: new Cesium.PropertyBag(result),
    });
  }

  setAll(results) {
    this.clear();
    for (const r of results) this.add(r);
  }

  setVisible(visible) {
    this.collection.show = visible;
  }

  /** Zoom map to fit all camera entities (after scan). */
  flyToResults(viewer, { duration = 1.0 } = {}) {
    const ents = this.collection.entities.values;
    if (!ents.length) return;
    viewer.flyTo(this.collection, { duration });
  }
}
