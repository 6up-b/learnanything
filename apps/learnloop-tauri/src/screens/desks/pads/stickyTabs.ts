// The sticky-tab stack's geometry (spec §10.1), pure: where each tab sticks, which pad is active, how much
// each tab merges into its paper (m over 56 px) and each tab's side margin under the three width grades. The
// window writes these per tab each scroll frame (never as an inherited variable, §3.6).

/** Presentation values from the mockup (spec §4.3). */
export const TAB_SIZES = { tab: 30, mergeOver: 56, orderStep: 9, distanceBase: 14, distanceStep: 9, distanceCap: 4 } as const;

export type TabGrade = "flat" | "order" | "distance";

export interface PadGeometry {
  /** The tab's top in the scroller's content (natural flow). */
  tabTop: number;
  /** The paper's top and bottom in the content. */
  paperTop: number;
  paperBottom: number;
}

/** Each tab sticks at `top: i·30` and `bottom: (n−1−i)·30`: the stuck position of tab i in the viewport. */
export function stuckTop(i: number, n: number, natural: number, viewport: number): number {
  const top = i * TAB_SIZES.tab;
  const bottom = viewport - (n - i) * TAB_SIZES.tab;
  return Math.max(top, Math.min(bottom, natural));
}

/** The paper's least height: one pad fills the column, with blank space under short content (O1). */
export function paperMinHeight(viewport: number, n: number): number {
  return Math.max(0, viewport - n * TAB_SIZES.tab);
}

/** The active pad: the one whose body crosses the scroller's upper third, or the last at the end. */
export function activePad(pads: PadGeometry[], scrollTop: number, viewport: number, scrollHeight: number): number {
  if (pads.length === 0) return -1;
  if (scrollTop + viewport >= scrollHeight - 1) return pads.length - 1;
  const line = scrollTop + viewport / 3;
  for (let i = 0; i < pads.length; i += 1) {
    if (line >= pads[i].tabTop && line < pads[i].paperBottom) return i;
  }
  return line < pads[0].tabTop ? 0 : pads.length - 1;
}

/** The fractional open pad: the active index plus how far its paper has scrolled past the upper third. */
export function fractionalOpen(pads: PadGeometry[], scrollTop: number, viewport: number, scrollHeight: number): number {
  const i = activePad(pads, scrollTop, viewport, scrollHeight);
  if (i < 0) return 0;
  const pad = pads[i];
  const span = Math.max(1, pad.paperBottom - pad.tabTop);
  const into = Math.max(0, Math.min(1, (scrollTop + viewport / 3 - pad.tabTop) / span));
  return Math.min(pads.length - 1, i + (i === pads.length - 1 ? 0 : into));
}

/** How much of tab i's own paper shows directly beneath the tab, over 56 px (0..1). */
export function mergeAmount(i: number, pads: PadGeometry[], scrollTop: number, viewport: number): number {
  const pad = pads[i];
  if (!pad) return 0;
  const tabY = stuckTop(i, pads.length, pad.tabTop - scrollTop, viewport);
  const from = tabY + TAB_SIZES.tab;
  const to = from + TAB_SIZES.mergeOver;
  // The paper is visible only between the pile above and the pile below.
  const visibleTop = Math.max(pad.paperTop - scrollTop, (i + 1) * TAB_SIZES.tab);
  const visibleBottom = Math.min(pad.paperBottom - scrollTop, viewport - (pads.length - 1 - i) * TAB_SIZES.tab);
  const overlap = Math.max(0, Math.min(to, visibleBottom) - Math.max(from, visibleTop));
  return Math.max(0, Math.min(1, overlap / TAB_SIZES.mergeOver));
}

/** A tab's side margin (and its paper's) under the grade: none; 9 px per index; or 14 px plus 9 px per unit of
 * distance from the fractional open pad, capped at four units. */
export function tabMargin(grade: TabGrade, i: number, open: number): number {
  if (grade === "flat") return 0;
  if (grade === "order") return TAB_SIZES.orderStep * i;
  return TAB_SIZES.distanceBase + TAB_SIZES.distanceStep * Math.min(TAB_SIZES.distanceCap, Math.abs(i - open));
}

/** Where to scroll so pad i's tab lands just below the pile of tabs above it. */
export function scrollTargetFor(i: number, pads: PadGeometry[]): number {
  const pad = pads[i];
  return pad ? Math.max(0, pad.tabTop - i * TAB_SIZES.tab) : 0;
}
