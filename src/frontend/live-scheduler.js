/** Single timer for REST live polls (SEPTA fallback, Indego). */
const TICK_MS = 10_000;

export class LiveTickScheduler {
  constructor({ onTick, onVisibilityResume }) {
    this.onTick = onTick;
    this.onVisibilityResume = onVisibilityResume || onTick;
    this._timer = null;
    this._paused = false;
    document.addEventListener("visibilitychange", () => {
      if (document.hidden) {
        this._paused = true;
      } else {
        this._paused = false;
        void this.onVisibilityResume();
      }
    });
  }

  start() {
    if (this._timer) return;
    this._timer = setInterval(() => {
      if (this._paused) return;
      void this.onTick();
    }, TICK_MS);
  }

  stop() {
    if (this._timer) {
      clearInterval(this._timer);
      this._timer = null;
    }
  }
}
