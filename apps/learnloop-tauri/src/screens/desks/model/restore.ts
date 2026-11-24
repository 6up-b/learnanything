// What a stored window restores as (the Reader's retirement, phase 2 step 2; docs/reviews/reader-rd-retire.md). Pure.
//
// The desks store each window's content reference as it was opened. Some kinds were the old Reader's adapters and have
// a true home on the workbench now; some may be kinds this version does not know (a newer client wrote them). Every
// stored window restores as something the learner can see and act on, never a crash and never a window silently lost:
//
// - a reading-path panel is the book's own path in the book's window (`p`, "what matters here?"): the book's window
//   (the one on the desk, else one opened in the panel's place) with its path open;
// - the Guide and Notes panels stay: they are still the hosts of the book window's rail (its portal) until the rail
//   leaves it; the library panel stays: its window is the Compare window's body, and its stored shape is unchanged;
// - a kind this version does not know restores as the book's window when it names a source (or a reading), and is
//   kept inert otherwise, named so the desk can say which window it could not show.
import type { ContentRefDto } from "../../../api/dto";

export type Restored =
  /** Shown as stored. */
  | { kind: "keep" }
  /** The book's window in this window's place: its reading when named (`extractionId`), the book being prepared when
   *  only its source is; `sourceId` null when only the reading is named (the desk asks which book it belongs to). */
  | { kind: "book"; sourceId: string | null; extractionId: string | null; showPath: boolean }
  /** Kept as stored but not shown: a window this version cannot open, named for the learner. */
  | { kind: "inert"; name: string };

const KNOWN = new Set(["source", "video", "pad", "lesson", "thread", "compare", "panel", "figure_notebook", "preparing"]);

function text(value: unknown): string | null {
  return typeof value === "string" && value.length > 0 ? value : null;
}

/** The plain name of a window this version cannot show, for the line that names it. */
function nameOf(kind: unknown): string {
  if (typeof kind !== "string" || !kind) return "a window with nothing to show";
  const words = kind.replace(/_/g, " ");
  return `${/^[aeiou]/i.test(words) ? "an" : "a"} ${words} window`;
}

/** What a stored window's content reference restores as. `stored` is the reference as the server returned it (any
 * shape: the type names only the kinds this version knows). */
export function restoreContent(stored: unknown): Restored {
  if (!stored || typeof stored !== "object") return { kind: "inert", name: nameOf(null) };
  const ref = stored as Record<string, unknown>;
  const kind = ref.kind;
  const sourceId = text(ref.sourceId);
  const extractionId = text(ref.extractionId);
  if (kind === "panel" && ref.panel === "path") {
    // The reading's path lives in the book's window now; a path panel with no book had nothing to show.
    return extractionId ? { kind: "book", sourceId: null, extractionId, showPath: true } : { kind: "inert", name: "a reading path with no book" };
  }
  if (kind === "panel" && (ref.panel === "guide" || ref.panel === "notes" || ref.panel === "library")) return { kind: "keep" };
  if (kind === "source" || kind === "video") {
    // A book's window that lost its reading (or its book) is the book's window again.
    if (sourceId && extractionId) return { kind: "keep" };
    if (sourceId || extractionId) return { kind: "book", sourceId, extractionId, showPath: false };
    return { kind: "inert", name: nameOf(kind) };
  }
  if (kind === "preparing") return sourceId ? { kind: "keep" } : { kind: "inert", name: "a book being prepared" };
  if (typeof kind === "string" && KNOWN.has(kind) && kind !== "panel") return { kind: "keep" };
  // A kind this version does not know (or a panel it does not): the book's window when it names one.
  if (sourceId || extractionId) return { kind: "book", sourceId, extractionId, showPath: false };
  return { kind: "inert", name: nameOf(kind === "panel" ? text(ref.panel) ?? "panel" : kind) };
}

/** The content a restored book's window opens with: its reading when known, else the book being prepared. */
export function bookContent(sourceId: string, extractionId: string | null, video: boolean): ContentRefDto {
  if (!extractionId) return { kind: "preparing", sourceId };
  return video ? { kind: "video", sourceId, extractionId } : { kind: "source", sourceId, extractionId, view: "render" };
}
