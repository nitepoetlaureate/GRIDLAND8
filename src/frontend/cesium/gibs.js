/**
 * NASA GIBS imagery providers for Cesium.
 *
 * GIBS serves global, daily, EPSG:4326 WMTS layers free of charge. We use the
 * KVP endpoint shape and pin TIME to "yesterday" (UTC) since today's product
 * may not have completed processing.
 *
 *   https://gibs.earthdata.nasa.gov/wmts/epsg4326/best/{LAYER}/default/{TIME}/{TILEMATRIXSET}/{z}/{y}/{x}.{ext}
 */
import * as Cesium from "cesium";

const BASE = "https://gibs.earthdata.nasa.gov/wmts/epsg4326/best";

function yesterdayUTC() {
  const d = new Date();
  d.setUTCDate(d.getUTCDate() - 1);
  return d.toISOString().slice(0, 10);
}

function makeProvider({ layer, format = "jpg", matrixSet = "250m", maxLevel = 8 }) {
  const time = yesterdayUTC();
  return new Cesium.UrlTemplateImageryProvider({
    url: `${BASE}/${layer}/default/${time}/${matrixSet}/{z}/{y}/{x}.${format}`,
    tilingScheme: new Cesium.GeographicTilingScheme(),
    maximumLevel: maxLevel,
    credit: new Cesium.Credit(
      `NASA EOSDIS GIBS · ${layer} · ${time}`,
      true,
    ),
  });
}

export const GIBS_LAYERS = {
  truecolor: {
    label: "Cloud cover (MODIS true color)",
    factory: () => makeProvider({
      layer: "MODIS_Terra_CorrectedReflectance_TrueColor",
      format: "jpg", matrixSet: "250m", maxLevel: 8,
    }),
  },
  fires: {
    label: "Active fires (VIIRS thermal)",
    factory: () => makeProvider({
      layer: "VIIRS_SNPP_Thermal_Anomalies_375m_Day",
      format: "png", matrixSet: "2km", maxLevel: 7,
    }),
  },
  aerosol: {
    label: "Aerosol optical depth (MODIS)",
    factory: () => makeProvider({
      layer: "MODIS_Combined_Value_Added_AOD",
      format: "png", matrixSet: "2km", maxLevel: 6,
    }),
  },
};

export class GibsLayers {
  constructor(viewer) {
    this.viewer = viewer;
    this._handles = new Map();
  }

  setEnabled(key, enabled) {
    if (enabled && !this._handles.has(key)) {
      const spec = GIBS_LAYERS[key];
      if (!spec) return;
      const provider = spec.factory();
      const layer = this.viewer.imageryLayers.addImageryProvider(provider);
      layer.alpha = 0.85;
      this._handles.set(key, layer);
    } else if (!enabled && this._handles.has(key)) {
      this.viewer.imageryLayers.remove(this._handles.get(key), true);
      this._handles.delete(key);
    }
  }

  isEnabled(key) {
    return this._handles.has(key);
  }
}
