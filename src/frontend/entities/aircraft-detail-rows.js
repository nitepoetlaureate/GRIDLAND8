/** Aircraft detail table rows (ADS-B enriched; route airports need flight-plan API). */

function inferFlightFromCallsign(callsign) {
  const cs = (callsign || "").trim().toUpperCase();
  if (!cs || cs.length < 3) return null;
  const m = cs.match(/^([A-Z]{2,3})(\d{1,5}[A-Z]?)/);
  if (!m) return null;
  return { airline: m[1], flight_number: m[2] };
}

export function aircraftDetailRows(ac) {
  if (!ac) return [];
  const rows = [
    ["ICAO24", ac.icao24],
    ["Callsign", ac.callsign?.trim() || "—"],
  ];
  if (ac.registration) rows.push(["Registration", ac.registration]);
  if (ac.aircraft_type || ac.type_desc) {
    rows.push(["Type", [ac.aircraft_type, ac.type_desc].filter(Boolean).join(" · ") || "—"]);
  }
  if (ac.operator) rows.push(["Operator", ac.operator]);
  if (ac.category) rows.push(["Category", ac.category]);
  const flight = inferFlightFromCallsign(ac.callsign);
  if (flight) {
    rows.push(["Flight", `${flight.airline} ${flight.flight_number}`]);
  }
  if (ac.origin_airport || ac.destination_airport) {
    rows.push(["From", ac.origin_airport || "—"]);
    rows.push(["To", ac.destination_airport || "—"]);
  } else if (ac.track_deg != null) {
    rows.push(["Track", `${Math.round(ac.track_deg)}° (heading)`]);
    if (ac.nav_altitude_mcp_ft != null) {
      const mcpFt = Math.round(ac.nav_altitude_mcp_ft);
      rows.push(["Selected alt (MCP)", `${mcpFt} ft`]);
    }
  }
  rows.push(["Position", `${Number(ac.lat).toFixed(5)}, ${Number(ac.lon).toFixed(5)}`]);
  if (ac.alt_m != null) {
    rows.push(["Altitude", `${Math.round(ac.alt_m)} m (${Math.round(ac.alt_m * 3.281)} ft)`]);
  }
  if (ac.velocity_ms != null) {
    rows.push(["Speed", `${Math.round(ac.velocity_ms / 0.514444)} kt`]);
  }
  if (ac.vertical_rate_fpm != null) {
    const dir = ac.vertical_rate_fpm > 0 ? "climbing" : ac.vertical_rate_fpm < 0 ? "descending" : "level";
    rows.push(["Vertical", `${Math.round(ac.vertical_rate_fpm)} ft/min (${dir})`]);
  }
  if (ac.squawk) rows.push(["Squawk", ac.squawk]);
  if (ac.on_ground != null) rows.push(["On ground", ac.on_ground ? "yes" : "no"]);
  if (ac.origin_country) rows.push(["Country (ICAO)", ac.origin_country]);
  if (ac.distance_nm != null) rows.push(["Distance", `${ac.distance_nm.toFixed(1)} nm`]);
  return rows;
}
