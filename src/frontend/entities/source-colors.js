/** Per-source point colors for map layers. */
import * as Cesium from "cesium";

export const CAMERA_SOURCE_COLORS = {
  osm: "#ffb454",
  livecam: "#ff6b6b",
  penndot: "#4dabf7",
  nyctmc: "#69db7c",
  caltrans: "#ffd43b",
  wsdot: "#ffd43b",
  n511ny: "#ffd43b",
  castlerock_511: "#a9e34b",
  nps_webcams: "#63e6be",
  mapillary: "#da77f2",
  cam2: "#b197fc",
};

export function colorForCameraSource(source) {
  const hex = CAMERA_SOURCE_COLORS[source] || "#ffb454";
  return Cesium.Color.fromCssColorString(hex);
}

export const POI_COLORS = {
  crime: "#ff6b6b",
  shooting: "#e03131",
  park: "#51cf66",
  polling: "#74c0fc",
  zoning: "#9775fa",
  service_request: "#ffa94d",
  indego: "#3dd68c",
};
