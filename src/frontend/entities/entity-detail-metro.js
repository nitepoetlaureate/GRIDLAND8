/** Detail panel rows for SEPTA MFL/BSL metro entities. */

function esc(s) {
  return String(s ?? "").replace(/[&<>"']/g, (c) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  })[c]);
}

export function metroDetailRows(item, bundle) {
  if (!item) return [];
  const lineName = item.line === "MFL" ? "Market-Frankford Line" : "Broad Street Line";
  const rows = [
    ["Line", lineName],
    ["Type", item.kind === "metro_station" ? "Station" : "Train / run"],
  ];
  if (item.kind === "metro_vehicle") {
    rows.push(["Route ID", item.route || "—"]);
    rows.push(["Destination", item.destination || "—"]);
    rows.push(["Position quality", item.gps_live ? "Live GPS" : "Schedule only (no onboard GPS)"]);
    if (item.late_min != null && item.late_min !== "") {
      rows.push(["Late (min)", String(item.late_min)]);
    }
  }
  rows.push(["Coordinates", `${Number(item.lat).toFixed(5)}, ${Number(item.lon).toFixed(5)}`]);

  const lineAlerts = (bundle?.lines || []).find((l) => l.code === item.line);
  if (lineAlerts?.alerts?.length) {
    const a0 = lineAlerts.alerts[0];
    rows.push(["Alert", a0.current_message || a0.advisory_message || "—"]);
  }
  if (lineAlerts?.elevators?.length) {
    const e0 = lineAlerts.elevators[0];
    rows.push(["Elevator", `${e0.station}: ${e0.message || "outage"}`]);
  }
  return rows;
}

export function metroCameraListHtml(cameras, onSelectAttr = "") {
  if (!cameras?.length) {
    return `<p class="entity-detail-empty">No traffic cameras within ~400 m. SEPTA station CCTV is not public API.</p>`;
  }
  const items = cameras.map((c) => {
    const feed = c.has_feed ? " 📷" : "";
    const dist = c.distance_km != null ? ` (${c.distance_km} km)` : "";
    const cid = c.id ? `camera:${c.id}` : "";
    return `<li><button type="button" class="metro-cam-link" data-camera-id="${esc(cid)}" ${onSelectAttr}>${esc(c.label || c.id)}${esc(dist)}${feed}</button></li>`;
  }).join("");
  return `<div class="metro-cameras"><h5>Nearby cameras</h5><ul>${items}</ul></div>`;
}
