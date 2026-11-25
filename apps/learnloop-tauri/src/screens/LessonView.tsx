// Teacher TE1: a lesson (spec_teacher_v1 §19), as the lesson screen and as a lesson window show it.
//
// Reader workbench RD9a (spec_reader_workbench_v2 §11.1): this is the lesson screen's content, extracted, and used
// by both: `frame="screen"` is the full-screen lesson as it always was (LessonScreen); `frame="window"` is the same
// lesson inside a desk's window or stack tab, with the window's lifecycle (§3.6): a paused window starts no turn,
// reads nothing and polls nothing until it is live again, and its activity listeners go through the window's hub.
// The window sets the colour variables to the paper's, so the same markup reads as a pad; display math is fitted
// there (a pad is narrower than the screen). A finished lesson reopened is its review: lesson.view replays what was
// recorded, with no model call and nothing new written, and no control that would start a turn.
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
//
// Reader RW5d P4b (spec_reader_show_me_figures_v1 §6.5): the teacher's visual
// lands inline in its turn, drawn by the Reader's FigureInline (grammar or
// sketch). Its own predictions are suppressed in a lesson (the teacher poses
// the prediction or the check): the lesson's figure controller has the
// predictions contract off, and the server sends none. No "not right?", no
// region and no rich version in a lesson; a figure that couldn't be built or
// isn't shown says so in one quiet line.
//
// Teacher TE2-log (spec_teacher_v1 §11.6): while the view says `activityLog`, the
// screen reports its own activity intervals (foreground with input, or not) to
// lesson.activity, before every lesson step, when the window hides and when the
// screen closes (lessonActivity.ts). Times only; logging never blocks a step.
//
// Teacher TE2 (spec_teacher_v1 §11.3, §11.5, §19): a quick question the teacher asks for is written while the
// learner reads ("Preparing a question on this…", with "Teach it anyway"); the screen checks back until it is
// ready, then it opens like any question on your own: no sources, no help, the reply box away, until it is
// answered. A lesson can start from what the learner types ("What do you want to learn?"): the topics it needs are
// listed, and each part nothing in their books covers is offered once ("Not in your books yet: … Add it as a
// topic?"); a topic added that way is taught from LearnLoop's model.

import { useCallback, useEffect, useMemo, useRef, useState, type CSSProperties, type ReactNode } from "react";
import { api } from "../api/client";
import { createLessonActivity, type LessonActivityTracker } from "./lessonActivity";
import type {
  FigureViewDto, LessonFeedEntryDto, LessonFigureStatus, LessonGoalDto, LessonTurnInput, LessonViewDto,
} from "../api/dto";
import { getCommandError } from "../errors";
import { COLOR, FONT_MONO, Faint } from "../components/term";
import { Waiting } from "../components/Waiting";
import { WAITING_COPY } from "../copy/waiting";
import { DIAGNOSIS_POLL_MS } from "../components/DiagnosisCard";
import { MarkdownMath } from "../render/MarkdownMath";
import { FigureInline } from "./reader/figures/FigureInline";
import { figurePlacementKey, type FiguresContract, type FiguresCtl } from "./reader/figures/useFigures";
import { useListenerHub, useWhenLive, useWindowPaused } from "./desks/lifecycle";
import { FitMath } from "./desks/fitMath";

export type LessonEntry =
  | { kind: "open"; entry: "learning_object" | "reader_selection" | "new_topic"; learningObjectIds?: string[];
      selection?: { extractionId: string; spanIds: string[]; blockIds?: string[] }; title?: string;
      /** Teacher TE1b: the Start of Today's suggestion card (its decision and the lesson id its response recorded). */
      suggestion?: { decisionId: string; lessonId: string };
      /** IH7 (the owner's decision 2): the "learn this" preference this lesson was asked for with. */
      preferenceId?: string;
      /** A lesson opened from a diagnostic check: its episode, so the brief carries what the check found. */
      probeEpisodeId?: string }
  | { kind: "resume"; lessonId: string }
  /** Teacher TE2: start from what the learner types. */
  | { kind: "typed" };

/** How often the screen checks back on a question being prepared (the diagnosis card's own interval, reused). */
export const PROBE_POLL_MS = DIAGNOSIS_POLL_MS;

const TAP_LABELS = ["1", "2", "3", "4", "5"];
const CLOSE_WORDS: Record<string, string> = {
  goal_reached: "Lesson finished.",
  learner_stop: "Lesson stopped.",
  budget: "This lesson reached its spending cap.",
  plan_unavailable: "The teacher became unavailable, so the lesson closed.",
  teacher_contract_failure: "The lesson couldn’t continue. Return to Path to choose what to study next.",
  protection_changed: "This lesson ended. Everything so far is saved; start a new lesson to continue.",
};

function dueWords(due: string): string {
  const day = new Date(`${due}T12:00:00`);
  if (Number.isNaN(day.getTime())) return due;
  const days = Math.max(0, Math.round((day.getTime() - Date.now()) / 86_400_000));
  return days <= 1 ? "in about a day" : `in about ${days} days`;
}

/** Where the lesson is shown: the full screen (its own place), or a desk's window or stack tab. */
export type LessonFrame = "screen" | "window";

export interface LessonViewProps {
  entry: LessonEntry;
  /** `kept`: the lesson is still open (Close never stops one), so the host can say where it is now. A window closes
   *  through its own head, so it passes none. */
  onClose?: (kept: boolean) => void;
  /** "Check what I already know first" over the lesson's topics (the existing quick check). */
  onQuickCheck?: (learningObjectIds: string[]) => void;
  /** TE2 landing ruling R2 (spec_teacher_v1 rev 5 §11.5): a typed goal's leftover offers "Look in my library"
   *  first, opening the Library search with its phrase, before "Create it". */
  onLookInLibrary?: (phrase: string) => void;
  /** A hand-off from a diagnostic check: an opening that fails for any reason (the teacher's route down, lessons
   *  switched off, a refusal) goes back to the caller, which opens the tutor instead of leaving this screen's retry. */
  onOpenFailed?: (message: string) => void;
  onError: (message: string) => void;
  /** Default "screen". */
  frame?: LessonFrame;
  /** Each lesson state shown (a window learns its lesson's id from the first: an opening has none before). */
  onView?: (view: LessonViewDto) => void;
  /** A window's "Start a fresh lesson" (ruling R1) opens the new lesson beside this one; without it a window, which
   *  replays this lesson, offers none. */
  onStartFresh?: (learningObjectIds: string[]) => void;
  /** Whether a step is in flight (a window's opening tab offers to let a failed opening go only once it is not). */
  onBusy?: (busy: boolean) => void;
  /** A desk window's way to the lesson screen for a quick question, settled when the screen closes (the owner's
   *  interim until RD7's administration guard: a quick question is never answered in a window). */
  onProbe?: () => Promise<void>;
  /** A window's opening turn goes through its host, which sends it once and shares it with any later view of the same
   *  opening (a window closed and brought back). Without it, the turn is sent here. */
  shareOpening?: (send: () => Promise<LessonViewDto>) => Promise<LessonViewDto>;
}

export function LessonView({
  entry,
  onClose,
  onQuickCheck,
  onLookInLibrary,
  onOpenFailed,
  onError,
  frame = "screen",
  onView,
  onStartFresh,
  onBusy,
  shareOpening,
  onProbe,
}: LessonViewProps) {
  const windowed = frame === "window";
  // Every read and step says where the lesson is shown: a window's never serves or answers a quick question.
  const framed = windowed ? { frame: "window" as const } : {};
  // The window's lifecycle (outside the desks: never paused, listeners straight on the window, as before).
  const paused = useWindowPaused();
  const pausedRef = useRef(paused);
  pausedRef.current = paused;
  const whenLive = useWhenLive();
  const hub = useListenerHub();
  const [view, setViewState] = useState<LessonViewDto | null>(null);
  // A recovery read a failed step asks for (the lesson that exists, the step that was saved): made only while the view
  // is mounted and live, so a closed, hidden or folded window reads nothing (a read can serve a ready question).
  const mounted = useRef(true);
  useEffect(() => () => { mounted.current = false; }, []);
  const [recover, setRecover] = useState<string | null>(null);
  const readWhenLive = useCallback((lessonId: string) => { if (mounted.current) setRecover(lessonId); }, []);
  const onViewRef = useRef(onView);
  onViewRef.current = onView;
  const setView = useCallback((next: LessonViewDto) => {
    setViewState(next);
    onViewRef.current?.(next);
  }, []);
  const [busy, setBusy] = useState(false);
  const onBusyRef = useRef(onBusy);
  onBusyRef.current = onBusy;
  useEffect(() => {
    onBusyRef.current?.(busy);
  }, [busy]);
  // Which wait `busy` is, so the waiting line says the true one (the goal lookup is not the teacher writing).
  const [busyFor, setBusyFor] = useState<"turn" | "goal" | "check">("turn");
  const [unavailable, setUnavailable] = useState<string | null>(null);
  const [reply, setReply] = useState("");
  // What the learner just sent (a reply, a prediction), shown in the thread until the lesson shows it: the box is
  // cleared at Send and a turn takes up to a minute or more, and without this the words vanished meanwhile.
  const [sent, setSent] = useState<string | null>(null);
  // How the last step ended when it returned nothing: "error" lost the step (its words go back in the box),
  // "unavailable" kept it for Try again.
  const lastFailure = useRef<"error" | "unavailable" | null>(null);
  const [answer, setAnswer] = useState("");
  const [thinking, setThinking] = useState("");
  const [tap, setTap] = useState<number | null>(null);
  const [checkOpen, setCheckOpen] = useState(false);
  const [predictionAnswer, setPredictionAnswer] = useState("");
  /** What "Try again" sends after an outage (null: nothing to retry). */
  const [retry, setRetry] = useState<LessonTurnInput | null>(null);
  /** TE2-log: the screen's activity intervals (null while the view doesn't ask for them). */
  const activity = useRef<LessonActivityTracker | null>(null);
  /** TE2: the quick question's answer, and the typed goal before the lesson opens. */
  const [probeAnswer, setProbeAnswer] = useState("");
  const [probeTap, setProbeTap] = useState<number | null>(null);
  const [goalText, setGoalText] = useState("");
  const [goal, setGoal] = useState<LessonGoalDto | null>(null);
  const [addTopics, setAddTopics] = useState<Record<string, boolean>>({});
  const [subjectId, setSubjectId] = useState<string>("");

  const run = useCallback(async (input: LessonTurnInput) => {
    setBusy(true);
    // An answer to a check or a probe is graded before the teacher writes: the wait says which.
    setBusyFor(input.action === "answer_check" || input.action === "answer_probe" ? "check" : "turn");
    setUnavailable(null);
    setRetry(null);
    lastFailure.current = null;
    // TE2-log: the intervals so far reach the sidecar before the step (a close's receipt counts them).
    activity.current?.flush();
    try {
      const next = input.action === "open" && shareOpening ? await shareOpening(() => api.lessonTurn({ ...input, ...framed })) : await api.lessonTurn({ ...input, ...framed });
      setView(next);
      return next;
    } catch (error) {
      const err = getCommandError(error);
      const code = err?.code ?? "";
      const message = err?.message ?? String(error);
      const existing = ((err?.details ?? {}) as Record<string, unknown>).lesson_id;
      if (code === "lesson_exists" && typeof existing === "string" && existing) {
        // TE1b: a suggested lesson already opened (a second Start): show it, never another.
        readWhenLive(existing);
        return null;
      }
      if (input.action === "open" && onOpenFailed) {
        onOpenFailed(message);
        return null;
      }
      if (code === "plan_unavailable" || code === "teacher_unavailable" || code === "provider_unavailable") {
        lastFailure.current = "unavailable";
        setUnavailable(message);
        const details = (err?.details ?? {}) as Record<string, unknown>;
        const saved = details.lesson_id ?? details.lessonId;
        // Only the sidecar's own word that the lesson was saved makes a resume possible. An opening's
        // `lessonId` is the id a suggestion's Start reserved, which names no lesson until the open
        // succeeds (codex review F2): its retry repeats the (idempotent) open.
        const lessonId = typeof saved === "string" && saved ? saved : input.action === "open" ? undefined : input.lessonId;
        if (lessonId) {
          // The sidecar says what Try again does: `repeat` when nothing of the failed step was recorded (an
          // Add whose topic check failed), so the same step is sent again; otherwise the recorded step is resumed.
          setRetry(details.retry === "repeat" && input.action !== "open" ? input : { action: "resume", lessonId });
          readWhenLive(lessonId);
        } else {
          // Nothing was saved (the opening never reached the teacher): repeat it.
          setRetry(input);
        }
      } else {
        lastFailure.current = "error";
        onError(message);
      }
      return null;
    } finally {
      setBusy(false);
    }
  }, [onError, onOpenFailed, shareOpening, readWhenLive]);
  useEffect(() => {
    if (!recover || paused) return;
    const lessonId = recover;
    setRecover(null);
    void api.lessonView({ lessonId, ...framed }).then((next) => { if (mounted.current) setView(next); }).catch(() => undefined);
  }, [recover, paused, setView]);

  /** Send what the learner wrote, keeping it on screen while the teacher writes. A step that failed outright puts it
   *  back in its box (unless something new was typed there); one kept for Try again stays shown. */
  const sendShown = useCallback(async (input: LessonTurnInput, text: string, restore: (text: string) => void) => {
    setSent(text);
    const next = await run(input);
    if (next || lastFailure.current === "error") setSent(null);
    if (!next && lastFailure.current === "error") restore(text);
  }, [run]);

  useEffect(() => {
    let cancelled = false;
    const start = () => {
    if (entry.kind === "typed") {
      // TE2: nothing opens until the learner says what they want to learn.
    } else if (entry.kind === "resume") {
      void api.lessonView({ lessonId: entry.lessonId, ...framed }).then((next) => {
        if (cancelled) return;
        setView(next);
        // A reply saved before a restart still waits for the teacher: Continue answers it.
        if (next.awaitingTeacher && !next.closed) void run({ action: "resume", lessonId: entry.lessonId });
      }).catch((error: unknown) => onError(getCommandError(error)?.message ?? String(error)));
    } else {
      void run({ action: "open", entry: entry.entry, learningObjectIds: entry.learningObjectIds ?? [],
                 ...(entry.selection ? { selection: entry.selection } : {}),
                 ...(entry.suggestion ? { origin: "router_suggestion" as const,
                                          suggestionDecisionId: entry.suggestion.decisionId,
                                          lessonId: entry.suggestion.lessonId } : {}),
                 ...(entry.preferenceId && !entry.suggestion ? { preferenceId: entry.preferenceId } : {}),
                 ...(entry.probeEpisodeId && !entry.suggestion ? { probeEpisodeId: entry.probeEpisodeId } : {}) });
    }
    };
    // A window opened while paused (a stack tab out of view, another desk) opens or reads its lesson only once it is
    // live: a paused window starts no turn. Outside the desks nothing is ever paused, so this starts at once.
    if (pausedRef.current) void whenLive().then(() => { if (!cancelled) start(); });
    else start();
    return () => { cancelled = true; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const lessonId = view?.lessonId;
  const openCheck = view?.openCheck ?? null;
  // A finished lesson reopened is its review: it records no new activity. One that closes while shown keeps its
  // tracker, so its last interval still reaches the sidecar.
  const [seenOpen, setSeenOpen] = useState(false);
  useEffect(() => { if (view && !view.closed) setSeenOpen(true); }, [view]);
  const activityLog = Boolean(view?.activityLog) && seenOpen;
  useEffect(() => {
    if (!lessonId || !activityLog) return;
    // A paused window is not in the foreground, whatever the page's focus.
    const inForeground = () => document.visibilityState === "visible" && document.hasFocus() && !pausedRef.current;
    const tracker = createLessonActivity({
      lessonId, foreground: inForeground(),
      send: (batch) => api.lessonActivity(batch),
    });
    activity.current = tracker;
    const onInput = () => tracker.input();
    const onForeground = () => tracker.foreground(inForeground());
    const inputs = ["keydown", "pointerdown", "wheel", "scroll"] as const;
    // Through the window's hub: in the desks only the active window hears input, and N windows never mean N
    // handlers on the page (spec §3.6).
    const removals = [
      ...inputs.map((name) => hub.listen("window", name, onInput, { capture: true, passive: true })),
      hub.listen("document", "visibilitychange", onForeground),
      hub.listen("window", "focus", onForeground),
      hub.listen("window", "blur", onForeground),
    ];
    return () => {
      for (const remove of removals) remove();
      tracker.stop();
      activity.current = null;
    };
  }, [lessonId, activityLog, hub]);
  // A window paused or live again changes whether the lesson is in the foreground.
  useEffect(() => {
    activity.current?.foreground(document.visibilityState === "visible" && document.hasFocus() && !paused);
  }, [paused]);
  useEffect(() => {
    setAnswer("");
    setThinking("");
    setTap(null);
    setCheckOpen(false);
  }, [openCheck?.checkRef]);
  const probe = view?.probe ?? null;
  // In a window a quick question only waits: it is answered on the lesson screen.
  const probeOpen = Boolean(probe && probe.status === "open" && !windowed);
  const probeWaiting = Boolean(probe && (probe.status === "waiting" || (probe.status === "open" && windowed)));
  useEffect(() => {
    setProbeAnswer("");
    setProbeTap(null);
  }, [probe?.probeRef]);
  useEffect(() => {
    // TE2: check back on a question being prepared (no model call: lesson.view), until it is ready.
    // A paused window polls nothing; live again, it checks back on the same question.
    if (!lessonId || !probe || probe.status !== "preparing" || busy || paused) return;
    const timer = window.setTimeout(() => {
      void api.lessonView({ lessonId, ...framed }).then(setView).catch(() => undefined);
    }, PROBE_POLL_MS);
    return () => window.clearTimeout(timer);
  }, [lessonId, probe, busy, paused]);

  const findGoal = useCallback(async () => {
    const text = goalText.trim();
    if (!text) return;
    setBusy(true);
    setBusyFor("goal");
    try {
      const found = await api.lessonGoal({ text });
      setGoal(found);
      setAddTopics({});
      setSubjectId(found.subjectId ?? found.subjects[0]?.subjectId ?? "");
    } catch (error) {
      onError(getCommandError(error)?.message ?? String(error));
    } finally {
      setBusy(false);
    }
  }, [goalText, onError]);

  const startTyped = useCallback(async () => {
    const text = goalText.trim();
    if (!text) return;
    const accepted = Object.entries(addTopics).filter(([, yes]) => yes).map(([phrase]) => phrase);
    await run({ action: "open", entry: "typed_goal", goalText: text, addTopics: accepted,
                ...(accepted.length && subjectId ? { subjectId } : {}) });
  }, [goalText, addTopics, subjectId, run]);

  const submitProbe = useCallback(async () => {
    if (!lessonId || !probe || !probeAnswer.trim()) return;
    await run({ action: "answer_probe", lessonId, probeRef: probe.probeRef, answer: probeAnswer.trim(),
                ...(probeTap !== null ? { tap: probeTap } : {}) });
  }, [lessonId, probe, probeAnswer, probeTap, run]);

  const teachAnyway = useCallback(async () => {
    if (!lessonId) return;
    await run({ action: "teach_anyway", lessonId });
  }, [lessonId, run]);

  const send = useCallback(async () => {
    if (!lessonId || !reply.trim()) return;
    const text = reply.trim();
    setReply("");
    await sendShown({ action: "reply", lessonId, text }, text, (lost) => setReply((box) => (box.trim() ? box : lost)));
  }, [lessonId, reply, sendShown]);

  const submitCheck = useCallback(async () => {
    if (!lessonId || !openCheck || !answer.trim()) return;
    await run({ action: "answer_check", lessonId, checkRef: openCheck.checkRef, answer: answer.trim(),
                ...(tap !== null ? { tap } : {}), ...(thinking.trim() ? { thinking: thinking.trim() } : {}) });
  }, [lessonId, openCheck, answer, tap, thinking, run]);

  const submitPrediction = useCallback(async () => {
    if (!lessonId || !predictionAnswer.trim()) return;
    const value = predictionAnswer.trim();
    setPredictionAnswer("");
    await sendShown({ action: "answer_prediction", lessonId, answer: value }, value,
                    (lost) => setPredictionAnswer((box) => (box.trim() ? box : lost)));
  }, [lessonId, predictionAnswer, sendShown]);

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
  // The lesson (a turn's reply, or the saved lesson read after an outage) shows the sent words itself now.
  useEffect(() => {
    if (sent !== null && feed.some((item) => item.kind === "learner" && item.text === sent)) setSent(null);
  }, [feed, sent]);
  const title = entry.kind === "open" ? entry.title : undefined;
  const look = windowed ? WINDOW_LOOK : SCREEN_LOOK;
  const heading = view?.goal ?? title ?? null;

  return (
    <LessonRoot windowed={windowed}>
      <div {...look.bar}>
        {windowed ? (
          <span className="ll-heading">{heading ?? "Lesson"}</span>
        ) : (
          <span style={{ fontFamily: FONT_MONO, color: COLOR.text, fontSize: 14 }}>
            Lesson{view?.goal ? ` · ${view.goal}` : title ? ` · ${title}` : ""}
          </span>
        )}
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
        {onClose ? <button type="button" onClick={() => onClose(Boolean(view && !view.closed))}>Close</button> : null}
      </div>
      <div {...look.body}>
        <article {...look.article}>
          {entry.kind === "typed" && !view ? (
            <section data-testid="lesson-goal-start">
              <label htmlFor="lesson-goal-text" style={{ display: "block", fontWeight: 600, marginBottom: 6 }}>
                What do you want to learn?
              </label>
              <textarea id="lesson-goal-text" aria-label="What do you want to learn?" value={goalText}
                        placeholder="e.g. how do I diagonalize a matrix, and when can't I"
                        onChange={(e) => { setGoalText(e.target.value); setGoal(null); }}
                        style={{ width: "100%", minHeight: 60 }} />
              <div style={{ marginTop: 6 }}>
                <button type="button" data-testid="lesson-goal-find" disabled={busy || !goalText.trim()}
                        onClick={() => void findGoal()}>
                  Find it in my books
                </button>
              </div>
              {goal && (goal.status === "unavailable" || goal.status === "no_inputs") ? (
                <div role="status" style={{ color: COLOR.textDim, marginTop: 8 }}>{goal.message}</div>
              ) : null}
              {goal && goal.topics.length ? (
                <div data-testid="lesson-goal-topics" style={{ marginTop: 10 }}>
                  <Faint>This lesson covers</Faint>
                  <ul>{goal.topics.map((topic) => <li key={topic.learningObjectId}>{topic.title}</li>)}</ul>
                </div>
              ) : null}
              {goal ? goal.unmatched.map((left) => (
                <div key={left.phrase} data-testid="lesson-goal-unmatched" style={{ marginTop: 8 }}>
                  Not in your books yet: “{left.phrase}”. Add it as a topic?{" "}
                  {onLookInLibrary ? (
                    <>
                      <button type="button" data-testid="lesson-goal-look-in-library"
                              onClick={() => onLookInLibrary(left.phrase)}>Look in my library</button>{" "}
                    </>
                  ) : null}
                  <button type="button" aria-pressed={addTopics[left.phrase] === true}
                          onClick={() => setAddTopics((prev) => ({ ...prev, [left.phrase]: true }))}>Create it</button>{" "}
                  <button type="button" aria-pressed={addTopics[left.phrase] === false}
                          onClick={() => setAddTopics((prev) => ({ ...prev, [left.phrase]: false }))}>No</button>
                  {addTopics[left.phrase] ? (
                    <Faint style={{ display: "block" }}>
                      It will be taught from LearnLoop&apos;s model, not from your books.
                    </Faint>
                  ) : null}
                </div>
              )) : null}
              {goal && Object.values(addTopics).some(Boolean) && !goal.subjectId && goal.subjects.length > 1 ? (
                <label style={{ display: "block", marginTop: 8 }}>
                  <Faint>Which subject is it part of?</Faint>{" "}
                  <select aria-label="Subject" value={subjectId} onChange={(e) => setSubjectId(e.target.value)}>
                    {goal.subjects.map((s) => <option key={s.subjectId} value={s.subjectId}>{s.title}</option>)}
                  </select>
                </label>
              ) : null}
              {goal && (goal.topics.length || Object.values(addTopics).some(Boolean)) ? (
                <div style={{ marginTop: 10 }}>
                  <button type="button" data-testid="lesson-goal-start-button" disabled={busy}
                          onClick={() => void startTyped()}>
                    Start the lesson
                  </button>
                </div>
              ) : null}
            </section>
          ) : null}
          {feed.map((item, index) => (
            <FeedEntry key={index} item={item} openCheckRef={openCheck?.checkRef ?? null} checkOpen={checkOpen}
                       onOpenCheck={() => setCheckOpen(true)} windowed={windowed} />
          ))}
          {sent !== null ? (
            <div data-testid="lesson-learner-sent" style={{ margin: "10px 0 10px 40px", padding: "8px 12px", border: `1px solid ${COLOR.border}`,
                                                       fontFamily: FONT_MONO, fontSize: 12 }}>
              {sent}
              <Faint style={{ display: "block", marginTop: 2 }}>{busy ? "Sending…" : "Your reply"}</Faint>
            </div>
          ) : null}
          {view && view.closed && view.closeReason === "protection_changed" && view.learningObjectIds?.length
            && (!windowed || onStartFresh) ? (
            <div style={{ marginTop: 10 }}>
              <button type="button" data-testid="lesson-start-fresh" disabled={busy}
                      onClick={() => (windowed && onStartFresh ? onStartFresh(view.learningObjectIds ?? []) : void startFresh())}>
                Start a fresh lesson
              </button>
            </div>
          ) : null}
          {view && !view.closed && probe && probe.status === "preparing" ? (
            <section data-testid="lesson-probe-preparing" role="status" style={{ margin: "10px 0" }}>
              <Faint>{probe.label}</Faint>
              {probe.teachAnyway ? (
                <div style={{ marginTop: 6 }}>
                  <button type="button" data-testid="lesson-teach-anyway" disabled={busy} onClick={() => void teachAnyway()}>
                    Teach it anyway
                  </button>
                </div>
              ) : null}
            </section>
          ) : null}
          {view && !view.closed && probe && probeWaiting ? (
            <section data-testid="lesson-probe-waiting" role="status" style={{ margin: "10px 0" }}>
              <Faint>A quick question is waiting · it is asked on the lesson screen, on your own.</Faint>
              {onProbe && lessonId ? (
                <div style={{ marginTop: 6 }}>
                  <button type="button" data-testid="lesson-probe-screen" disabled={busy}
                          onClick={() => void onProbe().then(() => readWhenLive(lessonId))}>
                    Answer it on the lesson screen
                  </button>
                </div>
              ) : null}
            </section>
          ) : null}
          {view && !view.closed && probe && probeOpen ? (
            <section data-testid="lesson-probe" style={{ margin: "10px 0", padding: 10, border: `1px solid ${COLOR.border}` }}>
              <Faint>{probe.label}</Faint>
              <Prose windowed={windowed} value={probe.question ?? ""} />
              <Faint style={{ display: "block", marginTop: 4 }}>On your own: no notes or help for this one.</Faint>
              <textarea aria-label="Your answer to the question" value={probeAnswer}
                        onChange={(e) => setProbeAnswer(e.target.value)} style={{ width: "100%", minHeight: 70, marginTop: 6 }} />
              {probeAnswer.trim() ? (
                <div data-testid="lesson-probe-tap" style={{ display: "flex", gap: 6, alignItems: "center", marginTop: 6 }}>
                  <Faint>How sure are you?</Faint>
                  {TAP_LABELS.map((label, index) => (
                    <button key={label} type="button" aria-pressed={probeTap === index + 1}
                            onClick={() => setProbeTap(index + 1)}>{label}</button>
                  ))}
                </div>
              ) : null}
              <button type="button" data-testid="lesson-probe-submit" disabled={busy || !probeAnswer.trim()}
                      onClick={() => void submitProbe()} style={{ marginTop: 8 }}>
                Submit answer
              </button>
            </section>
          ) : null}
          {busy ? (
            // A lesson turn took 11 to 83 s in the walks; finding a typed goal in the books is a lookup, not the teacher.
            busyFor === "goal"
              ? <Waiting testId="lesson-wait" line={WAITING_COPY.lookingInBooks} />
              : busyFor === "check"
                ? <Waiting testId="lesson-wait" line="Checking your answer…" later={WAITING_COPY.teacherWritingLater} />
                : <Waiting testId="lesson-wait" line={WAITING_COPY.teacherWriting} later={WAITING_COPY.teacherWritingLater} />
          ) : null}
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
              <textarea aria-label="Your thinking (optional)" placeholder="Your thinking is optional. The teacher can use it. Only your answer is graded."
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
          {view && !view.closed && !probeOpen && !probeWaiting ? (
            <section style={{ marginTop: 14 }}>
              <textarea aria-label="Reply to the teacher" placeholder={openCheck ? "ask for help with the check…" : "reply…"}
                        value={reply} onChange={(e) => setReply(e.target.value)} style={{ width: "100%", minHeight: 50 }} />
              <button type="button" disabled={busy || !reply.trim()} onClick={() => void send()}>Send</button>
            </section>
          ) : null}
        </article>
        <aside data-testid="lesson-plan" {...look.plan}>
          <Faint style={{ fontSize: 10, letterSpacing: "0.14em" }}>Lesson outline</Faint>
          {(view?.plan ?? []).length === 0 ? <Faint>The outline appears after the teacher plans the lesson.</Faint> : null}
          <ol style={{ paddingLeft: 18 }}>
            {(view?.plan ?? []).map((node, index) => (
              <li key={node.id} data-position={node.position}
                  style={{ color: node.position === "current" ? COLOR.text : node.position === "visited" ? COLOR.textDim : COLOR.textFaint,
                           fontWeight: node.position === "current" ? 600 : 400 }}>
                {node.statement ?? `Lesson step ${index + 1}`}
              </li>
            ))}
          </ol>
          {view ? (
            <details style={{ marginTop: 16 }}>
              <summary><Faint>How this lesson was made</Faint></summary>
              <div style={{ fontFamily: FONT_MONO, fontSize: 11, color: COLOR.textFaint }}>
                <div>Teaching rules · {view.inspector.doctrine}</div>
                <div>AI service and model · {view.inspector.route ?? "–"} · {view.inspector.model ?? "–"}</div>
                <div>Learning estimates · {view.inspector.forecasts.length}</div>
              </div>
            </details>
          ) : null}
        </aside>
      </div>
    </LessonRoot>
  );
}

/** The screen is a full-screen dialog; a window's lesson fills its window or tab (the window owns its place). */
function LessonRoot({ windowed, children }: { windowed: boolean; children: ReactNode }) {
  if (windowed) return <section className="desk-lesson" aria-label="Lesson" data-testid="lesson-view">{children}</section>;
  return (
    <div role="dialog" aria-label="Lesson" data-testid="lesson-screen"
         style={{ position: "fixed", inset: 0, background: COLOR.bg, zIndex: 40, display: "flex", flexDirection: "column" }}>
      {children}
    </div>
  );
}

type Look = Record<"bar" | "body" | "article" | "plan", { style?: CSSProperties; className?: string }>;
/** The lesson screen's layout, as it always was. */
const SCREEN_LOOK: Look = {
  bar: { style: { display: "flex", alignItems: "center", gap: 12, padding: "10px 22px", borderBottom: `1px solid ${COLOR.border}` } },
  body: { style: { display: "flex", flex: 1, minHeight: 0 } },
  article: { style: { flex: 1, overflowY: "auto", padding: "18px 32px", maxWidth: 820, lineHeight: 1.6 } },
  plan: { style: { width: 260, borderLeft: `1px solid ${COLOR.border}`, padding: "18px 16px", overflowY: "auto" } },
};
/** A window's: one column (a pad is too narrow for the map beside the lesson), styled by the desk's sheet. */
const WINDOW_LOOK: Look = {
  bar: { className: "ll-bar" },
  body: { className: "ll-body" },
  article: { className: "ll-article" },
  plan: { className: "ll-plan" },
};

/** The lesson's Markdown and math; in a window display math is fitted to the pad's width, never clipped. */
function Prose({ value, windowed }: { value: string; windowed: boolean }) {
  if (!windowed) return <MarkdownMath value={value} />;
  return <FitMath><MarkdownMath value={value} /></FitMath>;
}

/** Reader RW5d P4b: what a lesson figure that isn't drawn says (code-owned words). */
export const LESSON_FIGURE_COPY: Readonly<Record<Exclude<LessonFigureStatus, "shown">, string>> = Object.freeze({
  failed: "Couldn’t make a figure for this step. You can continue the lesson.",
  withheld: "No figure for this step: it would give an answer away, or its passage is held out now.",
  unavailable: "The figure model isn’t available right now, so this step has no figure.",
});

/** The lesson's figure contract: no predictions (the teacher poses them), no region, no "not right?". */
export const LESSON_FIGURE_CONTRACT: FiguresContract = Object.freeze({ predictions: false, region: false, revisions: false });

/** One lesson figure's controller: drawn and expanded in place, nothing requested, predicted or revised. */
function useLessonFigureCtl(figure: FigureViewDto): FiguresCtl {
  const [expandedKey, setExpandedKey] = useState<string | null>(figurePlacementKey(figure));
  return useMemo<FiguresCtl>(() => ({
    enabled: true,
    contract: LESSON_FIGURE_CONTRACT,
    figures: [figure],
    pending: [],
    expandedKey,
    setExpanded: (target) => setExpandedKey(target ? figurePlacementKey(target) : null),
    request: async () => "skipped",
    revise: () => undefined,
    predict: async () => null,
    explain: async () => null,
    under: () => ({ figures: [], pending: [], richPending: [], followed: [] }),
    followed: [],
    follow: async () => false,
    richPending: [],
    cancelRich: () => undefined,
    retryRich: () => undefined,
    manimOptIn: null,
    optInSpanId: null,
    answerManimOptIn: () => undefined,
  }), [figure, expandedKey]);
}

function LessonFigure({ figure }: { figure: FigureViewDto }) {
  // Suppressed in a lesson, whatever the figure carries (the server sends none; belt and braces).
  const shown = useMemo(() => ({ ...figure, predictions: [], fuller: null }), [figure]);
  const ctl = useLessonFigureCtl(shown);
  return <FigureInline figure={shown} ctl={ctl} />;
}

function FeedEntry({ item, openCheckRef, checkOpen, onOpenCheck, windowed }: {
  item: LessonFeedEntryDto; openCheckRef: string | null; checkOpen: boolean; onOpenCheck: () => void; windowed: boolean;
}) {
  switch (item.kind) {
    case "message":
      return (
        <div style={{ marginBottom: 14 }}>
          <Prose windowed={windowed} value={item.text} />
          {item.choices.length ? <Faint>{item.choices.join(" · ")}</Faint> : null}
        </div>
      );
    case "prediction":
      return (
        <div data-testid="lesson-prediction" style={{ margin: "10px 0", paddingLeft: 10, borderLeft: `2px solid ${COLOR.border}` }}>
          <Faint>Predict</Faint>
          <Prose windowed={windowed} value={item.prompt} />
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
          <Prose windowed={windowed} value={item.question} />
        </div>
      );
    }
    case "learner":
      return (
        <div data-testid="lesson-learner" style={{ margin: "10px 0 10px 40px", padding: "8px 12px", border: `1px solid ${COLOR.border}`,
                                                  fontFamily: FONT_MONO, fontSize: 12 }}>
          {item.text}
          {/* An answer kept when the lesson's spending limit stopped its grading says it didn't count. */}
          {item.note ? <div data-testid="lesson-learner-note" style={{ color: COLOR.textDim, marginTop: 4 }}>{item.note}</div> : null}
        </div>
      );
    case "check_result":
      return (
        <div data-testid="lesson-check-result" style={{ margin: "6px 0 12px", color: COLOR.textDim }}>
          <strong>{item.result}</strong>
          {item.graderFeedback ? <div><Prose windowed={windowed} value={item.graderFeedback} /></div> : null}
          {item.answerLabel ? <Faint>{item.answerLabel}</Faint> : null}
        </div>
      );
    case "probe_question":
      return (
        <div data-testid="lesson-probe-question" style={{ margin: "10px 0", padding: 10, border: `1px solid ${COLOR.border}` }}>
          <Faint>A quick question</Faint>
          <Prose windowed={windowed} value={item.question} />
        </div>
      );
    case "probe_result":
      return (
        <div data-testid="lesson-probe-result" style={{ margin: "6px 0 12px", color: COLOR.textDim }}>
          <strong>{item.result}</strong>
          {item.graderFeedback ? <div><Prose windowed={windowed} value={item.graderFeedback} /></div> : null}
        </div>
      );
    case "notice":
      return <div role="status" style={{ color: COLOR.textDim, margin: "8px 0" }}>{item.text}</div>;
    case "figure":
      return (
        <div data-testid="lesson-figure" data-status={item.status} style={{ margin: "6px 0 14px" }}>
          {item.status === "shown" && item.figure ? (
            <LessonFigure figure={item.figure} />
          ) : (
            <Faint>{LESSON_FIGURE_COPY[item.status === "shown" ? "withheld" : item.status] ?? LESSON_FIGURE_COPY.failed}</Faint>
          )}
        </div>
      );
    case "close":
      return (
        <div data-testid="lesson-close" style={{ marginTop: 18, padding: 12, border: `1px solid ${COLOR.border}` }}>
          <div style={{ fontWeight: 600 }}>{CLOSE_WORDS[item.reason] ?? "Lesson closed."}</div>
          {item.recap ? <Prose windowed={windowed} value={item.recap} /> : null}
          {item.delayedChecks.length ? (
            <ul>
              {item.delayedChecks.map((check, index) => (
                <li key={index}>
                  A cold check comes {dueWords(check.due)}. Answer it on your own{check.purpose === "transfer" ? ", in a new situation" : ""}.
                </li>
              ))}
            </ul>
          ) : (
            <Faint>No later cold check could be set this time.</Faint>
          )}
        </div>
      );
  }
}
