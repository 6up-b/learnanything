import { getCurrentWindow } from "@tauri-apps/api/window";
import { useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState } from "react";
import { api } from "../api/client";
import type {
  AttemptResultDto,
  AttemptType,
  CandidateErrorTypeDto,
  GuidedRedoDto,
  PracticeItemDetail,
  ProbeBlockEndDto,
  ProbeContractDto,
  RubricCriterionDto,
  SelfGradeErrorAttributionDto,
  SelfGradeInputDto,
  SessionSnapshot,
  TeachBackStateDto,
  TeachBackTurnDto
} from "../api/dto";
import { Card, EntityLink, KeyBar, Pill, SectionHeader } from "../components/ui";
import { CardControls } from "../components/CardControls";
import { ItemPresentation } from "../components/ItemPresentation";
import { BlockBar, COLOR, Faint, FONT_MONO, modePillColor, TermSelect } from "../components/term";
import { masteryTone } from "../app/algoConfig";
import { isTypingTarget } from "../app/keyboard";
import { MarkdownMath } from "../render/MarkdownMath";
import { MathLiveEditor } from "../render/MathLiveEditor";
import { errorMessage, getCommandError } from "../errors";

type CommittedAttemptRecovery = {
  attemptId: string;
  attemptType: string | null;
  message: string;
};

type PracticeCheckpointIdentity = {
  practiceItemId: string;
  submissionId: string;
};

function committedAttemptRecovery(error: unknown): CommittedAttemptRecovery | null {
  const command = getCommandError(error);
  if (command?.code !== "submission_committed" || !command.details || typeof command.details !== "object") {
    return null;
  }
  const details = command.details as {
    attempt_id?: unknown;
    attemptId?: unknown;
    attempt_type?: unknown;
    attemptType?: unknown;
  };
  const attemptId = details.attempt_id ?? details.attemptId;
  if (typeof attemptId !== "string" || !attemptId.trim()) return null;
  const attemptType = details.attempt_type ?? details.attemptType;
  return {
    attemptId: attemptId.trim(),
    attemptType: typeof attemptType === "string" ? attemptType : null,
    message: command.message
  };
}

/** Runtime guard for the measurement contract. TypeScript only checks compile
 * time; a stale/malformed sidecar response must never silently enable hints or
 * ordinary submission during a diagnostic serve. */
function activeProbeContract(contract: ProbeContractDto): ProbeContractDto | null {
  if (
    !contract ||
    typeof contract !== "object" ||
    !Number.isInteger(contract.version) ||
    typeof contract.active !== "boolean"
  ) {
    throw new Error("The diagnostic safety contract was malformed. Retry before answering.");
  }
  if (!contract.active) return null;
  const restrictions = contract.restrictions;
  if (
    typeof contract.presentationId !== "string" ||
    !contract.presentationId.trim() ||
    contract.forcedAttemptType !== "diagnostic_probe" ||
    !restrictions ||
    restrictions.hintsDisabled !== true ||
    restrictions.askTutorDisabled !== true ||
    restrictions.workedExampleDisabled !== true ||
    restrictions.answerRevealDisabled !== true ||
    restrictions.feedbackDeferred !== true
  ) {
    throw new Error("The diagnostic safety contract was incomplete. Retry before answering.");
  }
  return contract;
}

export function PracticeScreen({
  session,
  practiceItemId,
  gradingReady,
  gradingProvider,
  restoredAnswer,
  restoredHints,
  restoredSubmissionId,
  restoredTeachBack,
  onFeedback,
  onBlockEnd,
  onContinueDiagnostic,
  onBack,
  onCheckpointCleared,
  onDraftSaved,
  onTeachBackActive,
  onAskAvailabilityChange,
  onInspect,
  onAsk,
  onError,
  primed = false,
  redo = null
}: {
  session: SessionSnapshot;
  practiceItemId: string;
  /** This item is a primed retry launched from the feedback source panel. */
  primed?: boolean;
  /** Fix 3 guided partial redo: the preserved learner work is rendered locked
   *  above the editor and the learner rewrites only the failed portion; the
   *  submit composes prefix + redo text as the primed answer. */
  redo?: GuidedRedoDto | null;
  gradingReady: boolean;
  gradingProvider: string;
  restoredAnswer?: string;
  restoredHints?: number;
  restoredSubmissionId?: string | null;
  restoredTeachBack?: TeachBackStateDto | null;
  onFeedback: (attemptId: string) => void;
  /** §5.7: a diagnostic block just closed — releasedFeedback covers every
   *  attempt in it, not just the one that closed it. */
  onBlockEnd: (blockEnd: ProbeBlockEndDto, learningObjectId: string, learningObjectTitle: string) => void;
  /** §5.7 continuity: jump straight to the next observation in an open
   *  episode with no visible queue round-trip. */
  onContinueDiagnostic: (practiceItemId: string) => void;
  onBack: () => void;
  onCheckpointCleared: (identity?: PracticeCheckpointIdentity) => void;
  /** Mirror of the last flushed draft, so App can restore it if this item is
   *  re-opened before the backend checkpoint is reloaded. */
  onDraftSaved: (draft: { practiceItemId: string; answerMd: string; hintsUsed: number; submissionId: string }) => void;
  onTeachBackActive: (active: boolean) => void;
  /** Gate App-level Ask commands while the probe contract is loading or active. */
  onAskAvailabilityChange: (allowed: boolean) => void;
  onInspect: (id: string) => void;
  onAsk: (target: {
    context: "practice";
    practiceItemId: string;
    sessionId: string;
    openedAtMs: number;
    proactiveOpen?: boolean;
  }) => void;
  onError: (message: string) => void;
}) {
  const [item, setItem] = useState<PracticeItemDetail | null>(null);
  const [answer, setAnswer] = useState(restoredAnswer ?? "");
  // Meas §3.A6: the optional one-line justification, when this serve elicits
  // one. Held apart from `answer` on purpose — it must never reach the draft
  // checkpoint, because a restored draft that silently contained a "[Why this
  // approach]" block would make the learner's line un-retractable.
  const [whyLine, setWhyLine] = useState("");
  const [hintsUsed, setHintsUsed] = useState(restoredHints ?? 0);
  const [submitting, setSubmitting] = useState(false);
  // Probe redesign §12: when the LO has an in-progress diagnostic episode, the
  // sidecar commits a presentation and this contract enforces measurement
  // conditions — forced diagnostic_probe, no hints, no ask-tutor, deferred
  // feedback, and a "stop diagnosing" escape into tutoring.
  const [probe, setProbe] = useState<ProbeContractDto | null>(null);
  const [probeLoadState, setProbeLoadState] = useState<"loading" | "ready" | "error">("loading");
  const [itemLoadError, setItemLoadError] = useState<string | null>(null);
  const [probeLoadError, setProbeLoadError] = useState<string | null>(null);
  const [loadRevision, setLoadRevision] = useState(0);
  const [committedRecovery, setCommittedRecovery] = useState<CommittedAttemptRecovery | null>(null);
  // §7.1: the learner's committed answer confidence (1–5) during a diagnostic
  // block. Logged-only — it never changes grading or scheduling.
  const [answerConfidence, setAnswerConfidence] = useState<number | null>(null);
  const [fallbackRequired, setFallbackRequired] = useState(!gradingReady);
  // The self-grade panel is only revealed once the learner clicks Submit (and
  // grading actually needs a self-grade), never while they are still answering.
  const [selfGradeVisible, setSelfGradeVisible] = useState(false);
  const [selfGrade, setSelfGrade] = useState<SelfGradeInputDto>({
    criterionPoints: {},
    confidence: 3,
    fatalErrors: [],
    notes: "",
    errorAttributions: []
  });
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const mountedRef = useRef(true);
  const submissionId = useRef(restoredSubmissionId?.trim() || crypto.randomUUID());
  const latestDraft = useRef({
    sessionId: session.sessionId,
    practiceItemId,
    answerMd: answer,
    hintsUsed,
    submissionId: submissionId.current
  });
  const suppressDraftFlush = useRef(false);
  const isTeachBack = item?.practiceMode === "teach_back";
  // Teach-back conversations own the checkpoint (the sidecar stores the
  // conversation envelope in current_answer); the plain draft flush must never
  // overwrite it. Start closed until item detail proves this is ordinary
  // practice; this also protects a new teach-back whose mode call is slow.
  const teachBackRef = useRef(true);
  // Report the mode upward: App's command-palette ask path must refuse to open
  // the tutor during a teach-back conversation. Until the item detail loads,
  // fall back to the restored checkpoint (a resumed conversation is already
  // teach-back). The cleanup resets the flag on unmount/item switch.
  const teachBackActive = item ? item.practiceMode === "teach_back" : Boolean(restoredTeachBack);
  useEffect(() => {
    onTeachBackActive(teachBackActive);
    return () => onTeachBackActive(false);
  }, [teachBackActive, onTeachBackActive]);
  // When this item was opened — the ask overlay reports secondsIntoAttempt
  // from it, and the submitted attempt reports `latencySeconds` from it.
  const openedAtMs = useRef(Date.now());
  // Wall-clock seconds from presentation to submission. Deliberately NOT
  // idle-adjusted: subtracting time the learner "wasn't really working" would be
  // a fabrication, and the metric that consumes this (B5's
  // `learner_minutes_to_cold_success`) is denominated in the learner's actual
  // elapsed experience. The whole backend path — `SubmitAttemptInput`, the
  // sidecar handler, `AttemptDraft`, the `latency_seconds` column — already
  // existed; only this client-side value was missing, so every attempt to date
  // recorded NULL and the metric was permanently uncomputable.
  const elapsedSeconds = () =>
    Math.max(0, Math.round((Date.now() - openedAtMs.current) / 1000));
  useEffect(() => {
    mountedRef.current = true;
    return () => { mountedRef.current = false; };
  }, []);
  useEffect(() => {
    openedAtMs.current = Date.now();
    submissionId.current = restoredSubmissionId?.trim() || crypto.randomUUID();
    setAnswerConfidence(null);
  }, [practiceItemId, restoredSubmissionId]);
  const openAsk = (options?: { proactiveOpen?: boolean }) =>
    onAsk({
      context: "practice",
      practiceItemId,
      sessionId: session.sessionId,
      openedAtMs: openedAtMs.current,
      ...options
    });
  // The editor grows with its content but is capped so the answer card never
  // pushes the Submit button (or anything below the editor) off-screen — once it
  // hits the cap it scrolls internally instead. The cap is "viewport below the
  // editor's top, minus whatever sits beneath it (counts, hints, panel, submit)
  // and the key bar". Those sibling heights don't depend on the editor height,
  // so there's no feedback loop.
  const editorSlotRef = useRef<HTMLDivElement>(null);
  const belowRef = useRef<HTMLDivElement>(null);
  const [editorMaxHeight, setEditorMaxHeight] = useState(0);

  const recomputeEditorMax = useCallback(() => {
    const slot = editorSlotRef.current;
    if (!slot) return;
    const top = slot.getBoundingClientRect().top;
    const below = belowRef.current?.offsetHeight ?? 0;
    const keybar = (document.querySelector(".keybar") as HTMLElement | null)?.offsetHeight ?? 36;
    const next = Math.max(140, Math.floor(window.innerHeight - top - below - keybar - 28));
    setEditorMaxHeight(next);
  }, []);

  useEffect(() => {
    latestDraft.current = {
      sessionId: session.sessionId,
      practiceItemId,
      answerMd: answer,
      hintsUsed,
      submissionId: submissionId.current
    };
    suppressDraftFlush.current = false;
  }, [answer, hintsUsed, practiceItemId, restoredSubmissionId, session.sessionId]);

  const flushDraft = useCallback(async () => {
    if (suppressDraftFlush.current || teachBackRef.current) return;
    await api.savePracticeDraft(latestDraft.current);
  }, []);

  useEffect(() => {
    setAnswer(restoredAnswer ?? "");
    setHintsUsed(restoredHints ?? 0);
    setFallbackRequired(!gradingReady);
    setSelfGradeVisible(false);
    setFieldErrors({});
    setSubmitting(false);
    setWhyLine("");
  }, [gradingReady, practiceItemId, restoredAnswer, restoredHints]);

  useEffect(() => {
    let cancelled = false;
    setItem(null);
    setItemLoadError(null);
    setProbe(null);
    setProbeLoadState("loading");
    setProbeLoadError(null);
    setCommittedRecovery(null);
    teachBackRef.current = true;

    const recoverOrLoad = async () => {
      const retryKey = restoredSubmissionId?.trim();
      if (retryKey) {
        try {
          const recovery = await api.recoverPracticeSubmission({
            sessionId: session.sessionId,
            practiceItemId,
            submissionId: retryKey
          });
          if (cancelled) return;
          if (recovery.status === "recovered" && recovery.result) {
            // The exact original payload carries deferred/block-end routing and
            // does not require the now-single-use item to still be active.
            suppressDraftFlush.current = true;
            const recoveredItem = await api.getPracticeItem(practiceItemId).catch(() => null);
            // The screen may have unmounted while the optional title lookup was
            // in flight. Never route a stale result; retain its retry key so the
            // still-current surface can recover it authoritatively.
            if (cancelled) return;
            const routed = await routeAfterAttempt(
              recovery.result,
              recoveredItem,
              () => cancelled,
            );
            if (!routed) return;
            // Route first, then acknowledge. If routing mounts a new item and
            // it saves before this call lands, the sidecar's atomic key compare
            // preserves that newer checkpoint instead of deleting by session.
            await acknowledgeCheckpoint(practiceItemId, retryKey);
            return;
          }
          if (recovery.status !== "pending" || recovery.result !== null) {
            throw new Error("The saved submission recovery response was malformed.");
          }
        } catch (error) {
          if (cancelled) return;
          const recovery = committedAttemptRecovery(error);
          if (recovery) setCommittedRecovery(recovery);
          else setItemLoadError(errorMessage(error, "Could not verify the saved submission before reopening practice."));
          return;
        }
      }

      // No committed result exists, so this really is an item serve. The
      // session id lets the sidecar decide (and bound) the §3.A6 elicitation.
      api.getPracticeItem(practiceItemId, session.sessionId)
        .then((detail) => {
          if (cancelled) return;
          teachBackRef.current = detail.practiceMode === "teach_back";
          setItem(detail);
          setSelfGrade((current) => ({
            ...current,
            criterionPoints: Object.fromEntries((detail.rubric?.criteria ?? []).map((criterion) => [criterion.id, 0])),
            errorAttributions: []
          }));
        })
        .catch((error) => {
          if (!cancelled) setItemLoadError(errorMessage(error, "Could not load this practice item."));
        });
      // Committing the presentation is the serve event (§5.1). Only a
      // successful `active:false` response means ordinary practice.
      api.getProbeContract(practiceItemId, session.sessionId)
        .then((contract) => {
          if (cancelled) return;
          setProbe(activeProbeContract(contract));
          setProbeLoadState("ready");
        })
        .catch((error) => {
          if (cancelled) return;
          setProbe(null);
          setProbeLoadError(errorMessage(error, "Could not verify whether this is a diagnostic item."));
          setProbeLoadState("error");
        });
    };
    void recoverOrLoad();
    return () => { cancelled = true; };
  }, [loadRevision, practiceItemId, restoredSubmissionId, session.sessionId]);

  useEffect(() => {
    const timer = setTimeout(() => {
      void flushDraft().catch((error) => onError(errorMessage(error, "Could not save the practice draft.")));
    }, 350);
    return () => clearTimeout(timer);
  }, [answer, flushDraft, hintsUsed, onError, practiceItemId, session.sessionId]);

  useEffect(() => {
    return () => {
      void flushDraft().catch((error) => onError(errorMessage(error, "Could not save the practice draft.")));
      // Reported only on unmount — reporting on every debounced flush would
      // loop the draft back through restoredAnswer while the user is typing.
      if (!suppressDraftFlush.current && !teachBackRef.current) {
        const { practiceItemId: id, answerMd, hintsUsed: hints, submissionId: retryKey } = latestDraft.current;
        onDraftSaved({ practiceItemId: id, answerMd, hintsUsed: hints, submissionId: retryKey });
      }
    };
  }, [flushDraft, onError, onDraftSaved]);

  useEffect(() => {
    const appWindow = getCurrentWindow();
    let unlisten: (() => void) | undefined;
    let closing = false;
    appWindow.onCloseRequested(async (event) => {
      if (closing) return;
      event.preventDefault();
      closing = true;
      try {
        await flushDraft();
      } catch (error) {
        onError(errorMessage(error, "Could not save the practice draft before closing."));
      } finally {
        await appWindow.destroy();
      }
    }).then((listener) => {
      unlisten = listener;
    }).catch((error) => onError(errorMessage(error, "Could not register the close handler.")));
    return () => unlisten?.();
  }, [flushDraft, onError]);

  const practiceReady = item !== null && probeLoadState === "ready";
  const probeActive = Boolean(probe?.active && probe.presentationId);
  const interactionReady = practiceReady && committedRecovery === null;

  useEffect(() => {
    onAskAvailabilityChange(interactionReady && !probeActive && !isTeachBack);
    return () => onAskAvailabilityChange(false);
  }, [interactionReady, isTeachBack, onAskAvailabilityChange, probeActive]);

  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      if (committedRecovery) {
        if (event.key.toLowerCase() === "r") {
          event.preventDefault();
          setLoadRevision((value) => value + 1);
        }
        return;
      }
      if (event.key === "Escape") {
        event.preventDefault();
        onBack();
        return;
      }
      // Until both the item and its diagnostic contract are verified, all
      // actions except leaving the screen remain closed.
      if (!interactionReady) return;
      const ctrl = event.ctrlKey || event.metaKey;
      if (ctrl && event.key === "Enter") {
        // Teach-back conversations handle ^enter themselves (send turn).
        if (!isTeachBack) {
          event.preventDefault();
          void submit();
        }
      } else if (ctrl && event.key.toLowerCase() === "h") {
        event.preventDefault();
        if (!isTeachBack) revealHint();
      } else if (ctrl && event.key.toLowerCase() === "d") {
        event.preventDefault();
        if (!isTeachBack) void dontKnow();
      } else if (ctrl && event.key.toLowerCase() === "s") {
        event.preventDefault();
        void skip();
      } else if (event.key === "?" && !ctrl && !isTypingTarget(event.target)) {
        event.preventDefault();
        if (isTeachBack) {
          // No hints in teach-back: the tutor could leak what the naive
          // student is probing for.
          onError("ask-tutor is disabled during a teach-back conversation.");
        } else if (probeActive) {
          // §5.5: Ask Tutor is disabled during a diagnostic block; the escape
          // hatch is the explicit stop-and-teach action, which ends measurement.
          onError("ask-tutor is disabled during a diagnostic check — use “stop diagnosing & teach me” instead.");
        } else {
          openAsk();
        }
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  });

  // Recompute the editor cap whenever the layout around it can shift: content
  // (which can rewrap the prompt), hint reveals, the self-grade panel, item
  // swaps, and window resizes. A ResizeObserver catches everything else.
  useLayoutEffect(() => {
    recomputeEditorMax();
  }, [answer, hintsUsed, fallbackRequired, selfGradeVisible, item, recomputeEditorMax]);

  useEffect(() => {
    const onResize = () => recomputeEditorMax();
    window.addEventListener("resize", onResize);
    const observer = new ResizeObserver(() => recomputeEditorMax());
    if (belowRef.current) observer.observe(belowRef.current);
    return () => {
      window.removeEventListener("resize", onResize);
      observer.disconnect();
    };
  }, [recomputeEditorMax]);

  const scorePreview = useMemo(() => {
    if (!item?.rubric) return 0;
    let score = Math.round(Object.values(selfGrade.criterionPoints).reduce((sum, value) => sum + Number(value || 0), 0));
    score = Math.max(0, Math.min(item.rubric.maxPoints, score));
    for (const fatalId of selfGrade.fatalErrors ?? []) {
      const fatal = item.rubric.fatalErrors.find((candidate) => candidate.id === fatalId);
      if (fatal) score = Math.min(score, fatal.maxGrade);
    }
    return score;
  }, [item, selfGrade]);

  function revealHint() {
    if (!practiceReady) return;
    if (probeActive) {
      // §5.5: authored hints are disabled during a diagnostic block.
      onError("hints are disabled during a diagnostic check — answer with what you know, or stop diagnosing.");
      return;
    }
    setHintsUsed((value) => Math.min(item?.hints.length ?? 0, value + 1));
  }

  async function stopDiagnosing() {
    if (!item) return;
    try {
      await api.stopProbeDiagnosing(item.id);
      setProbe(null);
      // §3: measurement ends and tutoring begins. The typed transition
      // decision is already persisted, so the tutor opens proactively.
      openAsk({ proactiveOpen: true });
    } catch (error) {
      onError(errorMessage(error, "Could not stop the diagnostic check."));
    }
  }

  async function routeAfterAttempt(
    result: AttemptResultDto,
    recoveredItem: PracticeItemDetail | null = item,
    cancelled: () => boolean = () => false,
  ): Promise<boolean> {
    if (cancelled()) return false;
    const learningObjectId = recoveredItem?.learningObjectId ?? result.learningObjectId;
    const learningObjectTitle = recoveredItem?.learningObjectTitle ?? result.learningObjectId;
    // §5.7: the block just closed — the unified review covers every attempt
    // in it (releasedFeedback), not just the one that closed it.
    if (result.probeBlockEnd) {
      onBlockEnd(result.probeBlockEnd, learningObjectId, learningObjectTitle);
      return true;
    }
    // §5.6: feedback stays deferred while the diagnostic block is still
    // measuring — stay inside the block by jumping straight to whatever the
    // episode serves next, instead of round-tripping through the queue.
    if (result.probeEpisode?.feedbackDeferred) {
      try {
        const next = await api.getNextProbeItem(learningObjectId);
        if (cancelled()) return false;
        if (next.active && next.practiceItemId) {
          onContinueDiagnostic(next.practiceItemId);
          return true;
        }
      } catch (error) {
        if (cancelled()) return false;
        onError(errorMessage(error, "Could not open the next diagnostic item."));
      }
      if (cancelled()) return false;
      onBack();
      return true;
    }
    if (cancelled()) return false;
    onFeedback(result.attemptId);
    return true;
  }

  async function submit() {
    if (!item || !interactionReady || submitting) return;
    const submittedItemId = item.id;
    const submittedKey = submissionId.current;
    // First Submit click when a self-grade is required only reveals the panel;
    // the actual attempt is submitted on the next click once it's been graded.
    if (fallbackRequired && !selfGradeVisible) {
      setSelfGradeVisible(true);
      return;
    }
    const validation = validateSelfGrade(item, selfGrade, fallbackRequired);
    setFieldErrors(validation);
    if (Object.keys(validation).length) return;
    setSubmitting(true);
    try {
      // The retry key must be durable before grading begins. If the app or
      // sidecar disappears after the attempt commits but before the response,
      // the restarted screen reuses this exact key and recovers the attempt.
      await flushDraft();
      if (!mountedRef.current) return;
      const result = await api.submitAttempt({
        sessionId: session.sessionId,
        practiceItemId: submittedItemId,
        // A guided redo submits the COMPOSED answer: the preserved (locked)
        // prefix plus the learner's rewritten portion, separated by a paragraph
        // break — mirroring repair_splice's end-append join. The grader sees
        // one whole answer; only the redo text was written now.
        answerMd: redo ? composeRedoAnswer(redo.learnerWorkPrefix, answer) : answer,
        // Meas §3.A6 rule 3 made structural, and made structural on the WIRE:
        // the volunteered line is its own field, and the sidecar joins it into
        // the single trace the grader reads. This client never learns the
        // heading that delimits it — that used to be a constant duplicated here
        // and in `trace_evidence.py`, kept equal by a comment, with the backend
        // parsing for it to score the reward and count the session budget. A
        // blank line is submitted as nothing at all; there is no representation
        // for "declined", so nothing can turn an empty field into a hint, a
        // skip, or a failure.
        explanationMd: whyLine.trim() || null,
        // §12: an active diagnostic block forces the recording attempt type.
        attemptType: probeActive ? "diagnostic_probe" : chooseAttemptType(item.attemptTypesAllowed, hintsUsed),
        hintsUsed,
        latencySeconds: elapsedSeconds(),
        primed,
        probePresentationId: probeActive ? probe?.presentationId : null,
        answerConfidence,
        assessmentContractVersionId: item.assessmentContractVersionId,
        submissionId: submittedKey,
        // Drop attributions for any criterion the learner ultimately left at full
        // credit, so a restored score never ships a stale error tag.
        selfGrade: fallbackRequired ? { ...selfGrade, errorAttributions: prunedAttributions(item, selfGrade) } : null
      });
      suppressDraftFlush.current = true;
      if (!mountedRef.current) return;
      const routed = await routeAfterAttempt(result, item, () => !mountedRef.current);
      if (routed) await acknowledgeCheckpoint(submittedItemId, submittedKey);
    } catch (error) {
      const recovery = committedAttemptRecovery(error);
      if (recovery) {
        // An attempt id does not carry the authoritative post-submit route. In
        // particular, a diagnostic may still defer feedback or may have closed
        // a block. Keep the checkpoint/key and fail closed rather than opening
        // feedback or advancing from incomplete information.
        setCommittedRecovery(recovery);
        return;
      }
      const command = getCommandError(error);
      if (command?.code === "grading_fallback_required") {
        setFallbackRequired(true);
        setSelfGradeVisible(true);
        onError(command.message);
      } else {
        onError(errorMessage(error, "Could not submit this attempt."));
      }
    } finally {
      setSubmitting(false);
    }
  }

  async function dontKnow() {
    if (!item || !interactionReady || submitting) return;
    const submittedItemId = item.id;
    const submittedKey = submissionId.current;
    setSubmitting(true);
    try {
      await flushDraft();
      if (!mountedRef.current) return;
      const result = await api.submitDontKnow({
        sessionId: session.sessionId,
        practiceItemId: submittedItemId,
        hintsUsed,
        latencySeconds: elapsedSeconds(),
        probePresentationId: probeActive ? probe?.presentationId : null,
        answerConfidence,
        assessmentContractVersionId: item.assessmentContractVersionId,
        submissionId: submittedKey
      });
      suppressDraftFlush.current = true;
      if (!mountedRef.current) return;
      const routed = await routeAfterAttempt(result, item, () => !mountedRef.current);
      if (routed) await acknowledgeCheckpoint(submittedItemId, submittedKey);
    } catch (error) {
      const recovery = committedAttemptRecovery(error);
      if (recovery) {
        setCommittedRecovery(recovery);
      } else {
        onError(errorMessage(error, "Could not record “I don't know”."));
      }
    } finally {
      setSubmitting(false);
    }
  }

  async function skip() {
    if (!item || !interactionReady) return;
    const skippedIdentity = { practiceItemId: item.id, submissionId: submissionId.current };
    try {
      await api.skipPracticeItem({ sessionId: session.sessionId, practiceItemId: item.id });
      if (!mountedRef.current) return;
      suppressDraftFlush.current = true;
      // skip_practice_item owns its checkpoint delete; only mirror that clear
      // locally when this is still the item/key App knows about.
      onCheckpointCleared(skippedIdentity);
      onBack();
    } catch (error) {
      onError(errorMessage(error, "Could not skip this practice item."));
    }
  }

  async function acknowledgeCheckpoint(practiceItemId: string, expectedSubmissionId: string): Promise<boolean> {
    try {
      const result = await api.acknowledgePracticeSubmission({
        sessionId: session.sessionId,
        practiceItemId,
        submissionId: expectedSubmissionId,
      });
      if (!result.acknowledged || result.status === "checkpoint_mismatch") return false;
      onCheckpointCleared({ practiceItemId, submissionId: expectedSubmissionId });
      return true;
    } catch (error) {
      onError(errorMessage(error, "Could not acknowledge the saved practice result."));
      return false;
    }
  }

  const loadError = itemLoadError ?? probeLoadError;
  if (committedRecovery) {
    const diagnostic = committedRecovery.attemptType === "diagnostic_probe" || probeActive;
    return (
      <div className="screen">
        <div className="screen-scroll">
          <SectionHeader>Attempt recorded · route recovery required</SectionHeader>
          <Card focused>
            <div style={{ color: COLOR.amber, lineHeight: 1.6 }}>
              Your answer was recorded once. LearnLoop kept its saved submission key and will not grade it again.
            </div>
            <div style={{ color: COLOR.textDim, lineHeight: 1.6, marginTop: 8 }}>
              {diagnostic
                ? "The diagnostic result did not include enough durable routing information to decide whether feedback is still deferred or the block ended. Feedback and block advancement remain locked."
                : "The full completion route could not be recovered, so LearnLoop has not opened feedback or advanced the session."}
            </div>
            <div style={{ color: COLOR.textFaint, fontFamily: FONT_MONO, fontSize: 11, marginTop: 8 }}>
              attempt {committedRecovery.attemptId} · {committedRecovery.message}
            </div>
            <div className="form-row" style={{ marginTop: 14 }}>
              <button
                className="queue-row focused"
                type="button"
                disabled={submitting}
                onClick={() => setLoadRevision((value) => value + 1)}
              >
                <span className="queue-title">{submitting ? "Recovering..." : "Retry safe recovery"}</span>
              </button>
            </div>
          </Card>
        </div>
        <KeyBar keys={[{ key: "r", label: "retry same saved submission" }]} />
      </div>
    );
  }

  if (loadError) {
    return (
      <div className="screen">
        <div className="screen-scroll">
          <SectionHeader>Practice item unavailable</SectionHeader>
          <Card focused>
            <div style={{ color: COLOR.red, lineHeight: 1.6 }}>{loadError}</div>
            <div className="form-row" style={{ marginTop: 14 }}>
              <button className="queue-row focused" type="button" onClick={() => setLoadRevision((value) => value + 1)}>
                <span className="queue-title">Retry loading</span>
              </button>
              <button className="queue-row" type="button" onClick={onBack}>
                <span className="queue-title">Back to Today</span>
              </button>
            </div>
          </Card>
        </div>
        <KeyBar keys={[{ key: "esc", label: "today" }]} />
      </div>
    );
  }

  if (!practiceReady || !item) {
    return (
      <div className="screen-scroll">
        <Card>{item ? "Verifying diagnostic safeguards..." : "Loading practice item..."}</Card>
      </div>
    );
  }

  return (
    <div className="screen">
      <div className="screen-scroll">
        <SectionHeader>Practice item</SectionHeader>
        <Card focused>
          <div className="queue-meta">
            <EntityLink id={item.id} onInspect={onInspect} />
            <EntityLink id={item.learningObjectId} onInspect={onInspect}>{item.learningObjectTitle}</EntityLink>
            <Pill tone={modePillColor(item.practiceMode)}>{item.practiceMode}</Pill>
            {item.subject ? <Pill tone="slate">{item.subject}</Pill> : null}
            {fallbackRequired ? <Pill tone="amber">self-grade required</Pill> : <Pill tone="green">{gradingProvider} grading</Pill>}
          </div>
          {probeActive ? (
            <div className="hint-banner" style={{ display: "flex", flexDirection: "column", gap: 8 }}>
              <div style={{ display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap" }}>
                <Pill tone="cyan">Diagnostic check</Pill>
                <BlockBar
                  value={(probe?.observationNumber ?? 1) - 1}
                  max={probe?.maximumObservations ?? 4}
                  width={probe?.maximumObservations ?? 4}
                  color={COLOR.cyan}
                />
                <span style={{ fontFamily: FONT_MONO, fontSize: 12, color: COLOR.amber }}>
                  question {probe?.observationNumber ?? 1} of up to {probe?.maximumObservations ?? 4}
                </span>
                <span style={{ fontSize: 12, opacity: 0.75 }}>
                  Answer with what you know — this helps find exactly where to focus next. Full
                  feedback arrives once this short check wraps up; hints and ask-tutor are paused
                  for now.
                </span>
              </div>
              <div style={{ display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap" }}>
                <button
                  type="button"
                  className="queue-row"
                  style={{ marginLeft: "auto" }}
                  onClick={() => void stopDiagnosing()}
                  title="end the diagnostic block and start tutoring"
                >
                  stop diagnosing &amp; teach me
                </button>
              </div>
            </div>
          ) : null}
          {/* 1f: a cold-lane follow-up (repair cold retry / certification cold
              probe) is one delayed unassisted measurement. apply_attempt hard-
              rejects it hinted or primed ("a cold retry must be unassisted and
              unprimed"), so say that HERE, next to where the hint key lives,
              before the learner voids it.

              The marker is deliberately PROVENANCE-FREE: naming the repair (or
              the factor) this check verifies would point the learner straight at
              the material the check exists to measure them retrieving unaided.
              What it verifies is said afterwards, in the feedback banner. */}
          {item.activeFollowupKind === "cold_retry" || item.activeFollowupKind === "certification_cold_probe" ? (
            <div className="hint-banner" style={{ borderColor: COLOR.amber }}>
              <Pill tone="amber">unassisted check</Pill>{" "}
              {primed
                ? "this question is due as an unassisted check, but it was opened primed — the attempt will be rejected. Go back and open it from the queue instead."
                : "hints will void this measurement and the attempt will be rejected. Answer with what you can retrieve on your own."}
            </div>
          ) : null}
          {item.mastery != null ? (
            <div className="queue-meta" style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 12 }}>
              <Faint style={{ fontSize: 10, letterSpacing: "0.1em", textTransform: "uppercase" }}>mastery estimate</Faint>
              <BlockBar value={item.mastery.mean} width={10} color={masteryTone(item.mastery.mean, COLOR)} />
              <span style={{ fontFamily: FONT_MONO, color: COLOR.text }}>{item.mastery.mean.toFixed(2)}</span>
              <Faint>±{Math.sqrt(item.mastery.variance).toFixed(2)}</Faint>
            </div>
          ) : null}
          {/* Meas §3.A2/§3.A3: the whole stimulus, not just the prompt. An
              error hunt's worked solution and a laddered-stem part's shared
              setup are as load-bearing as the question itself, and this is the
              renderer both practice and exams mount so a surface cannot carry
              one and forget the other. */}
          <ItemPresentation presentation={item.presentation} />
          {!probeActive ? (
            <CardControls
              key={`${item.id}:${item.prompt}`}
              practiceItemId={item.id}
              prompt={item.prompt}
              expectedAnswer={null}
              onError={onError}
              onChanged={() => {
                api.getPracticeItem(item.id, session.sessionId)
                  .then(setItem)
                  .catch((error) => onError(errorMessage(error, "The card changed, but its updated practice view could not be loaded.")));
              }}
              onRetired={() => {
                // Retirement already clears the durable checkpoint server-side.
                // Suppress the unmount flush so this screen cannot recreate a
                // draft pointing at the card that was just retired.
                suppressDraftFlush.current = true;
                onCheckpointCleared();
                onBack();
              }}
              onTeachBack={isTeachBack ? undefined : onContinueDiagnostic}
            />
          ) : null}
          {item.sourceRefs.length > 0 ? (
            <div style={{ marginTop: 6, fontSize: 11, color: COLOR.textFaint, lineHeight: 1.6 }}>
              {item.sourceRefs.map((ref, index) => (
                <div
                  key={`${ref.refId}:${index}`}
                  title={[ref.refId, ref.quote].filter(Boolean).join("\n\n")}
                  style={{ display: "flex", gap: 8, alignItems: "baseline" }}
                >
                  <span style={{ color: COLOR.textDim }}>{ref.displayName}</span>
                  <span style={{ fontFamily: FONT_MONO }}>
                    {ref.locator ?? ref.path ?? ref.refType}
                  </span>
                </div>
              ))}
            </div>
          ) : null}
          {isTeachBack ? (
            <TeachBackConversation
              key={item.id}
              session={session}
              item={item}
              restoredState={
                restoredTeachBack && restoredTeachBack.practiceItemId === item.id ? restoredTeachBack : null
              }
              onFeedback={onFeedback}
              onCheckpointCleared={onCheckpointCleared}
              markSubmitted={() => {
                suppressDraftFlush.current = true;
              }}
            />
          ) : (
          <>
          {redo ? (
            <div style={{ marginTop: 10 }}>
              <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" }}>
                <Pill tone="amber">guided redo</Pill>
                <span style={{ fontSize: 12, color: COLOR.textDim }}>
                  your correct work is kept below — rewrite only the part that went wrong
                </span>
              </div>
              {redo.redoInstruction ? (
                <div style={{ marginTop: 6, fontSize: 12, color: COLOR.text, lineHeight: 1.55 }}>
                  <Faint>what to fix:</Faint> {redo.redoInstruction}
                </div>
              ) : null}
              {redo.failedCheckpointIds.length > 0 ? (
                <div style={{ marginTop: 4, display: "flex", gap: 6, flexWrap: "wrap", alignItems: "center" }}>
                  <Faint style={{ fontSize: 11 }}>failed steps</Faint>
                  {redo.failedCheckpointIds.map((checkpointId) => (
                    <Pill key={checkpointId} tone="red">{checkpointId}</Pill>
                  ))}
                </div>
              ) : null}
              <div
                aria-label="your preserved work (read-only)"
                style={{
                  borderLeft: `3px solid ${COLOR.green}`,
                  background: "rgba(255,255,255,0.03)",
                  padding: "8px 12px",
                  marginTop: 8,
                  fontSize: 13,
                  lineHeight: 1.6,
                  opacity: 0.85
                }}
              >
                <Faint style={{ display: "block", fontSize: 10, letterSpacing: "0.1em", textTransform: "uppercase" }}>
                  your work so far — kept
                </Faint>
                <MarkdownMath value={redo.learnerWorkPrefix} />
              </div>
              {/* Cold-retry status for the bound episode — the same honesty
                  RepairScreen renders: only a scheduled independent cold retry
                  converts this repair to Demonstrated credit. */}
              {redo.episodeId ? (
                redo.coldItemId ? (
                  <div style={{ display: "flex", alignItems: "center", gap: 8, marginTop: 8, fontSize: 12, color: COLOR.textDim }}>
                    <Pill tone="green">cold retry scheduled</Pill>
                    <span>
                      an unassisted cold retry on a different question is scheduled for a later session
                      (tomorrow or later) — only that converts to Demonstrated credit
                    </span>
                  </div>
                ) : (
                  <div style={{ display: "flex", alignItems: "center", gap: 8, marginTop: 8, fontSize: 12, color: COLOR.textDim }}>
                    <Pill tone="red">not measurable</Pill>
                    <span>
                      {redo.coldUnmeasurableReason === "no_independent_surface"
                        ? "no independent question exists on this topic yet, so no unassisted cold retry can be scheduled — this repair cannot convert to Demonstrated credit until another surface is authored"
                        : redo.coldUnmeasurableReason === "case_unresolvable"
                        ? "the diagnosed cause behind this repair could no longer be resolved, so no unassisted cold retry can be scheduled — this redo counts as primed practice only"
                        : "no unassisted cold retry could be scheduled for this repair, so it cannot convert to Demonstrated credit"}
                    </span>
                  </div>
                )
              ) : null}
            </div>
          ) : null}
          <div className="answer-editor-slot" ref={editorSlotRef}>
            <MathLiveEditor
              value={answer}
              onChange={setAnswer}
              disabled={submitting}
              placeholder={redo ? "continue from your kept work — rewrite only the failed part" : "type your answer — $math$ renders as you type"}
              maxHeight={editorMaxHeight}
              ariaLabel={redo ? "redo the failed part" : "answer"}
            />
          </div>
          <div ref={belowRef}>
            <div className="queue-meta">{answer.length} chars · {answer.split(/\s+/).filter(Boolean).length} words</div>
            {/* §4.6 calibration duel — predicting the correctness of the answer
                they just composed (not the prompt). Shown only once the draft is
                non-empty; a 1–5 tap that is stored as-is (never mapped to a
                probability in the UI). Locked once Submit is pressed (pre-reveal),
                always skippable, never gates submission, absence is unscored — no
                nagging. Selection is marked by the focused class + a caret, not by
                color alone. */}
            {answer.trim() ? (
              <div
                role="group"
                aria-label="How likely is this answer to be correct? (optional, 1 unlikely to 5 certain)"
                style={{ display: "flex", alignItems: "center", gap: 6, marginTop: 8, fontSize: 11 }}
              >
                <Faint>How likely is this answer to be correct? (optional)</Faint>
                {[1, 2, 3, 4, 5].map((level) => {
                  const on = answerConfidence === level;
                  const locked = submitting || selfGradeVisible;
                  return (
                    <button
                      key={level}
                      type="button"
                      className={on ? "queue-row focused" : "queue-row"}
                      style={{ padding: "0 7px", fontFamily: FONT_MONO, opacity: on ? 1 : 0.55 }}
                      onClick={() => setAnswerConfidence(on ? null : level)}
                      disabled={locked}
                      aria-pressed={on}
                      aria-label={`answer confidence ${level} of 5`}
                    >
                      {on ? "▸" : ""}{level}
                    </button>
                  );
                })}
                {answerConfidence != null && !submitting && !selfGradeVisible ? (
                  <button
                    type="button"
                    className="queue-row"
                    style={{ padding: "0 7px", opacity: 0.55 }}
                    onClick={() => setAnswerConfidence(null)}
                    aria-label="clear answer confidence"
                  >
                    clear
                  </button>
                ) : null}
              </div>
            ) : null}
            {/* Meas §3.A6 elicitation — one line at a decision point, offered
                only where the answer underdetermines the reasoning, and only
                while the per-session budget lasts. It is a field, not a step:
                it never gates Submit, it is never validated, and a blank one
                is submitted as nothing at all (see withElicitedExplanation). */}
            {item.elicitation?.elicit && item.elicitation.prompt ? (
              <div style={{ marginTop: 10 }}>
                <label
                  htmlFor="elicitation-line"
                  style={{ display: "block", fontSize: 11, marginBottom: 4, color: COLOR.textDim }}
                >
                  {item.elicitation.prompt}{" "}
                  <Faint>· skipping this costs nothing</Faint>
                </label>
                <input
                  id="elicitation-line"
                  type="text"
                  className="text-input"
                  value={whyLine}
                  onChange={(event) => setWhyLine(event.target.value)}
                  disabled={submitting}
                  placeholder="one line — or leave it blank"
                  style={{ width: "100%", fontSize: 12 }}
                />
              </div>
            ) : null}
            {item.hints.slice(0, hintsUsed).map((hint, index) => (
              <div className="hint-banner" key={hint}>
                <Pill tone="amber">hint {index + 1}/{item.hints.length}</Pill> {hint}
              </div>
            ))}
            {submitting ? <div className="grading-panel">grading attempt...</div> : null}
            {fallbackRequired && selfGradeVisible ? (
              <SelfGradePanel
                item={item}
                value={selfGrade}
                setValue={setSelfGrade}
                scorePreview={scorePreview}
                fieldErrors={fieldErrors}
              />
            ) : null}
            <div className="form-row" style={{ marginTop: 16 }}>
              <button className="queue-row focused" type="button" onClick={() => void submit()} disabled={submitting}>
                <span className="queue-hotkey">^↵</span>
                <span className="queue-title">Submit</span>
                <span className="queue-score">
                  {selfGradeVisible ? `${scorePreview}/${item.rubric?.maxPoints ?? 4}` : ""}
                </span>
              </button>
            </div>
          </div>
          </>
          )}
        </Card>
      </div>
      <KeyBar keys={isTeachBack ? [
        { key: "^enter", label: "send" },
        { key: "^s", label: "skip" },
        { key: "esc", label: "today" }
      ] : probeActive ? [
        { key: "^enter", label: "submit" },
        { key: "^d", label: "don't know" },
        { key: "^s", label: "skip" },
        { key: "esc", label: "today" }
      ] : [
        { key: "^enter", label: "submit" },
        { key: "^h", label: "hint" },
        { key: "^d", label: "don't know" },
        { key: "^s", label: "skip" },
        { key: "?", label: "ask tutor" },
        { key: "esc", label: "today" }
      ]} />
    </div>
  );
}

// ── Teach-back conversation ──────────────────────────────────────────────────
// The learner teaches; the AI plays a curious naive student that never
// confirms, corrects, or reveals. The transcript replaces the answer box and
// the whole conversation is graded as one attempt when the question budget is
// exhausted (or the learner finishes early). The sidecar owns the state via
// the session checkpoint; `restoredState` rehydrates it after a restart.
function TeachBackConversation({
  session,
  item,
  restoredState,
  onFeedback,
  onCheckpointCleared,
  markSubmitted
}: {
  session: SessionSnapshot;
  item: PracticeItemDetail;
  restoredState: TeachBackStateDto | null;
  onFeedback: (attemptId: string) => void;
  onCheckpointCleared: () => void;
  markSubmitted: () => void;
}) {
  const [turns, setTurns] = useState<TeachBackTurnDto[]>(restoredState?.turns ?? []);
  const [asked, setAsked] = useState(restoredState?.askedCount ?? 0);
  const [budget, setBudget] = useState<number | null>(restoredState ? restoredState.planned.length : null);
  const [input, setInput] = useState("");
  const [pending, setPending] = useState(false);
  const [finishing, setFinishing] = useState(false);
  const [inlineError, setInlineError] = useState<string | null>(null);
  const [startFailed, setStartFailed] = useState(false);
  // Guards the mount-time start against a double mount (same idiom as
  // startupStartedRef in App.tsx); the retry button bypasses it on purpose.
  const startedRef = useRef(false);
  const transcriptRef = useRef<HTMLDivElement | null>(null);

  const lastRole = turns.length > 0 ? turns[turns.length - 1].role : null;
  // Resume gap: the answer was checkpointed but the next question was never
  // generated — "continue" works without new text, and anything typed is
  // appended server-side to the pending learner turn.
  const needsText = turns.length === 0 || lastRole === "ai";

  const start = useCallback(() => {
    setInlineError(null);
    setStartFailed(false);
    api
      .startTeachBack({ sessionId: session.sessionId, practiceItemId: item.id })
      .then((result) => {
        // start is idempotent server-side and returns the authoritative
        // conversation state (the in-progress one when checkpointed, empty
        // otherwise). The locally restored snapshot can be stale — App only
        // reads the checkpoint at startup — so the server's copy always wins.
        setBudget(result.budget);
        setTurns(result.state.turns);
        setAsked(result.state.askedCount);
      })
      .catch((error) => {
        setStartFailed(true);
        setInlineError(errorMessage(error, "Could not start the teach-back conversation."));
      });
  }, [session.sessionId, item.id]);

  useEffect(() => {
    // Always sync with the server on mount; the restored snapshot (seeded into
    // state above) only bridges the gap while the call is in flight or if it
    // fails.
    if (startedRef.current) return;
    startedRef.current = true;
    start();
  }, [start]);

  useEffect(() => {
    const node = transcriptRef.current;
    if (node) node.scrollTop = node.scrollHeight;
  }, [turns.length, pending]);

  async function send(finish = false) {
    if (pending || startFailed) return;
    const text = input.trim();
    if (needsText && !text && !finish) return;
    setPending(true);
    setFinishing(finish);
    setInlineError(null);
    try {
      const result = await api.submitTeachBackTurn({
        sessionId: session.sessionId,
        practiceItemId: item.id,
        answerMd: text,
        finish
      });
      if (result.done) {
        markSubmitted();
        onCheckpointCleared();
        onFeedback(result.attemptId);
      } else {
        setTurns(result.state.turns);
        setAsked(result.asked);
        setBudget(result.budget);
        setInput("");
      }
    } catch (error) {
      setInlineError(errorMessage(error, "Could not send this teach-back turn."));
    } finally {
      setPending(false);
      setFinishing(false);
    }
  }

  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      if ((event.ctrlKey || event.metaKey) && event.key === "Enter") {
        event.preventDefault();
        void send();
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  });

  const submitLabel =
    turns.length === 0 ? "Start teaching" : lastRole === "learner" ? "Continue" : "Send answer";
  const questionsAnswered = asked > 0 && lastRole === "learner";

  return (
    <div style={{ marginTop: 12 }}>
      <div className="queue-meta" style={{ alignItems: "center", gap: 8 }}>
        <Pill tone="amber">teach-back</Pill>
        {budget !== null ? (
          <Pill>{asked > 0 ? `question ${Math.min(asked, budget)} of ${budget}` : `${budget} follow-up question${budget === 1 ? "" : "s"} planned`}</Pill>
        ) : null}
        <span style={{ opacity: 0.65, fontSize: 12 }}>
          the AI plays a student — it will not confirm or correct
        </span>
      </div>
      {item.teachBackSource?.questConnection === "connected" &&
      item.teachBackSource.questSentence ? (
        <div
          style={{
            marginTop: 9,
            borderLeft: `3px solid ${COLOR.cyan}`,
            background: COLOR.bgElev,
            color: COLOR.textDim,
            fontSize: 12,
            lineHeight: 1.5,
            padding: "8px 11px"
          }}
        >
          This transfer question connects to:{" "}
          <span style={{ color: COLOR.text }}>
            {item.teachBackSource.questSentence}
          </span>
        </div>
      ) : null}

      {/* transcript */}
      <div
        ref={transcriptRef}
        style={{ maxHeight: "44vh", overflowY: "auto", margin: "10px 0", display: "flex", flexDirection: "column", gap: 10 }}
      >
        {turns.map((turn, index) => (
          <div
            key={`${index}-${turn.role}`}
            style={
              turn.role === "learner"
                ? { alignSelf: "flex-end", maxWidth: "85%", border: "1px solid #7a5a2a", borderLeft: "3px solid #e3a063", background: "#1c1710", padding: "8px 12px" }
                : { alignSelf: "flex-start", maxWidth: "85%", border: "1px solid #2a2a2a", borderLeft: "3px solid #3a3a3a", background: "#141414", padding: "8px 12px" }
            }
          >
            <div style={{ fontSize: 10, opacity: 0.6, marginBottom: 4, textTransform: "uppercase", letterSpacing: 1 }}>
              {turn.role === "learner" ? (index === 0 ? "you · opening explanation" : "you") : "student"}
            </div>
            <div className="markdown" style={{ fontSize: 13, lineHeight: 1.6 }}>
              <MarkdownMath value={turn.contentMd} />
            </div>
          </div>
        ))}
        {pending ? (
          <div style={{ alignSelf: "flex-start", opacity: 0.6, fontSize: 12 }}>
            {finishing || (budget !== null && asked >= budget && lastRole === "ai") ? "grading the conversation …" : "the student is thinking …"}
          </div>
        ) : null}
      </div>

      {inlineError ? (
        <div className="hint-banner" style={{ borderColor: "#e07e7e" }}>
          <Pill tone="red">error</Pill> {inlineError}
          {startFailed ? (
            <button type="button" className="queue-row" style={{ marginLeft: 10 }} onClick={start}>
              retry
            </button>
          ) : null}
        </div>
      ) : null}

      {/* input */}
      {!startFailed ? (
        <>
          <MathLiveEditor
            value={input}
            onChange={setInput}
            disabled={pending}
            placeholder={
              turns.length === 0
                ? "teach the concept in your own words — $math$ renders as you type"
                : lastRole === "learner"
                  ? "add to your previous answer (optional), then continue"
                  : "answer the student's question"
            }
            maxHeight={220}
            ariaLabel="teach-back answer"
          />
          <div className="queue-meta">{input.length} chars · {input.split(/\s+/).filter(Boolean).length} words</div>
          <div className="form-row" style={{ marginTop: 12, display: "flex", alignItems: "center", gap: 12 }}>
            <button className="queue-row focused" type="button" onClick={() => void send()} disabled={pending}>
              <span className="queue-hotkey">^↵</span>
              <span className="queue-title">{submitLabel}</span>
              <span className="queue-score">{budget !== null ? `${asked}/${budget}` : ""}</span>
            </button>
            {questionsAnswered || turns.length > 0 ? (
              <button
                type="button"
                className="queue-row"
                onClick={() => void send(true)}
                disabled={pending || turns.length === 0}
                title="stop here and grade the conversation so far"
              >
                finish &amp; grade now
              </button>
            ) : null}
          </div>
        </>
      ) : null}
    </div>
  );
}

function SelfGradePanel({
  item,
  value,
  setValue,
  scorePreview,
  fieldErrors
}: {
  item: PracticeItemDetail;
  value: SelfGradeInputDto;
  setValue: (next: SelfGradeInputDto) => void;
  scorePreview: number;
  fieldErrors: Record<string, string>;
}) {
  return (
    <div className="self-grade-panel">
      <div>
        <b>AI grading is unavailable</b> · grade your answer to continue · live score{" "}
        {scorePreview}/{item.rubric?.maxPoints ?? 4}
      </div>
      <div className="self-grade-grid">
        {item.rubric?.criteria.map((criterion) => {
          const awarded = value.criterionPoints[criterion.id] ?? 0;
          const docked = awarded < criterion.points;
          return (
            <div className="criterion-block" key={criterion.id}>
              <label className="criterion-row">
                <span>{criterion.description}</span>
                <input
                  className="number-input"
                  type="number"
                  min={0}
                  max={criterion.points}
                  step={0.25}
                  value={awarded}
                  onChange={(event) => {
                    const points = Number(event.target.value);
                    const stillDocked = points < criterion.points;
                    setValue({
                      ...value,
                      criterionPoints: { ...value.criterionPoints, [criterion.id]: points },
                      // Restoring a criterion to full credit retracts its attributions.
                      errorAttributions: stillDocked
                        ? value.errorAttributions ?? []
                        : (value.errorAttributions ?? []).filter((a) => a.criterionId !== criterion.id)
                    });
                  }}
                />
              </label>
              {fieldErrors[criterion.id] ? <span className="field-error">{fieldErrors[criterion.id]}</span> : null}
              {docked ? (
                <CriterionErrorPicker criterion={criterion} candidates={item.candidateErrorTypes} value={value} setValue={setValue} />
              ) : null}
            </div>
          );
        })}
        {item.rubric?.fatalErrors.length ? (
          <label>
            fatal errors
            <select
              className="text-input"
              multiple
              value={value.fatalErrors ?? []}
              onChange={(event) => setValue({
                ...value,
                fatalErrors: Array.from(event.currentTarget.selectedOptions).map((option) => option.value)
              })}
            >
              {item.rubric.fatalErrors.map((fatal) => (
                <option key={fatal.id} value={fatal.id}>{fatal.id} caps at {fatal.maxGrade}</option>
              ))}
            </select>
          </label>
        ) : null}
        <label>
          confidence
          <TermSelect
            value={String(value.confidence)}
            options={[1, 2, 3, 4, 5].map((n) => ({ value: String(n), label: String(n) }))}
            onChange={(v) => setValue({ ...value, confidence: Number(v) })}
            width={110}
          />
          {fieldErrors.confidence ? <span className="field-error">{fieldErrors.confidence}</span> : null}
        </label>
        <label>
          notes
          <textarea
            className="self-grade-notes"
            value={value.notes ?? ""}
            onChange={(event) => setValue({ ...value, notes: event.target.value })}
          />
        </label>
      </div>
    </div>
  );
}

// Spawned beneath a rubric criterion the learner scored below full credit: a
// multi-select of error types they can attribute to that specific criterion.
// Concept-relevant types lead; the rest follow after a divider. Selections are
// optional and mirror Codex error attributions once resolved server-side.
function CriterionErrorPicker({
  criterion,
  candidates,
  value,
  setValue
}: {
  criterion: RubricCriterionDto;
  candidates: CandidateErrorTypeDto[];
  value: SelfGradeInputDto;
  setValue: (next: SelfGradeInputDto) => void;
}) {
  const selected = new Set(
    (value.errorAttributions ?? []).filter((a) => a.criterionId === criterion.id).map((a) => a.errorType)
  );
  const toggle = (errorType: string) => {
    const list = value.errorAttributions ?? [];
    const exists = list.some((a) => a.criterionId === criterion.id && a.errorType === errorType);
    setValue({
      ...value,
      errorAttributions: exists
        ? list.filter((a) => !(a.criterionId === criterion.id && a.errorType === errorType))
        : [...list, { errorType, criterionId: criterion.id }]
    });
  };
  const relevant = candidates.filter((c) => c.relevant);
  const others = candidates.filter((c) => !c.relevant);
  const chip = (c: CandidateErrorTypeDto) => (
    <button
      type="button"
      key={c.id}
      className={[
        "attribution-chip",
        c.relevant ? "relevant" : "",
        selected.has(c.id) ? "on" : "",
        c.isMisconception ? "misconception" : ""
      ].filter(Boolean).join(" ")}
      onClick={() => toggle(c.id)}
      title={c.isMisconception ? "misconception" : undefined}
    >
      {c.isMisconception ? <span className="attribution-chip-mark">◆</span> : null}
      {c.title}
    </button>
  );
  return (
    <div className="attribution-box">
      <div className="attribution-head">
        attribute error(s) <span className="attribution-optional">· optional</span>
      </div>
      {candidates.length === 0 ? (
        <div className="attribution-empty">no error types defined in this vault</div>
      ) : (
        <div className="attribution-chips">
          {relevant.map(chip)}
          {relevant.length > 0 && others.length > 0 ? <span className="attribution-divider">others</span> : null}
          {others.map(chip)}
        </div>
      )}
    </div>
  );
}

// Keep only attributions whose criterion is still below full credit (or that
// aren't tied to a criterion), so a restored score never ships a stale tag.
function prunedAttributions(item: PracticeItemDetail, grade: SelfGradeInputDto): SelfGradeErrorAttributionDto[] {
  const docked = new Set(
    (item.rubric?.criteria ?? [])
      .filter((criterion) => (grade.criterionPoints[criterion.id] ?? 0) < criterion.points)
      .map((criterion) => criterion.id)
  );
  return (grade.errorAttributions ?? []).filter((a) => a.criterionId == null || docked.has(a.criterionId));
}

// These mirror learnloop.attempt_types so the client only ever submits an
// attempt type the item actually permits. An empty allow-list means the
// backend imposes no per-item restriction (every supported type is fine).
const NON_RECORDING_ATTEMPT_TYPES: ReadonlySet<AttemptType> = new Set(["guided_walkthrough", "skip"]);

function defaultAttemptType(allowed: readonly AttemptType[]): AttemptType {
  if (allowed.length === 0) return "independent_attempt";
  if (allowed.includes("independent_attempt")) return "independent_attempt";
  for (const candidate of allowed) {
    if (!NON_RECORDING_ATTEMPT_TYPES.has(candidate)) return candidate;
  }
  return "independent_attempt";
}

// Guided redo (Fix 3): compose the preserved prefix and the learner's rewritten
// portion into one answer. A paragraph break separates them unless one is
// already there — the same end-append junction rule repair_splice enforces
// server-side, so the graded text never runs the redo into the kept sentence.
function composeRedoAnswer(prefix: string, redoText: string): string {
  const suffix = redoText.replace(/^[ \t]+/, "");
  if (!prefix.trim()) return redoText;
  if (/\n[ \t]*\n[ \t]*$/.test(prefix) || /^[ \t]*\n/.test(redoText)) return prefix + redoText;
  return `${prefix}\n\n${suffix}`;
}

// Prefer hinted_attempt when hints were used and the item allows it; otherwise
// fall back to the item's default recording attempt type.
function chooseAttemptType(allowed: readonly AttemptType[], hintsUsed: number): AttemptType {
  const allows = (type: AttemptType) => allowed.length === 0 || allowed.includes(type);
  if (hintsUsed > 0 && allows("hinted_attempt")) return "hinted_attempt";
  return defaultAttemptType(allowed);
}

function validateSelfGrade(
  item: PracticeItemDetail,
  value: SelfGradeInputDto,
  required: boolean
): Record<string, string> {
  if (!required) return {};
  const errors: Record<string, string> = {};
  for (const criterion of item.rubric?.criteria ?? []) {
    const points = value.criterionPoints[criterion.id];
    if (!Number.isFinite(points) || points < 0 || points > criterion.points) {
      errors[criterion.id] = `0..${criterion.points}`;
    }
  }
  if (!Number.isInteger(value.confidence) || value.confidence < 1 || value.confidence > 5) {
    errors.confidence = "1..5";
  }
  return errors;
}
