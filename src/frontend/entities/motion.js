/** Smooth position updates for live entities (SEPTA, aircraft). */
import * as Cesium from "cesium";

const DEFAULT_SECONDS = 12;
const _props = new WeakMap();

function finiteCoord(lon, lat, h = 0) {
  const lo = Number(lon);
  const la = Number(lat);
  const ht = Number(h);
  if (!Number.isFinite(lo) || !Number.isFinite(la)) return null;
  return { lon: lo, lat: la, h: Number.isFinite(ht) ? ht : 0 };
}

function readStartPosition(entity, fallback) {
  const rec = _props.get(entity);
  if (rec?.prop) {
    try {
      const cur = rec.prop.getValue(Cesium.JulianDate.now());
      if (cur) return Cesium.Cartesian3.clone(cur);
    } catch {
      /* ignore */
    }
  }
  const pos = entity.position;
  if (pos?.getValue) {
    try {
      const cur = pos.getValue(Cesium.JulianDate.now());
      if (cur) return Cesium.Cartesian3.clone(cur);
    } catch {
      /* ignore */
    }
  }
  return Cesium.Cartesian3.clone(fallback);
}

function pruneSamples(prop, now, keepSeconds = 30) {
  try {
    const times = prop._property?._times || prop._times;
    if (!times?.length) return;
    const cutoff = Cesium.JulianDate.addSeconds(
      now, -keepSeconds, new Cesium.JulianDate(),
    );
    while (times.length > 2 && Cesium.JulianDate.lessThan(times[0], cutoff)) {
      prop.removeSample(times[0]);
    }
  } catch {
    /* Cesium internals vary by version */
  }
}

/**
 * Reuse one SampledPositionProperty per entity; append samples for smooth motion.
 */
export function animateTo(entity, lon, lat, heightM = 0, seconds = DEFAULT_SECONDS) {
  const to = finiteCoord(lon, lat, heightM);
  if (!to) return;

  const end = Cesium.Cartesian3.fromDegrees(to.lon, to.lat, to.h);
  const now = Cesium.JulianDate.now();
  const start = readStartPosition(entity, end);
  let rec = _props.get(entity);
  if (!rec) {
    const prop = new Cesium.SampledPositionProperty();
    prop.setInterpolationOptions({
      interpolationDegree: 1,
      interpolationAlgorithm: Cesium.LinearApproximation,
    });
    rec = { prop };
    _props.set(entity, rec);
    entity.position = prop;
  }
  const { prop } = rec;
  prop.addSample(now, start);
  const endTime = Cesium.JulianDate.addSeconds(now, seconds, new Cesium.JulianDate());
  prop.addSample(endTime, end);
  pruneSamples(prop, now);
}

export function enableGlobeAnimation(viewer) {
  viewer.clock.shouldAnimate = true;
  viewer.clock.multiplier = 1;
}

export function requestSceneRender(viewer) {
  viewer?.scene?.requestRender?.();
}
