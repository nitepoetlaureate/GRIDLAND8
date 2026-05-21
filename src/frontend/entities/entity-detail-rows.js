/** Row builders for entity detail tables (shared with transit layer). */

export function transitDetailRows(v) {
  if (!v) return [];
  const isRail = v.kind === "regional_rail";
  const rows = [
    ["Mode", isRail ? "Regional Rail" : "Bus / Trolley"],
    ["Route / Line", v.route || "—"],
    ["Destination", v.destination || "—"],
  ];
  if (isRail) {
    rows.push(["Train #", String(v.id || "").replace(/^septa_train_/, "") || "—"]);
    rows.push(["Service", v.service || "—"]);
    rows.push(["Origin station", v.source_station || "—"]);
    rows.push(["Current stop", v.current_stop || "—"]);
    rows.push(["Next stop", v.next_stop || "—"]);
    rows.push(["Track", v.track || "—"]);
    if (v.consist) rows.push(["Consist", v.consist]);
  } else {
    rows.push(["Direction", v.direction || "—"]);
    rows.push(["Next stop", v.next_stop || "—"]);
    rows.push(["Seats", v.seat_availability || "—"]);
  }
  if (v.heading != null && v.heading !== "") {
    rows.push(["Heading°", String(v.heading)]);
  }
  const late = v.late_min;
  rows.push(["Late (min)", late == null || late === "" ? "—" : String(late)]);
  rows.push(["Position", `${Number(v.lat).toFixed(5)}, ${Number(v.lon).toFixed(5)}`]);
  return rows;
}
