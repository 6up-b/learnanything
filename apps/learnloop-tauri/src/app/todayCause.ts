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
// (docs/reviews/ux-first-questions-progress.md). A topic also gets its first questions before its section is
// finished, once the learner has seen every passage it cites: those are "questions from what you've read", and a
// section read in part with none yet says where to read to (docs/reviews/first-evening-step-4.md, -step-8.md).
// Wherever Today says where questions come from, it says one thing: QUESTIONS_FROM_READING, and MORE_AS_YOU_READ
// after questions offered. "As you finish sections" stopped being the rule when a part read could give questions.
//
// Today's list comes first: when it still has questions, there is something
// to practise, whatever the books say. The plan alone cannot tell a stop the
// router chose with work left from a day with nothing left to plan (its
// stopReason is free text, sometimes the model's own rationale), so Today
// reads the list instead of guessing.
//
// Pure: the phone imports it (`@desktop/app/todayCause`), so it reaches no
// Tauri binding (apps/learnloop-mobile/src/desktopImports.test.ts).

import type { AiConnectionDto, BuildDetailDto, PendingAddDto, QueueSnapshot, ReadingQuestionsDto, ScheduledItemDto, SourceLibraryCard, SourceStatusLineDto, WritingDetailDto } from "../api/dto";
import { WAITING_COPY } from "../copy/waiting";

/** Where questions come from, in the one set of words every screen that says it uses (Today on the desktop and the
 *  phone, the Library's card details, the Reader's guide; the sidecar's card line and whole-book notice say the same
 *  in its `READING_RULE`). */
export const QUESTIONS_FROM_READING = "Questions are written from the parts you read.";
/** The same rule said after questions offered, or none up today. */
export const MORE_AS_YOU_READ = "More come as you read on.";
/** The heading above work under way (a book being got ready, questions being written or waiting for the book), in
 *  place of "Nothing planned for today." or "Nothing more to plan today.": the cause line below says what is under
 *  way, and "nothing" above it read as nothing coming. */
export const NO_QUESTIONS_YET = "No questions ready yet.";

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
/** A book's topics whose questions were written so far, and those still being written, across every wave of its
 *  writing (the fact's `topics`). */
type TopicCount = { written: number; writing: number };

export type TodayCause =
  /** Today's list still has questions: the plan stopped with something left. */
  | { kind: "list_has_more" }
  /** Questions written from what the learner finished reading. `count`: how many are on today's list (or, where the
   *  list is not read, how many were written); `itemId`: the first of them on today's list, which Begin opens (null:
   *  no Begin). */
  | { kind: "questions_ready"; title: string; part: string | null; count: number; itemId: string | null; card: SourceLibraryCard;
      /** Every one of them came from a section the learner has not finished: questions "from what you've read". */
      fromReading?: boolean }
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
      /** `topics`: the book's own count across waves, where the line can say it (preferred to `progress`, one wave's). */
      writing: { progress: Progress | null; topics?: TopicCount | null } | null;
      failedTopics: boolean;
      resumeId: string | null;
      fromReading?: boolean;
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
  | { kind: "on_the_way"; title: string; card: SourceLibraryCard | null; progress: { done: number; total: number } | null; minutes: number | null;
      /** `fromReading`: what waits is a section the learner read part of, not one they finished. */
      waiting?: { part: string | null; fromReading?: boolean } | null; firstBuild?: boolean;
      /** Its getting ready waits its turn behind this book's work. */
      behind?: string | null;
      /** Books whose getting ready waits its turn behind this one's. */
      queued?: readonly string[];
      /** What the build is doing now, in recorded facts (`app/waitDetail`); absent where the line carries none. */
      detail?: BuildDetailDto | null } & AllRead
  /** The questions of a section the learner finished are being written; `progress`: how many of its topics are done,
   *  where the fact says it for that section. `failedTopics`: some of its topics' questions could not be written while
   *  the rest still are; said beside the writing, with no Try again (a resume requeues nothing while the job runs). */
  | { kind: "section_writing"; title: string; part: string | null; card: SourceLibraryCard; progress?: Progress | null; failedTopics?: boolean;
      /** The book's topics written so far and still being written, across its waves, where the line can say it. */
      topics?: TopicCount | null;
      /** The writing is of sections the learner has not finished: questions from what they've read. */
      fromReading?: boolean;
      /** What the writing is doing now, in recorded facts (`app/waitDetail`); absent where the fact carries none. */
      detail?: WritingDetailDto | null } & AllRead
  /** A section the learner finished waits for its book to be ready: its questions are written then. `fromReading`: it is
   *  a section they read part of. */
  | { kind: "section_waiting"; title: string; part: string | null; card: SourceLibraryCard; fromReading?: boolean }
  /** The learner read part of a section and no topic of it has every passage seen yet: reading on brings the first
   *  questions. `place`: where reading on must reach for the nearest topic, when the book's facts say. */
  | { kind: "read_further"; title: string; card: SourceLibraryCard; place?: { part: string | null; heading: string | null; words: string | null; sectionEnd: boolean } | null }
  /** Every question written from the book's reading waits for the learner's OK (`count`: those an OK would apply). No
   *  screen yet lets them be looked at without their answers, so nothing here opens one. */
  | { kind: "held"; title: string; card: SourceLibraryCard; count: number }
  /** On the phone: what the learner read qualifies topics for questions, which the desktop writes when it runs. */
  | { kind: "reading_saved"; title: string; card: SourceLibraryCard }
  /** Only books kept for practice (past exams): nothing to read. */
  | { kind: "no_reading" }
  /** Nothing read yet that could give questions: a book's first questions come from the parts the learner reads. */
  | { kind: "finish_section"; card: SourceLibraryCard | null }
  /** A book's questions from reading exist and none is on today's list. */
  | { kind: "none_up"; title: string; card: SourceLibraryCard };

/** Every section of the named book is finished (`allRead`, the book's fact): a wait for its questions then says it is all
 *  read, never "Keep reading meanwhile." `phone`: said on the phone, where the work is the desktop's. Both present only
 *  when the book is all read. */
type AllRead = { allRead?: true; phone?: true };

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

type Rank = "waiting_ok" | "needs_ai" | "failed" | "no_topics" | "section_failed" | "needs_look" | "on_the_way" | "section_writing" | "section_waiting" | "reading_saved";
const ORDER: readonly Rank[] = ["waiting_ok", "needs_ai", "failed", "no_topics", "section_failed", "needs_look", "on_the_way", "section_writing", "section_waiting", "reading_saved"];

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

/** Whether every one of these sections is one the learner has not finished (read in part, or with questions from the
 *  part read): their questions are "from what you've read". False for none. */
function fromReading(questions: ReadingQuestionsDto, labels: readonly string[]): boolean {
  const partial = new Set([...(questions.partRead ?? []), ...(questions.owed ?? [])]);
  return labels.length > 0 && labels.every((label) => partial.has(label));
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

/** The book's topics written so far and still being written, across every wave of its writing, where the line can say
 *  them: a line that names the book, or one that names the part every question and every writing of the book is from
 *  (a count over several sections beside one section's name would not be that section's). Null when the fact has no
 *  such count (nothing being written, or an older sidecar): the wave's own `progress` is said then, as before. */
function bookTopics(questions: ReadingQuestionsDto, part: string | null): TopicCount | null {
  const topics = questions.topics;
  if (!topics || topics.writing <= 0) return null;
  if (part === null) return topics;
  const own = [...questions.sections, ...questions.writing].every((label) => label === part)
    && questions.failed.every((entry) => entry.label === part || entry.label.startsWith(`${part}: `));
  return own ? topics : null;
}

/** The writing's detail, its topic placed in the book's count ("topic 3 of 5" beside "2 topics written · 3 more being
 *  written"): the sidecar places it among its own job's topics, which restart with each wave. A topic with no place
 *  (other writing runs beside it) keeps none. */
function placedDetail(detail: WritingDetailDto, topics: TopicCount | null): WritingDetailDto {
  const topic = detail.topic;
  if (!topics || !topic || topic.index === null || topic.total === null) return detail;
  return { ...detail, topic: { ...topic, index: topics.written + 1, total: topics.written + topics.writing } };
}

function allReadOf(questions: ReadingQuestionsDto | null, phone: boolean): AllRead {
  if (questions?.allRead !== true) return {};
  return phone ? { allRead: true, phone: true } : { allRead: true };
}

/** The questions written from the learner's reading, across the readable books (their `itemIds`): the questions Today
 *  offers from what was read. */
export function readingItemIds(cards: readonly SourceLibraryCard[] | null | undefined): string[] {
  return (cards ?? []).filter((card) => card.readerEnabled !== false).flatMap((card) => questionsOf(card)?.itemIds ?? []);
}

/** A book's questions offered (or, on the phone, written) together with the writing still under way or stopped topics:
 *  null when neither, and the plain offer stands. */
function readyWithSectionWork(card: SourceLibraryCard, questions: ReadingQuestionsDto, count: number, itemId: string | null): TodayCause | null {
  if (questions.writing.length === 0 && questions.failed.length === 0) return null;
  const stopped = stoppedEntries(questions);
  const part = partName(questions.sections, questions.sectionCount);
  const topics = bookTopics(questions, part);
  return {
    kind: "questions_ready_with_section_work",
    title: readableTitle(card.title),
    part,
    count,
    itemId,
    card,
    writing: questions.writing.length > 0 ? { progress: writingProgress(questions), ...(topics ? { topics } : {}) } : null,
    failedTopics: questions.failed.length > 0,
    resumeId: stopped[0]?.resumeId ?? null,
    ...(fromReading(questions, questions.sections) ? { fromReading: true } : {})
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
          ?? { kind: "questions_ready", title: readableTitle(card.title), part: partName(questions.sections, questions.sectionCount), count: mine.length, itemId: mine[0], card,
            ...(fromReading(questions, questions.sections) ? { fromReading: true } : {}) };
      }
    }
    // Only a book's questions that wait (answered and not due again, or kept for a later check) left on the list: the books say
    // what comes next (more being written, or none up today), below.
    if (listed.length === 0 || listed.some((id) => !notNow.has(id))) return { kind: "list_has_more" };
  }
  const found: Array<{ rank: Rank; title: string; card: SourceLibraryCard | null; batchId: string | null; line?: SourceStatusLineDto | null }> = [];
  for (const card of readable) {
    const rank = rankOf(shownLine(card, input.ai), input.ai);
    if (rank) found.push({ rank, title: readableTitle(card.title), card, batchId: null });
    // A finished section's questions being written, or stopped, whatever the card's own line says. A topic that failed
    // in a section still being written is said with that writing, not as a stop: Try again would requeue nothing.
    const questions = questionsOf(card);
    if (questions && stoppedEntries(questions).length > 0) found.push({ rank: "section_failed", title: readableTitle(card.title), card, batchId: null });
    if (questions?.writing.length) found.push({ rank: "section_writing", title: readableTitle(card.title), card, batchId: null });
    // A topic of a section read in part qualifies and its questions are not started: the desktop starts them on this
    // very read, so it says they are being written; the phone leaves them to the desktop and says so.
    else if (questions?.owed?.length) found.push({ rank: unknown ? "reading_saved" : "section_writing", title: readableTitle(card.title), card, batchId: null });
    if (questions?.waiting?.length || questions?.beforeBuild?.length) found.push({ rank: "section_waiting", title: readableTitle(card.title), card, batchId: null });
  }
  for (const entry of input.pending ?? []) {
    const rank = rankOf(entry.statusLine, input.ai);
    // A link still being fetched has no card to open or act on: its OK goes
    // through the Library (an upload's OK), its failure retries by its batch.
    if (rank) found.push({ rank: rank === "waiting_ok" || rank === "needs_ai" || rank === "no_topics" ? "needs_look" : rank, title: entry.title, card: null, batchId: entry.batchId, line: entry.statusLine });
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
        const waiting = questions?.waiting?.length
          ? { part: partName(questions.waiting, questions.sectionCount) }
          : questions?.beforeBuild?.length ? { part: partName(questions.beforeBuild, questions.sectionCount), fromReading: true } : null;
        // Only a build's own line says its steps and, where the library measured a build, its minutes: a build line with
        // no minutes is the library's first. The sidecar copies the sections' `questions.progress` onto a line with none of
        // its own ("Chapters found"), which says nothing about the library's builds.
        const copied = questions?.progress && line?.progress
          && questions.progress.done === line.progress.done && questions.progress.total === line.progress.total;
        const firstBuild = Boolean(line?.progress) && !copied && (line?.minutes ?? null) === null;
        // One book is got ready at a time: one queued behind another's work says which, and the book at work names those behind it.
        const behind = (first.line ?? line)?.waitingBehind ?? null;
        const queued = hits.slice(1).filter((hit) => (hit.line ?? hit.card?.statusLine)?.waitingBehind === first.title).map((hit) => hit.title);
        return { kind: "on_the_way", title: first.title, card: first.card, progress: line?.progress ?? null, minutes: line?.minutes ?? null, waiting, firstBuild,
          ...(behind ? { behind } : {}), ...(queued.length ? { queued } : {}), ...(!behind && line?.buildDetail ? { detail: line.buildDetail } : {}),
          ...allReadOf(questions, unknown) };
      }
      case "section_writing": {
        // Where the list is not read (the phone), questions already written are said with the writing.
        const written = unknown && questions && askableWritten(questions) > 0 && first.card
          ? readyWithSectionWork(first.card, questions, askableWritten(questions), null)
          : null;
        if (written) return written;
        const labels = questions?.writing.length ? questions.writing : questions?.owed ?? [];
        const part = partName(labels, questions?.sectionCount ?? 0);
        const topics = questions ? bookTopics(questions, part) : null;
        return {
          kind: "section_writing",
          title: first.title,
          part,
          card: first.card as SourceLibraryCard,
          progress: questions ? writingProgress(questions) : null,
          failedTopics: (questions?.failed.length ?? 0) > 0,
          ...(topics ? { topics } : {}),
          ...(questions && fromReading(questions, labels) ? { fromReading: true } : {}),
          ...(questions?.writing.length && questions.writingDetail ? { detail: placedDetail(questions.writingDetail, topics) } : {}),
          ...allReadOf(questions, unknown)
        };
      }
      case "section_waiting": {
        const finished = questions?.waiting ?? [];
        const labels = finished.length ? finished : questions?.beforeBuild ?? [];
        return { kind: "section_waiting", title: first.title, part: partName(labels, questions?.sectionCount ?? 0), card: first.card as SourceLibraryCard,
          ...(finished.length === 0 && labels.length > 0 ? { fromReading: true } : {}) };
      }
      case "reading_saved":
        return { kind: "reading_saved", title: first.title, card: first.card as SourceLibraryCard };
    }
  }
  if (readable.length === 0) return { kind: "no_reading" };
  for (const card of readable) {
    // Every question from its reading held for the learner's OK. Not "needs a look in your Library": the screens there
    // show a held question's answer before it was tried. Held rows no OK could apply are not counted.
    const questions = questionsOf(card);
    if (questions && (questions.awaitingOk ?? 0) > 0 && questions.count === 0) {
      return { kind: "held", title: readableTitle(card.title), card, count: questions.awaitingOk as number };
    }
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
    return { kind: "questions_ready", title: readableTitle(askable.title), part: partName(questions.sections, questions.sectionCount), count: askableWritten(questions), itemId: null, card: askable,
      ...(fromReading(questions, questions.sections) ? { fromReading: true } : {}) };
  }
  // A built book with no section finished: the step that brings its first questions comes before a book whose
  // questions are not up today. A section finished with nothing to write is finished all the same: asking for it to
  // be finished contradicts the Reader, which shows it done.
  const finishedNone = (card: SourceLibraryCard) => (questionsOf(card)?.noneNeeded?.length ?? 0) > 0;
  // Read in part, with no topic's passages all seen yet: reading on is what brings the first questions.
  const readSome = readable.find((card) => questionsOf(card)?.count === 0 && (questionsOf(card)?.readFurther?.length ?? 0) > 0);
  if (readSome) {
    const questions = questionsOf(readSome) as ReadingQuestionsDto;
    const to = questions.readTo ?? null;
    return { kind: "read_further", title: readableTitle(readSome.title), card: readSome,
      place: to ? { part: partName([to.section], questions.sectionCount), heading: to.heading, words: to.words, sectionEnd: to.sectionEnd } : null };
  }
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

/** Whether the cause is work under way (a book being got ready, questions being written, or waiting for the book or
 *  the desktop): the cause line says it, and the heading above says no questions are ready yet. */
export function causeUnderway(cause: TodayCause | null | undefined): boolean {
  return cause?.kind === "on_the_way" || cause?.kind === "section_writing" || cause?.kind === "section_waiting" || cause?.kind === "reading_saved";
}

/** The line for questions held for the learner's OK, beside whatever else Today says, or null when none: how many an
 *  OK would apply, across the books ("more" when some of their questions are already there). It names no question and
 *  opens nothing: no screen yet shows a held question without its answer. */
export function heldLine(cards: readonly SourceLibraryCard[] | null | undefined): string | null {
  const readable = (cards ?? []).filter((card) => card.readerEnabled !== false);
  const held = readable.reduce((sum, card) => sum + (questionsOf(card)?.awaitingOk ?? 0), 0);
  if (held <= 0) return null;
  const more = readable.some((card) => (questionsOf(card)?.count ?? 0) > 0) ? "more " : "";
  return held === 1 ? `1 ${more}question needs your OK.` : `${held} ${more}questions need your OK.`;
}

/** Of today's list, the questions that cannot be asked now: answered and not due again yet (`listWaiting`), or a
 *  book's question kept for a later check on your own (its `laterItemIds`). "More for today" counts only the rest. */
export function notAskableOnList(cards: readonly SourceLibraryCard[] | null | undefined, listItemIds: readonly string[],
                                 listWaiting: readonly string[]): string[] {
  const later = new Set((cards ?? []).flatMap((card) => questionsOf(card)?.laterItemIds ?? []));
  const waiting = new Set(listWaiting);
  return [...new Set(listItemIds.filter((id) => waiting.has(id) || later.has(id)))];
}

/** Where reading on must reach for the first questions, as far as the book's facts say it. */
function readToSentence(cause: Extract<TodayCause, { kind: "read_further" }>): string {
  const place = cause.place;
  const book = `“${cause.title}”`;
  if (place?.heading) return `Read through “${place.heading}” in ${book} for your first questions.`;
  if (place?.sectionEnd) {
    return place.part ? `Read to the end of “${place.part}” in ${book} for your first questions.` : `Read to the end of ${book} for your first questions.`;
  }
  if (place?.words) return `Read as far as the passage that begins “${place.words}” in ${book} for your first questions.`;
  return `Read a little further in ${book} for your first questions.`;
}

/** A finished section's questions, promised for when its book is ready. */
function waitingWords(title: string, part: string | null, fromReading = false): string {
  if (fromReading) return `Questions from what you’ve read will follow when “${title}” is ready.`;
  return part
    ? `Your questions from “${part}” will be written as soon as “${title}” is ready.`
    : `Your questions from what you read will be written as soon as “${title}” is ready.`;
}

function minutesWords(minutes: number): string {
  return minutes < 1 ? "usually under a minute" : `usually about ${Math.round(minutes)} min`;
}

/** Why a book's getting ready waits behind another's. */
export const ONE_BOOK_AT_A_TIME = "LearnLoop gets one book ready at a time.";

function topicsDone(progress: Progress): string {
  return `${progress.done} of ${progress.total} ${progress.total === 1 ? "topic" : "topics"} done`;
}

function topicsWord(n: number): string {
  return n === 1 ? "1 topic" : `${n} topics`;
}

/** The book's count, said the same way wherever Today says it: "2 topics written · 3 more being written" ("4 topics
 *  being written" before the first is). It never starts again with a wave, and never says a share or a time. */
export function topicCountWords(topics: TopicCount): string {
  return topics.written > 0
    ? `${topicsWord(topics.written)} written · ${topics.writing} more being written`
    : `${topicsWord(topics.writing)} being written`;
}

/** Said when every section of a book is finished, in place of "Keep reading meanwhile." */
export function allReadWords(title: string): string {
  return `You’ve read all of “${title}”.`;
}

/** Where a book's questions go once written (the Reader's finished section says it too). */
export const ON_TODAY = "They'll be on Today.";

/** Beside it, for a learner with nothing left to read who might think something is asked of them. */
export const NOTHING_TO_DO = "You don’t need to do anything for them.";

/** What closing the app does to the work, said while a book read to its end waits for it. A running job's lease is
 *  failed as interrupted when the app next opens (content/pipeline/runner.py `recover_stale_leases`), and nothing tries
 *  it again on its own: the book's Try again (or Retry) does. "You can close it and come back" would be false. */
export const KEEP_OPEN = "Leave LearnLoop open meanwhile: closing it stops the work until you try again.";
/** The same on the phone, whose Today reads the desktop's work: closing the phone app stops nothing. */
export const KEEP_OPEN_ON_DESKTOP = "Leave LearnLoop open on your desktop meanwhile: closing it there stops the work until you try again.";

/** The action beside a wait for a book read to its end: nothing is left to continue reading in it. */
export const OPEN_THE_BOOK = "Open the book";

/** What to know while a book read to its end waits: all read, where its questions go (when its finished sections wait
 *  for them, `promise`), the first build's time where it is the first, and what closing the app does. One block. */
function allReadBlock(cause: { title: string; phone?: true }, said: { promise?: string | null; onToday: boolean; first?: boolean }): string {
  return [allReadWords(cause.title), said.promise ?? null, said.onToday ? `${ON_TODAY} ${NOTHING_TO_DO}` : null,
    said.first ? WAITING_COPY.firstBuildLater : null, cause.phone ? KEEP_OPEN_ON_DESKTOP : KEEP_OPEN].filter(Boolean).join(" ");
}

/** The words of a cause that is a wait: the waiting indicator's line, what to know meanwhile (`after`), and the
 *  indicator's quieter second line where something true can be said (`later`). */
export function causeWait(cause: TodayCause): { line: string; after: string; later: string | null } | null {
  switch (cause.kind) {
    case "on_the_way": {
      if (cause.behind) {
        return { line: `“${cause.title}” is waiting its turn behind “${cause.behind}”`,
          after: `${ONE_BOOK_AT_A_TIME} ${cause.allRead ? allReadBlock(cause, { onToday: false }) : "Keep reading meanwhile."}`, later: null };
      }
      const amount = cause.progress && cause.progress.total > 0 ? ` · ${cause.progress.done} of ${cause.progress.total} steps done` : "";
      const usually = cause.minutes !== null ? ` · ${minutesWords(cause.minutes)}` : "";
      const queued = cause.queued?.length ? `${cause.queued.map((title) => `“${title}”`).join(" and ")} ${cause.queued.length === 1 ? "is waiting its" : "are waiting their"} turn behind it. ` : "";
      const promise = cause.waiting ? waitingWords(cause.title, cause.waiting.part, cause.waiting.fromReading === true) : null;
      if (cause.allRead) {
        // The first-time sentence is in the block: the indicator does not say it a second time.
        return { line: `Getting “${cause.title}” ready for questions${amount}${usually}`,
          after: queued + allReadBlock(cause, { promise, onToday: promise !== null, first: cause.firstBuild === true }), later: null };
      }
      return {
        line: `Getting “${cause.title}” ready for questions${amount}${usually}`,
        after: queued + (promise ? `${promise} Keep reading meanwhile.` : `${QUESTIONS_FROM_READING} Keep reading meanwhile.`),
        later: cause.firstBuild ? WAITING_COPY.firstBuildLater : null
      };
    }
    case "section_writing": {
      const amount = cause.topics ? ` · ${topicCountWords(cause.topics)}`
        : cause.progress && cause.progress.total > 0 ? ` · ${topicsDone(cause.progress)}` : "…";
      const after = cause.allRead ? allReadBlock(cause, { onToday: true }) : "Keep reading meanwhile.";
      if (cause.fromReading) {
        return {
          line: cause.part ? `Writing questions from what you’ve read of “${cause.part}”${amount}` : `Writing questions from what you’ve read in “${cause.title}”${amount}`,
          after,
          later: null
        };
      }
      return {
        line: cause.part ? `Writing questions from “${cause.part}”, the part you read${amount}` : `Writing questions from what you read in “${cause.title}”${amount}`,
        after,
        later: null
      };
    }
    default:
      return null;
  }
}

/** Where a book's questions came from, as the offer names it: what the learner has read, of a section or of the book. */
function fromWhatYouRead(cause: { title: string; part: string | null }): string {
  return cause.part ? `from what you’ve read of “${cause.part}”` : `from what you’ve read in “${cause.title}”`;
}

function readySentence(cause: { title: string; part: string | null; count: number; fromReading?: boolean }): string {
  if (cause.fromReading) {
    return `${questionsWord(cause.count)} ${fromWhatYouRead(cause)} ${cause.count === 1 ? "is" : "are"} ready. ${MORE_AS_YOU_READ}`;
  }
  return cause.part
    ? `${questionsWord(cause.count)} from “${cause.part}”, the part you read. ${MORE_AS_YOU_READ}`
    : `${questionsWord(cause.count)} from what you read in “${cause.title}”. ${MORE_AS_YOU_READ}`;
}

/** On the phone, for reading that qualifies topics whose questions the desktop writes (the phone writes none). */
export const READING_SAVED = "Your reading is saved. Questions will be written when the desktop is running.";

/** Said beside questions offered while some topics' questions could not be written. The fact names the failed topics
 *  only inside one label per section, so it says no count. */
export const TOPICS_NOT_WRITTEN = "Not every topic's questions could be written.";

/** The questions offered, and more being written ("2 of 8 topics done" where the fact says it for these sections). */
export function readyWithWorkSentence(cause: Extract<TodayCause, { kind: "questions_ready_with_section_work" }>): string {
  if (!cause.writing) return readySentence(cause);
  const progress = cause.writing.progress;
  const more = cause.writing.topics
    ? `${topicCountWords(cause.writing.topics)}.`
    : `More are being written${progress && progress.total > 0 ? ` (${topicsDone(progress)})` : ""}.`;
  const verb = cause.count === 1 ? "is" : "are";
  if (cause.fromReading) return `${questionsWord(cause.count)} ${fromWhatYouRead(cause)} ${verb} ready. ${more}`;
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
      return `LearnLoop found no topics to practise in “${cause.title}”. Try again, or keep reading: what you read gets its questions once topics are found.`;
    case "section_waiting":
      return waitingWords(cause.title, cause.part, cause.fromReading === true);
    case "read_further":
      return readToSentence(cause);
    case "held":
      return `${questionsWord(cause.count)} from what you’ve read in “${cause.title}” ${cause.count === 1 ? "needs" : "need"} your OK.`;
    case "reading_saved":
      return READING_SAVED;
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
        ? `Read “${readableTitle(cause.card.title)}” for your first questions. ${QUESTIONS_FROM_READING}`
        : QUESTIONS_FROM_READING;
    case "none_up":
      return `Nothing from “${cause.title}” is up today. ${MORE_AS_YOU_READ}`;
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
      return cause.card ? (cause.allRead ? OPEN_THE_BOOK : "Continue reading") : null;
    case "section_waiting":
    case "finish_section":
    case "none_up":
    case "read_further":
    case "reading_saved":
    case "held":
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
