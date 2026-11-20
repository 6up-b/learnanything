// UX fix stage 3 (UX journey audit P1, F1, UX-4, UX-6): an empty Today says
// why, and offers the one step that would change it.
//
// The cause is read from what the desktop already has: the book cards' own
// status lines (the sidecar's `source_status_line`, add_source.py), the links
// still being added, the AI connection, and today's list. Nothing here
// estimates or decides anything; it picks which of the cards' states to name
// on Today, and says it in Today's words. The book card keeps its own line.
//
// Today's list comes first: when it still has questions, there is something
// to practise, whatever the books say. The plan alone cannot tell a stop the
// router chose with work left from a day with nothing left to plan (its
// stopReason is free text, sometimes the model's own rationale), so Today
// reads the list instead of guessing.

import type { AiConnectionDto, PendingAddDto, SourceLibraryCard, SourceStatusLineDto } from "../api/dto";
import { CONSENT_ACTION, SIDECAR_CONSENT_LABEL, readableTitle } from "../components/BookCard";

export { CONSENT_ACTION };

/** The failure labels of a card's retry (add_source.py: an import that
 *  failed, "Try again"; question writing that stopped, "Retry"). Other retry
 *  actions ("Build them as you read", "Finish moving them", "Get it ready")
 *  are not failures. */
const FAILURE_RETRY_LABELS: ReadonlySet<string> = new Set(["Retry", "Try again"]);

export type TodayCause =
  /** Today's list still has questions: the plan stopped with something left. */
  | { kind: "list_has_more" }
  /** A book's questions wait for the one-time OK. */
  | { kind: "waiting_ok"; title: string; others: number }
  /** No AI can write questions yet. */
  | { kind: "needs_ai"; title: string }
  /** Getting a book ready, or writing its questions, stopped. */
  | { kind: "failed"; title: string; target: { sourceId: string } | { batchId: string } }
  /** A book's card asks for something else (a cost, a setting, changes to look at). */
  | { kind: "needs_look"; title: string }
  /** A book is being got ready, or its questions are being written. */
  | { kind: "on_the_way"; title: string; card: SourceLibraryCard | null }
  /** Only books kept for practice (past exams): nothing to read. */
  | { kind: "no_reading" }
  /** Every book's questions are built: reading on brings more. */
  | { kind: "all_read"; card: SourceLibraryCard | null };

function shownLine(card: SourceLibraryCard, ai: AiConnectionDto | null): SourceStatusLineDto | null {
  // As the shelf shows it (BookCard): the no-AI version while no AI can write.
  return (ai && ai.canAuthor === false ? card.statusLine?.withoutAi : null) ?? card.statusLine ?? null;
}

type Rank = "waiting_ok" | "needs_ai" | "failed" | "needs_look" | "on_the_way";
const ORDER: readonly Rank[] = ["waiting_ok", "needs_ai", "failed", "needs_look", "on_the_way"];

function rankOf(line: SourceStatusLineDto | null, ai: AiConnectionDto | null): Rank | null {
  if (!line) return null;
  const action = line.action;
  if (action?.kind === "connect_ai") {
    // The connection says which is missing; without it, the sidecar's label does.
    const consent = ai ? ai.needs === "consent" || (ai.needs === null && action.label === SIDECAR_CONSENT_LABEL) : action.label === SIDECAR_CONSENT_LABEL;
    return consent ? "waiting_ok" : "needs_ai";
  }
  if (line.tone === "working") return "on_the_way";
  if (line.tone === "problem" && action?.kind === "retry" && FAILURE_RETRY_LABELS.has(action.label)) return "failed";
  if (action || line.tone === "problem") return "needs_look";
  return null;
}

/**
 * Why Today has nothing to practise, or null while it cannot be told yet (the
 * library or the list not read). `listItems` is the number of questions on
 * today's list (null: not read); pass 0 where the list does not apply.
 */
export function todayCause(input: {
  cards: readonly SourceLibraryCard[] | null | undefined;
  pending?: readonly PendingAddDto[] | null;
  ai: AiConnectionDto | null;
  listItems: number | null;
}): TodayCause | null {
  if (input.listItems === null || !input.cards) return null;
  if (input.listItems > 0) return { kind: "list_has_more" };
  const readable = input.cards.filter((card) => card.readerEnabled !== false);
  const found: Array<{ rank: Rank; title: string; card: SourceLibraryCard | null; batchId: string | null }> = [];
  for (const card of readable) {
    const rank = rankOf(shownLine(card, input.ai), input.ai);
    if (rank) found.push({ rank, title: readableTitle(card.title), card, batchId: null });
  }
  for (const entry of input.pending ?? []) {
    const rank = rankOf(entry.statusLine, input.ai);
    // A link still being fetched has no card to open or act on: its OK goes
    // through the Library (an upload's OK), its failure retries by its batch.
    if (rank) found.push({ rank: rank === "waiting_ok" || rank === "needs_ai" ? "needs_look" : rank, title: entry.title, card: null, batchId: entry.batchId });
  }
  for (const rank of ORDER) {
    const hits = found.filter((entry) => entry.rank === rank);
    const first = hits[0];
    if (!first) continue;
    switch (rank) {
      case "waiting_ok":
        return { kind: "waiting_ok", title: first.title, others: hits.length - 1 };
      case "needs_ai":
        return { kind: "needs_ai", title: first.title };
      case "failed":
        return { kind: "failed", title: first.title, target: first.card ? { sourceId: first.card.sourceId } : { batchId: first.batchId as string } };
      case "needs_look":
        return { kind: "needs_look", title: first.title };
      case "on_the_way":
        return { kind: "on_the_way", title: first.title, card: first.card };
    }
  }
  if (readable.length === 0) return { kind: "no_reading" };
  return { kind: "all_read", card: readable.find((card) => card.readiness === "ready") ?? readable[0] ?? null };
}

/** The cause in one plain sentence (or two short ones), as Today says it. */
export function causeSentence(cause: TodayCause): string {
  switch (cause.kind) {
    case "list_has_more":
      return "Today's list still has questions, if you'd like some.";
    case "waiting_ok":
      return `Questions for “${cause.title}”${cause.others > 0 ? ` and ${cause.others} more` : ""} are waiting for your OK.`;
    case "needs_ai":
      return `LearnLoop needs an AI connected to write questions for “${cause.title}”.`;
    case "failed":
      return `Couldn't get questions ready for “${cause.title}”.`;
    case "needs_look":
      return `“${cause.title}” needs a look in your Library.`;
    case "on_the_way":
      return `Questions for “${cause.title}” are on their way. Keep reading meanwhile.`;
    case "no_reading":
      return "LearnLoop writes questions from what you read. Add a book, paper or lecture to read.";
    case "all_read":
      return "Everything you've read has its questions. Reading on brings more.";
  }
}

/** "Practise for this goal" found nothing (audit UX-6, F1): the same cause,
 *  for the goal. A goal with questions of its own that are not up today says
 *  so instead; Today cannot tell which book a goal reads from. */
export const GOAL_NOTHING_LEAD = "Nothing for this goal is ready to practise yet:";
export const GOAL_NOT_UP_TODAY = "Nothing for this goal is up today. Its questions come back on the days they're due.";

export function goalCauseSentence(cause: TodayCause): string {
  const sentence = causeSentence(cause);
  // After the colon the sentence starts in lower case, except a name ("LearnLoop needs…").
  const joined = sentence.startsWith("LearnLoop") ? sentence : `${sentence.charAt(0).toLowerCase()}${sentence.slice(1)}`;
  return `${GOAL_NOTHING_LEAD} ${joined}`;
}

/** The finished plan's line: nothing else is asked of the learner today. */
export const PLAN_FINISHED = "Nothing else is needed today.";

/** Said in place when Keep going comes back with nothing added (UX-4). */
export const KEEP_GOING_NOTHING_LEAD = "Nothing more to plan today.";

/** The one action beside a cause: its label, or null where there is none. */
export function causeActionLabel(cause: TodayCause): string | null {
  switch (cause.kind) {
    case "list_has_more":
      return "Open today's list";
    case "waiting_ok":
      return CONSENT_ACTION;
    case "needs_ai":
      return "Connect";
    case "failed":
      return "Try again";
    case "needs_look":
      return "Open Library";
    case "on_the_way":
      return cause.card ? "Continue reading" : null;
    case "no_reading":
      return "+ Add";
    case "all_read":
      return cause.card ? "Continue reading" : null;
  }
}

/** Whether the action sends passages to a model, so "what's sent" is beside it. */
export function causeSendsPassages(cause: TodayCause): boolean {
  return cause.kind === "waiting_ok" || cause.kind === "failed";
}

export const WHATS_SENT = "what's sent";
