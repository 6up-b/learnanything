// Ask your library (reader workbench RW4a; spec §7.3; UX §4.5, W9, W10).
//
// The comparing posture's state: a library question answered sources first
// (the passages land first, the organizer's one-line notes when ready), the
// "personalized" chip, pins, the display-only compare table, the tutor over
// the pinned passages, "practice this question" (find_practice with a Reader
// caller: it proposes, the plan's learner pick serves) and peek. Every
// model-backed part follows the seven-state contract (UX §4.0) at its own
// landing place; nothing here moves focus, animates or opens a modal.
//
// Off (no `libraryAsk` key in the prompt contract) the hook asks nothing and
// `enabled` is false, so no entry point renders (G20, U13).
//
// The ask, the notes, compare and the tutor each run as a sidecar job (the
// sidecar never waits on a model on its request path, so reading, peeking and
// opening another source go on meanwhile): the hook reads the job until it is
// done, and *cancel* (or closing the pane, asking again or leaving the Reader)
// cancels it; a cancelled or superseded job's result never lands, nor does its
// late failure (Codex review F6; re-review F12, F13). A read of a job answers
// at once (a wait would hold the serial sidecar), so the hook paces its reads
// (re-review F11).
//
// Reader CA3 (ux_reader_compare_ask_v1 §4; K12), only while the contract's
// `libraryAsk.compareScope` is on: one comparison request for every door
// (`comparePayload`): the selection verb and the tutor's offer open a
// comparison with no library answer first (`compareFrom`), the ask box reads
// named books first (`askBox`: one Decider reading, then the comparison at
// once, or today's library answer), and a library answer's "compare these
// books" compares the answer's books with no pins (`compareBooks`). The chips
// (`×`, "+ add a book") and the refine box (`/`, `refine`) re-run the same
// request; the earlier table stays one key away (`previous`). Off, none of it
// exists and every call is RW4a's/RW4d's.
import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "../../api/client";
import type {
  CompareDoor,
  CompareRequestDto,
  CompareScopeReadingDto,
  CompareTableDto,
  LibraryBookDto,
  FindPracticeResultDto,
  LibraryAskDto,
  LibraryAskEntry,
  LibraryJobDto,
  LibraryNotesDto,
  LibraryTutorDto,
  ReaderPromptContractDto,
  SpanViewDto,
} from "../../api/dto";
import { errorMessage, getCommandError } from "../../errors";
import { phaseForError, type ModelActionPhase } from "./ModelActionState";

export const LIBRARY_COPY = {
  title: "ASK YOUR LIBRARY",
  placeholder: "ask your library…",
  searching: "looking in your books",
  noting: "noting what each contributes",
  found: (basis: string) => `found by ${basis}`,
  notesBy: "notes by LearnLoop's model",
  personalizedOn: "personalized ●",
  personalizedOff: "personalized ○",
  personalizedWhy: "On: the notes may point out a passage that speaks to an open question of yours. Off: plain search order, and nothing about you is sent.",
  nothing: "Nothing in your books matched this yet.",
  compare: "compare pinned",
  compareNeeds: "pin passages from two places to compare them",
  comparing: "comparing your sources",
  askTutor: "ask the tutor about pinned",
  tutorWriting: "writing an answer from the pinned passages",
  tutorPlaceholder: "your question (empty: the library question)",
  practice: "practice this question",
  practiceLooking: "looking for practice",
  practiceNothing: "Nothing in practice fits yet.",
  speaksTo: "speaks to your open question about",
  modelsLabel: "model's label",
  prerequisitesTitle: "What this builds on",
  shown: "shown on your own",
  notShown: "not yet shown on your own",
  close: "esc back to reading",
} as const;

/** Reader CA3's words (§4.2, §4.3, X1, X2). */
export const SCOPE_COPY = {
  title: "COMPARE",
  reading: "reading which books you named",
  comparing: "comparing",
  allBooks: "all your books",
  yourPassage: "your passage",
  on: "on:",
  change: "change",
  addBook: "+ add a book",
  addPlaceholder: "a book in your library…",
  remove: (title: string) => `stop comparing ${title}`,
  notInLibrary: (name: string) => `“${name}” isn't in your library`,
  pending: "finding each book's passages, then lining them up",
  chooseBooks: "choose books ▸",
  compareBooks: "compare these books ▸",
  compareAll: (words: string) => `couldn't read which books you named · compare all your books on “${words}” ▸`,
  refine: "what do you want to see? a geometric view, an application, just the proofs… or other books",
  refineKeys: "/ refine · ↵ · esc",
  refining: "reading what you want to see",
  refineMissed: "Couldn't read that; the comparison is unchanged.",
  previous: "previous ▸",
  hidePrevious: "◂ back to this comparison",
  previousLabel: "the earlier comparison",
  askTutor: "ask the tutor about this comparison",
  askTutorNote: "answers only from these passages",
  /** Codex re-review F10: what the tutor's context budget (or a filter) left out, said. */
  tutorLeftOut: (count: number, reason: string) => `left out ${count === 1 ? "1 passage" : `${count} passages`}: ${reason}`,
  /** Codex review F2: every book was removed, so nothing is compared until one is chosen. */
  noBooks: "no books chosen · add one to compare",
  /** Codex review F8: the stored-size bound on views (a `keep` guardrail, §5.4), shown only when reached. */
  viewLimit: (max: number) => `${countWord(max)} views is the most a comparison keeps · remove one to add this`,
  removeView: (view: string, pending: string) => `remove “${view}” and add “${pending}”`,
  keepViews: "keep these",
  /** Codex review F1: the selection verb while a problem is open in the workbench. */
  waitsForWork: "Your comparison opens beside the book. Leave for now (your steps are kept) and it starts.",
} as const;

const COUNT_WORDS = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight"];
function countWord(n: number): string {
  return COUNT_WORDS[n] ?? String(n);
}

/** What one comparison request asks (every door builds one; K12). */
export interface CompareRequest {
  door: CompareDoor;
  askId?: string | null;
  question?: string | null;
  extractionId?: string | null;
  anchorSpanIds?: string[];
  sourceIds?: string[];
  pinnedSpanKeys?: string[];
  openSourceId?: string | null;
  requestedPerspectives?: string[];
  toolCallId?: string | null;
  /** The bound workbench session the request comes from (Codex review F1). */
  workbenchSessionId?: string | null;
}

/** The one payload every door sends (C1, K12): the same keys, whatever the door. */
export function comparePayload(request: CompareRequest): Required<CompareRequestDto> {
  return {
    door: request.door,
    askId: request.askId ?? null,
    question: request.question ?? null,
    extractionId: request.extractionId ?? null,
    anchorSpanIds: request.anchorSpanIds ?? [],
    sourceIds: request.sourceIds ?? [],
    pinnedSpanKeys: request.pinnedSpanKeys ?? [],
    openSourceId: request.openSourceId ?? null,
    requestedPerspectives: request.requestedPerspectives ?? [],
    toolCallId: request.toolCallId ?? null,
    workbenchSessionId: request.workbenchSessionId ?? null,
  };
}

/** The routed line's chips: the books, the topic, what wasn't matched (§4.2). */
export interface ScopeChips {
  /** The books compared (named or chosen); empty: every book with a match. */
  books: LibraryBookDto[];
  /** The anchor leads ("your passage"). */
  anchored: boolean;
  topic: string | null;
  unmatched: string | null;
  /** The reading the current books came from: the ask box's, or a refinement's
   *  (Codex review F9); an `×` or "+ add a book" is a learner correction of it. */
  judgmentId: string | null;
  /** The ask box's reading of the learner's words: "change" (rewording them)
   *  corrects it, whichever reading set the books since (F9). */
  askJudgmentId?: string | null;
  /** The learner's own words, kept for "change". */
  words: string | null;
  /** The learner removed every book: nothing is compared until one is chosen
   *  (an empty choice, never "every book": Codex review F2). */
  emptied?: boolean;
}

export type SourceCaller = { kind: "reader"; ref: string | null };

export interface LibraryAskRequest {
  query: string;
  entry: LibraryAskEntry;
  extractionId: string | null;
  spanIds: string[];
}

interface Stage<T> {
  phase: ModelActionPhase;
  value: T | null;
  failure: string | null;
  /** The learner cancelled it (idle, with a way to start it again). */
  cancelled?: boolean;
}

const IDLE = { phase: "idle" as ModelActionPhase, value: null, failure: null };
const CANCELLED = { phase: "idle" as ModelActionPhase, value: null, failure: null, cancelled: true };

type JobStage = "ask" | "notes" | "compare" | "tutor" | "scope";
const JOB_STAGES: JobStage[] = ["ask", "notes", "compare", "tutor", "scope"];
/** The pause between reads of a pending job (the sidecar's read never waits, F11). */
export const JOB_POLL_MS = 250;

function pause(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/** Refusals that say why: held-out material, or (RW4d fix round 5) a
 *  comparison withheld whole because a passage it drew on is held out now. */
const SAYS_WHY = new Set(["exam_material", "comparison_withheld"]);

/** A refusal that says why, else the stage's own line. */
function failureLine(error: unknown, fallback: string): string {
  const code = getCommandError(error)?.code;
  return code && SAYS_WHY.has(code) ? errorMessage(error) : fallback;
}

export interface LibraryAskState {
  key: number;
  request: LibraryAskRequest;
  personalized: boolean;
  ask: Stage<LibraryAskDto>;
  notes: Stage<LibraryNotesDto>;
  pinned: string[];
  compare: Stage<CompareTableDto>;
  tutor: Stage<LibraryTutorDto>;
  practice: Stage<FindPracticeResultDto>;
  peek: { key: string; phase: ModelActionPhase; view: SpanViewDto | null } | null;
  /** CA3: a comparison opened with no library answer (its request), else null. */
  direct?: CompareRequest | null;
  /** CA3: the ask box's reading of named books (pending while read). */
  scope?: Stage<CompareScopeReadingDto>;
  /** CA3: the routed line (absent before a comparison is asked). */
  chips?: ScopeChips | null;
  /** CA3: the library's books, for "+ add a book". */
  library?: LibraryBookDto[];
  /** CA3: the request the comparison stage last ran (re-run by chips and refine). */
  lastCompare?: CompareRequest | null;
  /** CA3: earlier tables of this comparison, newest last (never paid for twice). */
  previous?: CompareTableDto[];
  /** CA3: the refine box's reading. */
  refine?: Stage<CompareScopeReadingDto>;
  /** CA3: the ask box couldn't read the words: comparing them all is one press away. */
  compareAllWords?: string | null;
  /** What the tutor's answer is about: the pins, or the comparison shown (Codex
   *  review F5, F6: an answer about a comparison is cleared when it is re-run). */
  tutorBasis?: "pins" | "comparison" | null;
  /** Codex review F8: a view asked for at the bound, waiting on the learner's choice of one to remove. */
  viewLimit?: { pending: string; views: string[] } | null;
}

/** The organizer's status as a state: notes landed, capped, unreachable or failed. */
export function notesPhase(status: string): ModelActionPhase {
  if (status === "judged" || status === "cached" || status === "empty_pool") return "landed";
  if (status === "capped" || status.startsWith("over_budget")) return "capped";
  if (status.startsWith("unavailable") || status.startsWith("skipped")) return "unreachable";
  if (status === "cancelled") return "idle";
  return "failed";
}

/** compare_sources' status as a state ("too_few_sources" lands, with its line). */
export function comparePhase(status: string): ModelActionPhase {
  if (status === "ok" || status === "too_few_sources") return "landed";
  if (status.startsWith("over_budget")) return "capped";
  if (status.startsWith("unavailable") || status.startsWith("skipped")) return "unreachable";
  if (status === "cancelled") return "idle";
  return "failed";
}

/** The books a comparison compares now: the chips, else the table's own books. */
function shownCompared(current: LibraryAskState): string[] {
  if (current.chips?.books.length) return current.chips.books.map((book) => book.sourceId);
  const table = current.compare.value ?? current.previous?.[current.previous.length - 1] ?? null;
  return [...new Set((table?.rows ?? []).flatMap((row) => (row.sourceId ? [row.sourceId] : [])))];
}

export function useLibraryAsk({
  contract,
  openSourceId,
  onError,
}: {
  contract: ReaderPromptContractDto | null | undefined;
  /** The source open beside the answer: its passage leads a comparison. */
  openSourceId: string | null;
  onError: (message: string) => void;
}) {
  const settings = contract?.libraryAsk ?? null;
  const enabled = Boolean(settings);
  // RW4d: keep this comparison and its perspectives field (absent while off).
  const keep = settings && contract?.compareKeep?.library ? contract.compareKeep : null;
  // CA3: compare from anywhere (absent while reader_compare.scope_enabled is off).
  const scopeOn = Boolean(settings?.compare && settings?.compareScope);
  const [state, setState] = useState<LibraryAskState | null>(null);
  const keyRef = useRef(0);
  const stateRef = useRef<LibraryAskState | null>(null);
  stateRef.current = state;

  const update = useCallback((key: number, patch: (current: LibraryAskState) => Partial<LibraryAskState>) => {
    setState((current) => (current && current.key === key ? { ...current, ...patch(current) } : current));
  }, []);

  // Each stage's job in flight, and its epoch: a cancel (or a newer run of the
  // stage) bumps the epoch, so the older job's result is dropped on arrival.
  const jobsRef = useRef<Partial<Record<JobStage, string>>>({});
  const epochsRef = useRef<Record<JobStage, number>>({ ask: 0, notes: 0, compare: 0, tutor: 0, scope: 0 });

  const cancelStage = useCallback((stage: JobStage) => {
    epochsRef.current[stage] += 1;
    const jobId = jobsRef.current[stage];
    delete jobsRef.current[stage];
    if (jobId) void api.readerLibraryJobCancel({ jobId }).catch(() => undefined);
  }, []);

  /** Start a stage's job and read it until it is done; null once cancelled or
   * superseded, whether it then answers or fails (a stale failure is dropped
   * here, so no stage's catch sees it: re-review F12). */
  const runJob = useCallback(async <T,>(stage: JobStage, start: () => Promise<LibraryJobDto<T>>): Promise<T | null> => {
    cancelStage(stage);
    const epoch = epochsRef.current[stage];
    const live = () => epochsRef.current[stage] === epoch;
    try {
      let job = await start();
      if (!live()) {
        // Started after a cancel or after the Reader closed: cancel it, never read it (F13).
        if (job.state === "pending") void api.readerLibraryJobCancel({ jobId: job.jobId }).catch(() => undefined);
        return null;
      }
      jobsRef.current[stage] = job.jobId;
      while (job.state === "pending") {
        await pause(JOB_POLL_MS);
        if (!live()) return null;
        job = await api.readerLibraryJob<T>({ jobId: job.jobId });
        if (!live()) return null;
      }
      if (jobsRef.current[stage] === job.jobId) delete jobsRef.current[stage];
      return job.state === "done" ? job.result : null;
    } catch (error) {
      if (!live()) return null;
      if (jobsRef.current[stage]) delete jobsRef.current[stage];
      throw error;
    }
  }, [cancelStage]);

  const loadNotes = useCallback(async (key: number, askId: string) => {
    update(key, () => ({ notes: { phase: "pending", value: null, failure: null } }));
    try {
      const notes = await runJob("notes", () => api.readerLibraryAskNotes({ askId }));
      if (notes === null) return;
      update(key, () => ({ notes: { phase: notesPhase(notes.status), value: notes, failure: null } }));
    } catch (error) {
      update(key, () => ({ notes: { phase: phaseForError(error), value: null, failure: "Couldn't write the notes." } }));
    }
  }, [runJob, update]);

  const run = useCallback(async (request: LibraryAskRequest, personalized: boolean,
                                 extra: Partial<LibraryAskState> = {}) => {
    if (!enabled) return;
    for (const stage of JOB_STAGES) cancelStage(stage);
    const key = ++keyRef.current;
    setState({
      key, request, personalized, ask: { phase: "pending", value: null, failure: null }, notes: IDLE, pinned: [],
      compare: IDLE, tutor: IDLE, practice: IDLE, peek: null, ...extra,
    });
    try {
      const ask = await runJob("ask", () => api.readerLibraryAsk({
        query: request.query, entry: request.entry, extractionId: request.extractionId,
        spanIds: request.spanIds, personalized,
      }));
      if (keyRef.current !== key || ask === null) return;
      update(key, () => ({ ask: { phase: "landed", value: ask, failure: null } }));
      if (ask.hits.length > 0) void loadNotes(key, ask.askId);
    } catch (error) {
      if (keyRef.current !== key) return;
      update(key, () => ({ ask: { phase: phaseForError(error), value: null, failure: failureLine(error, "Couldn't look in your books.") } }));
    }
  }, [enabled, cancelStage, loadNotes, runJob, update]);

  /** Ask (the learner's act). The personalized chip starts at the vault's default. */
  const ask = useCallback((request: LibraryAskRequest) => {
    void run(request, settings?.personalizedDefault ?? true);
  }, [run, settings]);

  const retry = useCallback(() => {
    const current = stateRef.current;
    if (current) void run(current.request, current.personalized);
  }, [run]);

  /** The chip: asking again with personalization on or off (a new ask). */
  const setPersonalized = useCallback((on: boolean) => {
    const current = stateRef.current;
    if (current && current.personalized !== on) void run(current.request, on);
  }, [run]);

  const retryNotes = useCallback(() => {
    const current = stateRef.current;
    if (current?.ask.value) void loadNotes(current.key, current.ask.value.askId);
  }, [loadNotes]);

  /** Cancel a pending part: its job is cancelled and its result never lands. */
  const cancelNotes = useCallback(() => {
    const current = stateRef.current;
    cancelStage("notes");
    if (current) update(current.key, () => ({ notes: CANCELLED }));
  }, [cancelStage, update]);
  const cancelCompare = useCallback(() => {
    const current = stateRef.current;
    cancelStage("compare");
    if (current) update(current.key, () => ({ compare: CANCELLED }));
  }, [cancelStage, update]);
  const cancelTutor = useCallback(() => {
    const current = stateRef.current;
    cancelStage("tutor");
    if (current) update(current.key, () => ({ tutor: CANCELLED }));
  }, [cancelStage, update]);

  const togglePin = useCallback((hitKey: string) => {
    const current = stateRef.current;
    if (!current) return;
    update(current.key, (s) => ({
      pinned: s.pinned.includes(hitKey) ? s.pinned.filter((k) => k !== hitKey) : [...s.pinned, hitKey],
    }));
  }, [update]);

  /** Two pinned passages from different sources (the service has no source cap). */
  const canCompare = (() => {
    if (!settings?.compare || !state?.ask.value) return false;
    const sources = new Set(state.pinned.map((k) => state.ask.value?.hits.find((h) => h.key === k)?.sourceId ?? k));
    return state.pinned.length >= 2 && sources.size >= 2;
  })();

  /** CA3: run one comparison request in the compare stage (every door, chips and refine). */
  const runCompare = useCallback(async (key: number, request: CompareRequest) => {
    // Codex review F6: a tutor answer about the comparison being replaced is
    // about other passages: its job is cancelled and its answer cleared.
    const about = stateRef.current?.key === key ? stateRef.current.tutorBasis : null;
    if (about === "comparison") cancelStage("tutor");
    update(key, (s) => ({
      compare: { phase: "pending", value: null, failure: null }, lastCompare: request, viewLimit: null,
      // The table being replaced stays one key away (never paid for twice).
      previous: s.compare.value ? [...(s.previous ?? []), s.compare.value] : s.previous ?? [],
      ...(s.tutorBasis === "comparison" ? { tutor: IDLE, tutorBasis: null } : {}),
    }));
    try {
      const table = await runJob("compare", () => api.readerLibraryCompare(comparePayload(request)));
      if (table === null) return;
      const phase = comparePhase(table.status);
      update(key, (s) => ({
        compare: { phase, value: table, failure: phase === "failed" ? "Couldn't compare these books." : null },
        library: table.library?.length ? table.library : s.library ?? [],
      }));
    } catch (error) {
      update(key, () => ({ compare: { phase: phaseForError(error), value: null, failure: failureLine(error, "Couldn't compare these books.") } }));
    }
  }, [cancelStage, runJob, update]);

  /** Compare the pins; RW4d's requested perspectives go along only when given (and only while keep is on). */
  const compare = useCallback(async (perspectives: string[] = []) => {
    const current = stateRef.current;
    if (!current?.ask.value || !settings?.compare) return;
    const key = current.key;
    const askId = current.ask.value.askId;
    const pinnedSpanKeys = current.pinned;
    const requested = keep?.perspectives ? perspectives.slice(0, keep.maxPerspectives) : [];
    if (scopeOn) {
      // CA3: the pins are one more door of the one request.
      void runCompare(key, { door: "pins", askId, pinnedSpanKeys, openSourceId, requestedPerspectives: requested });
      return;
    }
    update(key, () => ({ compare: { phase: "pending", value: null, failure: null } }));
    try {
      const table = await runJob("compare", () => api.readerLibraryCompare(
        requested.length ? { askId, pinnedSpanKeys, openSourceId, requestedPerspectives: requested } : { askId, pinnedSpanKeys, openSourceId }));
      if (table === null) return;
      const phase = comparePhase(table.status);
      update(key, () => ({ compare: { phase, value: table, failure: phase === "failed" ? "Couldn't compare these passages." : null } }));
    } catch (error) {
      update(key, () => ({ compare: { phase: phaseForError(error), value: null, failure: failureLine(error, "Couldn't compare these passages.") } }));
    }
  }, [settings, keep, openSourceId, runJob, update, scopeOn, runCompare]);

  /** CA3: open a comparison with no library answer (the selection verb, the tutor's offer, the ask box). */
  const compareFrom = useCallback((request: CompareRequest, chips: ScopeChips | null = null,
                                   library: LibraryBookDto[] = []) => {
    if (!enabled || !scopeOn) return;
    for (const stage of JOB_STAGES) cancelStage(stage);
    const key = ++keyRef.current;
    const query = request.question ?? "";
    setState({
      key, request: { query, entry: "reader", extractionId: request.extractionId ?? null, spanIds: request.anchorSpanIds ?? [] },
      personalized: false, ask: IDLE, notes: IDLE, pinned: [], compare: IDLE, tutor: IDLE, practice: IDLE, peek: null,
      direct: request, chips: chips ?? { books: [], anchored: Boolean(request.anchorSpanIds?.length), topic: query || null,
        unmatched: null, judgmentId: null, words: null },
      library, previous: [],
    });
    void runCompare(key, { ...request, openSourceId: request.openSourceId ?? openSourceId });
  }, [enabled, scopeOn, cancelStage, runCompare, openSourceId]);

  /** CA3: the ask box (Ctrl+Shift+F; Ask on the library page): read the words for
   *  named books first, then compare at once, or answer as today's library ask. */
  const askBox = useCallback(async (request: LibraryAskRequest) => {
    if (!enabled) return;
    if (!scopeOn) {
      void run(request, settings?.personalizedDefault ?? true);
      return;
    }
    for (const stage of JOB_STAGES) cancelStage(stage);
    const key = ++keyRef.current;
    setState({
      key, request, personalized: settings?.personalizedDefault ?? true, ask: IDLE, notes: IDLE, pinned: [],
      compare: IDLE, tutor: IDLE, practice: IDLE, peek: null, scope: { phase: "pending", value: null, failure: null },
    });
    let reading: CompareScopeReadingDto | null = null;
    try {
      reading = await runJob("scope", () => api.readerCompareScope({ text: request.query, mode: "ask", extractionId: request.extractionId }));
      if (keyRef.current !== key || reading === null) return;
    } catch {
      if (keyRef.current !== key) return;
    }
    if (reading?.status === "read" && reading.intent === "compare") {
      const titles = new Map((reading.library ?? []).map((book) => [book.sourceId, book.title]));
      compareFrom({ door: "ask_box", question: reading.topic || request.query, extractionId: request.extractionId,
        sourceIds: reading.sourceIds }, {
        books: reading.sourceIds.map((sourceId) => ({ sourceId, title: titles.get(sourceId) ?? sourceId })),
        anchored: false, topic: reading.topic || request.query, unmatched: reading.unmatched,
        judgmentId: reading.judgmentId, askJudgmentId: reading.judgmentId, words: request.query,
      }, reading.library ?? []);
      return;
    }
    // A library question (or a reading that failed): today's sources-first answer;
    // when nothing could be read, comparing all the books is one press away.
    const missed = !reading || reading.status === "fallback" && reading.reason !== "too_few_books" && reading.reason !== "cold_attempt";
    void run(request, settings?.personalizedDefault ?? true, missed ? { compareAllWords: request.query } : {});
  }, [enabled, scopeOn, settings, cancelStage, runJob, run, compareFrom]);

  /** CA3: "compare all your books on …" after a reading that failed. */
  const compareAll = useCallback(() => {
    const current = stateRef.current;
    if (!current?.compareAllWords) return;
    compareFrom({ door: "ask_box", question: current.compareAllWords, extractionId: current.request.extractionId, sourceIds: [] }, {
      books: [], anchored: false, topic: current.compareAllWords, unmatched: null, judgmentId: null, words: current.compareAllWords,
    });
  }, [compareFrom]);

  /** CA3: a library answer's "compare these books": the answer's books, no pins. */
  const compareBooks = useCallback(() => {
    const current = stateRef.current;
    const ask = current?.ask.value;
    if (!current || !ask || !scopeOn) return;
    const seen = new Map<string, string>();
    for (const hit of ask.hits) if (hit.sourceId && !seen.has(hit.sourceId)) seen.set(hit.sourceId, hit.sourceTitle ?? hit.sourceId);
    const books = [...seen].map(([sourceId, title]) => ({ sourceId, title }));
    update(current.key, () => ({
      chips: { books, anchored: false, topic: ask.query, unmatched: null, judgmentId: null, words: null },
    }));
    void runCompare(current.key, { door: "library_answer", askId: ask.askId, sourceIds: books.map((book) => book.sourceId), openSourceId });
  }, [scopeOn, update, runCompare, openSourceId]);

  /** The comparison's own row (once its first table landed), else the library answer's. */
  const comparisonAskId = (current: LibraryAskState): string | null =>
    current.compare.value?.askId ?? [...(current.previous ?? [])].reverse().find((table) => table.askId)?.askId
      ?? current.ask.value?.askId ?? null;

  /** CA3: compare these books (the chips, or a refinement's change). An empty
   *  choice stops the comparison and keeps the picker: it never means "every
   *  book" (Codex review F2). */
  const compareChosen = useCallback((current: LibraryAskState, books: LibraryBookDto[],
                                     chips: Partial<ScopeChips> = {}, perspectives?: string[]) => {
    const key = current.key;
    const last = current.lastCompare ?? current.direct ?? null;
    if (books.length === 0) {
      cancelStage("compare");
      update(key, (s) => ({
        chips: s.chips ? { ...s.chips, ...chips, books: [], emptied: true } : s.chips,
        compare: IDLE, viewLimit: null,
        previous: s.compare.value ? [...(s.previous ?? []), s.compare.value] : s.previous ?? [],
        ...(s.tutorBasis === "comparison" ? { tutor: IDLE, tutorBasis: null } : {}),
      }));
      if (current.tutorBasis === "comparison") cancelStage("tutor");
      return;
    }
    update(key, (s) => ({ chips: s.chips ? { ...s.chips, ...chips, books, emptied: false } : s.chips }));
    const askId = comparisonAskId(current);
    const sourceIds = books.map((book) => book.sourceId);
    const requestedPerspectives = perspectives ?? last?.requestedPerspectives ?? [];
    if (askId) {
      void runCompare(key, { door: "refine", askId, sourceIds, openSourceId, requestedPerspectives,
        workbenchSessionId: last?.workbenchSessionId ?? null });
    } else if (current.direct) {
      // The first comparison has not landed (no row yet): start it again with these books.
      const base = stateRef.current?.chips ?? current.chips;
      compareFrom({ ...current.direct, sourceIds }, base ? { ...base, ...chips, books, emptied: false } : null);
    }
  }, [cancelStage, update, runCompare, compareFrom, openSourceId]);

  /** CA3: the chips changed (× or "+ add a book"): the same request re-runs with those books. */
  const setBooks = useCallback((books: LibraryBookDto[]) => {
    const current = stateRef.current;
    if (!current?.chips || !scopeOn) return;
    // The learner's change corrects the reading that set the books shown (F9).
    const judgmentId = current.chips.judgmentId;
    if (judgmentId) {
      void api.readerCompareScopeCorrection({ judgmentId, sourceIds: books.map((book) => book.sourceId) }).catch(() => undefined);
    }
    compareChosen(current, books);
  }, [scopeOn, compareChosen]);

  /** CA3: "change": the learner rewords the ask box (a learner correction of the reading). */
  const reword = useCallback((): string | null => {
    const current = stateRef.current;
    const chips = current?.chips;
    // Rewording corrects the ask box's reading of the words (F9), not a refinement's.
    const judgmentId = chips?.askJudgmentId ?? null;
    if (judgmentId) {
      void api.readerCompareScopeCorrection({ judgmentId, sourceIds: null }).catch(() => undefined);
    }
    return chips?.words ?? current?.request.query ?? null;
  }, []);

  /** CA3: the refine box (`/`): other books change the chips; a view becomes a requested perspective. */
  const refine = useCallback(async (words: string) => {
    const current = stateRef.current;
    const text = words.trim();
    if (!current?.chips || !scopeOn || !text) return;
    const key = current.key;
    const compared = current.chips.books.length ? current.chips.books
      : (current.compare.value?.rows ?? []).flatMap((row) => (row.sourceId ? [{ sourceId: row.sourceId, title: row.sourceTitle ?? row.sourceId }] : []));
    update(key, () => ({ refine: { phase: "pending", value: null, failure: null } }));
    let reading: CompareScopeReadingDto | null = null;
    try {
      reading = await runJob("scope", () => api.readerCompareScope({
        text, mode: "refine", extractionId: current.request.extractionId, currentSourceIds: compared.map((book) => book.sourceId) }));
      if (keyRef.current !== key || reading === null) return;
    } catch {
      if (keyRef.current !== key) return;
    }
    const now = stateRef.current?.key === key ? stateRef.current : null;
    const askId = now ? comparisonAskId(now) : null;
    if (now && reading?.status === "read" && reading.intent === "books" && reading.change && askId) {
      const titles = new Map([...(reading.library ?? []), ...compared].map((book) => [book.sourceId, book.title]));
      const named = reading.sourceIds;
      const ids = reading.change === "add" ? [...new Set([...compared.map((book) => book.sourceId), ...named])]
        : reading.change === "only" ? named : compared.map((book) => book.sourceId).filter((id) => !named.includes(id));
      const books = ids.map((sourceId) => ({ sourceId, title: titles.get(sourceId) ?? sourceId }));
      update(key, () => ({ refine: { phase: "landed", value: reading, failure: null } }));
      // The books now come from this reading: a later × corrects it, not the
      // ask box's (Codex review F9); "change" still rewords the ask box's.
      compareChosen(now, books, { unmatched: reading.unmatched ?? null,
        judgmentId: reading.judgmentId ?? now.chips?.judgmentId ?? null });
      return;
    }
    if (now && reading?.status === "read" && reading.intent === "views" && askId && keep?.perspectives) {
      const before = now.lastCompare?.requestedPerspectives ?? [];
      if (!before.includes(text) && before.length >= keep.maxPerspectives) {
        // Codex review F8 (§5.4): at the bound nothing is dropped unasked; the
        // learner chooses which view to remove for this one.
        update(key, () => ({ refine: IDLE, viewLimit: { pending: text, views: before } }));
        return;
      }
      const requested = [...before.filter((value) => value !== text), text];
      update(key, () => ({ refine: { phase: "landed", value: reading, failure: null } }));
      void runCompare(key, { door: "refine", askId, sourceIds: compared.map((book) => book.sourceId), openSourceId,
        requestedPerspectives: requested, workbenchSessionId: now.lastCompare?.workbenchSessionId ?? null });
      return;
    }
    update(key, () => ({ refine: { phase: "failed", value: reading, failure: SCOPE_COPY.refineMissed } }));
  }, [scopeOn, keep, update, runJob, runCompare, compareChosen, openSourceId]);

  /** Codex review F8: at the bound, the learner removes one view and the waiting one is added. */
  const replaceView = useCallback((remove: string) => {
    const current = stateRef.current;
    const limit = current?.viewLimit;
    const askId = current ? comparisonAskId(current) : null;
    if (!current?.chips || !limit || !askId || !limit.views.includes(remove)) return;
    const compared = shownCompared(current);
    void runCompare(current.key, { door: "refine", askId, sourceIds: compared, openSourceId,
      requestedPerspectives: [...limit.views.filter((view) => view !== remove), limit.pending],
      workbenchSessionId: current.lastCompare?.workbenchSessionId ?? null });
  }, [runCompare, openSourceId]);
  const keepViews = useCallback(() => {
    const current = stateRef.current;
    if (current?.viewLimit) update(current.key, () => ({ viewLimit: null }));
  }, [update]);

  /** The tutor over the pins, or (CA3, `about: "comparison"`) over the
   *  comparison shown: its passages, every block of an anchor (Codex review F4,
   *  F5), whatever is pinned. A comparison with no library answer asks about it.
   *  The comparison is named, never sent as keys: a stored one by its id
   *  (Codex re-review F10), one not stored by the passages the server kept
   *  for it (`passagesId`, Codex final verify F10). The server reads every
   *  passage it compared, however many, so none is cut to fit the request. */
  const askTutor = useCallback(async (question: string, about?: "pins" | "comparison") => {
    const current = stateRef.current;
    if (!current) return;
    const basis = about ?? (current.pinned.length || !current.direct ? "pins" : "comparison");
    const shown = basis === "comparison" ? current.compare.value : null;
    const comparisonId = shown?.comparisonId ?? null;
    const passagesId = comparisonId ? null : shown?.passagesId ?? null;
    const pins = basis !== "comparison" ? current.pinned : [];
    const askIdOf = basis === "comparison" ? shown?.askId ?? null : current.ask.value?.askId ?? null;
    if (!askIdOf || (pins.length === 0 && !comparisonId && !passagesId)) return;
    const key = current.key;
    update(key, () => ({ tutor: { phase: "pending", value: null, failure: null }, tutorBasis: basis }));
    const askId = askIdOf;
    const pinnedSpanKeys = pins;
    try {
      const answer = await runJob("tutor", () => api.readerLibraryAskTutor({
        askId, pinnedSpanKeys, ...(comparisonId ? { comparisonId } : passagesId ? { passagesId } : {}),
        question: question.trim() || null,
      }));
      if (answer === null) return;
      update(key, () => ({ tutor: { phase: "landed", value: answer, failure: null } }));
    } catch (error) {
      update(key, () => ({ tutor: { phase: phaseForError(error), value: null, failure: failureLine(error, "Couldn't write an answer.") } }));
    }
  }, [runJob, update]);

  /** "Practice this question": the same find_practice call as DL3's box (proposes only). */
  const practice = useCallback(async () => {
    const current = stateRef.current;
    // CA3: "practice this" on a comparison with no library answer: its question.
    const ask = current?.ask.value ?? (current?.direct ? {
      query: current.compare.value?.scope?.question ?? current.request.query, learningObjectIds: [] as string[],
      extractionId: current.request.extractionId } : null);
    if (!current || !ask) return;
    const key = current.key;
    update(key, () => ({ practice: { phase: "pending", value: null, failure: null } }));
    try {
      const result = await api.findPractice({
        query: ask.query, learningObjectIds: ask.learningObjectIds, facetIds: [], excludeItemIds: [],
        intent: "practice", caller: { kind: "reader", ref: ask.extractionId },
      });
      update(key, () => ({ practice: { phase: "landed", value: result, failure: null } }));
      if (result.proposalId && result.items.length > 0) {
        // The proposals the learner now sees (the sources spec's impressions).
        void api.recordProposalImpressions({
          proposalId: result.proposalId, surface: "reader",
          keys: result.items.map((item) => ({ kind: "item" as const, practiceItemId: item.practiceItemId })),
        }).catch(() => undefined);
      }
    } catch (error) {
      update(key, () => ({ practice: { phase: phaseForError(error), value: null, failure: "Couldn't look for practice." } }));
    }
  }, [update]);

  /** Peek: the passage with its neighbours, in the pane (Esc closes it). */
  const peek = useCallback(async (hitKey: string) => {
    const current = stateRef.current;
    const hit = current?.ask.value?.hits.find((h) => h.key === hitKey);
    if (!current || !hit) return;
    const key = current.key;
    update(key, () => ({ peek: { key: hitKey, phase: "pending", view: null } }));
    try {
      const { spanView } = await api.getSpanView({ extractionId: hit.extractionId, spanId: hit.spanId, context: "library" });
      update(key, (s) => (s.peek?.key === hitKey ? { peek: { key: hitKey, phase: "landed", view: spanView } } : {}));
    } catch (error) {
      onError(errorMessage(error));
      update(key, (s) => (s.peek?.key === hitKey ? { peek: null } : {}));
    }
  }, [onError, update]);

  const closePeek = useCallback(() => {
    const current = stateRef.current;
    if (current?.peek) update(current.key, () => ({ peek: null }));
  }, [update]);

  /** Leave the comparing posture: its jobs are cancelled and a late result can't reopen it. */
  const close = useCallback(() => {
    for (const stage of JOB_STAGES) cancelStage(stage);
    keyRef.current += 1;
    setState(null);
  }, [cancelStage]);

  // Leaving the Reader: every job still running is cancelled and no longer
  // read, and a job that starts afterwards is cancelled unread (re-review F13).
  useEffect(() => () => {
    for (const stage of JOB_STAGES) cancelStage(stage);
    keyRef.current += 1;
  }, [cancelStage]);

  // Switched off while open (a contract reload): nothing stays.
  useEffect(() => {
    if (!enabled) {
      for (const stage of JOB_STAGES) cancelStage(stage);
      keyRef.current += 1;
      setState(null);
    }
  }, [enabled, cancelStage]);

  /** CA3: run the last comparison request again (a retry after a failure). */
  const retryCompare = useCallback(() => {
    const current = stateRef.current;
    const last = current?.lastCompare;
    if (current && last) void runCompare(current.key, last);
  }, [runCompare]);

  return {
    enabled, settings, keep, state, open: state !== null, ask, retry, setPersonalized, retryNotes, togglePin, canCompare,
    compare, askTutor, practice, peek, closePeek, close, cancelNotes, cancelCompare, cancelTutor,
    // CA3 (absent in effect while scopeOn is false: each returns without a call).
    scopeOn, askBox, compareFrom, compareBooks, compareAll, setBooks, reword, refine, retryCompare,
    replaceView, keepViews,
  };
}

export type LibraryAskController = ReturnType<typeof useLibraryAsk>;
