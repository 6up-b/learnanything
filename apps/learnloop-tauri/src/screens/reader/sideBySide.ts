// Reader CA6: side by side, the pure parts (ux_reader_compare_ask_v1 §6.4, K14, C5).
//
// Which section a pane opens on and where follow along takes the other one,
// read from C0a's reader.correspondents in the API's order. Following uses
// judged coverage only: an unchecked search hit can be opened by the learner
// (`s` on CA5a's list, or Ctrl+\ when nothing is judged yet), but it never
// moves a pane on its own.
import type { CorrespondentSectionDto, CorrespondentsDto } from "../../api/dto";

/** Below this window width side by side isn't offered: `s` and Ctrl+\ peek
 *  instead (§6.4's layout bound, keep: two readable source columns plus the
 *  rail's gutter; not a parameter of any decision). */
export const SIDE_BY_SIDE_MIN_WIDTH = 1040;

export type Pane = "main" | "side";

/** Where the second pane opens (or a following pane goes). */
export interface PaneTarget {
  sourceId: string;
  sourceTitle: string;
  extractionId: string;
  sectionId: string;
  title: string;
  /** The jump locator (the section's first readable passage). */
  spanId: string | null;
  /** Judged coverage, or an unchecked search hit the learner opened. */
  by: "judged" | "search";
}

export function targetOf(hit: CorrespondentSectionDto): PaneTarget {
  return {
    sourceId: hit.sourceId,
    sourceTitle: hit.sourceTitle,
    extractionId: hit.jump.extractionId || hit.extractionId,
    sectionId: hit.jump.sectionId || hit.sectionId,
    title: hit.title,
    spanId: hit.jump.spanId,
    by: hit.by === "search" ? "search" : "judged",
  };
}

/** Every judged correspondent, in the API's order (LO by LO, book by book). */
export function judgedInOrder(view: CorrespondentsDto | null): CorrespondentSectionDto[] {
  if (!view || view.status !== "judged") return [];
  return view.learningObjects.flatMap((group) => group.sources.flatMap((source) => source.sections))
    .filter((section) => section.by !== "search");
}

/** Follow along's target: the first of this book's judged correspondents, in
 *  the API's order (null: none here, the follower stays put). */
export function firstJudgedIn(view: CorrespondentsDto | null, sourceId: string): CorrespondentSectionDto | null {
  return judgedInOrder(view).find((section) => section.sourceId === sourceId && Boolean(section.jump.spanId)) ?? null;
}

/** Ctrl+\'s target: the first correspondent in the API's order; with nothing
 *  judged, the first search hit the learner asked for by pressing (shown as
 *  "found by search, not checked"). */
export function firstCorrespondent(view: CorrespondentsDto | null): CorrespondentSectionDto | null {
  const judged = judgedInOrder(view).find((section) => Boolean(section.jump.spanId));
  if (judged) return judged;
  if (!view || view.status !== "unchecked") return null;
  for (const source of view.search?.sources ?? []) {
    const hit = source.sections.find((section) => Boolean(section.jump.spanId));
    if (hit) return hit;
  }
  return null;
}

/** A section's short name: its number (`§5.A`) when its title starts with one, else its title. */
export function sectionShort(title: string): string {
  const numbered = title.match(/^§?\s*(\d[\dA-Za-z]*(?:\.[\dA-Za-z]+)*)\b/);
  return numbered ? `§${numbered[1]}` : title;
}

/** The crumb: `side by side with Axler §5.A`. */
export function crumbLabel(target: Pick<PaneTarget, "sourceTitle" | "title">): string {
  return `side by side with ${target.sourceTitle} ${sectionShort(target.title)}`;
}

export function isNarrowWindow(width: number): boolean {
  return width < SIDE_BY_SIDE_MIN_WIDTH;
}

const SPLIT_KEY = "learnloop.reader.side-by-side-split";

/** The split, remembered per device (the main pane's share of the width). */
export function readSplit(): number {
  try {
    const value = Number(window.localStorage.getItem(SPLIT_KEY));
    if (Number.isFinite(value) && value >= 0.25 && value <= 0.75) return value;
  } catch {
    /* A per-device preference; side by side works without it. */
  }
  return 0.5;
}

export function writeSplit(value: number): void {
  try {
    window.localStorage.setItem(SPLIT_KEY, String(value));
  } catch {
    /* As above. */
  }
}

/** Keep both panes readable: the split stays between a quarter and three quarters (a layout bound). */
export function clampSplit(value: number): number {
  return Math.min(0.75, Math.max(0.25, value));
}
