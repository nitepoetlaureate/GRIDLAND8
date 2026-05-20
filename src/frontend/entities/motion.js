/** Smooth position updates for live entities (SEPTA, aircraft). */
import * as Cesium from "cesium";

const DEFAULT_SECONDS = 12;

/**
 * Interpolate entity position over `seconds` (matches typical poll interval).
 * Requires viewer.clock.shouldAnimate = true.
 */
export function animateTo(entity, lon, lat, heightM = 0, seconds = DEFAULT_SECONDS) {
  const end = Cesium.Cartesian3.fromDegrees(lon, lat, heightM);
  const now = Cesium.JulianDate.now();
  let start = end;
  const pos = entity.position;
  if (pos?.getValue) {
    try {
      start = pos.getValue(now) || end;
    } catch {
      start = end;
    }
  }
  const prop = new Cesium.SampledPositionProperty();
  prop.setInterpolationOptions({
    interpolationDegree: 1,
    interpolationAlgorithm: Cesium.LinearApproximation,
  });
  prop.addSample(now, start);
  prop.addSample(Cesium.JulianDate.addSeconds(now, seconds, new Cesium.JulianDate()), end);
  entity.position = prop;
}

export function enableGlobeAnimation(viewer) {
  viewer.clock.shouldAnimate = true;
  viewer.clock.multiplier = 1;
}
