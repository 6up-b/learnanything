// Reader RW5d P2, the sketch compartment (G-SM14's remedy; spec_reader_show_me_figures_v1 §9.3-9.4):
// the messages that set it up, validated on every side.
//
// The Reader (sketchCompartment.ts) makes a sandboxed iframe (`allow-scripts`
// only, so its origin is opaque) on sketch-frame.html, whose CSP has
// `connect-src 'none'` and `worker-src blob:`. Inside it, the frame's one
// script creates the sketch Worker from a blob, so the Worker inherits that
// policy (a URL-loaded Worker would have had none: the G-SM14 probe). Two
// private MessageChannels, never a window message after the first handshake:
//
// - control (Reader <-> frame): Reader sends `boot {worker, engine}` (the
//   Worker's bundled source and the pinned engine's bytes, with the engine
//   channel's far port) and `stop`; the frame answers `connected`, `started`
//   or `failed {message}`. Anything else is dropped, both ways.
// - engine (Reader <-> Worker): exactly sketchProtocol.ts's requests and
//   replies (load, init, step, read), validated there.
//
// Nothing from the compartment is ever forwarded anywhere: the Reader parses
// these closed shapes and nothing else.

/** The frame document, served from the app's own assets (Tauri adds its CSP header; the page's frame-src names it). */
export const SKETCH_FRAME_PATH = "/sketch-frame.html";
/** keep (machine safety): the pinned engine is 869,346 bytes; a boot carrying more is refused (frame and Worker). */
export const SKETCH_ENGINE_MAX_BYTES = 2 * 1024 * 1024;
/** keep (machine safety): the bundled Worker source is tens of KiB; a boot carrying more is refused (frame). */
export const SKETCH_WORKER_SOURCE_MAX_CHARS = 1024 * 1024;
/** keep (display): the longest reason a `failed` notice may carry (the protocol's REPLY_MESSAGE_MAX). */
export const FRAME_MESSAGE_MAX = 600;

/** What the frame may tell the Reader. */
export type FrameNotice = { kind: "connected" } | { kind: "started" } | { kind: "failed"; message: string };

const isPlain = (value: unknown): value is Record<string, unknown> =>
  typeof value === "object" && value !== null && !Array.isArray(value) && Object.getPrototypeOf(value) === Object.prototype;

const hasOnly = (value: Record<string, unknown>, keys: string[]) =>
  Object.keys(value).length === keys.length && keys.every((key) => key in value);

/** The Reader's side of the control channel: a notice, or null (dropped) for anything else. An over-long
 *  reason is refused, and the notice still counts as a failure (with a code-written reason). */
export function parseFrameNotice(data: unknown): FrameNotice | null {
  if (!isPlain(data) || typeof data.kind !== "string") return null;
  if ((data.kind === "connected" || data.kind === "started") && hasOnly(data, ["kind"])) return { kind: data.kind };
  if (data.kind === "failed" && hasOnly(data, ["kind", "message"])) {
    const message = typeof data.message === "string" && data.message.length <= FRAME_MESSAGE_MAX
      ? data.message
      : "the sketch engine could not start here";
    return { kind: "failed", message };
  }
  return null;
}

/** What the Worker's owner (the frame) may send it, once: the engine's bytes and the engine channel's port. */
export function parseWorkerBoot(data: unknown, ports: readonly unknown[]): { engine: ArrayBuffer; port: MessagePort } | null {
  if (!isPlain(data) || data.kind !== "boot" || !hasOnly(data, ["kind", "engine"])) return null;
  // Not `instanceof`: a buffer that crossed a channel may come from another realm's constructor.
  if (Object.prototype.toString.call(data.engine) !== "[object ArrayBuffer]") return null;
  if ((data.engine as ArrayBuffer).byteLength === 0 || (data.engine as ArrayBuffer).byteLength > SKETCH_ENGINE_MAX_BYTES) return null;
  if (ports.length !== 1 || !ports[0] || typeof (ports[0] as MessagePort).postMessage !== "function") return null;
  return { engine: data.engine as ArrayBuffer, port: ports[0] as MessagePort };
}

/** The Worker's own network, import and context-making globals, removed once the engine is compiled
 *  (supplementary: the frame's CSP is the boundary, and the program inside the engine has no bindings).
 *  The G-SM14 probe found `fetch` and `importScripts` on WorkerGlobalScope.prototype in WebKitGTK, where
 *  deleting the own property only shadowed them; so every object on the global's prototype chain is
 *  cleared too, and the Worker constructors, which made a fresh, intact context, go as well. */
export const STRIPPED_GLOBALS = [
  "fetch", "XMLHttpRequest", "WebSocket", "EventSource", "importScripts", "indexedDB", "caches",
  "Worker", "SharedWorker", "WebTransport", "BroadcastChannel", "RTCPeerConnection",
] as const;

export function stripNetwork(scope: object): string[] {
  const kept: string[] = [];
  for (const name of STRIPPED_GLOBALS) {
    for (let level: object | null = scope; level; level = Object.getPrototypeOf(level)) {
      if (!Object.prototype.hasOwnProperty.call(level, name)) continue;
      try {
        delete (level as Record<string, unknown>)[name];
      } catch {
        // a non-configurable property stays (checked below)
      }
    }
    try {
      if ((scope as Record<string, unknown>)[name] !== undefined) {
        (scope as Record<string, unknown>)[name] = undefined;
      }
    } catch {
      // read-only: reported below
    }
    if ((scope as Record<string, unknown>)[name] !== undefined) kept.push(name);
  }
  return kept;
}
