// The companion's pure half (spec §8.2, §8.3, §4.3): where each dock is on the stage, where an anchored
// summon lands, which dock a drop snaps to, how far it slides to avoid what it would cover, the pill in the
// overview, and the state machine of its keys and hand-offs. Rects are in stage coordinates.
import type { CompanionDock } from "../../../api/dto";
import type { Rect, Stage } from "../geometry";

/** Presentation values from the mockup (spec §4.3), not model constants. */
export const COMPANION_SIZES = {
  /** Space between a dock and the stage's edges. */
  inset: 14,
  width: 400,
  /** The open-at-cursor width below a 1240 px window (the stage's width when the window's is unknown). */
  narrowWidth: 360,
  narrowBelow: 1240,
  /** Below a 1400 px window (the laptop, where the shelf is a rail) every dock is at most 330 px wide and
   * half the stage high, as the mockup's. */
  laptopBelow: 1400,
  laptopWidth: 330,
  laptopShare: 0.5,
  /** Docked height, as a share of the stage (the `right` dock is the stage's height less two insets). */
  dockShare: 0.52,
  rightWidth: 420,
  rightShare: 0.34,
  /** Anchored: 400 × min(440, 55 % of the stage), 10 px from the anchor. */
  anchoredHeight: 440,
  anchoredShare: 0.55,
  anchorGap: 10,
  /** The overview's pill. */
  pillWidth: 300,
  pillHeight: 38,
  /** Avoid slides at most this far, once. */
  avoidMax: 600,
  avoidMargin: 12,
  /** An anchored companion hands off to its dock when its text scrolls away, but not in its first 250 ms. */
  handOffAfterMs: 250,
} as const;

export const DOCKS: readonly CompanionDock[] = ["br", "bl", "right", "cb"];

export function dockRect(dock: CompanionDock, stage: Stage): Rect {
  const { inset } = COMPANION_SIZES;
  const laptop = stage.viewport !== undefined && stage.viewport < COMPANION_SIZES.laptopBelow;
  const fit = (w: number, h: number) =>
    laptop ? { w: Math.min(w, COMPANION_SIZES.laptopWidth), h: Math.round(Math.min(h, stage.height * COMPANION_SIZES.laptopShare)) } : { w, h };
  if (dock === "right") {
    const { w, h } = fit(Math.min(COMPANION_SIZES.rightWidth, stage.width * COMPANION_SIZES.rightShare), Math.max(0, stage.height - 2 * inset));
    return { x: stage.width - w - inset, y: inset, w, h };
  }
  const { w, h } = fit(Math.min(COMPANION_SIZES.width, Math.max(0, stage.width - 2 * inset)), Math.round(stage.height * COMPANION_SIZES.dockShare));
  const y = stage.height - h - inset;
  if (dock === "bl") return { x: inset, y, w, h };
  if (dock === "cb") return { x: Math.round((stage.width - w) / 2), y, w, h };
  return { x: stage.width - w - inset, y, w, h };
}

/** Summoned at the cursor: 10 px below the anchor if it fits, else above, clamped to the stage. */
export function anchoredRect(anchor: Rect, stage: Stage): Rect {
  const w = Math.min((stage.viewport ?? stage.width) < COMPANION_SIZES.narrowBelow ? COMPANION_SIZES.narrowWidth : COMPANION_SIZES.width, stage.width - 16);
  const h = Math.min(COMPANION_SIZES.anchoredHeight, Math.round(stage.height * COMPANION_SIZES.anchoredShare));
  const below = anchor.y + anchor.h + COMPANION_SIZES.anchorGap;
  const above = anchor.y - COMPANION_SIZES.anchorGap - h;
  const y = below + h <= stage.height - 8 ? below : above >= 8 ? above : stage.height - h - 8;
  const x = Math.max(8, Math.min(anchor.x, stage.width - w - 8));
  return { x, y: Math.max(8, Math.min(y, stage.height - h - 8)), w, h };
}

/** The dock whose rect's centre is nearest a drop point. */
export function nearestDock(point: { x: number; y: number }, stage: Stage): CompanionDock {
  let best: CompanionDock = "br";
  let distance = Infinity;
  for (const dock of DOCKS) {
    const r = dockRect(dock, stage);
    const d = Math.hypot(r.x + r.w / 2 - point.x, r.y + r.h / 2 - point.y);
    if (d < distance) {
      distance = d;
      best = dock;
    }
  }
  return best;
}

export function pillRect(stage: Stage): Rect {
  return {
    x: stage.width - COMPANION_SIZES.pillWidth - 16,
    y: stage.height - COMPANION_SIZES.pillHeight - COMPANION_SIZES.inset,
    w: COMPANION_SIZES.pillWidth,
    h: COMPANION_SIZES.pillHeight,
  };
}

export function intersects(a: Rect, b: Rect): boolean {
  return a.x < b.x + b.w && b.x < a.x + a.w && a.y < b.y + b.h && b.y < a.y + a.h;
}

/** When something the learner is looking at (the selection, a lit passage, a highlight) lies under the
 * panel, the sideways shift that clears it: the shorter way that stays on the stage, at most 600 px.
 * 0 when nothing is covered or no shift within the limit clears it. */
export function avoidOffset(panel: Rect, obstacles: Rect[], stage: Stage): number {
  const covered = obstacles.filter((rect) => intersects(panel, rect));
  if (covered.length === 0) return 0;
  const left = Math.min(...covered.map((rect) => rect.x));
  const right = Math.max(...covered.map((rect) => rect.x + rect.w));
  const toLeft = left - COMPANION_SIZES.avoidMargin - (panel.x + panel.w);
  const toRight = right + COMPANION_SIZES.avoidMargin - panel.x;
  const fits = (dx: number) => Math.abs(dx) <= COMPANION_SIZES.avoidMax && panel.x + dx >= 0 && panel.x + panel.w + dx <= stage.width;
  const options = [toLeft, toRight].filter(fits).sort((a, b) => Math.abs(a) - Math.abs(b));
  return options[0] ?? 0;
}

// -- the states and their transitions (spec §8.2, §8.3) ---------------------------------------------

export type CompanionMode = "docked" | "hidden" | "anchored";

export interface CompanionState {
  mode: CompanionMode;
  /** How it was last opened: from the drawer (shift+c, the tab) or at the cursor (c). `c` sends a drawer
   * summon back to the drawer and dissolves a cursor summon in place. */
  origin: "drawer" | "cursor";
  /** While anchored: the rect it sits at. */
  anchored: Rect | null;
  /** The last move's kind, so the view animates the right transition (and a test can check that no
   * transition passes through the dock). */
  last: "none" | "summon" | "dissolve" | "hide" | "show" | "hand-off" | "snap";
}

export const HIDDEN: CompanionState = { mode: "hidden", origin: "drawer", anchored: null, last: "none" };

export type CompanionEvent =
  /** `c` (or `alt+c` while typing), with where it would anchor. */
  | { kind: "c"; anchor: Rect | null; stage: Stage }
  /** `shift+c`, or the tab. */
  | { kind: "dock" }
  /** The anchored text scrolled away, the view moved, the overview opened, or the handle was dragged. */
  | { kind: "hand-off" }
  | { kind: "hide" };

export function companionStep(state: CompanionState, event: CompanionEvent): CompanionState {
  switch (event.kind) {
    case "c":
      if (state.mode === "hidden") {
        // No companion showing: open at the cursor (else, with no anchor at all, at its dock).
        if (!event.anchor) return { mode: "docked", origin: "drawer", anchored: null, last: "show" };
        return { mode: "anchored", origin: "cursor", anchored: anchoredRect(event.anchor, event.stage), last: "summon" };
      }
      if (state.mode === "anchored") return { ...HIDDEN, last: "dissolve" };
      // Docked: back to the drawer.
      return { ...HIDDEN, last: "hide" };
    case "dock":
      if (state.mode === "anchored") return { mode: "docked", origin: "drawer", anchored: null, last: "hand-off" };
      if (state.mode === "hidden") return { mode: "docked", origin: "drawer", anchored: null, last: "show" };
      return state;
    case "hand-off":
      return state.mode === "anchored" ? { mode: "docked", origin: state.origin, anchored: null, last: "hand-off" } : state;
    case "hide":
      return state.mode === "hidden" ? state : { ...HIDDEN, last: state.mode === "anchored" ? "dissolve" : "hide" };
  }
}
