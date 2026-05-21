/** Client-side geo helpers (mirror backend/shared/geo.py). */

export function radius_km_from_height_m(heightM) {
  const h = Math.max(100, Number(heightM) || 12000);
  return Math.min(80, Math.max(2, h / 800));
}

export function distance_nm_from_height_m(heightM) {
  const km = radius_km_from_height_m(heightM);
  const nm = km / 1.852;
  return Math.max(50, Math.min(400, Math.round(nm)));
}

export function bboxQueryParams(bbox) {
  if (!bbox) return "";
  const q = new URLSearchParams({
    min_lat: String(bbox.min_lat),
    min_lon: String(bbox.min_lon),
    max_lat: String(bbox.max_lat),
    max_lon: String(bbox.max_lon),
  });
  return `&${q.toString()}`;
}
