/** Debounced viewport center + bbox for live layer subscriptions. */
import * as Cesium from "cesium";
import { distance_nm_from_height_m, radius_km_from_height_m } from "./geo.js";

const DEBOUNCE_MS = 400;

export function isPhillyArea(lat, lon) {
  return lat > 39.86 && lat < 40.14 && lon > -75.28 && lon < -74.95;
}

export function viewportFromViewer(viewer) {
  const carto = viewer.camera.positionCartographic;
  const lat = Cesium.Math.toDegrees(carto.latitude);
  const lon = Cesium.Math.toDegrees(carto.longitude);
  const heightM = carto.height;
  const radiusKm = radius_km_from_height_m(heightM);
  const pad = radiusKm / 111.0;
  const cosLat = Math.max(0.5, Math.abs(Math.cos(carto.latitude)));
  return {
    lat,
    lon,
    heightM,
    radiusKm,
    distanceNm: distance_nm_from_height_m(heightM),
    bbox: {
      min_lat: lat - pad,
      max_lat: lat + pad,
      min_lon: lon - pad / cosLat,
      max_lon: lon + pad / cosLat,
    },
    philly: isPhillyArea(lat, lon),
  };
}

export class ViewportSubscriptionManager {
  constructor(viewer, onChange) {
    this.viewer = viewer;
    this.onChange = onChange || (() => {});
    this._timer = null;
    this._last = null;
    viewer.camera.moveEnd.addEventListener(() => this._schedule());
  }

  _schedule() {
    if (this._timer) clearTimeout(this._timer);
    this._timer = setTimeout(() => this._emit(), DEBOUNCE_MS);
  }

  _emit() {
    const vp = viewportFromViewer(this.viewer);
    this._last = vp;
    this.onChange(vp);
  }

  /** Push current viewport immediately (e.g. after scan fly). */
  refresh() {
    this._emit();
  }

  get last() {
    return this._last;
  }

  subscriptionPayload(vp = this._last) {
    if (!vp) return null;
    return {
      lat: vp.lat,
      lon: vp.lon,
      distance_nm: vp.distanceNm,
      transit: vp.philly,
      bbox: vp.bbox,
    };
  }
}
