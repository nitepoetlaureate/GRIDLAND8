/** Live camera / stream preview panel (bottom HUD). */

function esc(s) {
  return String(s ?? "").replace(/[&<>"']/g, (c) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  })[c]);
}

function proxyFrameUrl(upstream) {
  if (!upstream || !/^https?:\/\//i.test(upstream)) return null;
  const q = new URLSearchParams({ url: upstream });
  return `/api/cameras/frame?${q}`;
}

/** Resolve a refreshable image URL for known operator patterns. */
export function streamImageUrl(cam) {
  if (!cam) return null;
  const thumb = (cam.thumbnail_url || cam.thumbnailUrl || "").trim();
  const tags = cam.tags || {};
  const streamUrl = tags.stream_url || tags["camera:stream"] || tags.stream || "";
  if (tags.stream_type === "refresh_jpeg" && streamUrl) {
    return proxyFrameUrl(streamUrl);
  }
  if (thumb && /\.(jpg|jpeg|png|gif)/i.test(thumb)) {
    return proxyFrameUrl(thumb) || thumb;
  }
  if (cam.source === "nyctmc" && thumb) return proxyFrameUrl(thumb) || thumb;
  if (streamUrl && /^https?:\/\//i.test(streamUrl)) {
    return proxyFrameUrl(streamUrl) || streamUrl;
  }
  return thumb ? (proxyFrameUrl(thumb) || thumb) : null;
}

/** Probe whether a proxied feed URL returns an image (best-effort). */
export async function probeFeedUrl(url) {
  if (!url) return false;
  try {
    const r = await fetch(url, { method: "GET", cache: "no-store" });
    const ct = r.headers.get("content-type") || "";
    return r.ok && (ct.includes("image") || r.status === 200);
  } catch {
    return false;
  }
}

/**
 * Resolve a HUD feed URL: known patterns first, then optional async discovery.
 * @param {object} cam
 * @param {{ fetchFrame?: (id: string) => Promise<string|null> }} hooks
 */
export async function resolveCameraFeedUrl(cam, hooks = {}) {
  const direct = streamImageUrl(cam);
  if (direct) {
    if (await probeFeedUrl(direct)) return direct;
  }
  if (hooks.fetchFrame && cam?.id) {
    const rawId = String(cam.id).replace(/^camera:/, "");
    try {
      const url = await hooks.fetchFrame(rawId);
      if (url && await probeFeedUrl(url)) return url;
    } catch {
      /* ignore */
    }
  }
  return direct || null;
}

export class CameraFeedPanel {
  constructor(rootId = "camera-feed") {
    this.el = document.getElementById(rootId);
    if (!this.el) {
      this.el = document.createElement("div");
      this.el.id = rootId;
      this.el.className = "camera-feed";
      this.el.hidden = true;
      const panel = document.getElementById("panel");
      if (panel) panel.appendChild(this.el);
    }
    this._timer = null;
    this._imgUrl = null;
  }

  show(cam) {
    if (!this.el || !cam) return;
    const imgUrl = streamImageUrl(cam);
    const pageUrl = cam.url || "";
    const label = cam.label || cam.name || cam.id || "Camera";
    let body = `<h4>${esc(label)}</h4>`;
    body += `<div class="meta">${esc(cam.source)} · ${esc(cam.lat?.toFixed?.(5))}, ${esc(cam.lon?.toFixed?.(5))}</div>`;
    const penndotPage = cam.source === "penndot" && pageUrl;
    if (imgUrl) {
      body += `<div class="feed-frame"><img id="camera-feed-img" src="${esc(imgUrl)}" alt="live feed" /></div>`;
      body += `<div class="feed-hint">Image refreshes every 8s when supported by the operator.</div>`;
    } else if (penndotPage) {
      body += `<div class="feed-hint">PennDOT live video requires a <code>N511PA_API_KEY</code> in <code>.env</code>. Open the 511PA page below for the intersection view.</div>`;
      body += `<div class="feed-frame feed-frame--page"><iframe src="${esc(pageUrl)}" title="511PA camera page" loading="lazy"></iframe></div>`;
    } else {
      body += `<div class="feed-hint">No public still-image URL for this pin — location only. NYC/Caltrans keys unlock JPEG feeds elsewhere.</div>`;
    }
    if (pageUrl && !penndotPage) {
      body += `<div><a href="${esc(pageUrl)}" target="_blank" rel="noopener">Open operator page →</a></div>`;
    } else if (pageUrl && penndotPage) {
      body += `<div><a href="${esc(pageUrl)}" target="_blank" rel="noopener">Open on 511PA (new tab) →</a></div>`;
    }
    this.el.innerHTML = body;
    this.el.hidden = false;
    this._imgUrl = imgUrl;
    this._startRefresh();
  }

  hide() {
    this._stopRefresh();
    if (this.el) {
      this.el.hidden = true;
      this.el.innerHTML = "";
    }
    this._imgUrl = null;
  }

  _startRefresh() {
    this._stopRefresh();
    if (!this._imgUrl) return;
    this._timer = setInterval(() => {
      const img = document.getElementById("camera-feed-img");
      if (!img) return;
      const sep = this._imgUrl.includes("?") ? "&" : "?";
      img.src = `${this._imgUrl}${sep}_t=${Date.now()}`;
    }, 8000);
  }

  _stopRefresh() {
    if (this._timer) {
      clearInterval(this._timer);
      this._timer = null;
    }
  }
}
