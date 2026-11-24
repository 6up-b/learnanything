// Inline cold checks on the desks (spec §12.6 as the owner's decisions of 2026-11-23 corrected it; RD7's frontend half),
// the pure part: what the desks send as "visible" when a check opens or new content arrives, where each veil the server
// names lands in the page, and the words the card says.
//
// The server decides what is veiled (`check.begin_inline`, `check.protect_more`): every note-bearing surface on every
// desk by default, a source window's covered passages, their figures and every margin note, and everything visible when
// coverage cannot be read. The desks only apply what it names, and send back the ref of a veil the learner opens.
import type { CheckVeilRefDto, CheckVisibleDto } from "../../../api/dto";

/** The pill on every veil (the mockup's wording, verbatim). */
export const VEIL_LABEL = "hidden during this check · back when you answer";
/** What opening a veil can cost, said before it is opened (the owner's overlap rule: it may, not always). */
export const SHOW_ANYWAY_COST =
  "If it shows what the answer says, this answer counts as practice and the check stays due. If it doesn't, nothing changes.";

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
      return typeof ref.note_id === "string" ? `${window} [data-annotation-id="${quoted(ref.note_id)}"]` : null;
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
        entry.noteIds = unique([...host.querySelectorAll("[data-annotation-id]")].filter((element) => element.getAttribute("data-annotation-kind") === "note")
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
