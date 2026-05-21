/** Read API payload objects from Cesium entities (PropertyBag-safe). */
import * as Cesium from "cesium";

const NOW = () => Cesium.JulianDate.now();

/**
 * Unpack entity.properties whether it is a plain object, ConstantProperty, or
 * Cesium PropertyBag (one ConstantProperty per field — bag.getValue() is undefined).
 */
export function readEntityData(entity) {
  if (!entity) return null;
  if (entity._gridlandData) return entity._gridlandData;

  const props = entity.properties;
  if (!props) return null;

  const names = props.propertyNames;
  if (Array.isArray(names) && names.length > 0) {
    const out = {};
    for (const name of names) {
      const prop = props[name];
      if (prop == null) continue;
      out[name] = typeof prop.getValue === "function"
        ? prop.getValue(NOW())
        : prop;
    }
    return Object.keys(out).length ? out : null;
  }

  if (typeof props.getValue === "function") {
    const v = props.getValue(NOW());
    if (v != null && typeof v === "object") return v;
  }

  if (typeof props === "object" && !Array.isArray(props)) {
    const keys = Object.keys(props).filter((k) => k !== "propertyNames");
    if (keys.length) {
      const out = {};
      for (const k of keys) {
        const p = props[k];
        out[k] = p && typeof p.getValue === "function" ? p.getValue(NOW()) : p;
      }
      return out;
    }
  }

  return null;
}

/** HTML string from entity.description (InfoBox / fallback). */
export function readEntityDescriptionHtml(entity) {
  if (!entity?.description) return "";
  const d = entity.description;
  if (typeof d.getValue === "function") {
    return String(d.getValue(NOW()) ?? "");
  }
  return String(d ?? "");
}
