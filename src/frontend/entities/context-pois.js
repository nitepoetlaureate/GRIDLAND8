/** Context POIs from /api/context — crime, parks, 311, Indego, etc. */
import * as Cesium from "cesium";
import { POI_COLORS } from "./source-colors.js";

function esc(s) {
  return String(s ?? "").replace(/[&<>"']/g, (c) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  })[c]);
}

function tableHtml(rows) {
  return `<table style="font:12px monospace">` +
    rows.map(([k, v]) =>
      `<tr><td style="padding-right:8px;color:#8b95a6">${esc(k)}</td><td>${esc(v)}</td></tr>`
    ).join("") + `</table>`;
}

function addPoint(ds, { id, lat, lon, color, name, description, pixelSize = 9 }) {
  if (lat == null || lon == null) return;
  ds.entities.add({
    id,
    name,
    description,
    position: Cesium.Cartesian3.fromDegrees(lon, lat, 0),
    point: {
      pixelSize,
      color: Cesium.Color.fromCssColorString(color),
      outlineColor: Cesium.Color.BLACK,
      outlineWidth: 1,
      disableDepthTestDistance: Number.POSITIVE_INFINITY,
      scaleByDistance: new Cesium.NearFarScalar(500, 1.4, 8e5, 0.6),
      heightReference: Cesium.HeightReference.CLAMP_TO_GROUND,
    },
  });
}

export class ContextPoiLayer {
  constructor(viewer) {
    this.viewer = viewer;
    this.dataSource = new Cesium.CustomDataSource("context-pois");
    viewer.dataSources.add(this.dataSource);
    this.dataSource.clustering.enabled = true;
    this.dataSource.clustering.pixelRange = 28;
    this.dataSource.clustering.minimumClusterSize = 4;
  }

  clear() {
    this.dataSource.entities.removeAll();
  }

  setFromContext(ctx) {
    this.clear();
    if (!ctx) return;
    const odp = ctx.opendataphilly?.layers;
    if (odp) {
      for (const c of odp.crime_incidents || []) {
        addPoint(this.dataSource, {
          id: `crime:${c.id}`,
          lat: c.lat, lon: c.lon,
          color: POI_COLORS.crime,
          name: c.type || "Crime dispatch",
          description: tableHtml([
            ["Type", c.type], ["Block", c.block], ["UCR", c.ucr], ["At", c.at],
          ]),
          pixelSize: 8,
        });
      }
      for (const s of odp.shootings || []) {
        addPoint(this.dataSource, {
          id: `shooting:${s.id}`,
          lat: s.lat, lon: s.lon,
          color: POI_COLORS.shooting,
          name: "Shooting",
          description: tableHtml([
            ["Location", s.location], ["Code", s.code], ["Date", s.at],
          ]),
          pixelSize: 10,
        });
      }
      for (const p of odp.parks || []) {
        addPoint(this.dataSource, {
          id: `park:${p.id}`,
          lat: p.lat, lon: p.lon,
          color: POI_COLORS.park,
          name: p.name || "Park",
          description: tableHtml([
            ["Name", p.name], ["Address", p.address], ["Acreage", p.acreage],
          ]),
        });
      }
      for (const p of odp.polling_places || []) {
        addPoint(this.dataSource, {
          id: `poll:${p.id}`,
          lat: p.lat, lon: p.lon,
          color: POI_COLORS.polling,
          name: p.name || "Polling place",
          description: tableHtml([
            ["Place", p.name], ["Address", p.address], ["Ward", p.ward],
          ]),
          pixelSize: 7,
        });
      }
      for (const z of odp.zoning_overlays || []) {
        addPoint(this.dataSource, {
          id: `zone:${z.id}`,
          lat: z.lat, lon: z.lon,
          color: POI_COLORS.zoning,
          name: z.name || "Zoning overlay",
          description: tableHtml([
            ["Name", z.name], ["Type", z.type], ["Code", z.code_section],
          ]),
          pixelSize: 7,
        });
      }
    }
    for (const s of ctx.service_requests || []) {
      if (s.lat == null || s.lon == null) continue;
      addPoint(this.dataSource, {
        id: `311:${s.id ?? `${s.lat},${s.lon}`}`,
        lat: s.lat, lon: s.lon,
        color: POI_COLORS.service_request,
        name: s.service_name || "311 request",
        description: tableHtml([
          ["Service", s.service_name], ["Status", s.status], ["At", s.requested_at],
        ]),
        pixelSize: 7,
      });
    }
    for (const st of ctx.indego_stations || []) {
      addPoint(this.dataSource, {
        id: `indego-ctx:${st.station_id}`,
        lat: st.lat, lon: st.lon,
        color: POI_COLORS.indego,
        name: st.name || "Indego",
        description: tableHtml([
          ["Bikes", st.bikes], ["Docks", st.docks],
          ["Renting", st.is_renting], ["Returning", st.is_returning],
        ]),
        pixelSize: 10,
      });
    }
  }

  setVisible(visible) {
    this.dataSource.show = visible;
  }

  count() {
    return this.dataSource.entities.values.length;
  }
}
