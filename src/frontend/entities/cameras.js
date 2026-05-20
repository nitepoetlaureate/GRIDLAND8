/** Camera entity collection. Each result is a billboard pinned to lat/lon. */
import * as Cesium from "cesium";

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
    this.collection = new Cesium.CustomDataSource("cameras");
    viewer.dataSources.add(this.collection);
  }

  clear() {
    this.collection.entities.removeAll();
  }

  add(result) {
    this.collection.entities.add({
      id: `camera:${result.id}`,
      name: result.label || result.id,
      description: cameraDescription(result),
      position: Cesium.Cartesian3.fromDegrees(result.lon, result.lat, 10),
      point: {
        pixelSize: 8,
        color: Cesium.Color.fromCssColorString("#ffb454"),
        outlineColor: Cesium.Color.BLACK,
        outlineWidth: 1,
        heightReference: Cesium.HeightReference.RELATIVE_TO_GROUND,
      },
      label: {
        text: result.label,
        font: "11px monospace",
        fillColor: Cesium.Color.WHITE,
        outlineColor: Cesium.Color.BLACK,
        outlineWidth: 2,
        style: Cesium.LabelStyle.FILL_AND_OUTLINE,
        pixelOffset: new Cesium.Cartesian2(10, 0),
        distanceDisplayCondition: new Cesium.DistanceDisplayCondition(0, 4e4),
      },
      properties: result,
    });
  }

  setAll(results) {
    this.clear();
    for (const r of results) this.add(r);
  }

  setVisible(visible) {
    this.collection.show = visible;
  }
}
