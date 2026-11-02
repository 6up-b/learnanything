// Teacher TE1: the lesson screen (spec_teacher_v1 §19).
//
// Document typography, not chat bubbles: the teacher's text runs as a page;
// the learner's words sit in interjection cards. A plan map beside it shows
// where the lesson is (current, visited, upcoming): a position, never a
// completion. Predictions arrive open; a check stays collapsed until the
// learner opens it. Each check has an optional "your thinking" field (it goes
// to the teacher, never to the grader) and the confidence tap, shown once a
// draft exists. The close card promises only the checks that were actually
// set. "Check what I already know first" is offered at open and never
// prompted. Forecasts, receipts and routes stay in the inspector strip.
//
// Outages (review F11): when the teacher is unavailable the step that failed
// stays retryable. "Try again" resumes the saved lesson (an opening that failed
// after the lesson was saved carries its id, so it is resumed, never opened
// twice) or repeats an opening that saved nothing; after choosing "Use
// OpenRouter instead" the learner presses it to continue.

import { useCallback, useEffect, useMemo, useState } from "react";
import { api } from "../api/client";
import type { LessonFeedEntryDto, LessonTurnInput, LessonViewDto } from "../api/dto";
import { getCommandError } from "../errors";
import { COLOR, FONT_MONO, Faint } from "../components/term";
import { MarkdownMath } from "../render/MarkdownMath";

export type LessonEntry =
  | { kind: "open"; entry: "learning_object" | "reader_selection" | "new_topic"; learningObjectIds?: string[];
      selection?: { extractionId: string; spanIds: string[] }; title?: string;
      /** Teacher TE1b: the Start of Today's suggestion card (its decision and the lesson id its response recorded). */
      suggestion?: { decisionId: string; lessonId: string } }
  | { kind: "resume"; lessonId: string };

const TAP_LABELS = ["1", "2", "3", "4", "5"];
const CLOSE_WORDS: Record<string, string> = {
  goal_reached: "Lesson done.",
  learner_stop: "Lesson stopped.",
  budget: "This lesson reached its spending cap.",
  plan_unavailable: "The teacher became unavailable, so the lesson closed.",
  teacher_contract_failure: "The teacher kept getting its turns wrong, so the lesson closed.",
  protection_changed: "Some of what this lesson relied on is now kept for your exam or held out, so the lesson ended here.",
};

function dueWords(due: string): string {
  const day = new Date(`${due}T12:00:00`);
  if (Number.isNaN(day.getTime())) return due;
  const days = Math.max(0, Math.round((day.getTime() - Date.now()) / 86_400_000));
  return days <= 1 ? "in about a day" : `in about ${days} days`;
}

export function LessonScreen({
  entry,
  onClose,
  onQuickCheck,
  onError,
}: {
  entry: LessonEntry;
  onClose: () => void;
  /** "Check what I already know first" over the lesson's topics (the existing quick check). */
  onQuickCheck?: (learningObjectIds: string[]) => void;
  onError: (message: string) => void;
}) {
  const [view, setView] = useState<LessonViewDto | null>(null);
  const [busy, setBusy] = useState(false);
  const [unavailable, setUnavailable] = useState<string | null>(null);
  const [reply, setReply] = useState("");
  const [answer, setAnswer] = useState("");
  const [thinking, setThinking] = useState("");
  const [tap, setTap] = useState<number | null>(null);
  const [checkOpen, setCheckOpen] = useState(false);
  const [predictionAnswer, setPredictionAnswer] = useState("");
  /** What "Try again" sends after an outage (null: nothing to retry). */
  const [retry, setRetry] = useState<LessonTurnInput | null>(null);

  const run = useCallback(async (input: LessonTurnInput) => {
    setBusy(true);
    setUnavailable(null);
    setRetry(null);
    try {
      const next = await api.lessonTurn(input);
      setView(next);
      return next;
    } catch (error) {
      const err = getCommandError(error);
      const code = err?.code ?? "";
      const message = err?.message ?? String(error);
      const existing = ((err?.details ?? {}) as Record<string, unknown>).lesson_id;
      if (code === "lesson_exists" && typeof existing === "string" && existing) {
        // TE1b: a suggested lesson already opened (a second Start): show it, never another.
        void api.lessonView({ lessonId: existing }).then(setView).catch(() => undefined);
        return null;
      }
      if (code === "plan_unavailable" || code === "teacher_unavailable" || code === "provider_unavailable") {
        setUnavailable(message);
        const details = (err?.details ?? {}) as Record<string, unknown>;
        const saved = details.lesson_id ?? details.lessonId;
        const lessonId = typeof saved === "string" && saved ? saved : input.lessonId;
        if (lessonId) {
          // The step was saved: resume it, and show what the lesson holds so far.
          setRetry({ action: "resume", lessonId });
          void api.lessonView({ lessonId }).then(setView).catch(() => undefined);
        } else {
          // Nothing was saved (the opening never reached the teacher): repeat it.
          setRetry(input);
        }
      } else {
        onError(message);
      }
      return null;
    } finally {
      setBusy(false);
    }
  }, [onError]);

  useEffect(() => {
    let cancelled = false;
    if (entry.kind === "resume") {
      void api.lessonView({ lessonId: entry.lessonId }).then((next) => { if (!cancelled) setView(next); })
        .catch((error: unknown) => onError(getCommandError(error)?.message ?? String(error)));
    } else {
      void run({ action: "open", entry: entry.entry, learningObjectIds: entry.learningObjectIds ?? [],
                 ...(entry.selection ? { selection: entry.selection } : {}),
                 ...(entry.suggestion ? { origin: "router_suggestion" as const,
                                          suggestionDecisionId: entry.suggestion.decisionId,
                                          lessonId: entry.suggestion.lessonId } : {}) });
    }
    return () => { cancelled = true; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const lessonId = view?.lessonId;
  const openCheck = view?.openCheck ?? null;
  useEffect(() => {
    setAnswer("");
    setThinking("");
    setTap(null);
    setCheckOpen(false);
  }, [openCheck?.checkRef]);

  const send = useCallback(async () => {
    if (!lessonId || !reply.trim()) return;
    const text = reply.trim();
    setReply("");
    await run({ action: "reply", lessonId, text });
  }, [lessonId, reply, run]);

  const submitCheck = useCallback(async () => {
    if (!lessonId || !openCheck || !answer.trim()) return;
    await run({ action: "answer_check", lessonId, checkRef: openCheck.checkRef, answer: answer.trim(),
                ...(tap !== null ? { tap } : {}), ...(thinking.trim() ? { thinking: thinking.trim() } : {}) });
  }, [lessonId, openCheck, answer, tap, thinking, run]);

  const submitPrediction = useCallback(async () => {
    if (!lessonId || !predictionAnswer.trim()) return;
    const value = predictionAnswer.trim();
    setPredictionAnswer("");
    await run({ action: "answer_prediction", lessonId, answer: value });
  }, [lessonId, predictionAnswer, run]);

  const stop = useCallback(async () => {
    if (!lessonId) return;
    await run({ action: "stop", lessonId });
  }, [lessonId, run]);

  /** Ruling R1: a lesson ended by a protection change restarts as a fresh lesson with a fresh brief. */
  const startFresh = useCallback(async () => {
    const learningObjectIds = view?.learningObjectIds ?? [];
    if (!learningObjectIds.length) return;
    await run({ action: "open", entry: "learning_object", learningObjectIds });
  }, [view, run]);

  const feed = useMemo(() => view?.feed ?? [], [view]);
  const title = entry.kind === "open" ? entry.title : undefined;

  return (
    <div role="dialog" aria-label="Lesson" data-testid="lesson-screen"
         style={{ position: "fixed", inset: 0, background: COLOR.bg, zIndex: 40, display: "flex", flexDirection: "column" }}>
      <div style={{ display: "flex", alignItems: "center", gap: 12, padding: "10px 22px", borderBottom: `1px solid ${COLOR.border}` }}>
        <span style={{ fontFamily: FONT_MONO, color: COLOR.text, fontSize: 14 }}>
          Lesson{view?.goal ? ` · ${view.goal}` : title ? ` · ${title}` : ""}
        </span>
        <span style={{ flex: 1 }} />
        {view && !view.closed && onQuickCheck && view.feed.length <= 2 ? (
          <button type="button" data-testid="lesson-quick-check" disabled={busy}
                  onClick={() => onQuickCheck(view.quickCheck.learningObjectIds)}>
            Check what I already know first
          </button>
        ) : null}
        {view && !view.closed ? (
          <button type="button" onClick={() => void stop()} disabled={busy}>Stop the lesson</button>
        ) : null}
        <button type="button" onClick={onClose}>Close</button>
      </div>
      <div style={{ display: "flex", flex: 1, minHeight: 0 }}>
        <article style={{ flex: 1, overflowY: "auto", padding: "18px 32px", maxWidth: 820, lineHeight: 1.6 }}>
          {feed.map((item, index) => (
            <FeedEntry key={index} item={item} openCheckRef={openCheck?.checkRef ?? null} checkOpen={checkOpen}
                       onOpenCheck={() => setCheckOpen(true)} />
          ))}
          {view && view.closed && view.closeReason === "protection_changed" && view.learningObjectIds?.length ? (
            <div style={{ marginTop: 10 }}>
              <button type="button" data-testid="lesson-start-fresh" disabled={busy} onClick={() => void startFresh()}>
                Start a fresh lesson
              </button>
            </div>
          ) : null}
          {busy ? <Faint>The teacher is writing…</Faint> : null}
          {unavailable ? (
            <div role="status" data-testid="lesson-unavailable" style={{ color: COLOR.textDim }}>
              {unavailable}
              {retry ? (
                <div style={{ marginTop: 6 }}>
                  <button type="button" data-testid="lesson-retry" disabled={busy} onClick={() => void run(retry)}>
                    Try again
                  </button>
                </div>
              ) : null}
            </div>
          ) : null}
          {view && !view.closed && openCheck && checkOpen ? (
            <section data-testid="lesson-check-answer" style={{ borderTop: `1px solid ${COLOR.border}`, paddingTop: 10, marginTop: 10 }}>
              {openCheck.form === "choices" ? (
                <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
                  {openCheck.choices.map((choice, index) => (
                    <label key={index}>
                      <input type="radio" name="lesson-check" checked={answer === choice} onChange={() => setAnswer(choice)} />{" "}
                      {String.fromCharCode(65 + index)}. {choice}
                    </label>
                  ))}
                </div>
              ) : (
                <textarea aria-label="Your answer" value={answer} onChange={(e) => setAnswer(e.target.value)}
                          style={{ width: "100%", minHeight: 70 }} />
              )}
              <textarea aria-label="Your thinking (optional)" placeholder="your thinking (optional; the teacher reads it, the grader never does)"
                        value={thinking} onChange={(e) => setThinking(e.target.value)} style={{ width: "100%", minHeight: 40, marginTop: 6 }} />
              {answer.trim() ? (
                <div data-testid="lesson-tap" style={{ display: "flex", gap: 6, alignItems: "center", marginTop: 6 }}>
                  <Faint>How sure are you?</Faint>
                  {TAP_LABELS.map((label, index) => (
                    <button key={label} type="button" aria-pressed={tap === index + 1} onClick={() => setTap(index + 1)}>{label}</button>
                  ))}
                </div>
              ) : null}
              <button type="button" disabled={busy || !answer.trim()} onClick={() => void submitCheck()} style={{ marginTop: 8 }}>
                Submit answer
              </button>
            </section>
          ) : null}
          {view && !view.closed && view.openPrediction ? (
            <section data-testid="lesson-prediction-answer" style={{ marginTop: 10 }}>
              <input aria-label="Your prediction" value={predictionAnswer} onChange={(e) => setPredictionAnswer(e.target.value)}
                     style={{ width: "100%" }} />
              <button type="button" disabled={busy || !predictionAnswer.trim()} onClick={() => void submitPrediction()}>
                Say it
              </button>
            </section>
          ) : null}
          {view && !view.closed ? (
            <section style={{ marginTop: 14 }}>
              <textarea aria-label="Reply to the teacher" placeholder={openCheck ? "ask for help with the check…" : "reply…"}
                        value={reply} onChange={(e) => setReply(e.target.value)} style={{ width: "100%", minHeight: 50 }} />
              <button type="button" disabled={busy || !reply.trim()} onClick={() => void send()}>Send</button>
            </section>
          ) : null}
        </article>
        <aside data-testid="lesson-plan" style={{ width: 260, borderLeft: `1px solid ${COLOR.border}`, padding: "18px 16px", overflowY: "auto" }}>
          <Faint style={{ fontSize: 10, letterSpacing: "0.14em" }}>MAP</Faint>
          {(view?.plan ?? []).length === 0 ? <Faint>The map appears once the teacher plans the lesson.</Faint> : null}
          <ol style={{ paddingLeft: 18 }}>
            {(view?.plan ?? []).map((node) => (
              <li key={node.id} data-position={node.position}
                  style={{ color: node.position === "current" ? COLOR.text : node.position === "visited" ? COLOR.textDim : COLOR.textFaint,
                           fontWeight: node.position === "current" ? 600 : 400 }}>
                {node.statement ?? node.id}
              </li>
            ))}
          </ol>
          {view ? (
            <details style={{ marginTop: 16 }}>
              <summary><Faint>inspector</Faint></summary>
              <div style={{ fontFamily: FONT_MONO, fontSize: 11, color: COLOR.textFaint }}>
                <div>doctrine {view.inspector.doctrine}</div>
                <div>route {view.inspector.route ?? "–"} · {view.inspector.model ?? "–"}</div>
                <div>{view.inspector.forecasts.length} forecast(s)</div>
              </div>
            </details>
          ) : null}
        </aside>
      </div>
    </div>
  );
}

function FeedEntry({ item, openCheckRef, checkOpen, onOpenCheck }: {
  item: LessonFeedEntryDto; openCheckRef: string | null; checkOpen: boolean; onOpenCheck: () => void;
}) {
  switch (item.kind) {
    case "message":
      return (
        <div style={{ marginBottom: 14 }}>
          <MarkdownMath value={item.text} />
          {item.choices.length ? <Faint>{item.choices.join(" · ")}</Faint> : null}
        </div>
      );
    case "prediction":
      return (
        <div data-testid="lesson-prediction" style={{ margin: "10px 0", paddingLeft: 10, borderLeft: `2px solid ${COLOR.border}` }}>
          <Faint>Predict</Faint>
          <MarkdownMath value={item.prompt} />
        </div>
      );
    case "check": {
      const open = item.checkRef === openCheckRef;
      if (open && !checkOpen) {
        return (
          <button type="button" data-testid="lesson-check-collapsed" onClick={onOpenCheck} style={{ margin: "10px 0" }}>
            ▸ A check on this step (open it when you're ready)
          </button>
        );
      }
      return (
        <div data-testid="lesson-check" style={{ margin: "10px 0", padding: 10, border: `1px solid ${COLOR.border}` }}>
          <Faint>Check</Faint>
          <MarkdownMath value={item.question} />
        </div>
      );
    }
    case "learner":
      return (
        <div data-testid="lesson-learner" style={{ margin: "10px 0 10px 40px", padding: "8px 12px", border: `1px solid ${COLOR.border}`,
                                                  fontFamily: FONT_MONO, fontSize: 12 }}>
          {item.text}
        </div>
      );
    case "check_result":
      return (
        <div data-testid="lesson-check-result" style={{ margin: "6px 0 12px", color: COLOR.textDim }}>
          <strong>{item.result}</strong>
          {item.graderFeedback ? <div><MarkdownMath value={item.graderFeedback} /></div> : null}
          {item.answerLabel ? <Faint>{item.answerLabel}</Faint> : null}
        </div>
      );
    case "notice":
      return <div role="status" style={{ color: COLOR.textDim, margin: "8px 0" }}>{item.text}</div>;
    case "close":
      return (
        <div data-testid="lesson-close" style={{ marginTop: 18, padding: 12, border: `1px solid ${COLOR.border}` }}>
          <div style={{ fontWeight: 600 }}>{CLOSE_WORDS[item.reason] ?? "Lesson closed."}</div>
          {item.recap ? <MarkdownMath value={item.recap} /> : null}
          {item.delayedChecks.length ? (
            <ul>
              {item.delayedChecks.map((check, index) => (
                <li key={index}>
                  I&apos;ll ask you one question on {check.title ?? "this topic"}, on your own, {dueWords(check.due)}
                  {check.purpose === "transfer" ? " (in a new situation)" : ""}.
                </li>
              ))}
            </ul>
          ) : (
            <Faint>No later check could be set this time.</Faint>
          )}
        </div>
      );
  }
}
