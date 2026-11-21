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
// written they are on today's list at once. A section finished before the
// book's topics for it were in waits for them, and is written once they are
// (docs/reviews/ux31-section-done-before-build.md). A book whose build found
// no topic to practise says so, with Try again; its finished sections get their
// questions once a later build finds topics (docs/reviews/ux43-empty-build.md).
// A section's questions are written topic by topic and each topic's questions apply at once, so they can be
// offered while more are written, or beside a topic that could not be written
// (docs/reviews/ux-first-questions-progress.md).
//
// Today's list comes first: when it still has questions, there is something
// to practise, whatever the books say. The plan alone cannot tell a stop the
// router chose with work left from a day with nothing left to plan (its
// stopReason is free text, sometimes the model's own rationale), so Today
// reads the list instead of guessing.
//
// Pure: the phone imports it (`@desktop/app/todayCause`), so it reaches no
// Tauri binding (apps/learnloop-mobile/src/desktopImports.test.ts).

import type { AiConnectionDto, PendingAddDto, QueueSnapshot, ReadingQuestionsDto, ScheduledItemDto, SourceLibraryCard, SourceStatusLineDto } from "../api/dto";
import { WAITING_COPY } from "../copy/waiting";

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

type Progress = { done: number; total: number };

export type TodayCause =
  /** Today's list still has questions: the plan stopped with something left. */
  | { kind: "list_has_more" }
  /** Questions written from what the learner finished reading. `count`: how many are on today's list (or, where the
   *  list is not read, how many were written); `itemId`: the first of them on today's list, which Begin opens (null:
   *  no Begin). */
  | { kind: "questions_ready"; title: string; part: string | null; count: number; itemId: string | null; card: SourceLibraryCard }
  /** The same questions, while the reading's finished sections are still being written (`writing`: with how many
   *  topics are done, where the fact says it for the sections named), or after some topics' questions could not be
   *  written (`failedTopics`). `resumeId`: the stopped batch Try again resumes; null while that section is still being
   *  written, when a resume would requeue nothing. */
  | {
      kind: "questions_ready_with_section_work";
      title: string;
      part: string | null;
      count: number;
      itemId: string | null;
      card: SourceLibraryCard;
      writing: { progress: Progress | null } | null;
      failedTopics: boolean;
      resumeId: string | null;
    }
  /** A book's questions wait for the one-time OK. */
  | { kind: "waiting_ok"; title: string; others: number }
  /** No AI can write questions yet. */
  | { kind: "needs_ai"; title: string }
  /** Getting a book ready failed (`build: false`), or its build stopped (`build: true`; `retried`: after its own retry). */
  | { kind: "failed"; title: string; target: { sourceId: string } | { batchId: string }; build: boolean; retried: boolean }
  /** A book's build finished with no topic to practise: Try again (the card's retry, `sourceId`) asks once more;
   *  Continue reading opens the book. */
  | { kind: "no_topics"; title: string; card: SourceLibraryCard; sourceId: string }
  /** Writing the questions of a finished section stopped; `resumeId` tries it again. */
  | { kind: "section_failed"; title: string; part: string | null; resumeId: string }
  /** A book's card asks for something else (a cost, a setting, changes to look at). */
  | { kind: "needs_look"; title: string }
  /** A book is being got ready for questions; `progress` and `minutes` where the build says them. `waiting`: a section
   *  the learner finished waits for it (`part`: that section, or null for what they read of the book). */
  | { kind: "on_the_way"; title: string; card: SourceLibraryCard | null; progress: { done: number; total: number } | null; minutes: number | null; waiting?: { part: string | null } | null; firstBuild?: boolean }
  /** The questions of a section the learner finished are being written; `progress`: how many of its topics are done,
   *  where the fact says it for that section. `failedTopics`: some of its topics' questions could not be written while
   *  the rest still are; said beside the writing, with no Try again (a resume requeues nothing while the job runs). */
  | { kind: "section_writing"; title: string; part: string | null; card: SourceLibraryCard; progress?: Progress | null; failedTopics?: boolean }
  /** A section the learner finished waits for its book to be ready: its questions are written then. */
  | { kind: "section_waiting"; title: string; part: string | null; card: SourceLibraryCard }
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

/** A book's written questions that cannot be asked now (answered and not due again yet, or kept for a later check on
 *  your own): today's list keeps both, so being on it is not being askable. */
function laterOf(questions: ReadingQuestionsDto): ReadonlySet<string> {
  return new Set(questions.laterItemIds ?? []);
}

/** How many of a book's written questions can be asked now, where today's list is not read (the phone). */
function askableWritten(questions: ReadingQuestionsDto): number {
  // The later ones are some of the written ones (`itemIds`, which `count` counts).
  return Math.max(0, questions.count - laterOf(questions).size);
}

/** The questions on today's list that wait to come back: answered, and not due again yet (the list keeps them in its
 *  "later" part with their next due time; a question never answered has none). */
export function waitingOnList(rows: readonly Pick<ScheduledItemDto, "practiceItemId" | "dueAt" | "dueStatus">[], now: number = Date.now()): string[] {
  return rows
    .filter((row) => row.dueStatus === "later" && row.dueAt !== null && Date.parse(row.dueAt) > now)
    .map((row) => row.practiceItemId);
}

type Rank = "waiting_ok" | "needs_ai" | "failed" | "no_topics" | "section_failed" | "needs_look" | "on_the_way" | "section_writing" | "section_waiting";
const ORDER: readonly Rank[] = ["waiting_ok", "needs_ai", "failed", "no_topics", "section_failed", "needs_look", "on_the_way", "section_writing", "section_waiting"];

function rankOf(line: SourceStatusLineDto | null, ai: AiConnectionDto | null): Rank | null {
  if (!line) return null;
  const action = line.action;
  if (action?.kind === "connect_ai") {
    // The connection says which is missing; without it, the sidecar's label does.
    const consent = ai ? ai.needs === "consent" || (ai.needs === null && action.label === SIDECAR_CONSENT_LABEL) : action.label === SIDECAR_CONSENT_LABEL;
    return consent ? "waiting_ok" : "needs_ai";
  }
  if (line.tone === "working") return "on_the_way";
  // Told by its fact, before the label: its action is a retry labelled as an import failure's is.
  if (line.noTopics === true) return "no_topics";
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

/** Whether a stopped entry is a section still being written: one job writes a finished section, and its entry's label
 *  is the section's, or the section's followed by the topics that failed ("Section: Topic A, Topic B", add_source.py
 *  `reading_questions`). Such a job is still running: a resume requeues only stopped jobs, so it would do nothing. */
function stillWriting(entry: { label: string }, writing: readonly string[]): boolean {
  return writing.some((label) => entry.label === label || entry.label.startsWith(`${label}: `));
}

/** The stopped entries: those whose section is no longer being written, which a resume can requeue. */
function stoppedEntries(questions: ReadingQuestionsDto): ReadingQuestionsDto["failed"] {
  return questions.failed.filter((entry) => !stillWriting(entry, questions.writing));
}

/** How many topics of the sections being written are done. The fact's `progress` adds up every finished section of
 *  the reading, so it is said only where no other finished section shows in the fact (none gave questions or stopped
 *  outside the writing): otherwise the amount would not be the named section's. */
function writingProgress(questions: ReadingQuestionsDto): Progress | null {
  const progress = questions.progress;
  if (!progress || progress.total <= 0 || questions.writing.length === 0) return null;
  const others = questions.sections.some((label) => !questions.writing.includes(label))
    || questions.failed.some((entry) => !stillWriting(entry, questions.writing));
  return others ? null : progress;
}

/** A book's questions offered (or, on the phone, written) together with the writing still under way or stopped topics:
 *  null when neither, and the plain offer stands. */
function readyWithSectionWork(card: SourceLibraryCard, questions: ReadingQuestionsDto, count: number, itemId: string | null): TodayCause | null {
  if (questions.writing.length === 0 && questions.failed.length === 0) return null;
  const stopped = stoppedEntries(questions);
  return {
    kind: "questions_ready_with_section_work",
    title: readableTitle(card.title),
    part: partName(questions.sections, questions.sectionCount),
    count,
    itemId,
    card,
    writing: questions.writing.length > 0 ? { progress: writingProgress(questions) } : null,
    failedTopics: questions.failed.length > 0,
    resumeId: stopped[0]?.resumeId ?? null
  };
}

/**
 * Why Today has nothing to practise, or what it can offer, or null while it cannot be told yet (the library or the
 * list not read). `listItems` is the number of questions on today's list (null: not read); pass 0 where the list does
 * not apply. `listItemIds` are their question ids, to tell which are a book's questions from reading; `listWaiting`,
 * those of them answered and not due again yet (`waitingOnList`). `listUnknown`: the list is not read here at all (the
 * phone's Today): a book's questions are then named by how many were written and can be asked now, with no Begin,
 * and nothing is said about today's list.
 *
 * A book's question is offered only when it can be asked now: on today's list, not waiting to come back, and not kept
 * for a later check (the book's `laterItemIds`). The list keeps the others, so counting the list would offer, and
 * Begin would open, a question answered minutes ago.
 */
export function todayCause(input: {
  cards: readonly SourceLibraryCard[] | null | undefined;
  pending?: readonly PendingAddDto[] | null;
  ai: AiConnectionDto | null;
  listItems: number | null;
  listItemIds?: readonly string[] | null;
  listWaiting?: readonly string[] | null;
  listUnknown?: boolean;
}): TodayCause | null {
  const unknown = input.listUnknown === true;
  if ((!unknown && input.listItems === null) || !input.cards) return null;
  const readable = input.cards.filter((card) => card.readerEnabled !== false);
  if (!unknown && (input.listItems ?? 0) > 0) {
    // A book's questions from reading on today's list: offered by name, with Begin.
    const listed = input.listItemIds ?? [];
    const waiting = new Set(input.listWaiting ?? []);
    // A book's questions on the list that cannot be asked now: they neither make an offer nor "more on the list".
    const notNow = new Set<string>();
    for (const card of readable) {
      const questions = questionsOf(card);
      if (!questions) continue;
      const own = new Set(questions.itemIds);
      const later = laterOf(questions);
      for (const id of listed) if (own.has(id) && (waiting.has(id) || later.has(id))) notNow.add(id);
      const mine = listed.filter((id) => own.has(id) && !notNow.has(id));
      if (mine.length > 0) {
        // While more of them are written, or some topics could not be, Begin still offers these.
        return readyWithSectionWork(card, questions, mine.length, mine[0])
          ?? { kind: "questions_ready", title: readableTitle(card.title), part: partName(questions.sections, questions.sectionCount), count: mine.length, itemId: mine[0], card };
      }
    }
    // Only a book's questions that wait (answered and not due again, or kept for a later check) left on the list: the books say
    // what comes next (more being written, or none up today), below.
    if (listed.length === 0 || listed.some((id) => !notNow.has(id))) return { kind: "list_has_more" };
  }
  const found: Array<{ rank: Rank; title: string; card: SourceLibraryCard | null; batchId: string | null }> = [];
  for (const card of readable) {
    const rank = rankOf(shownLine(card, input.ai), input.ai);
    if (rank) found.push({ rank, title: readableTitle(card.title), card, batchId: null });
    // A finished section's questions being written, or stopped, whatever the card's own line says. A topic that failed
    // in a section still being written is said with that writing, not as a stop: Try again would requeue nothing.
    const questions = questionsOf(card);
    if (questions && stoppedEntries(questions).length > 0) found.push({ rank: "section_failed", title: readableTitle(card.title), card, batchId: null });
    if (questions?.writing.length) found.push({ rank: "section_writing", title: readableTitle(card.title), card, batchId: null });
    if (questions?.waiting?.length) found.push({ rank: "section_waiting", title: readableTitle(card.title), card, batchId: null });
  }
  for (const entry of input.pending ?? []) {
    const rank = rankOf(entry.statusLine, input.ai);
    // A link still being fetched has no card to open or act on: its OK goes
    // through the Library (an upload's OK), its failure retries by its batch.
    if (rank) found.push({ rank: rank === "waiting_ok" || rank === "needs_ai" || rank === "no_topics" ? "needs_look" : rank, title: entry.title, card: null, batchId: entry.batchId });
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
      case "no_topics":
        return { kind: "no_topics", title: first.title, card: first.card as SourceLibraryCard, sourceId: (first.card as SourceLibraryCard).sourceId };
      case "section_failed": {
        // Where the list is not read (the phone), questions already written are said with the stopped topics.
        const written = unknown && questions && askableWritten(questions) > 0 && first.card
          ? readyWithSectionWork(first.card, questions, askableWritten(questions), null)
          : null;
        if (written) return written;
        const stopped = questions ? stoppedEntries(questions) : [];
        return { kind: "section_failed", title: first.title, part: partName(stopped.map((entry) => entry.label), questions?.sectionCount ?? 0), resumeId: stopped[0].resumeId };
      }
      case "needs_look":
        return { kind: "needs_look", title: first.title };
      case "on_the_way": {
        // The book being got ready is where a finished section's questions come from: say that, not the rule.
        const waiting = questions?.waiting?.length ? { part: partName(questions.waiting, questions.sectionCount) } : null;
        // Only a build's own line says its steps and, where the library measured a build, its minutes: a build line with
        // no minutes is the library's first. The sidecar copies the sections' `questions.progress` onto a line with none of
        // its own ("Chapters found"), which says nothing about the library's builds.
        const copied = questions?.progress && line?.progress
          && questions.progress.done === line.progress.done && questions.progress.total === line.progress.total;
        const firstBuild = Boolean(line?.progress) && !copied && (line?.minutes ?? null) === null;
        return { kind: "on_the_way", title: first.title, card: first.card, progress: line?.progress ?? null, minutes: line?.minutes ?? null, waiting, firstBuild };
      }
      case "section_writing": {
        // Where the list is not read (the phone), questions already written are said with the writing.
        const written = unknown && questions && askableWritten(questions) > 0 && first.card
          ? readyWithSectionWork(first.card, questions, askableWritten(questions), null)
          : null;
        if (written) return written;
        return {
          kind: "section_writing",
          title: first.title,
          part: partName(questions?.writing ?? [], questions?.sectionCount ?? 0),
          card: first.card as SourceLibraryCard,
          progress: questions ? writingProgress(questions) : null,
          failedTopics: (questions?.failed.length ?? 0) > 0
        };
      }
      case "section_waiting":
        return { kind: "section_waiting", title: first.title, part: partName(questions?.waiting ?? [], questions?.sectionCount ?? 0), card: first.card as SourceLibraryCard };
    }
  }
  if (readable.length === 0) return { kind: "no_reading" };
  for (const card of readable) {
    // Questions from reading written but held for a look: the Library is where they are looked at.
    const questions = questionsOf(card);
    if (questions && questions.toLookAt > 0 && questions.count === 0) return { kind: "needs_look", title: readableTitle(card.title) };
  }
  const withQuestions = readable.find((card) => (questionsOf(card)?.count ?? 0) > 0);
  const askable = unknown
    ? readable.find((card) => {
        const questions = questionsOf(card);
        return questions !== null && askableWritten(questions) > 0;
      })
    : undefined;
  if (askable) {
    const questions = questionsOf(askable) as ReadingQuestionsDto;
    return { kind: "questions_ready", title: readableTitle(askable.title), part: partName(questions.sections, questions.sectionCount), count: askableWritten(questions), itemId: null, card: askable };
  }
  // A built book with no section finished: the step that brings its first questions comes before a book whose
  // questions are not up today. A section finished with nothing to write is finished all the same: asking for it to
  // be finished contradicts the Reader, which shows it done.
  const finishedNone = (card: SourceLibraryCard) => (questionsOf(card)?.noneNeeded?.length ?? 0) > 0;
  const unfinished = readable.find((card) => questionsOf(card)?.count === 0 && !finishedNone(card));
  if (unfinished) return { kind: "finish_section", card: unfinished };
  const finished = withQuestions ?? readable.find(finishedNone);
  if (finished) return { kind: "none_up", title: readableTitle(finished.title), card: finished };
  return { kind: "finish_section", card: readable.find((card) => card.readiness === "ready") ?? readable[0] ?? null };
}

/**
 * The question Today's Begin would open now: the first of a book's questions from reading that can be asked now, in
 * today's list order, as its row on the list; null when Today offers none. Feedback's Next goes on to it when the day's
 * plan has nothing next, so Next and Begin never disagree. `answered`: the question just answered, never offered again
 * even if the list read predates its answer.
 */
export function askableReadingQuestion(
  cards: readonly SourceLibraryCard[] | null | undefined,
  queue: QueueSnapshot | null | undefined,
  answered: string | null = null,
  now: number = Date.now()
): ScheduledItemDto | null {
  if (!cards || !queue) return null;
  const rows = queue.sections.flatMap((section) => section.items).filter((row) => row.practiceItemId !== answered);
  const cause = todayCause({
    cards, ai: null, listItems: rows.length, listItemIds: rows.map((row) => row.practiceItemId), listWaiting: waitingOnList(rows, now)
  });
  if (!cause || (cause.kind !== "questions_ready" && cause.kind !== "questions_ready_with_section_work") || !cause.itemId) return null;
  return rows.find((row) => row.practiceItemId === cause.itemId) ?? null;
}

function questionsWord(count: number): string {
  return count === 1 ? "1 question" : `${count} questions`;
}

/** A finished section's questions, promised for when its book is ready. */
function waitingWords(title: string, part: string | null): string {
  return part
    ? `Your questions from “${part}” will be written as soon as “${title}” is ready.`
    : `Your questions from what you read will be written as soon as “${title}” is ready.`;
}

function minutesWords(minutes: number): string {
  return minutes < 1 ? "usually under a minute" : `usually about ${Math.round(minutes)} min`;
}

function topicsDone(progress: Progress): string {
  return `${progress.done} of ${progress.total} ${progress.total === 1 ? "topic" : "topics"} done`;
}

/** The words of a cause that is a wait: the waiting indicator's line, what to know meanwhile (`after`), and the
 *  indicator's quieter second line where something true can be said (`later`). */
export function causeWait(cause: TodayCause): { line: string; after: string; later: string | null } | null {
  switch (cause.kind) {
    case "on_the_way": {
      const amount = cause.progress && cause.progress.total > 0 ? ` · ${cause.progress.done} of ${cause.progress.total} steps done` : "";
      const usually = cause.minutes !== null ? ` · ${minutesWords(cause.minutes)}` : "";
      return {
        line: `Getting “${cause.title}” ready for questions${amount}${usually}`,
        after: cause.waiting
          ? `${waitingWords(cause.title, cause.waiting.part)} Keep reading meanwhile.`
          : "Questions come as you finish sections. Keep reading meanwhile.",
        later: cause.firstBuild ? WAITING_COPY.firstBuildLater : null
      };
    }
    case "section_writing": {
      const amount = cause.progress && cause.progress.total > 0 ? ` · ${topicsDone(cause.progress)}` : "…";
      return {
        line: cause.part ? `Writing questions from “${cause.part}”, the part you read${amount}` : `Writing questions from what you read in “${cause.title}”${amount}`,
        after: "Keep reading meanwhile.",
        later: null
      };
    }
    default:
      return null;
  }
}

function readySentence(cause: { title: string; part: string | null; count: number }): string {
  return cause.part
    ? `${questionsWord(cause.count)} from “${cause.part}”, the part you read. More come as you finish sections.`
    : `${questionsWord(cause.count)} from what you read in “${cause.title}”. More come as you finish sections.`;
}

/** Said beside questions offered while some topics' questions could not be written. The fact names the failed topics
 *  only inside one label per section, so it says no count. */
export const TOPICS_NOT_WRITTEN = "Not every topic's questions could be written.";

/** The questions offered, and more being written ("2 of 8 topics done" where the fact says it for these sections). */
export function readyWithWorkSentence(cause: Extract<TodayCause, { kind: "questions_ready_with_section_work" }>): string {
  if (!cause.writing) return readySentence(cause);
  const progress = cause.writing.progress;
  const more = `More are being written${progress && progress.total > 0 ? ` (${topicsDone(progress)})` : ""}.`;
  const verb = cause.count === 1 ? "is" : "are";
  return cause.part
    ? `${questionsWord(cause.count)} from “${cause.part}” ${verb} ready. ${more}`
    : `${questionsWord(cause.count)} from what you read in “${cause.title}” ${verb} ready. ${more}`;
}

/** The line under questions offered, or under the writing still going on, when some topics' questions could not be
 *  written, or null. */
export function causeTopicsFailed(cause: TodayCause): string | null {
  return (cause.kind === "questions_ready_with_section_work" || cause.kind === "section_writing") && cause.failedTopics ? TOPICS_NOT_WRITTEN : null;
}

/** The cause in one plain sentence (or two short ones), as Today says it. */
export function causeSentence(cause: TodayCause): string {
  switch (cause.kind) {
    case "list_has_more":
      return "Today's list still has questions, if you'd like some.";
    case "questions_ready":
      return readySentence(cause);
    case "questions_ready_with_section_work": {
      const failed = causeTopicsFailed(cause);
      return failed ? `${readyWithWorkSentence(cause)} ${failed}` : readyWithWorkSentence(cause);
    }
    case "waiting_ok":
      return `Questions for “${cause.title}”${cause.others > 0 ? ` and ${cause.others} more` : ""} are waiting for your OK.`;
    case "needs_ai":
      return `LearnLoop needs an AI connected to write questions for “${cause.title}”.`;
    case "failed":
      if (!cause.build) return `Couldn't get questions ready for “${cause.title}”.`;
      return `Couldn't get “${cause.title}” ready for questions${cause.retried ? ", after trying twice" : ""}. Try again, or keep reading: nothing is lost.`;
    case "no_topics":
      return `LearnLoop found no topics to practise in “${cause.title}”. Try again, or keep reading: the sections you finish get their questions once topics are found.`;
    case "section_waiting":
      return waitingWords(cause.title, cause.part);
    case "section_failed":
      return cause.part
        ? `Couldn't write the questions from “${cause.part}”. Try again, or keep reading: nothing is lost.`
        : `Couldn't write the questions from what you read in “${cause.title}”. Try again, or keep reading: nothing is lost.`;
    case "needs_look":
      return `“${cause.title}” needs a look in your Library.`;
    case "on_the_way":
    case "section_writing": {
      const wait = causeWait(cause) as { line: string; after: string };
      const failed = causeTopicsFailed(cause);
      const after = failed ? `${failed} ${wait.after}` : wait.after;
      return wait.line.endsWith("…") ? `${wait.line} ${after}` : `${wait.line}. ${after}`;
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
    case "questions_ready_with_section_work":
      return cause.itemId ? "Begin ↵" : null;
    case "waiting_ok":
      return CONSENT_ACTION;
    case "needs_ai":
      return "Connect";
    case "failed":
    case "no_topics":
    case "section_failed":
      return "Try again";
    case "needs_look":
      return "Open Library";
    case "on_the_way":
    case "section_writing":
    case "section_waiting":
    case "finish_section":
    case "none_up":
      return cause.card ? "Continue reading" : null;
    case "no_reading":
      return "+ Add";
  }
}

/** The second action beside a cause, or null: reading on, beside a Try again that need not be pressed first. */
export function causeSecondActionLabel(cause: TodayCause): string | null {
  return cause.kind === "no_topics" ? "Continue reading" : null;
}

/** Whether the action sends passages to a model, so "what's sent" is beside it. */
export function causeSendsPassages(cause: TodayCause): boolean {
  return cause.kind === "waiting_ok" || cause.kind === "failed" || cause.kind === "no_topics" || cause.kind === "section_failed";
}

export const WHATS_SENT = "what's sent";
