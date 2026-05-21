/** CesiumJS viewer setup. Ion-free by default: OSM 2D imagery + ellipsoid terrain.
 *
 * Optional: set VITE_CESIUM_ION_ACCESS_TOKEN (free at ion.cesium.com) to enable
 * Cesium World Terrain and OSM 3D Buildings tileset.
 *
 * Cesium 1.104+ requires `baseLayer` (ImageryLayer), not `imageryProvider`.
 */
import * as Cesium from "cesium";
import "cesium/Build/Cesium/Widgets/widgets.css";

/** OSM raster tiles — discovery uses Overpass separately; this is only the basemap. */
const OSM_TEMPLATE =
  "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png";

/** Camera height presets (meters above ellipsoid). */
export const VIEW_PRESETS = {
  street: 350,
  neighborhood: 2500,
  metro: 12000,
  orbit: 50000,
};

function makeOsmLayer() {
  const provider = new Cesium.UrlTemplateImageryProvider({
    url: OSM_TEMPLATE,
    subdomains: ["a", "b", "c"],
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

/** Height for a discovery scan from radius (km) — avoids parking at 50 km altitude. */
export function heightForScanRadius(radiusKm) {
  const r = Number(radiusKm) || 25;
  return Math.min(VIEW_PRESETS.orbit, Math.max(VIEW_PRESETS.street * 2, r * 350));
}

function configureCameraController(viewer) {
  const ctrl = viewer.scene.screenSpaceCameraController;
  // Allow wheel / pinch zoom down to ~street level (meters above the ellipsoid).
  ctrl.minimumZoomDistance = 2.0;
  ctrl.maximumZoomDistance = 5.0e7;
  ctrl.enableCollisionDetection = false; // ellipsoid terrain — no mesh to collide with
  ctrl.minimumCollisionTerrainHeight = 0;
  // Tilt and look are required for oblique street-level views.
  ctrl.enableTilt = true;
  ctrl.enableLook = true;
  ctrl.enableTranslate = true;
  ctrl.enableZoom = true;
  ctrl.enableRotate = true;
}

async function applyIonEnhancements(viewer, ionToken) {
  if (!ionToken?.trim()) return { terrain: false, buildings: false };
  Cesium.Ion.defaultAccessToken = ionToken.trim();
  let terrain = false;
  let buildings = false;
  try {
    viewer.terrainProvider = await Cesium.createWorldTerrainAsync();
    viewer.scene.globe.depthTestAgainstTerrain = true;
    terrain = true;
  } catch (e) {
    console.warn("Cesium World Terrain unavailable:", e);
    viewer.terrainProvider = new Cesium.EllipsoidTerrainProvider();
  }
  try {
    const tileset = await Cesium.createOsmBuildingsAsync();
    viewer.scene.primitives.add(tileset);
    buildings = true;
  } catch (e) {
    console.warn("OSM 3D Buildings unavailable:", e);
  }
  return { terrain, buildings };
}

export async function createViewer(containerId, options = {}) {
  const ionToken = options.ionToken ?? import.meta.env.VITE_CESIUM_ION_ACCESS_TOKEN;
  if (!ionToken?.trim()) {
    Cesium.Ion.defaultAccessToken = undefined;
  }

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
    infoBox: false,
    selectionIndicator: true,
    terrainProvider: new Cesium.EllipsoidTerrainProvider(),
    // Retain sharp imagery when zoomed in (default can feel mushy).
    requestRenderMode: true,
  });

  configureCameraController(viewer);
  viewer.scene.globe.enableLighting = false;
  viewer.scene.skyAtmosphere.show = true;
  viewer.scene.fog.enabled = true;
  viewer.scene.globe.maximumScreenSpaceError = 1.5;

  const ion = await applyIonEnhancements(viewer, ionToken);
  viewer._gridlandMapStack = {
    basemap: "osm-raster",
    terrain: ion.terrain ? "cesium-world-terrain" : "ellipsoid",
    buildings3d: ion.buildings ? "cesium-osm-buildings" : "none",
  };
  return viewer;
}

export function flyTo(viewer, lat, lon, heightMeters = VIEW_PRESETS.metro, onComplete) {
  const dest = Cesium.Cartesian3.fromDegrees(lon, lat, heightMeters);
  viewer.camera.flyTo({
    destination: dest,
    duration: 1.2,
    complete: () => {
      const h = viewer.camera.positionCartographic?.height;
      onComplete?.({
        lat,
        lon,
        requestedHeightM: heightMeters,
        actualHeightM: h != null ? Math.round(h) : null,
      });
    },
  });
}

export function flyToPreset(viewer, lat, lon, preset, onComplete) {
  const h = VIEW_PRESETS[preset] ?? VIEW_PRESETS.metro;
  if (preset === "street") {
    const dest = Cesium.Cartesian3.fromDegrees(lon, lat, h);
    viewer.camera.flyTo({
      destination: dest,
      orientation: {
        heading: viewer.camera.heading,
        pitch: Cesium.Math.toRadians(-35),
        roll: 0,
      },
      duration: 1.2,
      complete: () => {
        const c = viewer.camera.positionCartographic;
        onComplete?.({
          lat,
          lon,
          requestedHeightM: h,
          actualHeightM: c != null ? Math.round(c.height) : null,
        });
      },
    });
    return;
  }
  flyTo(viewer, lat, lon, h, onComplete);
}

/** Read current camera state for debug / HUD. */
export function cameraState(viewer) {
  const c = viewer.camera.positionCartographic;
  if (!c) return null;
  return {
    lat: Cesium.Math.toDegrees(c.latitude),
    lon: Cesium.Math.toDegrees(c.longitude),
    heightM: Math.round(c.height),
    headingDeg: Math.round(Cesium.Math.toDegrees(viewer.camera.heading)),
    pitchDeg: Math.round(Cesium.Math.toDegrees(viewer.camera.pitch)),
  };
}
