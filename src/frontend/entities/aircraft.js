/** Aircraft entity collection. Reconciles incoming snapshots with existing
 *  entities — adds new ones, updates positions, removes stale ones. */
import * as Cesium from "cesium";

const STALE_MS = 30_000;

export class AircraftLayer {
  constructor(viewer) {
    this.viewer = viewer;
    this.collection = new Cesium.CustomDataSource("aircraft");
    viewer.dataSources.add(this.collection);
    /** Map<icao24, {entity, lastSeen}> */
    this._index = new Map();
  }

  update(snapshot) {
    const now = Date.now();
    const seen = new Set();
    for (const ac of snapshot.items) {
      seen.add(ac.icao24);
      const alt = ac.alt_m ?? 0;
      const pos = Cesium.Cartesian3.fromDegrees(ac.lon, ac.lat, alt);
      const existing = this._index.get(ac.icao24);
      if (existing) {
        existing.entity.position = pos;
        existing.lastSeen = now;
        existing.entity.label.text = this._labelText(ac);
      } else {
        const entity = this.collection.entities.add({
          position: pos,
          point: {
            pixelSize: 6,
            color: ac.on_ground
              ? Cesium.Color.fromCssColorString("#8b95a6")
              : Cesium.Color.fromCssColorString("#41d692"),
            outlineColor: Cesium.Color.BLACK,
            outlineWidth: 1,
          },
          label: {
            text: this._labelText(ac),
            font: "11px monospace",
            fillColor: Cesium.Color.WHITE,
            outlineColor: Cesium.Color.BLACK,
            outlineWidth: 2,
            style: Cesium.LabelStyle.FILL_AND_OUTLINE,
            pixelOffset: new Cesium.Cartesian2(8, -8),
            distanceDisplayCondition: new Cesium.DistanceDisplayCondition(0, 5e5),
          },
          properties: ac,
        });
        this._index.set(ac.icao24, { entity, lastSeen: now });
      }
    }
    for (const [icao24, rec] of this._index) {
      if (!seen.has(icao24) && now - rec.lastSeen > STALE_MS) {
        this.collection.entities.remove(rec.entity);
        this._index.delete(icao24);
      }
    }
  }

  _labelText(ac) {
    return ac.callsign?.trim() || ac.icao24.toUpperCase();
  }
}
