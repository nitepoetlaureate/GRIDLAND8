/** Camera entity collection. Each result is a billboard pinned to lat/lon. */
import * as Cesium from "cesium";

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
}
