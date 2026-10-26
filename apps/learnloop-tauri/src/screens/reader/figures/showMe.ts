// Reader RW5d P1: "show me" in the Reader's Ask rail (spec_reader_show_me_figures_v1 §6.2).
//
// The Ask box gains a second way to send: "show me ▸" (Alt+↵) sends the box's
// words as a figure goal instead of a question. The figure lands inline under
// the passage the learner was reading when they asked (the inquiry's passage,
// else the selection, else the reading position); the thread keeps one line
// per request that says where it came from and opens it there. Nothing here
// moves focus or starts anything on its own (W12): "open" is the learner's press.
import type { FigureViewDto } from "../../../api/dto";

export const SHOW_ME_COPY = {
  send: "show me ▸",
  keys: "alt+↵ show me ▸",
  where: "Sent with your selection or the passages LearnLoop finds to the model that builds the figure — never to grade you.",
  whereLabel: "ⓘ where this goes",
  pending: "◐ building an interactive version from your words · keep reading",
  landed: "▸ interactive version",
  fromYourBooks: "from your books:",
  notFromYourBooks: "not from your books — LearnLoop's model's illustration",
  fromYourSelection: "from your selection",
  open: "open",
  failed: "couldn't build an interactive version of this",
  dismiss: "✕",
} as const;

/** One "show me" request in the Ask rail's thread. */
export interface ShowMeLine {
  key: string;
  goal: string;
  state: "pending" | "landed" | "failed" | "cancelled";
  figure: FigureViewDto | null;
}

/** Where a landed figure's line says it came from (code-written, from the closed grounding value). */
export function showMeSourceLine(figure: FigureViewDto): string {
  if (figure.grounding === "none") return SHOW_ME_COPY.notFromYourBooks;
  if (figure.grounding === "anchor") return SHOW_ME_COPY.fromYourSelection;
  const passages = (figure.passages ?? []).map((passage) =>
    `§ ${[passage.sourceTitle, passage.section].filter(Boolean).join(" ") || passage.spanId}`);
  return passages.length ? `${SHOW_ME_COPY.fromYourBooks} ${passages.join(" · ")}` : SHOW_ME_COPY.fromYourBooks;
}

/** Alt+Enter (not Ctrl, which asks): the box's words go as a figure goal. */
export function isShowMeKey(event: { altKey: boolean; ctrlKey: boolean; metaKey: boolean; key: string }): boolean {
  return event.altKey && !event.ctrlKey && !event.metaKey && event.key === "Enter";
}
