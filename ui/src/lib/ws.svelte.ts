// wtl-dllm · ui/src/lib/ws.svelte.ts
// what: websocket client + frame playback state (runes store)
// why:  frames accumulate once; the playhead replays them at any speed, any direction
// by:   <wtl> watchthelight
// tags: ui, websocket, store

export type Frame = {
  step: number;
  total_steps: number;
  tokens: string[];
  committed: boolean[];
  conf: number[];
  just_committed: number[];
  done: boolean;
  answer?: string;
  verdict?: string;
  error?: string;
};

export type GenRequest = {
  level?: number;
  prompt?: string;
  canvas_len?: number;
  steps?: number;
  ordering?: string;
  temperature?: number;
  throttle_ms?: number;
  seed?: number;
  infill?: { prefix: string; suffix: string; hole_len: number };
};

const WS_URL = import.meta.env.VITE_WS_URL ?? "ws://localhost:7311/ws/generate";
const API_URL = (import.meta.env.VITE_WS_URL ?? "ws://localhost:7311")
  .replace(/^ws/, "http")
  .replace(/\/ws\/generate$/, "");

class Session {
  status = $state<"idle" | "streaming" | "done" | "error">("idle");
  frames = $state<Frame[]>([]);
  playhead = $state(0);
  playing = $state(false);
  speedMs = $state(120);
  errorMsg = $state("");
  info = $state<Record<string, unknown> | null>(null);
  levels = $state<Record<string, { canvas: number; example: string; prompt: string }> | null>(null);

  #ws: WebSocket | null = null;
  #timer: number | null = null;

  get current(): Frame | null {
    return this.frames[this.playhead] ?? null;
  }
  get last(): Frame | null {
    return this.frames[this.frames.length - 1] ?? null;
  }

  async loadMeta() {
    try {
      this.info = await (await fetch(`${API_URL}/api/info`)).json();
      this.levels = await (await fetch(`${API_URL}/api/levels`)).json();
    } catch {
      this.errorMsg = "server not reachable on 7311 — start it with scripts/run.ps1";
    }
  }

  run(req: GenRequest) {
    this.stop();
    this.frames = [];
    this.playhead = 0;
    this.errorMsg = "";
    this.status = "streaming";
    this.#ws = new WebSocket(WS_URL);
    this.#ws.onopen = () => this.#ws!.send(JSON.stringify(req));
    this.#ws.onmessage = (ev) => {
      const f: Frame = JSON.parse(ev.data);
      if (f.error) {
        this.status = "error";
        this.errorMsg = f.error;
        return;
      }
      this.frames.push(f);
      if (this.frames.length === 1) this.play();
      if (f.done) this.status = "done";
    };
    this.#ws.onerror = () => {
      this.status = "error";
      this.errorMsg = "connection failed — is the server up?";
    };
  }

  play() {
    if (this.#timer) return;
    this.playing = true;
    const tick = () => {
      if (this.playhead < this.frames.length - 1) {
        this.playhead++;
        this.#timer = window.setTimeout(tick, this.speedMs);
      } else if (this.status === "streaming") {
        this.#timer = window.setTimeout(tick, 40); // wait for more frames
      } else {
        this.pause();
      }
    };
    this.#timer = window.setTimeout(tick, this.speedMs);
  }

  pause() {
    if (this.#timer) clearTimeout(this.#timer);
    this.#timer = null;
    this.playing = false;
  }

  scrub(i: number) {
    this.pause();
    this.playhead = Math.max(0, Math.min(i, this.frames.length - 1));
  }

  stop() {
    this.pause();
    this.#ws?.close();
    this.#ws = null;
  }
}

export const session = new Session();
