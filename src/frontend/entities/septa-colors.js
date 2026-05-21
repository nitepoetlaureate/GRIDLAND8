/** SEPTA wayfinding colors — regional rail lines, Metro L (MFL), Broad (BSL). */

/** Market-Frankford Line (L) — SEPTA green */
export const MFL_COLOR = "#00A651";
/** Broad Street Line (B) — SEPTA orange */
export const BSL_COLOR = "#FF8200";

/** Regional rail line name → official map color (approximate SEPTA system map). */
const RAIL_LINE_COLORS = [
  ["Airport", "#FF8200"],
  ["Chestnut Hill East", "#8E258D"],
  ["Chestnut Hill West", "#56AD3D"],
  ["Cynwyd", "#709B8D"],
  ["Fox Chase", "#FF8200"],
  ["Lansdale", "#D52D2D"],
  ["Doylestown", "#D52D2D"],
  ["Manayunk", "#E96A9A"],
  ["Norristown", "#E96A9A"],
  ["Media", "#0571B1"],
  ["Elwyn", "#0571B1"],
  ["Paoli", "#F14729"],
  ["Thorndale", "#F14729"],
  ["Trenton", "#E91329"],
  ["West Trenton", "#E91329"],
  ["Warminster", "#00A651"],
  ["Wilmington", "#00A651"],
  ["Newark", "#00A651"],
  ["Glenside", "#E91329"],
  ["West Chester", "#E96A9A"],
];

const BUS_DEFAULT = "#003DA5";
const BUS_TROLLEY = "#6E4B9E";

export function metroLineColor(line) {
  return line === "BSL" ? BSL_COLOR : MFL_COLOR;
}

export function metroLineBadge(line) {
  return line === "BSL" ? "B" : "L";
}

export function metroLineLabel(line) {
  return line === "BSL" ? "Broad St (B)" : "Market-Frankford (L)";
}

/** @param {string} routeOrLine — TrainView line name or route id */
export function regionalRailColor(routeOrLine) {
  const s = String(routeOrLine || "").trim();
  if (!s) return "#41a8ff";
  const lower = s.toLowerCase();
  for (const [name, color] of RAIL_LINE_COLORS) {
    if (lower.includes(name.toLowerCase())) return color;
  }
  return "#41a8ff";
}

export function busRouteColor(route) {
  const r = String(route || "").toUpperCase();
  if (r.startsWith("T") || r.includes("TROLLEY")) return BUS_TROLLEY;
  return BUS_DEFAULT;
}
