import { getCurrentWindow } from "@tauri-apps/api/window";
import { useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState } from "react";
import { api } from "../api/client";
import type {
  AttemptType,
  CandidateErrorTypeDto,
  CommandError,
  PracticeItemDetail,
  RubricCriterionDto,
  SelfGradeErrorAttributionDto,
  SelfGradeInputDto,
  SessionSnapshot
} from "../api/dto";
import { Card, EntityLink, KeyBar, Pill, SectionHeader } from "../components/ui";
import { MarkdownMath } from "../render/MarkdownMath";
import { MathLiveEditor } from "../render/MathLiveEditor";

export function PracticeScreen({
  session,
  practiceItemId,
  gradingReady,
  gradingProvider,
  restoredAnswer,
  restoredHints,
  onFeedback,
  onBack,
  onCheckpointCleared,
  onInspect,
  onError
}: {
  session: SessionSnapshot;
  practiceItemId: string;
  gradingReady: boolean;
  gradingProvider: string;
  restoredAnswer?: string;
  restoredHints?: number;
  onFeedback: (attemptId: string) => void;
  onBack: () => void;
  onCheckpointCleared: () => void;
  onInspect: (id: string) => void;
  onError: (message: string) => void;
}) {
  const [item, setItem] = useState<PracticeItemDetail | null>(null);
  const [answer, setAnswer] = useState(restoredAnswer ?? "");
  const [hintsUsed, setHintsUsed] = useState(restoredHints ?? 0);
  const [submitting, setSubmitting] = useState(false);
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
    if (suppressDraftFlush.current) return;
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
        setItem(detail);
        setSelfGrade((current) => ({
          ...current,
          criterionPoints: Object.fromEntries((detail.rubric?.criteria ?? []).map((criterion) => [criterion.id, 0])),
          errorAttributions: []
        }));
      })
      .catch((error) => { if (!cancelled) onError(error.message); });
    return () => { cancelled = true; };
  }, [practiceItemId, onError]);

  useEffect(() => {
    const timer = setTimeout(() => {
      void flushDraft().catch((error) => onError(error.message));
    }, 350);
    return () => clearTimeout(timer);
  }, [answer, flushDraft, hintsUsed, onError, practiceItemId, session.sessionId]);

  useEffect(() => {
    return () => {
      void flushDraft().catch((error) => onError(error.message));
    };
  }, [flushDraft, onError]);

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
        event.preventDefault();
        void submit();
      } else if (ctrl && event.key.toLowerCase() === "h") {
        event.preventDefault();
        revealHint();
      } else if (ctrl && event.key.toLowerCase() === "d") {
        event.preventDefault();
        void dontKnow();
      } else if (ctrl && event.key.toLowerCase() === "s") {
        event.preventDefault();
        void skip();
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

  function revealHint() {
    setHintsUsed((value) => Math.min(item?.hints.length ?? 0, value + 1));
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
        attemptType: chooseAttemptType(item.attemptTypesAllowed, hintsUsed),
        hintsUsed,
        // Drop attributions for any criterion the learner ultimately left at full
        // credit, so a restored score never ships a stale error tag.
        selfGrade: fallbackRequired ? { ...selfGrade, errorAttributions: prunedAttributions(item, selfGrade) } : null
      });
      suppressDraftFlush.current = true;
      await clearCheckpoint();
      onFeedback(result.attemptId);
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
      const result = await api.submitDontKnow({ sessionId: session.sessionId, practiceItemId: item.id, hintsUsed });
      suppressDraftFlush.current = true;
      await clearCheckpoint();
      onFeedback(result.attemptId);
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
            <Pill>{item.practiceMode}</Pill>
            {fallbackRequired ? <Pill tone="amber">self-grade required</Pill> : <Pill tone="green">{gradingProvider} grading</Pill>}
          </div>
          <div className="markdown"><MarkdownMath value={item.prompt} /></div>
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
        </Card>
      </div>
      <KeyBar keys={[
        { key: "^enter", label: "submit" },
        { key: "^h", label: "hint" },
        { key: "^d", label: "don't know" },
        { key: "^s", label: "skip" },
        { key: "esc", label: "today" }
      ]} />
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
