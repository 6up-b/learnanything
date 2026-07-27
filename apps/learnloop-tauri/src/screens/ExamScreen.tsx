import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { api } from "../api/client";
import type {
  CommandError,
  ExamReportSnapshot,
  ExamSessionSnapshot,
  ExamFacetOutcomeDto
} from "../api/dto";
import { COLOR, FONT_MONO, Faint, KeyBar } from "../components/term";
import { Card, SectionHeader } from "../components/ui";
import { ItemPresentation } from "../components/ItemPresentation";
import { masteryTone } from "../app/algoConfig";
import { MathLiveEditor } from "../render/MathLiveEditor";

type Phase = "loading" | "error" | "exam" | "finishing" | "report";

// A linear, no-help assessment. Unlike PracticeScreen there are no hints, no
// tutor, no skip, and no per-item grade mid-flight — items are answered in a
// fixed order and only the aggregate report is revealed at the end. The session
// lives server-side, so navigating away and re-entering resumes it (startExam is
// idempotent and reports which items are already answered).
export function ExamScreen({
  goalId,
  onExit,
  onError
}: {
  goalId: string;
  onExit: () => void;
  onError: (message: string) => void;
}) {
  const [phase, setPhase] = useState<Phase>("loading");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [session, setSession] = useState<ExamSessionSnapshot | null>(null);
  const [answered, setAnswered] = useState<Set<string>>(new Set());
  const [answer, setAnswer] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [blankConfirm, setBlankConfirm] = useState(false);
  const [recorded, setRecorded] = useState(false);
  const [report, setReport] = useState<ExamReportSnapshot | null>(null);
  const startedRef = useRef(false);

  const items = session?.items ?? [];
  // The item under the cursor is the first one not yet answered (fixed order).
  const currentIndex = useMemo(
    () => items.findIndex((it) => !answered.has(it.practiceItemId)),
    [items, answered]
  );
  const current = currentIndex >= 0 ? items[currentIndex] : null;

  const finish = useCallback(
    (sessionId: string) => {
      setPhase("finishing");
      api
        .finishExam(sessionId)
        .then((snap) => {
          setReport(snap);
          setPhase("report");
        })
        .catch((error) => {
          const command = error as CommandError;
          setErrorMessage(command.message);
          setPhase("error");
        });
    },
    []
  );

  // Mount: start (or resume) the exam session. Guarded against a double mount.
  useEffect(() => {
    if (startedRef.current) return;
    startedRef.current = true;
    api
      .startExam(goalId)
      .then((snap) => {
        setSession(snap);
        setAnswered(new Set(snap.answeredItemIds));
        if (snap.items.length === 0) {
          setErrorMessage("This goal has no exam items available yet.");
          setPhase("error");
          return;
        }
        // A resumed session may already be fully answered — go straight to results.
        const allAnswered = snap.items.every((it) => snap.answeredItemIds.includes(it.practiceItemId));
        if (allAnswered) {
          finish(snap.sessionId);
        } else {
          setPhase("exam");
        }
      })
      .catch((error) => {
        const command = error as CommandError;
        setErrorMessage(command.message);
        setPhase("error");
      });
  }, [goalId, finish]);

  // New item under the cursor → reset the answer box and any transient state.
  useEffect(() => {
    setAnswer("");
    setBlankConfirm(false);
    setRecorded(false);
  }, [current?.practiceItemId]);

  const submit = useCallback(async () => {
    if (!session || !current || submitting) return;
    const trimmed = answer.trim();
    // Empty submissions count as an answer (there is no skip) — but nudge once.
    if (trimmed.length === 0 && !blankConfirm) {
      setBlankConfirm(true);
      return;
    }
    setSubmitting(true);
    try {
      await api.submitExamAnswer(session.sessionId, current.practiceItemId, answer);
      const nextAnswered = new Set(answered);
      nextAnswered.add(current.practiceItemId);
      // Brief acknowledgment, then auto-advance — exams never reveal per-item grades.
      setRecorded(true);
      const done = session.items.every((it) => nextAnswered.has(it.practiceItemId));
      window.setTimeout(() => {
        setAnswered(nextAnswered);
        if (done) finish(session.sessionId);
      }, 450);
    } catch (error) {
      onError((error as CommandError).message);
      setSubmitting(false);
      return;
    }
    // `submitting` is cleared by the item-change effect resetting state; guard the
    // brief window before advance so a double submit can't fire.
    window.setTimeout(() => setSubmitting(false), 460);
  }, [session, current, submitting, answer, blankConfirm, answered, finish, onError]);

  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      const ctrl = event.ctrlKey || event.metaKey;
      if (phase === "exam" && ctrl && event.key === "Enter") {
        event.preventDefault();
        void submit();
      } else if (event.key === "Escape") {
        event.preventDefault();
        onExit();
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [phase, submit, onExit]);

  if (phase === "loading" || phase === "finishing") {
    return (
      <div className="screen">
        <div className="screen-scroll">
          <Card>{phase === "loading" ? "Preparing exam…" : "Scoring exam…"}</Card>
        </div>
        <KeyBar keys={[{ key: "esc", label: "today" }]} />
      </div>
    );
  }

  if (phase === "error") {
    return (
      <div className="screen">
        <div className="screen-scroll">
          <SectionHeader>Practice exam</SectionHeader>
          <Card>
            <div style={{ color: COLOR.red, marginBottom: 10 }}>
              {errorMessage ?? "The exam could not be started."}
            </div>
            <button className="queue-row focused" type="button" onClick={onExit}>
              <span className="queue-hotkey">esc</span>
              <span className="queue-title">Back to today</span>
            </button>
          </Card>
        </div>
        <KeyBar keys={[{ key: "esc", label: "today" }]} />
      </div>
    );
  }

  if (phase === "report" && report) {
    return <ExamReport report={report} onExit={onExit} />;
  }

  // phase === "exam"
  const answeredCount = answered.size;
  return (
    <div className="screen">
      <div className="screen-scroll">
        <SectionHeader>Practice exam</SectionHeader>
        <Card focused>
          <div className="queue-meta" style={{ display: "flex", alignItems: "center", gap: 12 }}>
            <span style={{ fontFamily: FONT_MONO, color: COLOR.amber }}>
              {current ? current.index + 1 : answeredCount}/{current ? current.total : items.length}
            </span>
            <Faint>no hints · no tutor · answers are final</Faint>
          </div>
          {current ? (
            <>
              {/* Meas §3.A2/§3.A3: the same presentation payload and the same
                  renderer the practice surface mounts. Exams carried their own
                  prompt-only shape, so an error hunt reserved into a pool would
                  have been served here with no worked solution even after
                  practice was fixed — and an exam answer is held-out
                  measurement, which makes an unanswerable item worse here than
                  anywhere else. */}
              <ItemPresentation presentation={current.presentation} />

              <div style={{ marginTop: 12 }}>
                <MathLiveEditor
                  value={answer}
                  onChange={(next) => {
                    setAnswer(next);
                    if (blankConfirm) setBlankConfirm(false);
                  }}
                  disabled={submitting}
                  placeholder="type your answer — $math$ renders as you type"
                  maxHeight={280}
                  ariaLabel="exam answer"
                />
              </div>
              <div className="queue-meta">
                {answer.length} chars · {answer.split(/\s+/).filter(Boolean).length} words
              </div>
              {recorded ? (
                <div style={{ marginTop: 10, color: COLOR.green, fontFamily: FONT_MONO, fontSize: 13 }}>
                  recorded ✓
                </div>
              ) : blankConfirm ? (
                <div className="hint-banner" style={{ borderColor: COLOR.amber, marginTop: 10 }}>
                  <span style={{ color: COLOR.amber }}>Submit a blank answer?</span> This item has no
                  skip — press submit again to record it empty.
                </div>
              ) : null}
              <div className="form-row" style={{ marginTop: 16 }}>
                <button
                  className="queue-row focused"
                  type="button"
                  onClick={() => void submit()}
                  disabled={submitting}
                >
                  <span className="queue-hotkey">^↵</span>
                  <span className="queue-title">
                    {blankConfirm ? "Submit blank answer" : "Submit answer"}
                  </span>
                  <span className="queue-score" />
                </button>
              </div>
            </>
          ) : (
            <div>All items answered — scoring…</div>
          )}
        </Card>
      </div>
      <KeyBar
        keys={[
          { key: "^enter", label: "submit" },
          { key: "esc", label: "today" }
        ]}
      />
    </div>
  );
}

// ── Results ──────────────────────────────────────────────────────────────────
function pct(value: number | null): string {
  return value == null ? "—" : `${Math.round(value * 100)}%`;
}

function ExamReport({ report, onExit }: { report: ExamReportSnapshot; onExit: () => void }) {
  const predicted = report.predictedScoreFraction;
  const scored = report.scoreFraction;
  // Worst-first: lowest observed correctness leads (nulls sink to the bottom).
  const facets = useMemo(() => {
    const sortKey = (f: ExamFacetOutcomeDto) => (f.observedCorrectness == null ? Infinity : f.observedCorrectness);
    return [...report.perFacet].sort((a, b) => sortKey(a) - sortKey(b));
  }, [report.perFacet]);

  return (
    <div className="screen">
      <div className="screen-scroll">
        <SectionHeader>Exam results</SectionHeader>
        <Card focused>
          <div style={{ fontFamily: FONT_MONO, fontSize: 16, color: COLOR.text }}>
            {predicted != null ? (
              <>
                we projected <span style={{ color: COLOR.amber }}>{pct(predicted)}</span> — you scored{" "}
                <span style={{ color: scored != null ? masteryTone(scored, COLOR) : COLOR.text }}>
                  {pct(scored)}
                </span>
              </>
            ) : (
              <>
                you scored{" "}
                <span style={{ color: scored != null ? masteryTone(scored, COLOR) : COLOR.text }}>
                  {pct(scored)}
                </span>
              </>
            )}
          </div>
          {report.brier != null ? (
            <div style={{ marginTop: 6 }}>
              <Faint>calibration (Brier): {report.brier.toFixed(3)} — lower is better</Faint>
            </div>
          ) : null}
        </Card>

        <SectionHeader>Per facet · predicted vs observed</SectionHeader>
        <Card>
          {facets.length === 0 ? (
            <Faint>no per-facet outcomes</Faint>
          ) : (
            <div style={{ display: "grid", gap: 2 }}>
              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "1fr 70px 70px",
                  gap: 8,
                  fontSize: 11,
                  color: COLOR.textFaint,
                  fontFamily: FONT_MONO,
                  paddingBottom: 4
                }}
              >
                <span>facet</span>
                <span style={{ textAlign: "right" }}>predicted</span>
                <span style={{ textAlign: "right" }}>observed</span>
              </div>
              {facets.map((f, i) => {
                const tone =
                  f.observedCorrectness != null ? masteryTone(f.observedCorrectness, COLOR) : COLOR.textFaint;
                return (
                  <div
                    key={`${f.facetId}-${f.learningObjectId}-${i}`}
                    style={{
                      display: "grid",
                      gridTemplateColumns: "1fr 70px 70px",
                      gap: 8,
                      alignItems: "center",
                      fontSize: 12,
                      fontFamily: FONT_MONO,
                      padding: "4px 0",
                      borderTop: `1px solid ${COLOR.border}`
                    }}
                  >
                    <span style={{ overflowWrap: "anywhere", color: COLOR.text }}>{f.facetId}</span>
                    <span style={{ textAlign: "right", color: COLOR.textDim }}>{pct(f.predictedRecall)}</span>
                    <span style={{ textAlign: "right", color: tone }}>{pct(f.observedCorrectness)}</span>
                  </div>
                );
              })}
            </div>
          )}
        </Card>

        <SectionHeader>Per item · predicted vs observed</SectionHeader>
        <Card>
          {report.itemOutcomes.length === 0 ? (
            <Faint>no item outcomes</Faint>
          ) : (
            <div style={{ display: "flex", flexWrap: "wrap", gap: 10 }}>
              {report.itemOutcomes.map((it, i) => {
                const pred = it.predictedCorrectness;
                const obs = it.observedCorrectness;
                const obsTone = obs != null ? masteryTone(obs, COLOR) : COLOR.textFaint;
                return (
                  <div
                    key={`${it.practiceItemId}-${i}`}
                    title={`item ${i + 1} · predicted ${pct(pred)} · observed ${pct(obs)}`}
                    style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 2 }}
                  >
                    <span style={{ display: "flex", gap: 3, alignItems: "center" }}>
                      <span
                        style={{
                          width: 9,
                          height: 9,
                          borderRadius: "50%",
                          border: `1px solid ${COLOR.textDim}`,
                          opacity: pred == null ? 0.3 : 0.35 + 0.65 * pred
                        }}
                      />
                      <span
                        style={{
                          width: 9,
                          height: 9,
                          borderRadius: "50%",
                          background: obsTone,
                          opacity: obs == null ? 0.3 : 1
                        }}
                      />
                    </span>
                    <span style={{ fontSize: 9, color: COLOR.textFaint, fontFamily: FONT_MONO }}>{i + 1}</span>
                  </div>
                );
              })}
            </div>
          )}
          <div style={{ marginTop: 10, fontSize: 11, color: COLOR.textFaint, fontFamily: FONT_MONO }}>
            <span
              style={{
                display: "inline-block",
                width: 8,
                height: 8,
                borderRadius: "50%",
                border: `1px solid ${COLOR.textDim}`,
                marginRight: 5,
                verticalAlign: "middle"
              }}
            />
            predicted
            <span style={{ marginLeft: 14 }}>
              <span
                style={{
                  display: "inline-block",
                  width: 8,
                  height: 8,
                  borderRadius: "50%",
                  background: COLOR.green,
                  marginRight: 5,
                  verticalAlign: "middle"
                }}
              />
              observed
            </span>
          </div>
        </Card>

        <div className="form-row" style={{ marginTop: 18 }}>
          <button className="queue-row focused" type="button" onClick={onExit}>
            <span className="queue-hotkey">↵</span>
            <span className="queue-title">Back to today</span>
          </button>
        </div>
      </div>
      <KeyBar keys={[{ key: "esc", label: "today" }]} />
    </div>
  );
}
