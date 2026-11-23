// Pure layout for the reading view (spec §3.1 `geometry.ts`, §4.3, §5.2): every slot's rect, the
// camera that keeps the focus in view, the slivers, the soft crop, and focus mode's full-screen rect.
// The overview's half of `geom` arrives with the zoom engine; this file lays out the reading view only.

/** Design sizes from the mockup (spec §4.3). Presentation values, not model constants. */
export const DESK_SIZES = {
  side: 34,
  gap: 10,
  /** Two slots take 10 px less than the stage inside its margins, as the mockup's do (34 px left, 44 right). */
  trailing: 10,
  topBar: 38,
  footer: 26,
  shelf: 236,
  shelfRail: 44,
  /** Below this stage width the shelf folds to its rail. */
  shelfFoldBelow: 1400,
  sliver: 30,
  /** A window partly off screen fades to 55 % over its last 36 px. */
  cropFade: 36,
  cropOpacity: 0.55,
  /** Windows sit 8 px inside their row, top and bottom. */
  inset: 8,
  /** The gap between desk rows in the reading view. */
  rowGap: 180,
  pairDivider: 6,
} as const;

export interface Rect {
  x: number;
  y: number;
  w: number;
  h: number;
}

export interface Stage {
  width: number;
  height: number;
}

/** One uniform slot: two slots and the gap between them fill the stage inside its side margins, less the
 * mockup's 10 px on the right. */
export function slotWidth(stage: Stage): number {
  return Math.max(0, (stage.width - 2 * DESK_SIZES.side - DESK_SIZES.gap - DESK_SIZES.trailing) / 2);
}

/** The slots' rects on one desk row, in world coordinates of that row (y from the row's top). */
export function slotRects(slotCount: number, stage: Stage): Rect[] {
  const w = slotWidth(stage);
  const h = Math.max(0, stage.height - 2 * DESK_SIZES.inset);
  return Array.from({ length: slotCount }, (_, index) => ({
    x: DESK_SIZES.side + index * (w + DESK_SIZES.gap),
    y: DESK_SIZES.inset,
    w,
    h,
  }));
}

/** The panes of one slot: one fills it; a pair stacks top and bottom with equal heights. */
export function paneRects(slot: Rect, panes: number): Rect[] {
  if (panes < 2) return [slot];
  const half = (slot.h - DESK_SIZES.pairDivider) / 2;
  return [
    { x: slot.x, y: slot.y, w: slot.w, h: half },
    { x: slot.x, y: slot.y + half + DESK_SIZES.pairDivider, w: slot.w, h: half },
  ];
}

/** The strip's full width: the last slot's right edge plus the side margin. */
export function stripWidth(slotCount: number, stage: Stage): number {
  if (slotCount === 0) return stage.width;
  const rects = slotRects(slotCount, stage);
  const last = rects[rects.length - 1];
  return last.x + last.w + DESK_SIZES.side;
}

/** A desk row's top in the world: rows stack vertically like workspaces. */
export function rowTop(rowIndex: number, stage: Stage): number {
  return rowIndex * (stage.height + DESK_SIZES.rowGap);
}

function clampCam(camX: number, slotCount: number, stage: Stage): number {
  return Math.max(0, Math.min(camX, Math.max(0, stripWidth(slotCount, stage) - stage.width)));
}

/** The camera offset that brings slot `index` into view with the least movement from `camX`
 * (the mockup's ensureVisible). With `withPrevious`, the slot before it stays in view too. */
export function ensureVisible(camX: number, index: number, slotCount: number, stage: Stage, withPrevious = false): number {
  if (index < 0 || index >= slotCount) return clampCam(camX, slotCount, stage);
  const rects = slotRects(slotCount, stage);
  const rect = rects[index];
  const right = stage.width - DESK_SIZES.side;
  let next = camX;
  if (withPrevious && index > 0) {
    next = Math.max(rects[index - 1].x - DESK_SIZES.side, rect.x + rect.w - right);
  } else if (rect.x - next < DESK_SIZES.side) {
    next = rect.x - DESK_SIZES.side;
  } else if (rect.x + rect.w - next > right) {
    next = rect.x + rect.w - right;
  }
  return clampCam(next, slotCount, stage);
}

/** How much of a slot shows: its visible fraction and how far each side runs past the stage. */
export interface SlotVisibility {
  index: number;
  /** Fully inside the stage's side margins. */
  inView: boolean;
  /** Any part on screen. */
  onScreen: boolean;
  /** Pixels cut by the stage's left and right edges. */
  cutLeft: number;
  cutRight: number;
}

export function slotVisibility(camX: number, slotCount: number, stage: Stage): SlotVisibility[] {
  return slotRects(slotCount, stage).map((rect, index) => {
    const left = rect.x - camX;
    const right = left + rect.w;
    return {
      index,
      // Two pixels of slack, as the mockup's inView: rounding never takes a window out of view.
      inView: right > DESK_SIZES.side - 2 && left < stage.width - DESK_SIZES.side + 2,
      onScreen: right > 0 && left < stage.width,
      cutLeft: Math.max(0, -left),
      cutRight: Math.max(0, right - stage.width),
    };
  });
}

/** The slots shown in the viewport (in view), in order. */
export function slotsInView(camX: number, slotCount: number, stage: Stage): number[] {
  return slotVisibility(camX, slotCount, stage).filter((slot) => slot.inView).map((slot) => slot.index);
}

/** The off-screen neighbours each side of the view, for the 30 px slivers (spec §5.2). */
export function sliverSlots(camX: number, slotCount: number, stage: Stage): { left: number | null; right: number | null } {
  const shown = slotsInView(camX, slotCount, stage);
  if (shown.length === 0) return { left: null, right: null };
  const first = shown[0];
  const last = shown[shown.length - 1];
  return { left: first > 0 ? first - 1 : null, right: last < slotCount - 1 ? last + 1 : null };
}

/** The soft crop as a CSS mask: a window partly off screen fades at the screen edge over its last
 * 36 px to 55 %, so no text is cut mid-word. Null when nothing is cut. */
export function softCropMask(visibility: SlotVisibility, width: number): string | null {
  if (visibility.cutLeft <= 0 && visibility.cutRight <= 0) return null;
  const fade = DESK_SIZES.cropFade;
  const dim = `rgba(0,0,0,${DESK_SIZES.cropOpacity})`;
  const leftEdge = Math.min(width, visibility.cutLeft);
  const rightEdge = Math.max(0, width - visibility.cutRight);
  const stops: string[] = [];
  if (visibility.cutLeft > 0) stops.push(`${dim} ${leftEdge}px`, `#000 ${Math.min(width, leftEdge + fade)}px`);
  else stops.push("#000 0px");
  if (visibility.cutRight > 0) stops.push(`#000 ${Math.max(0, rightEdge - fade)}px`, `${dim} ${rightEdge}px`);
  else stops.push(`#000 ${width}px`);
  return `linear-gradient(to right, ${stops.join(", ")})`;
}

/** Reading measures in focus mode (spec §4.3), by window kind. */
export const FOCUS_MEASURE: Record<string, number> = {
  source: 980,
  pad: 820,
  pad_stack: 820,
  video: 900,
  paper: 820,
};

export const DOC_ZOOM = { min: 0.6, max: 2.2, step: 0.1 } as const;

/** Focus mode is truly full screen (owner decision 11): the whole viewport, chrome collapsed. */
export function focusRect(viewport: Stage): Rect {
  return { x: 0, y: 0, w: viewport.width, h: viewport.height };
}

export function stepZoom(zoom: number, direction: -1 | 0 | 1): number {
  if (direction === 0) return 1;
  const next = Math.round((zoom + direction * DOC_ZOOM.step) * 10) / 10;
  return Math.max(DOC_ZOOM.min, Math.min(DOC_ZOOM.max, next));
}

/** The stage left after the top bar, footer and shelf (or its rail below 1400 px). */
export function stageFor(viewport: Stage): Stage {
  const shelf = viewport.width < DESK_SIZES.shelfFoldBelow ? DESK_SIZES.shelfRail : DESK_SIZES.shelf;
  return {
    width: Math.max(0, viewport.width - shelf),
    height: Math.max(0, viewport.height - DESK_SIZES.topBar - DESK_SIZES.footer),
  };
}
