/** Cached canvas glyphs so layers are visually distinct on the map. */
import * as Cesium from "cesium";

const _cache = new Map();

function drawShape(ctx, style, size) {
  const s = size;
  const h = s / 2;
  ctx.clearRect(0, 0, s, s);
  ctx.beginPath();
  switch (style) {
    case "square":
      ctx.rect(4, 4, s - 8, s - 8);
      break;
    case "diamond":
      ctx.moveTo(h, 2);
      ctx.lineTo(s - 2, h);
      ctx.lineTo(h, s - 2);
      ctx.lineTo(2, h);
      ctx.closePath();
      break;
    case "triangle":
      ctx.moveTo(h, 3);
      ctx.lineTo(s - 3, s - 4);
      ctx.lineTo(3, s - 4);
      ctx.closePath();
      break;
    case "ring":
      ctx.arc(h, h, h - 4, 0, Math.PI * 2);
      break;
    default:
      ctx.arc(h, h, h - 3, 0, Math.PI * 2);
  }
  ctx.fill();
  ctx.strokeStyle = "rgba(0,0,0,0.85)";
  ctx.lineWidth = 2;
  ctx.stroke();
}

/**
 * @param {"square"|"diamond"|"triangle"|"ring"|"circle"} style
 * @param {string} fillCss
 * @returns {string} data URL for Cesium billboard
 */
export function glyphDataUrl(style, fillCss) {
  const key = `${style}:${fillCss}`;
  if (_cache.has(key)) return _cache.get(key);
  const size = 28;
  const canvas = document.createElement("canvas");
  canvas.width = size;
  canvas.height = size;
  const ctx = canvas.getContext("2d");
  if (!ctx) return "";
  ctx.fillStyle = fillCss;
  drawShape(ctx, style, size);
  const url = canvas.toDataURL("image/png");
  _cache.set(key, url);
  return url;
}

/** Standard billboard options for a layer glyph. */
export function glyphBillboard(style, fillCss, scale = 1.0) {
  const image = glyphDataUrl(style, fillCss);
  const px = Math.round(22 * scale);
  return {
    image,
    width: px,
    height: px,
    scale: 1.0,
    color: Cesium.Color.WHITE,
    verticalOrigin: Cesium.VerticalOrigin.CENTER,
    horizontalOrigin: Cesium.HorizontalOrigin.CENTER,
    disableDepthTestDistance: Number.POSITIVE_INFINITY,
    heightReference: Cesium.HeightReference.CLAMP_TO_GROUND,
  };
}

export const LAYER_LEGEND = [
  { label: "Cameras", icon: "camera", color: "#ffb454" },
  { label: "SEPTA bus", icon: "bus", color: "#003DA5" },
  { label: "Regional rail", icon: "train", color: "#E91329" },
  { label: "Metro L (MFL)", icon: "metro-station", color: "#00A651", badge: "L" },
  { label: "Metro B (BSL)", icon: "metro-station", color: "#FF8200", badge: "B" },
  { label: "Aircraft", icon: "plane", color: "#41d692" },
  { label: "Helicopter", icon: "helicopter", color: "#74c0fc" },
  { label: "Indego", icon: "bike", color: "#3dd68c" },
];
