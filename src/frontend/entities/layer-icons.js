/** Pictographic map icons (canvas) — distinct identity per entity type. */
import * as Cesium from "cesium";

const _cache = new Map();

function stroke(ctx) {
  ctx.strokeStyle = "rgba(0,0,0,0.9)";
  ctx.lineWidth = 1.5;
  ctx.lineJoin = "round";
  ctx.lineCap = "round";
}

function drawCamera(ctx, fill) {
  ctx.fillStyle = fill;
  ctx.fillRect(8, 10, 16, 12);
  ctx.beginPath();
  ctx.arc(16, 16, 5, 0, Math.PI * 2);
  ctx.fillStyle = "#1a2230";
  ctx.fill();
  ctx.strokeStyle = fill;
  ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.moveTo(16, 6);
  ctx.lineTo(20, 10);
  ctx.lineTo(12, 10);
  ctx.closePath();
  ctx.fill();
  stroke(ctx);
  ctx.strokeRect(8, 10, 16, 12);
}

function drawBus(ctx, fill) {
  ctx.fillStyle = fill;
  ctx.beginPath();
  ctx.moveTo(8, 9);
  ctx.lineTo(24, 9);
  ctx.quadraticCurveTo(27, 9, 27, 12);
  ctx.lineTo(27, 20);
  ctx.quadraticCurveTo(27, 23, 24, 23);
  ctx.lineTo(8, 23);
  ctx.quadraticCurveTo(5, 23, 5, 20);
  ctx.lineTo(5, 12);
  ctx.quadraticCurveTo(5, 9, 8, 9);
  ctx.closePath();
  ctx.fill();
  ctx.fillStyle = "#1a2230";
  ctx.fillRect(8, 12, 6, 5);
  ctx.fillRect(18, 12, 6, 5);
  ctx.fillStyle = "#fff";
  ctx.fillRect(7, 20, 18, 2);
  stroke(ctx);
  ctx.stroke();
}

function drawTrain(ctx, fill) {
  ctx.fillStyle = fill;
  ctx.fillRect(4, 11, 24, 12);
  ctx.fillStyle = "#fff";
  for (let x = 7; x <= 22; x += 5) {
    ctx.fillRect(x, 13, 3, 5);
  }
  ctx.fillStyle = "#1a2230";
  ctx.beginPath();
  ctx.arc(8, 24, 2.5, 0, Math.PI * 2);
  ctx.arc(24, 24, 2.5, 0, Math.PI * 2);
  ctx.fill();
  stroke(ctx);
  ctx.stroke();
}

function drawMetroTrain(ctx, fill, badge) {
  drawTrain(ctx, fill);
  if (badge) drawBadge(ctx, badge, fill);
}

function drawMetroStation(ctx, fill, badge) {
  ctx.fillStyle = fill;
  ctx.beginPath();
  ctx.arc(16, 16, 10, 0, Math.PI * 2);
  ctx.fill();
  stroke(ctx);
  ctx.stroke();
  if (badge) drawBadge(ctx, badge, "#fff", fill);
}

function drawPlane(ctx, fill) {
  ctx.fillStyle = fill;
  ctx.beginPath();
  ctx.moveTo(16, 4);
  ctx.lineTo(26, 18);
  ctx.lineTo(16, 15);
  ctx.lineTo(6, 18);
  ctx.closePath();
  ctx.fill();
  ctx.fillRect(14, 15, 4, 10);
  stroke(ctx);
  ctx.stroke();
}

function drawHelicopter(ctx, fill) {
  ctx.strokeStyle = fill;
  ctx.fillStyle = fill;
  ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.moveTo(4, 10);
  ctx.lineTo(28, 10);
  ctx.stroke();
  ctx.beginPath();
  ctx.ellipse(16, 14, 8, 5, 0, 0, Math.PI * 2);
  ctx.fill();
  ctx.fillRect(14, 18, 4, 6);
  stroke(ctx);
}

function drawBoat(ctx, fill) {
  ctx.fillStyle = fill;
  ctx.beginPath();
  ctx.moveTo(6, 18);
  ctx.quadraticCurveTo(16, 8, 26, 18);
  ctx.lineTo(6, 18);
  ctx.fill();
  ctx.fillStyle = "#fff";
  ctx.fillRect(14, 10, 4, 8);
  stroke(ctx);
  ctx.stroke();
}

function drawBike(ctx, fill) {
  ctx.strokeStyle = fill;
  ctx.fillStyle = fill;
  ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.arc(10, 20, 5, 0, Math.PI * 2);
  ctx.arc(22, 20, 5, 0, Math.PI * 2);
  ctx.stroke();
  ctx.beginPath();
  ctx.moveTo(10, 20);
  ctx.lineTo(16, 10);
  ctx.lineTo(22, 20);
  ctx.stroke();
}

function drawSatellite(ctx, fill) {
  ctx.fillStyle = fill;
  ctx.fillRect(13, 13, 6, 6);
  ctx.beginPath();
  ctx.moveTo(4, 16);
  ctx.lineTo(12, 16);
  ctx.moveTo(20, 16);
  ctx.lineTo(28, 16);
  ctx.moveTo(16, 4);
  ctx.lineTo(16, 12);
  ctx.moveTo(16, 20);
  ctx.lineTo(16, 28);
  ctx.strokeStyle = fill;
  ctx.lineWidth = 2;
  ctx.stroke();
}

function drawBadge(ctx, letter, textColor, bgColor) {
  ctx.fillStyle = bgColor || "#000";
  ctx.beginPath();
  ctx.arc(24, 8, 7, 0, Math.PI * 2);
  ctx.fill();
  ctx.fillStyle = textColor || "#fff";
  ctx.font = "bold 9px system-ui,sans-serif";
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  ctx.fillText(letter, 24, 9);
}

const DRAWERS = {
  camera: drawCamera,
  bus: drawBus,
  train: drawTrain,
  "metro-train": drawMetroTrain,
  "metro-station": drawMetroStation,
  plane: drawPlane,
  helicopter: drawHelicopter,
  boat: drawBoat,
  bike: drawBike,
  satellite: drawSatellite,
};

/**
 * @param {keyof DRAWERS} type
 * @param {string} fillCss
 * @param {{ badge?: string }} [opts]
 */
export function iconDataUrl(type, fillCss, opts = {}) {
  const key = `${type}:${fillCss}:${opts.badge || ""}`;
  if (_cache.has(key)) return _cache.get(key);
  const size = 32;
  const canvas = document.createElement("canvas");
  canvas.width = size;
  canvas.height = size;
  const ctx = canvas.getContext("2d");
  if (!ctx) return "";
  ctx.clearRect(0, 0, size, size);
  const drawer = DRAWERS[type];
  if (drawer) {
    if (type === "metro-train" || type === "metro-station") {
      drawer(ctx, fillCss, opts.badge);
    } else {
      drawer(ctx, fillCss);
    }
  }
  const url = canvas.toDataURL("image/png");
  _cache.set(key, url);
  return url;
}

export function iconBillboard(type, fillCss, scale = 1.0, opts = {}) {
  const image = iconDataUrl(type, fillCss, opts);
  const px = Math.round(26 * scale);
  const alt = type.includes("plane") || type === "helicopter"
    ? Cesium.HeightReference.NONE
    : Cesium.HeightReference.CLAMP_TO_GROUND;
  return {
    image,
    width: px,
    height: px,
    scale: 1.0,
    color: Cesium.Color.WHITE,
    verticalOrigin: Cesium.VerticalOrigin.CENTER,
    horizontalOrigin: Cesium.HorizontalOrigin.CENTER,
    disableDepthTestDistance: Number.POSITIVE_INFINITY,
    heightReference: alt,
    rotation: opts.rotation ?? 0,
  };
}

export function aircraftIconType(ac) {
  const cat = String(ac?.category || "").toUpperCase();
  if (cat.startsWith("H")) return "helicopter";
  return "plane";
}
