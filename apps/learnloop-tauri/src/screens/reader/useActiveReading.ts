// Active reading on a selection (reader workbench RW1b; spec §4.2; UX §4.3, S5).
//
// "Let me try the next step": the book's following blocks fold at once under a
// dotted rule (before the question is written), with "show" one press away;
// the question is written in the background by the quick-check producer; the
// learner writes their attempt (or presses "show me"), sees the book's step
// beside it, the fold opens, and they self-check: matches · partly · no.
// "Why does this step work?" and "What does this assume?" take the same shape
// without a fold; the expected answer is the book's words when the book says
// it, else LearnLoop's model's, labelled so. "Reconstruct this later" turns the
// derivation into a later practice item (undoable). "Another way to see this"
// asks the sources service for a different treatment, the open passage left
// out. None of it is ever an attempt; a missed answer is kept for learner-text
// gaps by the sidecar.
import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "../../api/client";
import type { InquirySelfCheck, ReaderActiveQuestionDto, ReaderActiveStyle } from "../../api/dto";
import { errorMessage, getCommandError } from "../../errors";
import { phaseForError, type ModelActionPhase } from "./ModelActionState";

/** How often a question being written is read back (a cheap local read). */
const POLL_MS = 2000;

export interface AnotherWayHit {
  extractionId: string;
  spanId: string;
  sourceId: string | null;
  sourceTitle: string | null;
  text: string;
  role: string | null;
  rationale: string | null;
}

export interface ActiveReadingState {
  key: number;
  style: ReaderActiveStyle;
  extractionId: string;
  anchorSpanIds: string[];
  foldedSpanIds: string[];
  foldOpen: boolean;
  batchId: string | null;
  question: ReaderActiveQuestionDto | null;
  phase: ModelActionPhase;
  failure: string | null;
  busy: boolean;
  reconstruct: { phase: "idle" | "pending" | "done" | "undone" | "failed"; message: string | null };
}

export interface AnotherWayState {
  key: number;
  phase: ModelActionPhase;
  hits: AnotherWayHit[];
  failure: string | null;
  quote: string;
}

const NO_RECONSTRUCT = { phase: "idle" as const, message: null };

function failureLine(code: string | null | undefined, message: string | null | undefined): string {
  if (code === "exam_material") return message ?? "This passage is held out of LearnLoop's models.";
  if (code === "no_next_step" || code === "no_passage") return message ?? "There is no next step to try here.";
  return "Couldn't write the question.";
}

export function useActiveReading({
  extractionId,
  sourceId,
  onError,
  onOpenRail,
}: {
  extractionId: string | null;
  sourceId: string | null;
  onError: (message: string) => void;
  /** The learner chose an active-reading action: show its card (their act). */
  onOpenRail: () => void;
}) {
  const [active, setActive] = useState<ActiveReadingState | null>(null);
  const [another, setAnother] = useState<AnotherWayState | null>(null);
  const keyRef = useRef(0);
  const activeRef = useRef<ActiveReadingState | null>(null);
  activeRef.current = active;

  const update = useCallback((key: number, patch: Partial<ActiveReadingState>) => {
    setActive((current) => (current && current.key === key ? { ...current, ...patch } : current));
  }, []);

  const commitReconstruct = useCallback(async (key: number, question: ReaderActiveQuestionDto) => {
    if (question.reconstruct?.disposition && question.reconstruct.disposition !== "stopped") {
      update(key, { reconstruct: { phase: "done", message: null } });
      return;
    }
    update(key, { reconstruct: { phase: "pending", message: null } });
    try {
      const made = await api.readerReconstruct({ questionId: question.id, learningObjectId: question.escalationLearningObjectId });
      update(key, { question: made.question, reconstruct: { phase: "done", message: null } });
    } catch (error) {
      const code = getCommandError(error)?.code;
      update(key, {
        reconstruct: {
          phase: "failed",
          message: code === "no_learning_object"
            ? "This passage isn't linked to a learning objective yet, so it can't become practice."
            : errorMessage(error),
        },
      });
    }
  }, [update]);

  const landed = useCallback((key: number, question: ReaderActiveQuestionDto) => {
    update(key, { question, phase: "landed", failure: null });
    if (question.questionStyle === "reconstruct") void commitReconstruct(key, question);
  }, [update, commitReconstruct]);

  /** Start one style on the selection; the fold (next step) shows at once. */
  const start = useCallback(async (style: ReaderActiveStyle, spanIds: string[], localFold: string[]) => {
    if (!extractionId || spanIds.length === 0) return;
    const key = ++keyRef.current;
    setAnother(null);
    setActive({
      key, style, extractionId, anchorSpanIds: spanIds, foldedSpanIds: style === "next_step" ? localFold : [],
      foldOpen: false, batchId: null, question: null, phase: "pending", failure: null, busy: false,
      reconstruct: NO_RECONSTRUCT,
    });
    onOpenRail();
    try {
      const asked = await api.readerActiveQuestion({ extractionId, spanIds, style });
      if (keyRef.current !== key) return;
      update(key, { anchorSpanIds: asked.anchorSpanIds, foldedSpanIds: asked.foldedSpanIds, batchId: asked.batchId });
      if (asked.question) landed(key, asked.question);
      else if (asked.status === "provider_unavailable") update(key, { phase: "unreachable", failure: asked.message });
      else if (asked.status === "no_next_step") update(key, { phase: "failed", failure: asked.message, foldOpen: true });
    } catch (error) {
      if (keyRef.current !== key) return;
      const code = getCommandError(error)?.code;
      update(key, { phase: phaseForError(error), failure: failureLine(code, errorMessage(error)), foldOpen: true });
    }
  }, [extractionId, onOpenRail, update, landed]);

  // The question being written is read back until it lands or its job ends.
  const [tick, setTick] = useState(0);
  const pendingKey = active && active.phase === "pending" && active.batchId ? active.key : null;
  useEffect(() => {
    const current = activeRef.current;
    if (pendingKey === null || !current || !current.batchId) return;
    const { key, style, anchorSpanIds, batchId } = current;
    const timer = window.setTimeout(async () => {
      try {
        const read = await api.readerActiveQuestionStatus({ extractionId: current.extractionId, anchorSpanIds, style, batchId });
        if (keyRef.current !== key) return;
        if (read.question) {
          landed(key, read.question);
          return;
        }
        if (read.job && (read.job.status === "failed" || read.job.status === "cancelled")) {
          const code = read.job.errorCode ?? null;
          update(key, {
            phase: code === "capped" ? "capped" : code === "provider_unavailable" ? "unreachable" : "failed",
            failure: failureLine(code, read.job.message),
          });
          return;
        }
      } catch {
        /* the next read tries again */
      }
      if (keyRef.current === key) setTick((value) => value + 1);
    }, POLL_MS);
    return () => window.clearTimeout(timer);
  }, [pendingKey, tick, landed, update]);

  const act = useCallback(async (input: { action: "answered" | "self_checked" | "dismissed"; response?: string | null; selfCheck?: InquirySelfCheck }) => {
    const current = activeRef.current;
    if (!current?.question) return;
    const key = current.key;
    update(key, { busy: true });
    try {
      const result = await api.readerActiveQuestionAction({ questionId: current.question.id, ...input });
      if (keyRef.current !== key) return;
      update(key, {
        question: result.question, busy: false,
        // The book's step is shown beside the answer, and the fold opens.
        foldOpen: input.action === "answered" || input.action === "dismissed" ? true : current.foldOpen,
      });
      if (input.action === "dismissed") setActive(null);
    } catch (error) {
      update(key, { busy: false });
      onError(errorMessage(error));
    }
  }, [update, onError]);

  const answer = useCallback((response: string) => act({ action: "answered", response }), [act]);
  const showMe = useCallback(() => act({ action: "answered", response: null }), [act]);
  const selfCheck = useCallback((value: InquirySelfCheck) => act({ action: "self_checked", selfCheck: value }), [act]);
  const dismiss = useCallback(() => {
    if (activeRef.current?.question) void act({ action: "dismissed" });
    else setActive(null);
  }, [act]);
  const unfold = useCallback(() => {
    const current = activeRef.current;
    if (current) update(current.key, { foldOpen: true });
  }, [update]);
  const close = useCallback(() => {
    keyRef.current += 1;
    setActive(null);
  }, []);
  const retry = useCallback(() => {
    const current = activeRef.current;
    if (current) void start(current.style, current.anchorSpanIds, current.foldedSpanIds);
  }, [start]);

  const undoReconstruct = useCallback(async () => {
    const current = activeRef.current;
    if (!current?.question) return;
    const key = current.key;
    try {
      const undone = await api.readerReconstructUndo({ questionId: current.question.id });
      update(key, { question: undone.question ?? current.question, reconstruct: { phase: "undone", message: null } });
    } catch (error) {
      onError(errorMessage(error));
    }
  }, [update, onError]);

  /** "Another way to see this": the sources service's alternative intent, the open passage left out. */
  const anotherWay = useCallback(async (quote: string, spanIds: string[]) => {
    if (!extractionId || spanIds.length === 0) return;
    const key = ++keyRef.current;
    setActive(null);
    setAnother({ key, phase: "pending", hits: [], failure: null, quote });
    onOpenRail();
    try {
      const found = await api.findSources({
        query: quote, intent: "alternative", limit: 2, caller: { kind: "reader", ref: extractionId },
        excludeSpanKeys: spanIds.map((spanId) => `${extractionId}:${spanId}`),
      });
      if (keyRef.current !== key) return;
      const hits = ((found.hits as Array<Record<string, unknown>> | undefined) ?? []).slice(0, 2).map((hit) => ({
        extractionId: String(hit.extractionId ?? ""), spanId: String(hit.spanId ?? ""),
        sourceId: (hit.sourceId as string | null) ?? null, sourceTitle: (hit.sourceTitle as string | null) ?? null,
        text: String(hit.text ?? ""), role: (hit.role as string | null) ?? null, rationale: (hit.rationale as string | null) ?? null,
      }));
      setAnother({ key, phase: "landed", hits, failure: null, quote });
    } catch (error) {
      if (keyRef.current !== key) return;
      setAnother({ key, phase: phaseForError(error), hits: [], failure: "Couldn't look in your books.", quote });
    }
  }, [extractionId, onOpenRail]);

  // Another book: nothing carries over.
  useEffect(() => {
    keyRef.current += 1;
    setActive(null);
    setAnother(null);
  }, [extractionId]);

  const folded = new Set(active && !active.foldOpen ? active.foldedSpanIds : []);
  return {
    active, another, folded, start, answer, showMe, selfCheck, dismiss, unfold, close, retry, undoReconstruct,
    anotherWay, closeAnother: () => setAnother(null), sourceId,
  };
}

export type ActiveReadingController = ReturnType<typeof useActiveReading>;
