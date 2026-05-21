/** Fly the map camera to a sensible viewing perspective for the selected entity. */
import * as Cesium from "cesium";
import { VIEW_PRESETS, flyTo } from "../cesium/viewer.js";

function toRad(deg) {
  return Cesium.Math.toRadians(Number(deg) || 0);
}

function offsetForKind(kind, data) {
  const heading = data?.track_deg != null
    ? toRad(Number(data.track_deg) + 180)
    : data?.heading != null
      ? toRad(Number(data.heading))
      : 0;

  switch (kind) {
    case "camera":
      // Oblique street-level view toward the lens location
      return new Cesium.HeadingPitchRange(heading, toRad(-38), 95);
    case "aircraft": {
      const alt = Number(data?.alt_m) || 0;
      const range = Math.max(600, Math.min(14_000, alt * 3.5 + 400));
      const pitch = alt > 2000 ? -22 : -32;
      return new Cesium.HeadingPitchRange(heading, toRad(pitch), range);
    }
    case "transit":
      return data?.kind === "regional_rail"
        ? new Cesium.HeadingPitchRange(heading, toRad(-28), 1400)
        : new Cesium.HeadingPitchRange(heading, toRad(-42), 260);
    case "indego":
      return new Cesium.HeadingPitchRange(0, toRad(-48), 160);
    case "satellite":
      return new Cesium.HeadingPitchRange(0, toRad(-20), 800_000);
    default:
      return new Cesium.HeadingPitchRange(0, toRad(-40), VIEW_PRESETS.neighborhood);
  }
}

function inferKind(id, data) {
  if (id.startsWith("camera:")) return "camera";
  if (id.startsWith("aircraft:")) return "aircraft";
  if (id.startsWith("septa_metro_")) return "transit";
  if (id.startsWith("septa_")) return "transit";
  if (id.startsWith("indego:")) return "indego";
  if (id.startsWith("satellite:") || data?.norad) return "satellite";
  return "poi";
}

function latLonFrom(entity, data) {
  if (data?.lat != null && data?.lon != null) {
    return { lat: Number(data.lat), lon: Number(data.lon) };
  }
  if (!entity?.position) return null;
  const p = entity.position.getValue?.(Cesium.JulianDate.now()) ?? entity.position;
  if (!p) return null;
  const carto = Cesium.Cartographic.fromCartesian(p);
  return {
    lat: Cesium.Math.toDegrees(carto.latitude),
    lon: Cesium.Math.toDegrees(carto.longitude),
  };
}

function flyToLatLon(viewer, lat, lon, kind, data, onComplete) {
  const offset = offsetForKind(kind, data);
  const range = offset.range;
  const pitch = offset.pitch;
  const heading = offset.heading;
  const height = Math.max(50, range * Math.sin(-pitch));
  const dest = Cesium.Cartesian3.fromDegrees(lon, lat, height);
  viewer.camera.flyTo({
    destination: dest,
    orientation: { heading, pitch, roll: 0 },
    duration: 1.1,
    complete: () => {
      viewer.scene.requestRender();
      onComplete?.();
    },
  });
}

/**
 * Fly to the selected entity with a type-appropriate offset (perspective).
 * @param {import('cesium').Viewer} viewer
 * @param {import('cesium').Entity} entity
 * @param {{ kind?: string, data?: object, onComplete?: () => void }} opts
 */
export function flyToSelectedEntity(viewer, entity, opts = {}) {
  if (!viewer || !entity) return;
  const id = String(entity.id ?? "");
  const data = opts.data ?? null;
  const kind = opts.kind ?? inferKind(id, data);
  const offset = offsetForKind(kind, data);
  const onComplete = opts.onComplete;

  const hasPosition = entity.position != null;
  if (hasPosition && !(entity.isCluster && entity.isCluster)) {
    try {
      viewer.flyTo(entity, {
        duration: 1.1,
        offset,
        complete: () => {
          viewer.scene.requestRender();
          onComplete?.();
        },
      });
      return;
    } catch {
      /* fall through to lat/lon */
    }
  }

  const ll = latLonFrom(entity, data);
  if (ll) {
    flyToLatLon(viewer, ll.lat, ll.lon, kind, data, onComplete);
    return;
  }

  onComplete?.();
}
