// UX fix stage 3 (UX journey audit P1, F1, UX-4, UX-6): an empty Today says
// why, and offers the one step that would change it. First questions arrive
// (P11, F20): once a learner's first questions exist, Today offers them by
// name; until then it says the rule that brings them.
//
// The cause is read from what the desktop already has: the book cards' own
// status lines (the sidecar's `source_status_line`, add_source.py) and the
// facts they carry, the links still being added, the AI connection, and
// today's list. Nothing here estimates or decides anything; it picks which of
// the cards' states to name on Today, and says it in Today's words. The book
// card keeps its own line.
//
// The rule Today says (docs/reviews/ux-first-questions-today.md, step 0): a
// book added through Add is built with no questions to practise; a section's
// questions are written when the learner finishes it (on the desktop: its
// quick check finished, or "Done with this section" at its end), and once
// written they are on today's list at once.
//
// Today's list comes first: when it still has questions, there is something
// to practise, whatever the books say. The plan alone cannot tell a stop the
// router chose with work left from a day with nothing left to plan (its
// stopReason is free text, sometimes the model's own rationale), so Today
// reads the list instead of guessing.
//
// Pure: the phone imports it (`@desktop/app/todayCause`), so it reaches no
// Tauri binding (apps/learnloop-mobile/src/desktopImports.test.ts).

import type { AiConnectionDto, PendingAddDto, ReadingQuestionsDto, SourceLibraryCard, SourceStatusLineDto } from "../api/dto";

/** The card's action that asks for the one-time OK to write questions (UX
 *  fix stage 3, audit F7: it read "Review", which opened the OK while the
 *  learner expected questions). Today's empty-day line uses the same words. */
export const CONSENT_ACTION = "Give your OK";

/** The sidecar's label on that action (add_source.py, `needs_consent`). */
export const SIDECAR_CONSENT_LABEL = "Review";

/** Never a file address on the surface: a stray ``file://…/linear_algebra.pdf``
 * reads as "Linear Algebra" (the sidecar already does this; this is the net). */
export function readableTitle(title: string): string {
  const trimmed = (title || "").trim();
  if (!trimmed.startsWith("file://") && !trimmed.startsWith("/")) return trimmed;
  const name = decodeURIComponent(trimmed.split("/").pop() ?? trimmed).replace(/\.[A-Za-z0-9]{1,5}$/, "");
  const words = name.split(/[_\-.\s]+/).filter(Boolean);
  if (words.length === 0) return trimmed;
  const lower = words.every((word) => word === word.toLowerCase());
  return words.map((word) => (lower ? word.charAt(0).toUpperCase() + word.slice(1) : word)).join(" ");
}

/** The failure labels of a card's retry that carries no fact of its own (add_source.py: an import that failed,
 *  "Try again"; question writing that stopped, "Retry", before the sidecar said `retried`). A stopped build is told
 *  by its `retried` fact. Other retry actions ("Build them as you read", "Finish moving them", "Get it ready") are
 *  not failures. */
const FAILURE_RETRY_LABELS: ReadonlySet<string> = new Set(["Retry", "Try again"]);

export type TodayCause =
  /** Today's list still has questions: the plan stopped with something left. */
  | { kind: "list_has_more" }
  /** Questions written from what the learner finished reading. `count`: how many are on today's list (or, where the
   *  list is not read, how many were written); `itemId`: the first of them on today's list, which Begin opens (null:
   *  no Begin). */
  | { kind: "questions_ready"; title: string; part: string | null; count: number; itemId: string | null; card: SourceLibraryCard }
  /** A book's questions wait for the one-time OK. */
  | { kind: "waiting_ok"; title: string; others: number }
  /** No AI can write questions yet. */
  | { kind: "needs_ai"; title: string }
  /** Getting a book ready failed (`build: false`), or its build stopped (`build: true`; `retried`: after its own retry). */
  | { kind: "failed"; title: string; target: { sourceId: string } | { batchId: string }; build: boolean; retried: boolean }
  /** Writing the questions of a finished section stopped; `resumeId` tries it again. */
  | { kind: "section_failed"; title: string; part: string | null; resumeId: string }
  /** A book's card asks for something else (a cost, a setting, changes to look at). */
  | { kind: "needs_look"; title: string }
  /** A book is being got ready for questions; `progress` and `minutes` where the build says them. */
  | { kind: "on_the_way"; title: string; card: SourceLibraryCard | null; progress: { done: number; total: number } | null; minutes: number | null }
  /** The questions of a section the learner finished are being written. */
  | { kind: "section_writing"; title: string; part: string | null; card: SourceLibraryCard }
  /** Only books kept for practice (past exams): nothing to read. */
  | { kind: "no_reading" }
  /** No section is finished yet: a book's first questions come when one is. */
  | { kind: "finish_section"; card: SourceLibraryCard | null }
  /** A book's questions from reading exist and none is on today's list. */
  | { kind: "none_up"; title: string; card: SourceLibraryCard };

function shownLine(card: SourceLibraryCard, ai: AiConnectionDto | null): SourceStatusLineDto | null {
  // As the shelf shows it (BookCard): the no-AI version while no AI can write.
  return (ai && ai.canAuthor === false ? card.statusLine?.withoutAi : null) ?? card.statusLine ?? null;
}

/** The book's reading facts, from its card's own line (the no-AI version carries none). */
function questionsOf(card: SourceLibraryCard): ReadingQuestionsDto | null {
  return card.statusLine?.questions ?? null;
}

type Rank = "waiting_ok" | "needs_ai" | "failed" | "section_failed" | "needs_look" | "on_the_way" | "section_writing";
const ORDER: readonly Rank[] = ["waiting_ok", "needs_ai", "failed", "section_failed", "needs_look", "on_the_way", "section_writing"];

function rankOf(line: SourceStatusLineDto | null, ai: AiConnectionDto | null): Rank | null {
  if (!line) return null;
  const action = line.action;
  if (action?.kind === "connect_ai") {
    // The connection says which is missing; without it, the sidecar's label does.
    const consent = ai ? ai.needs === "consent" || (ai.needs === null && action.label === SIDECAR_CONSENT_LABEL) : action.label === SIDECAR_CONSENT_LABEL;
    return consent ? "waiting_ok" : "needs_ai";
  }
  if (line.tone === "working") return "on_the_way";
  // A stopped build says so by its fact; an import that failed only by its label.
  if (line.tone === "problem" && action?.kind === "retry" && (line.retried !== undefined || FAILURE_RETRY_LABELS.has(action.label))) return "failed";
  if (action || line.tone === "problem") return "needs_look";
  return null;
}

/** The part of a book named on Today: its one section, by label; or null, and the book's title is said instead
 *  (several sections, or a reading that is one section, whose label names nothing: "Document"). */
export function partName(labels: readonly string[], sectionCount: number): string | null {
  const named = [...new Set(labels.map((label) => label.trim()).filter(Boolean))];
  if (named.length !== 1 || sectionCount <= 1) return null;
  return named[0];
}

/**
 * Why Today has nothing to practise, or what it can offer, or null while it cannot be told yet (the library or the
 * list not read). `listItems` is the number of questions on today's list (null: not read); pass 0 where the list does
 * not apply. `listItemIds` are their question ids, to tell which are a book's questions from reading. `listUnknown`:
 * the list is not read here at all (the phone's Today): a book's questions are then named by how many were written,
 * with no Begin, and nothing is said about today's list.
 */
export function todayCause(input: {
  cards: readonly SourceLibraryCard[] | null | undefined;
  pending?: readonly PendingAddDto[] | null;
  ai: AiConnectionDto | null;
  listItems: number | null;
  listItemIds?: readonly string[] | null;
  listUnknown?: boolean;
}): TodayCause | null {
  const unknown = input.listUnknown === true;
  if ((!unknown && input.listItems === null) || !input.cards) return null;
  const readable = input.cards.filter((card) => card.readerEnabled !== false);
  if (!unknown && (input.listItems ?? 0) > 0) {
    // A book's questions from reading on today's list: offered by name, with Begin.
    const listed = input.listItemIds ?? [];
    for (const card of readable) {
      const questions = questionsOf(card);
      const own = new Set(questions?.itemIds ?? []);
      const mine = listed.filter((id) => own.has(id));
      if (questions && mine.length > 0) {
        return { kind: "questions_ready", title: readableTitle(card.title), part: partName(questions.sections, questions.sectionCount), count: mine.length, itemId: mine[0], card };
      }
    }
    return { kind: "list_has_more" };
  }
  const found: Array<{ rank: Rank; title: string; card: SourceLibraryCard | null; batchId: string | null }> = [];
  for (const card of readable) {
    const rank = rankOf(shownLine(card, input.ai), input.ai);
    if (rank) found.push({ rank, title: readableTitle(card.title), card, batchId: null });
    // A finished section's questions being written, or stopped, whatever the card's own line says.
    const questions = questionsOf(card);
    if (questions?.failed.length) found.push({ rank: "section_failed", title: readableTitle(card.title), card, batchId: null });
    if (questions?.writing.length) found.push({ rank: "section_writing", title: readableTitle(card.title), card, batchId: null });
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
    const line = first.card?.statusLine ?? null;
    const questions = first.card ? questionsOf(first.card) : null;
    switch (rank) {
      case "waiting_ok":
        return { kind: "waiting_ok", title: first.title, others: hits.length - 1 };
      case "needs_ai":
        return { kind: "needs_ai", title: first.title };
      case "failed":
        return {
          kind: "failed",
          title: first.title,
          target: first.card ? { sourceId: first.card.sourceId } : { batchId: first.batchId as string },
          build: line?.retried !== undefined,
          retried: line?.retried === true
        };
      case "section_failed": {
        const stopped = questions?.failed ?? [];
        return { kind: "section_failed", title: first.title, part: partName(stopped.map((entry) => entry.label), questions?.sectionCount ?? 0), resumeId: stopped[0].resumeId };
      }
      case "needs_look":
        return { kind: "needs_look", title: first.title };
      case "on_the_way":
        return { kind: "on_the_way", title: first.title, card: first.card, progress: line?.progress ?? null, minutes: line?.minutes ?? null };
      case "section_writing":
        return { kind: "section_writing", title: first.title, part: partName(questions?.writing ?? [], questions?.sectionCount ?? 0), card: first.card as SourceLibraryCard };
    }
  }
  if (readable.length === 0) return { kind: "no_reading" };
  for (const card of readable) {
    // Questions from reading written but held for a look: the Library is where they are looked at.
    const questions = questionsOf(card);
    if (questions && questions.toLookAt > 0 && questions.count === 0) return { kind: "needs_look", title: readableTitle(card.title) };
  }
  const withQuestions = readable.find((card) => (questionsOf(card)?.count ?? 0) > 0);
  if (unknown && withQuestions) {
    const questions = questionsOf(withQuestions) as ReadingQuestionsDto;
    return { kind: "questions_ready", title: readableTitle(withQuestions.title), part: partName(questions.sections, questions.sectionCount), count: questions.count, itemId: null, card: withQuestions };
  }
  // A built book with no section finished: the step that brings its first questions comes before a book whose
  // questions are not up today.
  const unfinished = readable.find((card) => questionsOf(card)?.count === 0);
  if (unfinished) return { kind: "finish_section", card: unfinished };
  if (withQuestions) return { kind: "none_up", title: readableTitle(withQuestions.title), card: withQuestions };
  return { kind: "finish_section", card: readable.find((card) => card.readiness === "ready") ?? readable[0] ?? null };
}

function questionsWord(count: number): string {
  return count === 1 ? "1 question" : `${count} questions`;
}

function minutesWords(minutes: number): string {
  return minutes < 1 ? "usually under a minute" : `usually about ${Math.round(minutes)} min`;
}

/** The words of a cause that is a wait: the waiting indicator's line, and what to know meanwhile (`after`). */
export function causeWait(cause: TodayCause): { line: string; after: string } | null {
  switch (cause.kind) {
    case "on_the_way": {
      const amount = cause.progress && cause.progress.total > 0 ? ` · ${cause.progress.done} of ${cause.progress.total} steps done` : "";
      const usually = cause.minutes !== null ? ` · ${minutesWords(cause.minutes)}` : "";
      return {
        line: `Getting “${cause.title}” ready for questions${amount}${usually}`,
        after: "Questions come as you finish sections. Keep reading meanwhile."
      };
    }
    case "section_writing":
      return {
        line: cause.part ? `Writing questions from “${cause.part}”, the part you read…` : `Writing questions from what you read in “${cause.title}”…`,
        after: "Keep reading meanwhile."
      };
    default:
      return null;
  }
}

/** The cause in one plain sentence (or two short ones), as Today says it. */
export function causeSentence(cause: TodayCause): string {
  switch (cause.kind) {
    case "list_has_more":
      return "Today's list still has questions, if you'd like some.";
    case "questions_ready":
      return cause.part
        ? `${questionsWord(cause.count)} from “${cause.part}”, the part you read. More come as you finish sections.`
        : `${questionsWord(cause.count)} from what you read in “${cause.title}”. More come as you finish sections.`;
    case "waiting_ok":
      return `Questions for “${cause.title}”${cause.others > 0 ? ` and ${cause.others} more` : ""} are waiting for your OK.`;
    case "needs_ai":
      return `LearnLoop needs an AI connected to write questions for “${cause.title}”.`;
    case "failed":
      if (!cause.build) return `Couldn't get questions ready for “${cause.title}”.`;
      return `Couldn't get “${cause.title}” ready for questions${cause.retried ? ", after trying twice" : ""}. Try again, or keep reading: nothing is lost.`;
    case "section_failed":
      return cause.part
        ? `Couldn't write the questions from “${cause.part}”. Try again, or keep reading: nothing is lost.`
        : `Couldn't write the questions from what you read in “${cause.title}”. Try again, or keep reading: nothing is lost.`;
    case "needs_look":
      return `“${cause.title}” needs a look in your Library.`;
    case "on_the_way":
    case "section_writing": {
      const wait = causeWait(cause) as { line: string; after: string };
      return wait.line.endsWith("…") ? `${wait.line} ${wait.after}` : `${wait.line}. ${wait.after}`;
    }
    case "no_reading":
      return "LearnLoop writes questions from what you read. Add a book, paper or lecture to read.";
    case "finish_section":
      return cause.card
        ? `Your first questions come when you finish a section of “${readableTitle(cause.card.title)}”: finish its quick check, or press Done with this section at its end.`
        : "Your first questions come when you finish a section: finish its quick check, or press Done with this section at its end.";
    case "none_up":
      return `Nothing from “${cause.title}” is up today. More questions come as you finish sections.`;
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

/** The finished plan's line: nothing else is asked of the learner today. Said only when nothing is left: no block
 *  of the plan undone and nothing on today's list. */
export const PLAN_FINISHED = "Nothing else is needed today.";

/** A closed plan with work left (the plan stopped, or the learner did, while questions remain for today). */
export const PLAN_STOPPED_WITH_MORE = "The plan stopped here, but there's more for today if you'd like it.";

/** Said in place when Keep going comes back with nothing added (UX-4). */
export const KEEP_GOING_NOTHING_LEAD = "Nothing more to plan today.";

/** A lesson left open (closed with Close, or left for another screen): its line on Today, with Continue beside it. */
export function continueLessonLine(title: string): string {
  return `Continue your lesson on ${title}`;
}

/** Said when Close leaves a lesson open: where it went. */
export const LESSON_KEPT = "Your lesson is kept. It's on Today when you want it.";

/** The one action beside a cause: its label, or null where there is none. */
export function causeActionLabel(cause: TodayCause): string | null {
  switch (cause.kind) {
    case "list_has_more":
      return "Open today's list";
    case "questions_ready":
      return cause.itemId ? "Begin ↵" : null;
    case "waiting_ok":
      return CONSENT_ACTION;
    case "needs_ai":
      return "Connect";
    case "failed":
    case "section_failed":
      return "Try again";
    case "needs_look":
      return "Open Library";
    case "on_the_way":
    case "section_writing":
    case "finish_section":
    case "none_up":
      return cause.card ? "Continue reading" : null;
    case "no_reading":
      return "+ Add";
  }
}

/** Whether the action sends passages to a model, so "what's sent" is beside it. */
export function causeSendsPassages(cause: TodayCause): boolean {
  return cause.kind === "waiting_ok" || cause.kind === "failed" || cause.kind === "section_failed";
}

export const WHATS_SENT = "what's sent";
