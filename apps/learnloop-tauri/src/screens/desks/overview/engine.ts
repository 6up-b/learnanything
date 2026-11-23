// The overview's zoom engine (spec §6.3), pure: the overview's geometry and camera, the frame function
// that carries every window from its reading rect to its card rect at progress p, the chase and the
// settle spring that move p, the release rule, and the wheel's classification and end latch (§5.5).
//
// Coordinates. The windows live in one world container. In the reading view the world's transform is
// the identity and a window's rect is where it shows on the stage (its desk row and the desk's camera
// already applied). In the overview the world holds the overview's own layout (every desk a row of
// cards) under the camera translate(x, y) scale(s). A zoom interpolates the world's transform from one
// camera to the other in log scale and morphs each window's box between its two rects; the last frame
// is exactly the layout the commit writes, so the commit changes no pixel (the invariant, review F10).
import { DESK_SIZES, type Rect, type Stage } from "../geometry";

/** Design values from the mockup (spec §4.3). Presentation values, not model constants. */
export const OVERVIEW = {
  scale: 0.34,
  cardMin: 760,
  /** A desk row in the overview is this share of the stage's height. */
  rowShare: 0.75,
  rowGap: 330,
  /** Room left of the cards for the links' curves. */
  gutter: 170,
  /** The selection stays this far inside the edges (74 px from the top, under the desk label). */
  edge: 48,
  edgeTop: 74,
  /** The chase's time constant (s) and the settle spring's ω (rad/s, about 300 ms). */
  tau: 0.04,
  omega: 26,
  /** Release: entering completes at p + 0.15·v ≥ 0.4; leaving completes at p + 0.15·v ≤ 0.6. */
  enterAt: 0.4,
  leaveAt: 0.6,
  project: 0.15,
  /** Zoom by touchpad: 420 px of travel is the whole zoom. Pinch: p += dy/108. Ctrl+drag: 320 px. */
  touchTravel: 420,
  pinchTravel: 108,
  dragTravel: 320,
  /** A first delta this large, or deltas in lines or pages, is a mouse notch. */
  notchDelta: 40,
  /** A touch gesture ends after 80 ms idle; at either end the stream is latched for 150 ms. */
  gestureIdleMs: 80,
  latchMs: 150,
  /** Pan by alt + swipe snaps after 120 ms idle. */
  panSnapMs: 120,
  /** A card dragged farther than this moves; a shelf row, 5 px. */
  cardDragPx: 8,
  /** Fades over q (spec §6.3). */
  contentFade: [0.45, 0.85] as const,
  lateFade: [0.6, 1] as const,
  recede: 0.62,
  /** Reduced motion: the zoom is a crossfade of this long. */
  reducedMs: 250,
  /** The overview's keyboard camera eases over .2 s. */
  panEaseMs: 200,
} as const;

export interface Camera {
  x: number;
  y: number;
  s: number;
}

export const IDENTITY: Camera = { x: 0, y: 0, s: 1 };

// -- the overview's layout ---------------------------------------------------------------------------

export interface OverviewLayout {
  /** Card rects per desk, per slot, in the overview's world coordinates. */
  cards: Rect[][];
  /** The uppercase desk label's place per desk. */
  labels: { x: number; y: number }[];
  /** Each row's height (cards fill it, less the 8 px inset top and bottom). */
  rowHeight: number;
}

/** Every desk one row of cards (spec §6.1): cards at least 760 world px wide, rows 330 apart, the first
 * card after the links' gutter. */
export function overviewLayout(slotCounts: number[], slotWidth: number, stage: Stage): OverviewLayout {
  const rowHeight = stage.height * OVERVIEW.rowShare;
  const pitch = rowHeight + OVERVIEW.rowGap;
  const x0 = DESK_SIZES.side + OVERVIEW.gutter;
  const w = Math.max(slotWidth, OVERVIEW.cardMin);
  const cards = slotCounts.map((count, row) => Array.from({ length: count }, (_, index) => ({
    x: x0 + index * (w + DESK_SIZES.gap),
    y: row * pitch + DESK_SIZES.inset,
    w,
    h: rowHeight - 2 * DESK_SIZES.inset,
  })));
  return { cards, labels: slotCounts.map((_, row) => ({ x: x0, y: row * pitch - 14 })), rowHeight };
}

/** A rect as the camera shows it on the stage. */
export function onStage(rect: Rect, camera: Camera): Rect {
  return { x: rect.x * camera.s + camera.x, y: rect.y * camera.s + camera.y, w: rect.w * camera.s, h: rect.h * camera.s };
}

/** The camera that keeps `selected` inside the stage's edges with the least movement from `from`
 * (48 px; 74 px from the top so the desk label above the row shows). */
export function followSelection(from: Camera, selected: Rect, stage: Stage): Camera {
  const r = onStage(selected, from);
  let { x, y } = from;
  if (r.x < OVERVIEW.edge) x += OVERVIEW.edge - r.x;
  else if (r.x + r.w > stage.width - OVERVIEW.edge) x -= r.x + r.w - (stage.width - OVERVIEW.edge);
  if (r.y < OVERVIEW.edgeTop) y += OVERVIEW.edgeTop - r.y;
  else if (r.y + r.h > stage.height - OVERVIEW.edge) y -= r.y + r.h - (stage.height - OVERVIEW.edge);
  return { x: Math.round(x), y: Math.round(y), s: from.s };
}

/** The overview's camera on entering: the mockup's starting pan, moved to keep the selection in view. */
export function enteringCamera(selected: Rect | null, stage: Stage): Camera {
  const start: Camera = { x: 24, y: 70, s: OVERVIEW.scale };
  return selected ? followSelection(start, selected, stage) : start;
}

// -- the frame function ----------------------------------------------------------------------------

export interface ZoomItem {
  /** The window's rect in the reading view and in the overview (both in world coordinates). */
  a: Rect;
  b: Rect;
  /** Its laid-out box during this zoom: `a` when entering, `b` when leaving. */
  base: Rect;
  /** Its content shows during the zoom (it was on screen); the rest show only their card. */
  live: boolean;
  /** Recedes in the overview (unrelated to the selection). */
  recede?: boolean;
}

export interface ItemFrame {
  /** The window's transform from its laid-out box: translate(tx, ty) scale(sx, sy), origin 0 0. */
  tx: number;
  ty: number;
  sx: number;
  sy: number;
  /** The content's counter-scale, so text never stretches. */
  innerSx: number;
  innerSy: number;
  /** Its rect at this frame, in world coordinates. */
  rect: Rect;
  contentOpacity: number;
  cardOpacity: number;
  opacity: number;
}

export interface Frame {
  p: number;
  /** The linear fraction of the scale change. */
  q: number;
  camera: Camera;
  items: ItemFrame[];
  /** Links and desk labels. */
  lateOpacity: number;
  sliverOpacity: number;
  /** The reading view's amber focus edge. */
  focusEdge: number;
}

const clamp01 = (x: number) => Math.max(0, Math.min(1, x));
const lerp = (a: number, b: number, t: number) => a + (b - a) * t;

function ramp(q: number, [from, to]: readonly [number, number]): number {
  return clamp01((q - from) / (to - from));
}

/** One frame at progress p ∈ [0, 1] from camera A (reading) to camera B (overview). Transforms and
 * opacities only: nothing here needs a layout. */
export function frameAt(p: number, A: Camera, B: Camera, items: ZoomItem[]): Frame {
  const s = A.s * Math.pow(B.s / A.s, p);
  const q = A.s === B.s ? p : (A.s - s) / (A.s - B.s);
  const camera = { x: lerp(A.x, B.x, q), y: lerp(A.y, B.y, q), s };
  const fade = ramp(q, OVERVIEW.contentFade);
  const late = ramp(q, OVERVIEW.lateFade);
  return {
    p,
    q,
    camera,
    lateOpacity: late,
    sliverOpacity: Math.max(0, 1 - 3 * q),
    focusEdge: Math.max(0, 1 - 3 * q),
    items: items.map((item) => {
      const rect = {
        x: lerp(item.a.x, item.b.x, q),
        y: lerp(item.a.y, item.b.y, q),
        w: lerp(item.a.w, item.b.w, q),
        h: lerp(item.a.h, item.b.h, q),
      };
      const sx = rect.w / item.base.w;
      const sy = rect.h / item.base.h;
      return {
        tx: rect.x - item.base.x,
        ty: rect.y - item.base.y,
        sx,
        sy,
        innerSx: 1 / sx,
        innerSy: 1 / sy,
        rect,
        contentOpacity: item.live ? 1 - fade : 0,
        cardOpacity: item.live ? fade : 1,
        opacity: item.recede ? 1 - OVERVIEW.recede * q : 1,
      };
    }),
  };
}

/** Where a laid-out box shows under a transform, for checks: translate(tx, ty) scale(sx, sy) about 0 0. */
export function transformed(base: Rect, item: Pick<ItemFrame, "tx" | "ty" | "sx" | "sy">): Rect {
  return { x: base.x + item.tx, y: base.y + item.ty, w: base.w * item.sx, h: base.h * item.sy };
}

// -- moving p: the chase, the spring, the release -------------------------------------------------

export interface Motion {
  p: number;
  /** p per second. */
  v: number;
  /** Where the fingers have taken p (undecided); null once decided. */
  target: number;
  /** 0 or 1 once decided: the spring carries p there. */
  goal: 0 | 1 | null;
}

/** One step of dt seconds. Undecided, p chases the target (τ = 40 ms). Decided, a critically damped spring
 * (ω = 26) carries p to the goal from the speed it has, so there is no step in velocity when the fingers
 * lift. Returns the new motion and whether p has arrived at the goal. */
export function step(motion: Motion, dt: number): { motion: Motion; arrived: boolean } {
  const t = Math.min(0.05, Math.max(0.001, dt));
  if (motion.goal === null) {
    let p = motion.p + (motion.target - motion.p) * (1 - Math.exp(-t / OVERVIEW.tau));
    if (Math.abs(motion.target - p) < 5e-4) p = motion.target;
    return { motion: { ...motion, p, v: (p - motion.p) / t }, arrived: false };
  }
  const w = OVERVIEW.omega;
  const x0 = motion.p - motion.goal;
  const c = motion.v + w * x0;
  const k = Math.exp(-w * t);
  const x = (x0 + c * t) * k;
  let v = (c - w * (x0 + c * t)) * k;
  let p = motion.goal + x;
  if ((Math.abs(x) < 0.002 && Math.abs(v) < 0.05) || x0 * x < 0 || x0 === 0) p = motion.goal;
  if (p <= 0 || p >= 1) {
    p = clamp01(p);
    if (p !== motion.goal) v = 0;
  }
  return { motion: { ...motion, p, v }, arrived: p === motion.goal };
}

/** The fingers lifted: complete past 40 % of the way (counting where the last flick was heading), else
 * spring back. `base` is where the zoom started (0 reading, 1 overview). */
export function release(base: 0 | 1, target: number, v: number): 0 | 1 {
  const projected = target + v * OVERVIEW.project;
  if (base === 1) return projected <= OVERVIEW.leaveAt ? 0 : 1;
  return projected >= OVERVIEW.enterAt ? 1 : 0;
}

/** Settle at once (a key or a pointer press during a zoom): the release rule with no flick. */
export function settleNow(base: 0 | 1, motion: Motion): 0 | 1 {
  if (motion.goal !== null) return motion.goal;
  return release(base, motion.p, 0);
}

// -- the wheel (spec §5.5) -------------------------------------------------------------------------

export interface WheelLike {
  deltaX: number;
  deltaY: number;
  deltaMode: number;
  ctrlKey: boolean;
  altKey: boolean;
  shiftKey: boolean;
}

/** Deltas normalised to pixels: a line is 40 px, a page the stage's height. */
export function normalizedDelta(event: Pick<WheelLike, "deltaX" | "deltaY" | "deltaMode">, stageHeight: number): { dx: number; dy: number } {
  const unit = event.deltaMode === 1 ? 40 : event.deltaMode === 2 ? stageHeight : 1;
  return { dx: event.deltaX * unit, dy: event.deltaY * unit };
}

export type WheelKind = "pan" | "zoom" | "scroll";
export type ZoomSource = "touch" | "pinch" | "notch";

/** What a gesture is, decided by its first event and kept until it ends: alt + horizontal-dominant or
 * shift pans the strip; alt + vertical, or anything with Ctrl (a pinch arrives as ctrl+wheel), zooms; a
 * plain scroll is the window's own. Alt and Ctrl come from the tracked modifiers too (WebKitGTK). */
export function classifyWheel(event: WheelLike, mods: { alt: boolean; ctrl: boolean }, stageHeight: number): { kind: WheelKind; source?: ZoomSource } {
  const { dx, dy } = normalizedDelta(event, stageHeight);
  const alt = mods.alt || event.altKey;
  const ctrlEvent = event.ctrlKey || mods.ctrl;
  if (ctrlEvent) {
    // Chromium sends a touchpad pinch as ctrl+wheel without the Ctrl key held.
    const pinch = event.ctrlKey && !mods.ctrl;
    return { kind: "zoom", source: pinch ? "pinch" : zoomSource(event, dy) };
  }
  if (alt) {
    if (Math.abs(dx) > Math.abs(dy)) return { kind: "pan" };
    return { kind: "zoom", source: zoomSource(event, dy) };
  }
  if (event.shiftKey) return { kind: "pan" };
  return { kind: "scroll" };
}

function zoomSource(event: WheelLike, dy: number): ZoomSource {
  return event.deltaMode !== 0 || Math.abs(dy) >= OVERVIEW.notchDelta ? "notch" : "touch";
}

/** One zoom gesture's stream (a reducer): each event moves the target, decides at an end, or is
 * swallowed by the end latch. Pure; the caller arms the timers it asks for. */
export interface ZoomGesture {
  source: ZoomSource;
  /** p per second, smoothed: where the fingers are heading. */
  v: number;
  n: number;
  t: number;
  /** The direction latched at an end (+1 out, −1 in), or 0. */
  latch: number;
}

export type ZoomStep =
  | { kind: "swallow"; armMs: number }
  | { kind: "begin-and-target"; target: number; armMs: number }
  | { kind: "target"; target: number; armMs: number }
  | { kind: "goal"; goal: 0 | 1; armMs: number };

export function newZoomGesture(source: ZoomSource, now: number): ZoomGesture {
  return { source, v: 0, n: 0, t: now, latch: 0 };
}

/** One wheel event of a zoom gesture. `active` is whether a zoom is running; `inOverview` the committed
 * view; `target` the running zoom's target. dy > 0 zooms out (toward the overview). */
export function zoomWheel(
  gesture: ZoomGesture,
  dy: number,
  now: number,
  state: { active: boolean; inOverview: boolean; target: number },
): { gesture: ZoomGesture; step: ZoomStep } {
  const sign = Math.sign(dy);
  const g = { ...gesture };
  if (!sign) return { gesture: g, step: { kind: "swallow", armMs: g.latch ? OVERVIEW.latchMs : OVERVIEW.gestureIdleMs } };
  if (g.latch) {
    if (sign === g.latch) return { gesture: g, step: { kind: "swallow", armMs: OVERVIEW.latchMs } };
    g.latch = 0;
    g.v = 0;
    g.n = 0;
  }
  // Already at that end: the rest of the stream is the end's.
  if (!state.active && (sign > 0) === state.inOverview) {
    g.latch = sign;
    return { gesture: g, step: { kind: "swallow", armMs: OVERVIEW.latchMs } };
  }
  if (g.source === "notch") {
    g.latch = sign;
    return { gesture: g, step: { kind: "goal", goal: sign > 0 ? 1 : 0, armMs: OVERVIEW.latchMs } };
  }
  const dp = dy / (g.source === "pinch" ? OVERVIEW.pinchTravel : OVERVIEW.touchTravel);
  const dt = Math.max(0.004, (now - g.t) / 1000);
  g.t = now;
  if (g.n++) g.v += (dp / dt - g.v) * 0.35;
  const base = state.active ? state.target : state.inOverview ? 1 : 0;
  const target = clamp01(base + dp);
  if (sign > 0 ? target >= 1 : target <= 0) {
    g.latch = sign;
    return { gesture: g, step: { kind: "goal", goal: sign > 0 ? 1 : 0, armMs: OVERVIEW.latchMs } };
  }
  return { gesture: g, step: { kind: state.active ? "target" : "begin-and-target", target, armMs: OVERVIEW.gestureIdleMs } };
}

/** Ctrl+drag on the stage background: 320 px of vertical travel is the whole zoom (down zooms out). */
export function dragProgress(base: 0 | 1, dy: number): number {
  return clamp01(base + dy / OVERVIEW.dragTravel);
}

// -- overview navigation (spec §6.2) --------------------------------------------------------------

export interface Selection {
  row: number;
  slot: number;
}

/** h/l move within a desk; j/k move to the next desk's card nearest by x-centre. */
export function moveSelection(layout: OverviewLayout, from: Selection, direction: "left" | "right" | "up" | "down"): Selection {
  const rows = layout.cards;
  const current = rows[from.row]?.[from.slot];
  if (!current) return from;
  if (direction === "left" || direction === "right") {
    const slot = from.slot + (direction === "left" ? -1 : 1);
    return rows[from.row][slot] ? { row: from.row, slot } : from;
  }
  const step = direction === "up" ? -1 : 1;
  for (let row = from.row + step; row >= 0 && row < rows.length; row += step) {
    if (rows[row].length === 0) continue;
    const centre = current.x + current.w / 2;
    let best = 0;
    let distance = Infinity;
    rows[row].forEach((card, slot) => {
      const d = Math.abs(card.x + card.w / 2 - centre);
      if (d < distance) {
        distance = d;
        best = slot;
      }
    });
    return { row, slot: best };
  }
  return from;
}

/** The slot a card dropped at a world point lands in: its desk row by y, its index by x. */
export function dropTarget(layout: OverviewLayout, point: { x: number; y: number }): Selection | null {
  const pitch = layout.rowHeight + OVERVIEW.rowGap;
  const row = Math.floor((point.y + OVERVIEW.rowGap / 2) / pitch);
  if (row < 0 || row >= layout.cards.length) return null;
  const cards = layout.cards[row];
  let slot = cards.length;
  for (let index = 0; index < cards.length; index += 1) {
    if (point.x < cards[index].x + cards[index].w / 2) {
      slot = index;
      break;
    }
  }
  return { row, slot };
}
