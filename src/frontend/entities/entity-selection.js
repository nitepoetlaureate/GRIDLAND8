/** Apply HUD detail panel + fly-to perspective for the selected Cesium entity. */
import { readEntityData } from "./entity-data.js";
import { flyToSelectedEntity } from "./fly-to-selection.js";

function kindFor(id, data) {
  if (id.startsWith("camera:")) return "camera";
  if (id.startsWith("aircraft:")) return "aircraft";
  if (id.startsWith("septa_metro_")) return "transit";
  if (id.startsWith("septa_")) return "transit";
  if (id.startsWith("indego:")) return "indego";
  return "poi";
}

function afterFly(viewer, ctx) {
  viewer?.scene?.requestRender?.();
  ctx.viewport?.refresh?.();
}

export function applyEntitySelection(ent, ctx) {
  const {
    viewer, entityDetail, transit, aircraft, indego, cameras, septaMetro, viewport,
    cameraFeedHooks, onSelectCameraId,
  } = ctx;

  if (!ent) {
    entityDetail.hide();
    return;
  }

  const id = String(ent.id ?? "");
  const data = readEntityData(ent);
  const kind = kindFor(id, data);

  flyToSelectedEntity(viewer, ent, {
    kind,
    data: data || transit?.getVehicle?.(id) || indego?.getStation?.(id.slice(7)) || cameras?.get?.(id),
    onComplete: () => afterFly(viewer, ctx),
  });

  if (id.startsWith("camera:")) {
    const cam = data || cameras.get(id);
    entityDetail.showCamera(cam, cameraFeedHooks || {});
    return;
  }
  if (id.startsWith("septa_metro_")) {
    const item = data || ctx.septaMetro?.getItem?.(id);
    entityDetail.showMetro(item, ctx.septaMetro?.bundle?.(), {
      onSelectCameraId: ctx.onSelectCameraId,
    });
    return;
  }
  if (id.startsWith("septa_")) {
    entityDetail.showTransit(data || transit.getVehicle(id));
    return;
  }
  if (id.startsWith("indego:")) {
    const stationId = id.slice("indego:".length);
    entityDetail.showIndego(data || indego.getStation(stationId));
    return;
  }
  if (id.startsWith("aircraft:")) {
    const ac = aircraft.getByEntity(ent) || data;
    if (ac) {
      entityDetail.showAircraft(ac);
      return;
    }
  }

  const ac = aircraft.getByEntity(ent);
  if (ac) {
    entityDetail.showAircraft(ac);
    return;
  }

  entityDetail.showFromEntity(ent);
}
