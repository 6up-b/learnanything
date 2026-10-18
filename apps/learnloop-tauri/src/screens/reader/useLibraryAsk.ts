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
import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "../../api/client";
import type {
  CompareTableDto,
  FindPracticeResultDto,
  LibraryAskDto,
  LibraryAskEntry,
  LibraryNotesDto,
  LibraryTutorDto,
  ReaderPromptContractDto,
  SpanViewDto,
} from "../../api/dto";
import { errorMessage } from "../../errors";
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
}

const IDLE = { phase: "idle" as ModelActionPhase, value: null, failure: null };

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
  const [state, setState] = useState<LibraryAskState | null>(null);
  const keyRef = useRef(0);
  const stateRef = useRef<LibraryAskState | null>(null);
  stateRef.current = state;

  const update = useCallback((key: number, patch: (current: LibraryAskState) => Partial<LibraryAskState>) => {
    setState((current) => (current && current.key === key ? { ...current, ...patch(current) } : current));
  }, []);

  const loadNotes = useCallback(async (key: number, askId: string) => {
    update(key, () => ({ notes: { phase: "pending", value: null, failure: null } }));
    try {
      const notes = await api.readerLibraryAskNotes({ askId });
      update(key, () => ({ notes: { phase: notesPhase(notes.status), value: notes, failure: null } }));
    } catch (error) {
      update(key, () => ({ notes: { phase: phaseForError(error), value: null, failure: "Couldn't write the notes." } }));
    }
  }, [update]);

  const run = useCallback(async (request: LibraryAskRequest, personalized: boolean) => {
    if (!enabled) return;
    const key = ++keyRef.current;
    setState({
      key, request, personalized, ask: { phase: "pending", value: null, failure: null }, notes: IDLE, pinned: [],
      compare: IDLE, tutor: IDLE, practice: IDLE, peek: null,
    });
    try {
      const ask = await api.readerLibraryAsk({
        query: request.query, entry: request.entry, extractionId: request.extractionId,
        spanIds: request.spanIds, personalized,
      });
      if (keyRef.current !== key) return;
      update(key, () => ({ ask: { phase: "landed", value: ask, failure: null } }));
      if (ask.hits.length > 0) void loadNotes(key, ask.askId);
    } catch (error) {
      if (keyRef.current !== key) return;
      update(key, () => ({ ask: { phase: phaseForError(error), value: null, failure: "Couldn't look in your books." } }));
    }
  }, [enabled, loadNotes, update]);

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

  const compare = useCallback(async () => {
    const current = stateRef.current;
    if (!current?.ask.value || !settings?.compare) return;
    const key = current.key;
    update(key, () => ({ compare: { phase: "pending", value: null, failure: null } }));
    try {
      const table = await api.readerLibraryCompare({
        askId: current.ask.value.askId, pinnedSpanKeys: current.pinned, openSourceId,
      });
      const phase = comparePhase(table.status);
      update(key, () => ({ compare: { phase, value: table, failure: phase === "failed" ? "Couldn't compare these passages." : null } }));
    } catch (error) {
      update(key, () => ({ compare: { phase: phaseForError(error), value: null, failure: "Couldn't compare these passages." } }));
    }
  }, [settings, openSourceId, update]);

  const askTutor = useCallback(async (question: string) => {
    const current = stateRef.current;
    if (!current?.ask.value || current.pinned.length === 0) return;
    const key = current.key;
    update(key, () => ({ tutor: { phase: "pending", value: null, failure: null } }));
    try {
      const answer = await api.readerLibraryAskTutor({
        askId: current.ask.value.askId, pinnedSpanKeys: current.pinned, question: question.trim() || null,
      });
      update(key, () => ({ tutor: { phase: "landed", value: answer, failure: null } }));
    } catch (error) {
      update(key, () => ({ tutor: { phase: phaseForError(error), value: null, failure: "Couldn't write an answer." } }));
    }
  }, [update]);

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

  /** Leave the comparing posture: a late result can't reopen it. */
  const close = useCallback(() => {
    keyRef.current += 1;
    setState(null);
  }, []);

  // Switched off while open (a contract reload): nothing stays.
  useEffect(() => {
    if (!enabled) {
      keyRef.current += 1;
      setState(null);
    }
  }, [enabled]);

  return {
    enabled, settings, state, open: state !== null, ask, retry, setPersonalized, retryNotes, togglePin, canCompare,
    compare, askTutor, practice, peek, closePeek, close,
  };
}

export type LibraryAskController = ReturnType<typeof useLibraryAsk>;
