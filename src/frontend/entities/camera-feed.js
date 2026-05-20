/** Live camera / stream preview panel (bottom HUD). */

function esc(s) {
  return String(s ?? "").replace(/[&<>"']/g, (c) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  })[c]);
}

/** Resolve a refreshable image URL for known operator patterns. */
export function streamImageUrl(cam) {
  if (!cam) return null;
  const thumb = (cam.thumbnail_url || cam.thumbnailUrl || "").trim();
  if (thumb && /\.(jpg|jpeg|png|gif)/i.test(thumb)) return thumb;
  const src = cam.source || "";
  const tags = cam.tags || {};
  if (src === "nyctmc" && thumb) return thumb;
  const sw = tags.statewide_id || tags.statewideId;
  if (src === "penndot" && sw) {
    return `https://www.511pa.com/Traffic/Cctv/${sw}`;
  }
  const stream = tags["camera:stream"] || tags.stream_url || tags.stream;
  if (stream && /^https?:\/\//i.test(stream)) return stream;
  return thumb || null;
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
    if (imgUrl) {
      body += `<div class="feed-frame"><img id="camera-feed-img" src="${esc(imgUrl)}" alt="live feed" /></div>`;
      body += `<div class="feed-hint">Image refreshes every 8s when supported by the operator.</div>`;
    } else {
      body += `<div class="feed-hint">No public still-image URL for this source. PennDOT live video requires a 511PA API key.</div>`;
    }
    if (pageUrl) {
      body += `<div><a href="${esc(pageUrl)}" target="_blank" rel="noopener">Open operator page →</a></div>`;
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
