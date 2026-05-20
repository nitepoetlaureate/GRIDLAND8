/** CesiumJS viewer setup. Ion-free: OSM imagery, no terrain. */
import * as Cesium from "cesium";
import "cesium/Build/Cesium/Widgets/widgets.css";

export function createViewer(containerId) {
  Cesium.Ion.defaultAccessToken = undefined;
  const viewer = new Cesium.Viewer(containerId, {
    baseLayerPicker: false,
    geocoder: false,
    homeButton: false,
    sceneModePicker: false,
    navigationHelpButton: false,
    timeline: false,
    animation: false,
    fullscreenButton: false,
    selectionIndicator: false,
    infoBox: false,
    imageryProvider: new Cesium.OpenStreetMapImageryProvider({
      url: "https://tile.openstreetmap.org/",
    }),
    terrainProvider: new Cesium.EllipsoidTerrainProvider(),
  });
  viewer.scene.globe.enableLighting = false;
  viewer.scene.skyAtmosphere.show = true;
  viewer.scene.fog.enabled = true;
  return viewer;
}

export function flyTo(viewer, lat, lon, heightMeters = 25000) {
  viewer.camera.flyTo({
    destination: Cesium.Cartesian3.fromDegrees(lon, lat, heightMeters),
    duration: 1.5,
  });
}
