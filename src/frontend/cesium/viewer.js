/** CesiumJS viewer setup. Ion-free: OSM imagery, no terrain.
 *
 * Cesium 1.104+ removed the `imageryProvider` option from the Viewer
 * constructor. The basemap must be supplied as `baseLayer` (an ImageryLayer).
 * Passing `imageryProvider` silently does nothing and you get whatever default
 * imagery the build was compiled with — which, with Ion disabled, is nothing
 * (blank globe). See https://cesium.com/learn/cesiumjs/ref-doc/Viewer.html
 */
import * as Cesium from "cesium";
import "cesium/Build/Cesium/Widgets/widgets.css";

const OSM_TEMPLATE = "https://tile.openstreetmap.org/{z}/{x}/{y}.png";

function makeOsmLayer() {
  const provider = new Cesium.UrlTemplateImageryProvider({
    url: OSM_TEMPLATE,
    credit: new Cesium.Credit(
      '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
      true,
    ),
    maximumLevel: 19,
    tileWidth: 256,
    tileHeight: 256,
  });
  return new Cesium.ImageryLayer(provider);
}

export function createViewer(containerId) {
  Cesium.Ion.defaultAccessToken = undefined;
  const viewer = new Cesium.Viewer(containerId, {
    baseLayer: makeOsmLayer(),
    baseLayerPicker: false,
    geocoder: false,
    homeButton: false,
    sceneModePicker: false,
    navigationHelpButton: false,
    timeline: false,
    animation: false,
    fullscreenButton: false,
    infoBox: true,
    selectionIndicator: true,
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
