import { getCurrentWindow } from "@tauri-apps/api/window";
import { useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState } from "react";
import { api } from "../api/client";
import type {
  AttemptType,
  CandidateErrorTypeDto,
  CommandError,
  PracticeItemDetail,
  ProbeContractDto,
  RubricCriterionDto,
  SelfGradeErrorAttributionDto,
  SelfGradeInputDto,
  SessionSnapshot,
  TeachBackStateDto,
  TeachBackTurnDto
} from "../api/dto";
import { Card, EntityLink, KeyBar, Pill, SectionHeader } from "../components/ui";
import { BlockBar, COLOR, Faint, FONT_MONO, modePillColor } from "../components/term";
import { masteryTone } from "../app/algoConfig";
import { MarkdownMath } from "../render/MarkdownMath";
import { MathLiveEditor } from "../render/MathLiveEditor";

export function PracticeScreen({
  session,
  practiceItemId,
  gradingReady,
  gradingProvider,
  restoredAnswer,
  restoredHints,
  restoredTeachBack,
  onFeedback,
  onBack,
  onCheckpointCleared,
  onDraftSaved,
  onTeachBackActive,
  onInspect,
  onAsk,
  onError,
  primed = false
}: {
  session: SessionSnapshot;
  practiceItemId: string;
  /** This item is a primed retry launched from the feedback source panel. */
  primed?: boolean;
  gradingReady: boolean;
  gradingProvider: string;
  restoredAnswer?: string;
  restoredHints?: number;
  restoredTeachBack?: TeachBackStateDto | null;
  onFeedback: (attemptId: string) => void;
  onBack: () => void;
  onCheckpointCleared: () => void;
  /** Mirror of the last flushed draft, so App can restore it if this item is
   *  re-opened before the backend checkpoint is reloaded. */
  onDraftSaved: (draft: { practiceItemId: string; answerMd: string; hintsUsed: number }) => void;
  onTeachBackActive: (active: boolean) => void;
  onInspect: (id: string) => void;
  onAsk: (target: {
    context: "practice";
    practiceItemId: string;
    sessionId: string;
    openedAtMs: number;
  }) => void;
  onError: (message: string) => void;
}) {
  const [item, setItem] = useState<PracticeItemDetail | null>(null);
  const [answer, setAnswer] = useState(restoredAnswer ?? "");
  const [hintsUsed, setHintsUsed] = useState(restoredHints ?? 0);
  const [submitting, setSubmitting] = useState(false);
  // Probe redesign §12: when the LO has an in-progress diagnostic episode, the
  // sidecar commits a presentation and this contract enforces measurement
  // conditions — forced diagnostic_probe, no hints, no ask-tutor, deferred
  // feedback, and a "stop diagnosing" escape into tutoring.
  const [probe, setProbe] = useState<ProbeContractDto | null>(null);
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
  const latestDraft = useRef({
    sessionId: session.sessionId,
    practiceItemId,
    answerMd: answer,
    hintsUsed
  });
  const suppressDraftFlush = useRef(false);
  const isTeachBack = item?.practiceMode === "teach_back";
  // Teach-back conversations own the checkpoint (the sidecar stores the
  // conversation envelope in current_answer); the plain draft flush must never
  // overwrite it. Seeded from the restored checkpoint so a resumed conversation
  // is safe even before the item detail loads.
  const teachBackRef = useRef(Boolean(restoredTeachBack));
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
  // from it (there is no other attempt timer on this screen).
  const openedAtMs = useRef(Date.now());
  useEffect(() => {
    openedAtMs.current = Date.now();
    setAnswerConfidence(null);
  }, [practiceItemId]);
  const openAsk = () =>
    onAsk({
      context: "practice",
      practiceItemId,
      sessionId: session.sessionId,
      openedAtMs: openedAtMs.current
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
      hintsUsed
    };
    suppressDraftFlush.current = false;
  }, [answer, hintsUsed, practiceItemId, session.sessionId]);

  const flushDraft = useCallback(async () => {
    if (suppressDraftFlush.current || teachBackRef.current) return;
    await api.savePracticeDraft(latestDraft.current);
  }, []);

  useEffect(() => {
    setAnswer(restoredAnswer ?? "");
    setHintsUsed(restoredHints ?? 0);
    setFallbackRequired(!gradingReady);
    setSelfGradeVisible(false);
  }, [gradingReady, practiceItemId, restoredAnswer, restoredHints]);

  useEffect(() => {
    let cancelled = false;
    api.getPracticeItem(practiceItemId)
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
      .catch((error) => { if (!cancelled) onError(error.message); });
    // Ask the sidecar for the probe measurement contract; committing the
    // presentation is the serve event (§5.1). A failure here (older sidecar,
    // parked episode) just means ordinary practice.
    setProbe(null);
    api.getProbeContract(practiceItemId, session.sessionId)
      .then((contract) => {
        if (!cancelled) setProbe(contract.active ? contract : null);
      })
      .catch(() => { if (!cancelled) setProbe(null); });
    return () => { cancelled = true; };
  }, [practiceItemId, session.sessionId, onError]);

  useEffect(() => {
    const timer = setTimeout(() => {
      void flushDraft().catch((error) => onError(error.message));
    }, 350);
    return () => clearTimeout(timer);
  }, [answer, flushDraft, hintsUsed, onError, practiceItemId, session.sessionId]);

  useEffect(() => {
    return () => {
      void flushDraft().catch((error) => onError(error.message));
      // Reported only on unmount — reporting on every debounced flush would
      // loop the draft back through restoredAnswer while the user is typing.
      if (!suppressDraftFlush.current && !teachBackRef.current) {
        const { practiceItemId: id, answerMd, hintsUsed: hints } = latestDraft.current;
        onDraftSaved({ practiceItemId: id, answerMd, hintsUsed: hints });
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
        onError((error as Error).message);
      } finally {
        await appWindow.destroy();
      }
    }).then((listener) => {
      unlisten = listener;
    }).catch((error) => onError((error as Error).message));
    return () => unlisten?.();
  }, [flushDraft, onError]);

  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
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
      } else if (event.key === "Escape") {
        event.preventDefault();
        onBack();
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
    score = Math.max(0, Math.min(item.rubric.maxPoints, score, 4));
    for (const fatalId of selfGrade.fatalErrors ?? []) {
      const fatal = item.rubric.fatalErrors.find((candidate) => candidate.id === fatalId);
      if (fatal) score = Math.min(score, fatal.maxGrade);
    }
    return score;
  }, [item, selfGrade]);

  const probeActive = Boolean(probe?.active && probe.presentationId);

  function revealHint() {
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
      // §3: measurement ends and tutoring begins.
      openAsk();
    } catch (error) {
      onError((error as Error).message);
    }
  }

  function routeAfterAttempt(result: {
    attemptId: string;
    probeEpisode?: { feedbackDeferred: boolean } | null;
    probeBlockEnd?: { route: string | null } | null;
  }) {
    // §5.6/§5.7: feedback stays deferred while the diagnostic block is
    // measuring; the block-end hook releases the block's withheld feedback,
    // so a submission that closed the block routes straight to it.
    if (probeActive && result.probeEpisode?.feedbackDeferred && !result.probeBlockEnd) {
      onBack();
      return;
    }
    onFeedback(result.attemptId);
    if (result.probeBlockEnd?.route === "tutoring") {
      // §12.1: the typed transition decision is persisted server-side; open
      // the tutor so the diagnosed gap flows into instruction.
      openAsk();
    }
  }

  async function submit() {
    if (!item || submitting) return;
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
      const result = await api.submitAttempt({
        sessionId: session.sessionId,
        practiceItemId: item.id,
        answerMd: answer,
        // §12: an active diagnostic block forces the recording attempt type.
        attemptType: probeActive ? "diagnostic_probe" : chooseAttemptType(item.attemptTypesAllowed, hintsUsed),
        hintsUsed,
        primed,
        probePresentationId: probeActive ? probe?.presentationId : null,
        answerConfidence: probeActive ? answerConfidence : null,
        // Drop attributions for any criterion the learner ultimately left at full
        // credit, so a restored score never ships a stale error tag.
        selfGrade: fallbackRequired ? { ...selfGrade, errorAttributions: prunedAttributions(item, selfGrade) } : null
      });
      suppressDraftFlush.current = true;
      await clearCheckpoint();
      routeAfterAttempt(result);
    } catch (error) {
      const command = error as CommandError;
      if (command.code === "grading_fallback_required") {
        setFallbackRequired(true);
        setSelfGradeVisible(true);
        onError(command.message);
      } else {
        onError(command.message);
      }
    } finally {
      setSubmitting(false);
    }
  }

  async function dontKnow() {
    if (!item || submitting) return;
    setSubmitting(true);
    try {
      const result = await api.submitDontKnow({
        sessionId: session.sessionId,
        practiceItemId: item.id,
        hintsUsed,
        probePresentationId: probeActive ? probe?.presentationId : null,
        answerConfidence: probeActive ? answerConfidence : null
      });
      suppressDraftFlush.current = true;
      await clearCheckpoint();
      routeAfterAttempt(result);
    } catch (error) {
      onError((error as Error).message);
    } finally {
      setSubmitting(false);
    }
  }

  async function skip() {
    if (!item) return;
    try {
      await api.skipPracticeItem({ sessionId: session.sessionId, practiceItemId: item.id });
      suppressDraftFlush.current = true;
      await clearCheckpoint();
      onBack();
    } catch (error) {
      onError((error as Error).message);
    }
  }

  async function clearCheckpoint() {
    try {
      await api.clearSessionCheckpoint(session.sessionId);
      onCheckpointCleared();
    } catch (error) {
      onError((error as Error).message);
    }
  }

  if (!item) {
    return <div className="screen-scroll"><Card>Loading practice item...</Card></div>;
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
            <div className="hint-banner" style={{ display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap" }}>
              <Pill tone="cyan">
                Diagnostic · observation {probe?.observationNumber ?? 1} of up to {probe?.maximumObservations ?? 4}
              </Pill>
              <span style={{ fontSize: 12, opacity: 0.75 }}>
                {probe?.capabilitySummary ?? "Checking what you already know."}{" "}
                Feedback is delayed for measurement integrity; hints and ask-tutor are unavailable.
              </span>
              <span style={{ display: "inline-flex", alignItems: "center", gap: 4, fontSize: 11, opacity: 0.85 }}>
                <Faint>confidence</Faint>
                {[1, 2, 3, 4, 5].map((level) => (
                  <button
                    key={level}
                    type="button"
                    className="queue-row"
                    style={{
                      padding: "0 6px",
                      fontFamily: FONT_MONO,
                      opacity: answerConfidence === level ? 1 : 0.45
                    }}
                    onClick={() => setAnswerConfidence(answerConfidence === level ? null : level)}
                    title="how confident are you in your answer? (optional, 1 = guessing, 5 = certain)"
                  >
                    {level}
                  </button>
                ))}
              </span>
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
          ) : null}
          {item.mastery != null ? (
            <div className="queue-meta" style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 12 }}>
              <Faint style={{ fontSize: 10, letterSpacing: "0.1em", textTransform: "uppercase" }}>mastery</Faint>
              <BlockBar value={item.mastery.mean} width={10} color={masteryTone(item.mastery.mean, COLOR)} />
              <span style={{ fontFamily: FONT_MONO, color: COLOR.text }}>{item.mastery.mean.toFixed(2)}</span>
              <Faint>±{Math.sqrt(item.mastery.variance).toFixed(2)}</Faint>
            </div>
          ) : null}
          <div className="markdown"><MarkdownMath value={item.prompt} /></div>
          {item.sourceRefs.length > 0 ? (
            <div style={{ marginTop: 6, fontSize: 11, color: COLOR.textFaint, lineHeight: 1.6 }}>
              {item.sourceRefs.map((ref, index) => (
                <div key={`${ref.refId}:${index}`} title={ref.quote ?? undefined} style={{ display: "flex", gap: 8 }}>
                  <span style={{ fontFamily: FONT_MONO }}>{ref.refId}</span>
                  <span style={{ color: COLOR.textDim }}>{ref.locator ?? ref.path ?? ref.refType}</span>
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
          <div className="answer-editor-slot" ref={editorSlotRef}>
            <MathLiveEditor
              value={answer}
              onChange={setAnswer}
              disabled={submitting}
              placeholder="type your answer — $math$ renders as you type"
              maxHeight={editorMaxHeight}
              ariaLabel="answer"
            />
          </div>
          <div ref={belowRef}>
            <div className="queue-meta">{answer.length} chars · {answer.split(/\s+/).filter(Boolean).length} words</div>
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
              <button className="queue-row focused" type="button" onClick={submit} disabled={submitting}>
                <span className="queue-hotkey">^↵</span>
                <span className="queue-title">Submit</span>
                <span className="queue-score">{selfGradeVisible ? `${scorePreview}/4` : ""}</span>
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
        const command = error as CommandError;
        setStartFailed(true);
        setInlineError(command.message);
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
      setInlineError((error as CommandError).message);
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
      <div><b>AI grading is unavailable</b> · grade your answer to continue · live score {scorePreview}/4</div>
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
          <select
            className="text-input"
            value={value.confidence}
            onChange={(event) => setValue({ ...value, confidence: Number(event.target.value) })}
          >
            {[1, 2, 3, 4, 5].map((n) => <option key={n} value={n}>{n}</option>)}
          </select>
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
// "?" must never fire while the learner is typing an answer: guard plain
// inputs, textareas, the MathLive editor's <math-field>, and contenteditables.
function isTypingTarget(target: EventTarget | null): boolean {
  const element = target as HTMLElement | null;
  if (!element) return false;
  const tag = element.tagName?.toLowerCase();
  if (tag === "input" || tag === "textarea" || tag === "math-field") return true;
  return Boolean(element.isContentEditable);
}

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
