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
import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "../../api/client";
import type {
  CompareTableDto,
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

type JobStage = "ask" | "notes" | "compare" | "tutor";
const JOB_STAGES: JobStage[] = ["ask", "notes", "compare", "tutor"];
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

/** What the learner asked for: a library answer, or (CA5a) a comparison of
 *  these pins, which a retry or the personalization chip runs again (Codex
 *  review F5: never the ordinary answer and its notes in its place). */
export type LibraryAskIntent = { kind: "ask" } | { kind: "compare"; pins: string[] };

export interface LibraryAskState {
  key: number;
  request: LibraryAskRequest;
  intent: LibraryAskIntent;
  personalized: boolean;
  ask: Stage<LibraryAskDto>;
  notes: Stage<LibraryNotesDto>;
  pinned: string[];
  compare: Stage<CompareTableDto>;
  tutor: Stage<LibraryTutorDto>;
  practice: Stage<FindPracticeResultDto>;
  peek: { key: string; phase: ModelActionPhase; view: SpanViewDto | null } | null;
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
  const epochsRef = useRef<Record<JobStage, number>>({ ask: 0, notes: 0, compare: 0, tutor: 0 });

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

  // Defined below (it needs runJob and update); run reaches it through this ref.
  const runCompareRef = useRef<(key: number, askId: string, pins: string[]) => Promise<void>>(async () => undefined);

  const run = useCallback(async (request: LibraryAskRequest, personalized: boolean, intent: LibraryAskIntent = { kind: "ask" }) => {
    if (!enabled) return;
    if (intent.kind === "compare" && (!settings?.compare || intent.pins.length < 2)) return;
    for (const stage of JOB_STAGES) cancelStage(stage);
    const key = ++keyRef.current;
    const comparing = intent.kind === "compare";
    setState({
      key, request, intent, personalized, ask: { phase: "pending", value: null, failure: null },
      // A comparison's notes wait to be asked for ("write the notes").
      notes: comparing ? CANCELLED : IDLE, pinned: comparing ? [...intent.pins] : [],
      compare: IDLE, tutor: IDLE, practice: IDLE, peek: null,
    });
    try {
      const ask = await runJob("ask", () => api.readerLibraryAsk({
        query: request.query, entry: request.entry, extractionId: request.extractionId,
        spanIds: request.spanIds, personalized,
      }));
      if (keyRef.current !== key || ask === null) return;
      update(key, () => ({ ask: { phase: "landed", value: ask, failure: null } }));
      if (comparing) await runCompareRef.current(key, ask.askId, intent.pins);
      else if (ask.hits.length > 0) void loadNotes(key, ask.askId);
    } catch (error) {
      if (keyRef.current !== key) return;
      update(key, () => ({ ask: { phase: phaseForError(error), value: null, failure: failureLine(error, "Couldn't look in your books.") } }));
    }
  }, [enabled, settings, cancelStage, loadNotes, runJob, update]);

  /** Ask (the learner's act). The personalized chip starts at the vault's default. */
  const ask = useCallback((request: LibraryAskRequest) => {
    void run(request, settings?.personalizedDefault ?? true);
  }, [run, settings]);

  /** Run the same operation again: a comparison stays a comparison of the same pins. */
  const retry = useCallback(() => {
    const current = stateRef.current;
    if (current) void run(current.request, current.personalized, current.intent);
  }, [run]);

  /** The chip: asking again with personalization on or off (a new ask, the same intent). */
  const setPersonalized = useCallback((on: boolean) => {
    const current = stateRef.current;
    if (current && current.personalized !== on) void run(current.request, on, current.intent);
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

  const runCompare = useCallback(async (key: number, askId: string, pinnedSpanKeys: string[], perspectives: string[] = []) => {
    update(key, () => ({ compare: { phase: "pending", value: null, failure: null } }));
    const requested = keep?.perspectives ? perspectives.slice(0, keep.maxPerspectives) : [];
    try {
      const table = await runJob("compare", () => api.readerLibraryCompare(
        requested.length ? { askId, pinnedSpanKeys, openSourceId, requestedPerspectives: requested } : { askId, pinnedSpanKeys, openSourceId }));
      if (table === null) return;
      const phase = comparePhase(table.status);
      update(key, () => ({ compare: { phase, value: table, failure: phase === "failed" ? "Couldn't compare these passages." : null } }));
    } catch (error) {
      update(key, () => ({ compare: { phase: phaseForError(error), value: null, failure: failureLine(error, "Couldn't compare these passages.") } }));
    }
  }, [keep, openSourceId, runJob, update]);
  runCompareRef.current = runCompare;

  /** Compare the pins; RW4d's requested perspectives go along only when given (and only while keep is on). */
  const compare = useCallback(async (perspectives: string[] = []) => {
    const current = stateRef.current;
    if (!current?.ask.value || !settings?.compare) return;
    await runCompare(current.key, current.ask.value.askId, current.pinned, perspectives);
  }, [settings, runCompare]);

  /** Reader CA5a: compare two sections' passages through this same path. The
   *  ask is anchored on the open section (its title is the question), both
   *  passages are pinned, and the comparison runs once the ask lands. The
   *  organizer's notes wait to be asked for ("write the notes"): the learner
   *  asked to compare, so no other model call is made for them. */
  const compareWith = useCallback(async (request: LibraryAskRequest, pins: string[]) => {
    await run(request, settings?.personalizedDefault ?? true, { kind: "compare", pins });
  }, [run, settings]);

  const askTutor = useCallback(async (question: string) => {
    const current = stateRef.current;
    if (!current?.ask.value || current.pinned.length === 0) return;
    const key = current.key;
    update(key, () => ({ tutor: { phase: "pending", value: null, failure: null } }));
    const askId = current.ask.value.askId;
    const pinnedSpanKeys = current.pinned;
    try {
      const answer = await runJob("tutor", () => api.readerLibraryAskTutor({
        askId, pinnedSpanKeys, question: question.trim() || null,
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
    if (!current?.ask.value) return;
    const key = current.key;
    const ask = current.ask.value;
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

  return {
    enabled, settings, keep, state, open: state !== null, ask, retry, setPersonalized, retryNotes, togglePin, canCompare,
    compare, compareWith, askTutor, practice, peek, closePeek, close, cancelNotes, cancelCompare, cancelTutor,
  };
}

export type LibraryAskController = ReturnType<typeof useLibraryAsk>;
