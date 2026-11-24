// The notebook bridge, the workbench's side (spec §11.3): the four messages a notebook frame posts.
//
// A message is accepted only when it comes from the iframe this window created (`event.source` is its
// `contentWindow`), from that frame's own origin (`event.origin` equals the origin of its frame URL), and has
// exactly the shape of one of the four kinds. Notebook JavaScript (model-written widget code included) shares the
// frame's origin and can post these too, so a payload is never more than untrusted notebook text: the text is
// quoted as plain text (never HTML, never a command), and a rectangle or point is clamped to the frame's box.

export type BridgeKind = "companion" | "menu" | "click" | "escape";

export interface BridgeRect {
  x: number;
  y: number;
  width: number;
  height: number;
}

export type BridgeMessage =
  | { ll: "companion"; text: string; rect: BridgeRect | null; shift: boolean }
  | { ll: "menu"; text: string; rect: BridgeRect | null; x: number; y: number }
  | { ll: "click" }
  | { ll: "escape" };

/** The longest selection a frame may send (the proxy's bridge sends no more; anything longer is refused). */
export const BRIDGE_TEXT_MAX = 4000;

const KEYS: Record<BridgeKind, readonly string[]> = {
  companion: ["ll", "text", "rect", "shift"],
  menu: ["ll", "text", "rect", "x", "y"],
  click: ["ll"],
  escape: ["ll"],
};

function plainObject(value: unknown): value is Record<string, unknown> {
  if (value === null || typeof value !== "object" || Array.isArray(value)) return false;
  const proto = Object.getPrototypeOf(value);
  return proto === Object.prototype || proto === null;
}

function finite(value: unknown): value is number {
  return typeof value === "number" && Number.isFinite(value);
}

function rectOf(value: unknown): BridgeRect | null | undefined {
  if (value === null) return null;
  if (!plainObject(value)) return undefined;
  const keys = Object.keys(value).sort().join(",");
  if (keys !== "height,width,x,y") return undefined;
  const { x, y, width, height } = value;
  if (!finite(x) || !finite(y) || !finite(width) || !finite(height) || width < 0 || height < 0) return undefined;
  return { x, y, width, height };
}

/** The message's typed form, or null when its shape is not exactly one of the four. */
export function parseBridgeMessage(data: unknown): BridgeMessage | null {
  if (!plainObject(data)) return null;
  const kind = data.ll;
  if (kind !== "companion" && kind !== "menu" && kind !== "click" && kind !== "escape") return null;
  const keys = Object.keys(data);
  if (keys.length !== KEYS[kind].length || !keys.every((key) => KEYS[kind].includes(key))) return null;
  if (kind === "click" || kind === "escape") return { ll: kind };
  const text = data.text;
  if (typeof text !== "string" || text.length > BRIDGE_TEXT_MAX) return null;
  const rect = rectOf(data.rect);
  if (rect === undefined) return null;
  if (kind === "companion") {
    if (typeof data.shift !== "boolean") return null;
    return { ll: "companion", text, rect, shift: data.shift };
  }
  if (!finite(data.x) || !finite(data.y)) return null;
  return { ll: "menu", text, rect, x: data.x, y: data.y };
}

/** The origin a frame URL serves from, or null for a URL that is not one. */
export function frameOrigin(frameUrl: string): string | null {
  try {
    const url = new URL(frameUrl);
    return url.protocol === "http:" && url.hostname === "127.0.0.1" ? url.origin : null;
  } catch {
    return null;
  }
}

export interface BridgeSource {
  /** The iframe's window (`iframe.contentWindow`), or null before it loads. */
  window: unknown;
  /** The frame URL's origin. */
  origin: string | null;
}

/** Whether a `message` event is the frame's own: from its window and its origin. */
export function fromFrame(event: Pick<MessageEvent, "source" | "origin">, frame: BridgeSource): boolean {
  return frame.window !== null && frame.origin !== null && event.source === frame.window && event.origin === frame.origin;
}

function clamp(value: number, low: number, high: number): number {
  return Math.min(Math.max(value, low), high);
}

/** A message's geometry moved from the frame's viewport into the page's, and kept inside the frame's box. */
export function toPage(message: BridgeMessage, frameBox: { left: number; top: number; width: number; height: number }): BridgeMessage {
  const rect = (r: BridgeRect | null): BridgeRect | null => {
    if (!r) return null;
    const x = clamp(r.x, 0, frameBox.width);
    const y = clamp(r.y, 0, frameBox.height);
    return { x: frameBox.left + x, y: frameBox.top + y, width: clamp(r.width, 0, frameBox.width - x), height: clamp(r.height, 0, frameBox.height - y) };
  };
  if (message.ll === "companion") return { ...message, rect: rect(message.rect) };
  if (message.ll === "menu") {
    return { ...message, rect: rect(message.rect), x: frameBox.left + clamp(message.x, 0, frameBox.width), y: frameBox.top + clamp(message.y, 0, frameBox.height) };
  }
  return message;
}
