// Inline cold checks on the desks (spec §12.6 as the owner's decisions of 2026-11-23 corrected it; RD7's frontend half),
// the pure part: what the desks send as "visible" when a check opens or new content arrives, where each veil the server
// names lands in the page, and the words the card says.
//
// The server decides what is veiled (`check.begin_inline`, `check.protect_more`): every note-bearing surface on every
// desk by default, a source window's covered passages, their figures and every margin note, and everything visible when
// coverage cannot be read. The desks only apply what it names, and send back the ref of a veil the learner opens.
import type { CheckVeilRefDto, CheckVisibleDto, DeskWindowKind } from "../../../api/dto";

/** The pill on every veil (the mockup's wording, verbatim). */
export const VEIL_LABEL = "hidden during this check · back when you answer";
/** What opening a veil can cost, said before it is opened (the owner's overlap rule: it may, not always). */
export const SHOW_ANYWAY_COST =
  "If it shows what the answer says, this answer counts as practice and the check stays due. If it doesn't, nothing changes.";
/** Before a note's veil opens: a note's words are never read, so opening one always makes the answer practice. */
export const SHOW_NOTE_COST =
  "This is one of your notes. LearnLoop doesn't read your notes, so it can't tell whether this one gives the answer away: opening it makes this answer count as practice, and the check stays due.";
/** Before opening something the server cannot measure (a figure, a lesson, a thread with no exchanges, ink, a
 *  notebook cell, a part of the page the checks do not describe): opening it always makes the answer practice. */
export const SHOW_UNMEASURED_COST =
  "LearnLoop can't tell what this shows against the answer, so opening it makes this answer count as practice, and the check stays due.";

/** What opening this veil costs, said before it opens. */
export function costOf(ref: CheckVeilRefDto | null): string {
  if (ref && veilIsNote(ref)) return SHOW_NOTE_COST;
  if (!ref || ref.measured === false || ref.kind === "surface") return SHOW_UNMEASURED_COST;
  return SHOW_ANYWAY_COST;
}

/** What an open check does with each kind of window. "passages": a source's own text shows where the server judged
 *  it and does not veil it, everything else in the window is held; "whole": the window's body is held whole (the
 *  server names it; its head says what it is). A new window kind has no entry until someone decides (the type
 *  refuses it, and a test reads the kinds from the DTO). */
export const WINDOW_VEIL_DECISIONS: Record<DeskWindowKind, "passages" | "whole"> = {
  source: "passages",
  video: "passages",
  pad: "whole",
  pad_stack: "whole",
  lesson: "whole",
  thread: "whole",
  compare: "whole",
  panel: "whole",
  figure_notebook: "whole",
  // A book still being prepared shows its original's pages: the book's words, but no passage the server can judge
  // (it has no reading yet), so the whole body is held.
  preparing: "whole",
};

/** Whether this window's passages can show while a check is open (a kind without a decision never can). */
export function passagesCanShow(kind: string): boolean {
  return (WINDOW_VEIL_DECISIONS as Record<string, string | undefined>)[kind] === "passages";
}

/** The answered card's line when a note was opened (the reply's primedBy). */
export const PRIMED_BY_NOTE_WORDS =
  "counts as practice · you opened one of your notes during this check; LearnLoop cannot tell whether it gave the answer away, so this one counts as practice";

/** Whether a veil covers the learner's notes (what the server records unmeasured: a margin note, a window's notes, a
 *  note's search row). */
export function veilIsNote(ref: CheckVeilRefDto): boolean {
  if (ref.kind === "note") return true;
  if (Array.isArray(ref.note_ids) && ref.note_ids.length) return true;
  return ref.kind === "search_row" && Boolean(ref.ref_id) && !["pad", "exchange", "thread", "span"].includes(String(ref.row_kind ?? ""));
}

/** A veil ref's identity (its keys are the server's, snake_case), the same however it was sent. */
export function refKey(ref: Record<string, unknown>): string {
  const keys = Object.keys(ref).filter((key) => key !== "group").sort();
  return JSON.stringify(keys.map((key) => [key, ref[key]]));
}

function quoted(value: string): string {
  return value.replace(/["\\]/g, "\\$&");
}

/** Where a veil lands: a CSS selector for the elements it covers, in the stage. Null for refs with nothing on screen
 *  (a preview while the overview is closed, a search row while no search is open). */
export function veilSelector(ref: CheckVeilRefDto): string | null {
  const window = typeof ref.window_id === "string" ? `[data-desk-window="${quoted(ref.window_id)}"]` : "";
  switch (ref.kind) {
    case "window":
      // The body, not the head: the window still says what it is.
      return window ? `${window} [data-desk-pane-body]` : null;
    case "span":
      return typeof ref.span_id === "string"
        ? `${window} [data-span-id="${quoted(ref.span_id)}"], ${window} [data-transcript-span="${quoted(ref.span_id)}"]`
        : null;
    case "figure":
      return typeof ref.figure_id === "string" ? `${window} [data-figure="${quoted(ref.figure_id)}"]` : null;
    case "note":
      // The surface that shows the note's words, never the passage it is anchored to: a paragraph carries its
      // first annotation's id as an anchor, and veiling it as a note would make reading the book cost practice.
      return typeof ref.note_id === "string" ? `${window} [data-annotation-id="${quoted(ref.note_id)}"]:not([data-span-id]):not([data-transcript-span])` : null;
    case "companion":
      return "[data-companion-dock] [data-companion-body]";
    case "preview":
      return typeof ref.window_id === "string" ? `[data-desk-card="${quoted(ref.window_id)}"]` : null;
    case "search_row":
      // The desks close search before a check opens and keep it closed until the answer, so a row is never on screen
      // with a check open; the selector still covers every row if one ever is.
      return "[data-search-row]";
    default:
      return null;
  }
}

/** "veiled while you answer · <groups>" (each group once, counted when more than one). */
export function groupsLine(veiled: readonly CheckVeilRefDto[]): string {
  const counts = new Map<string, number>();
  for (const ref of veiled) counts.set(ref.group, (counts.get(ref.group) ?? 0) + 1);
  return [...counts].map(([group, n]) => (n > 1 ? `${group} (${n})` : group)).join(" · ");
}

export type CheckReason = "on_your_own" | "primed" | "with_help" | "seen_before" | "already_answered" | "practice";

/** The reply's reason in plain words (the card's line under the answer). */
export const REASON_WORDS: Record<CheckReason, string> = {
  on_your_own: "on your own · this settles the check",
  primed: "counts as practice · what you opened showed the answer, so the check stays due",
  with_help: "counts as practice · you took help, so the check stays due",
  seen_before: "counts as practice · you had seen this answer before, so the check comes back later",
  already_answered: "counts as practice · this check was already answered in Today",
  practice: "counts as practice · the check stays due",
};

/** The answered card's line when something the server cannot measure was opened (a region, a figure, ink…). */
export const PRIMED_UNMEASURED_WORDS =
  "counts as practice · you opened something during this check that LearnLoop can't measure against the answer, so this one counts as practice";

/** Why a check opens as practice (its serve-time eligibility), in plain words; an unknown reason says only that. */
const ELIGIBILITY_WORDS: Record<string, string> = {
  seen_before: "you have seen this answer before, so this one counts as practice and the check comes back later",
  primed: "something you saw showed the answer, so this one counts as practice",
  hold: "it was shown to you recently, so this one counts as practice and the check comes back later",
};

export function eligibilityWords(eligibility: string | null): string {
  return (eligibility && ELIGIBILITY_WORDS[eligibility]) ?? "this one counts as practice · the check stays due";
}

/** "› your answer · just now · on your own" or "· counts as practice". */
export function answeredHead(cold: boolean): string {
  return `› your answer · just now · ${cold ? "on your own" : "counts as practice"}`;
}

/** What the card says after the learner opened a veil: the cost, as it turned out. */
export function lookedLine(groups: readonly string[], coldNow: boolean | null): string | null {
  if (!groups.length) return null;
  const what = [...new Set(groups)].join(" · ");
  if (coldNow === false) return `you looked at ${what} first · this answer counts as practice`;
  return `you looked at ${what} · it said nothing of the answer, so this can still settle the check`;
}

/** The kinds the server knows a window by. */
export function windowKind(window: { kind: string; content?: { kind: string } | null }): string {
  const content = window.content?.kind;
  if (content === "source" || content === "video") return content;
  if (window.kind === "pad_stack" || content === "pad") return "pad_stack";
  if (content === "lesson" || content === "thread" || content === "panel") return content;
  return window.kind || content || "window";
}

const unique = (values: Iterable<string | null | undefined>): string[] => [...new Set([...values].filter((value): value is string => Boolean(value)))];

/** What is on screen, read from the page for the windows it shows and from the desks for the rest (another desk's
 *  windows are listed by kind, so a non-source window there is veiled whole before it is ever shown). */
export function visibleNow(stage: ParentNode | null, windows: ReadonlyArray<{ windowId: string; kind: string; content?: { kind: string; extractionId?: string } | null }>,
                           extra: { companionOpen: boolean; companionExchangeIds: readonly string[]; previewWindowIds: readonly string[] }): CheckVisibleDto {
  const out: CheckVisibleDto["windows"] = [];
  for (const window of windows) {
    const kind = windowKind(window);
    const host = stage?.querySelector(`[data-desk-window="${quoted(window.windowId)}"]`) ?? null;
    const entry: CheckVisibleDto["windows"][number] = { windowId: window.windowId, kind };
    if (kind === "source" || kind === "video") {
      const extractionId = window.content?.extractionId;
      if (extractionId) entry.extractionId = extractionId;
      if (host) {
        // Every passage the window has rendered, not only those scrolled into view: scrolling then shows nothing the
        // server has not already judged.
        const spans = [...host.querySelectorAll("[data-span-id], [data-transcript-span]")];
        entry.spanIds = unique(spans.map((element) => element.getAttribute("data-span-id") ?? element.getAttribute("data-transcript-span")));
        // A note's own surface (a rail card, a margin note), not a passage that carries the note's id as its anchor.
        entry.noteIds = unique([...host.querySelectorAll("[data-annotation-id]:not([data-span-id]):not([data-transcript-span])")].filter((element) => element.getAttribute("data-annotation-kind") === "note")
          .map((element) => element.getAttribute("data-annotation-id")));
        entry.figures = [...host.querySelectorAll("[data-figure]")].map((element) => ({
          figureId: element.getAttribute("data-figure") ?? "",
          spanId: element.closest("[data-figures-under]")?.getAttribute("data-figures-under") ?? element.closest("[data-span-id]")?.getAttribute("data-span-id") ?? null,
        })).filter((figure) => figure.figureId);
      }
    } else if (host) {
      const blocks = unique([...host.querySelectorAll("[data-block]")].map((element) => element.getAttribute("data-block")));
      if (blocks.length) entry.padBlockIds = blocks;
    }
    out.push(entry);
  }
  return {
    windows: out,
    companionOpen: extra.companionOpen,
    companionExchangeIds: [...extra.companionExchangeIds],
    previewWindowIds: [...extra.previewWindowIds],
  };
}

/** A key for "what is visible": a change sends `check.protect_more`, an unchanged view sends nothing. */
export function visibleKey(visible: CheckVisibleDto): string {
  return JSON.stringify(visible);
}
