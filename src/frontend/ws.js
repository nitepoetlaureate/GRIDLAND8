/** WebSocket client for /ws/live. Auto-reconnects with exponential backoff. */

export class LiveSocket {
  constructor({ url, subscription, onMessage, onStatus }) {
    this.url = url;
    this.subscription = subscription;
    this.onMessage = onMessage || (() => {});
    this.onStatus = onStatus || (() => {});
    this._ws = null;
    this._closed = false;
    this._backoff = 1000;
    this._reconnectTimer = null;
  }

  connect() {
    this._closed = false;
    this._open();
  }

  close() {
    this._closed = true;
    if (this._reconnectTimer) clearTimeout(this._reconnectTimer);
    if (this._ws) this._ws.close();
  }

  setSubscription(sub) {
    this.subscription = sub;
    if (this._ws && this._ws.readyState === WebSocket.OPEN) {
      this._ws.send(JSON.stringify(sub));
    }
  }

  _open() {
    this.onStatus("connecting");
    this._ws = new WebSocket(this.url);
    this._ws.addEventListener("open", () => {
      this._backoff = 1000;
      this.onStatus("open");
      this._ws.send(JSON.stringify(this.subscription));
    });
    this._ws.addEventListener("message", (ev) => {
      try {
        const data = JSON.parse(ev.data);
        this.onMessage(data);
      } catch (e) {
        console.warn("bad ws frame", e);
      }
    });
    this._ws.addEventListener("close", () => {
      this.onStatus("closed");
      if (!this._closed) this._scheduleReconnect();
    });
    this._ws.addEventListener("error", () => {
      this.onStatus("error");
    });
  }

  _scheduleReconnect() {
    const delay = Math.min(this._backoff, 30000);
    this._reconnectTimer = setTimeout(() => {
      this._backoff = Math.min(this._backoff * 2, 30000);
      this._open();
    }, delay);
  }
}

export function liveUrl(path = "/ws/live") {
  const proto = window.location.protocol === "https:" ? "wss:" : "ws:";
  return `${proto}//${window.location.host}${path}`;
}
