/** Aircraft entity collection. Handles snapshot + diff frames from /ws/live. */
import * as Cesium from "cesium";

const STALE_MS = 60_000;

export class AircraftLayer {
  constructor(viewer) {
    this.viewer = viewer;
    this.collection = new Cesium.CustomDataSource("aircraft");
    viewer.dataSources.add(this.collection);
    this._index = new Map();
  }

  handleFrame(frame) {
    if (frame.kind === "snapshot") this._applySnapshot(frame);
    else if (frame.kind === "diff") this._applyDiff(frame);
    this._expireStale();
  }

  _applySnapshot(frame) {
    this.collection.entities.removeAll();
    this._index.clear();
    const now = Date.now();
    for (const ac of frame.items) {
      this._index.set(ac.icao24, { entity: this._add(ac), lastSeen: now });
    }
  }

  _applyDiff(frame) {
    const now = Date.now();
    for (const ac of frame.added ?? []) {
      const rec = this._index.get(ac.icao24);
      if (rec) {
        this._update(rec.entity, ac);
        rec.lastSeen = now;
      } else {
        this._index.set(ac.icao24, { entity: this._add(ac), lastSeen: now });
      }
    }
    for (const ac of frame.updated ?? []) {
      const rec = this._index.get(ac.icao24);
      if (rec) {
        this._update(rec.entity, ac);
        rec.lastSeen = now;
      } else {
        this._index.set(ac.icao24, { entity: this._add(ac), lastSeen: now });
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
    return this.collection.entities.add({
      position: Cesium.Cartesian3.fromDegrees(ac.lon, ac.lat, ac.alt_m ?? 0),
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
  }

  _update(entity, ac) {
    entity.position = Cesium.Cartesian3.fromDegrees(ac.lon, ac.lat, ac.alt_m ?? 0);
    entity.label.text = this._labelText(ac);
    entity.point.color = ac.on_ground
      ? Cesium.Color.fromCssColorString("#8b95a6")
      : Cesium.Color.fromCssColorString("#41d692");
  }

  _labelText(ac) {
    return ac.callsign?.trim() || ac.icao24.toUpperCase();
  }

  setVisible(visible) {
    this.collection.show = visible;
  }
}
