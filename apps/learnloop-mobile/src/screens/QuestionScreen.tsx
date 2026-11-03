import { useCallback, useEffect, useRef, useState } from "react";
import type { AttemptResultDto, CommandError, PracticeItemDetail, SessionSnapshot } from "@desktop/api/dto";
import { MarkdownMath } from "@desktop/render/MarkdownMath";
import { MathLiveEditor } from "@desktop/render/MathLiveEditor";
import { committedAttempt } from "../api/http";
import { phone, type SubmitInput } from "../api/phone";
import { phoneAttemptType } from "../util/attemptType";
import { newUlid } from "../util/ulid";
import {
  clearQuestionDraft,
  NO_ASSIST,
  readQuestionDraft,
  rememberPendingSubmit,
  writeQuestionDraft,
  type DraftAssist,
  type SubmitOutcome
} from "../store/sessionCache";
import { RemoteImageAsLink } from "../components/RemoteImageAsLink";

/** §3.4: plain LaTeX entry with a small bar of common commands; a real math keyboard is later. */
const SYMBOLS = ["$", "^{}", "_{}", "\\frac{}{}", "\\sqrt{}", "\\sum", "\\int", "\\infty", "\\pi", "\\theta", "\\lambda", "\\le", "\\ge", "\\ne", "\\to"];
const DRAFT_DEBOUNCE_MS = 800;

export interface QuestionTarget {
  readonly practiceItemId: string;
  readonly schedulerCandidateId: string | null;
  /** A draft the checkpoint holds for this item. */
  readonly restored?: { answer: string; submissionId: string | null; stuck: boolean; assist: DraftAssist } | null;
}

/** Into the focused editor at the caret; at the end of the answer if it isn't focused. */
function insertSymbol(symbol: string, append: (text: string) => void): void {
  const editor = document.activeElement;
  const inserted =
    editor instanceof HTMLElement && editor.isContentEditable && typeof document.execCommand === "function"
      ? document.execCommand("insertText", false, symbol)
      : false;
  if (!inserted) append(symbol);
}

export const GRADING_DOWN = "AI grading is unavailable; your answer is saved. Retry later or finish on the desktop.";

/** What this screen opens on: its own copy if it has one, else the checkpoint's draft, else nothing. */
function openedDraft(sessionId: string, target: QuestionTarget) {
  const own = readQuestionDraft(sessionId, target.practiceItemId);
  if (own) return { ...own, schedulerCandidateId: own.schedulerCandidateId ?? target.schedulerCandidateId, own: true };
  const restored = target.restored;
  return {
    answer: restored?.answer ?? "",
    stuck: restored?.stuck ?? false,
    submissionId: restored?.submissionId ?? newUlid(),
    schedulerCandidateId: target.schedulerCandidateId,
    assist: restored?.assist ?? NO_ASSIST,
    sentInput: null as SubmitInput | null,
    // A key that came with the checkpoint may have a job or an attempt behind it.
    outcome: (restored?.submissionId ? "unknown" : "none") as SubmitOutcome,
    own: false
  };
}

export function QuestionScreen({
  session,
  target,
  frozen,
  onFeedback,
  onWaiting,
  onDesktopOnly,
  onSkipped,
  onBack,
  onError
}: {
  session: SessionSnapshot;
  target: QuestionTarget;
  /** The session moved to another device: nothing here writes (§6.5). */
  frozen: boolean;
  onFeedback: (attemptId: string, practiceItemId: string) => void;
  /** The host is already working on this key: wait for it there, not here. */
  onWaiting: (submissionId: string, practiceItemId: string) => void;
  onDesktopOnly: (practiceItemId: string) => void;
  /** True once the host has recorded it. A refusal is the App's to report. */
  onSkipped: (practiceItemId: string) => Promise<boolean>;
  onBack: () => void;
  onError: (error: unknown) => void;
}) {
  const { practiceItemId } = target;
  const sessionId = session.sessionId;
  const [opened] = useState(() => openedDraft(session.sessionId, target));
  const { schedulerCandidateId, assist } = opened;
  const [item, setItem] = useState<PracticeItemDetail | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [probeActive, setProbeActive] = useState(false);
  const [loadRevision, setLoadRevision] = useState(0);
  const [answer, setAnswer] = useState(opened.answer);
  const [stuck, setStuck] = useState(opened.stuck);
  const [submitting, setSubmitting] = useState(false);
  const [skipping, setSkipping] = useState(false);
  const [failure, setFailure] = useState<CommandError | null>(null);
  const submissionId = useRef(opened.submissionId);
  const sentInput = useRef<SubmitInput | null>(opened.sentInput);
  const outcome = useRef<SubmitOutcome>(opened.outcome);
  // A skip on its way ends this draft if it lands: no save may put the draft back meanwhile (F10).
  const skipInFlight = useRef(false);
  const shownAt = useRef(Date.now());
  // Its own copy may hold what never reached the checkpoint, or the checkpoint may have moved on to
  // another item since. A request already sent settles that at the submit.
  const dirty = useRef(opened.own && !opened.sentInput);
  const latest = useRef({ answer, stuck, frozen, ready: false });
  latest.current = { answer, stuck, frozen, ready: item !== null && !probeActive };

  /** The phone's copy of all this, written as it changes. */
  function remember(next: { answer?: string; stuck?: boolean } = {}) {
    writeQuestionDraft({
      sessionId,
      practiceItemId,
      answer: next.answer ?? latest.current.answer,
      stuck: next.stuck ?? latest.current.stuck,
      submissionId: submissionId.current,
      schedulerCandidateId,
      assist,
      sentInput: sentInput.current,
      outcome: outcome.current
    });
  }

  useEffect(() => {
    let cancelled = false;
    setLoadError(null);
    // The serve, and the serve event: committing a presentation is what the desktop's screen does
    // too (§6.4). Only an inactive contract means ordinary practice.
    Promise.all([phone.getPracticeItem(practiceItemId, sessionId), phone.getProbeContract(practiceItemId, sessionId)])
      .then(([detail, contract]) => {
        if (cancelled) return;
        setItem(detail);
        setProbeActive(Boolean(contract.active));
        shownAt.current = Date.now();
      })
      .catch((error: CommandError) => {
        if (cancelled) return;
        if (error.code === "desktop_only") {
          onDesktopOnly(practiceItemId);
          return;
        }
        onError(error);
        setLoadError(error.message);
      });
    return () => {
      cancelled = true;
    };
    // One load per item and per retry.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [practiceItemId, sessionId, loadRevision]);

  const saveDraft = useCallback(async () => {
    if (!dirty.current || skipInFlight.current || latest.current.frozen || !latest.current.ready) return;
    dirty.current = false;
    try {
      await phone.saveDraft({
        sessionId,
        practiceItemId,
        answerMd: latest.current.answer,
        submissionId: submissionId.current,
        schedulerCandidateId,
        // Each save replaces the count, and the flags live under the key they were set with.
        hintsUsed: assist.hintsUsed,
        ...(assist.planPresentationId ? { planPresentationId: assist.planPresentationId } : {}),
        ...(assist.firstHintProgress ? { firstHintProgress: assist.firstHintProgress } : {}),
        ...(assist.hintSeen ? { hintSeen: true } : {}),
        ...(assist.pageSeen ? { pageSeen: true } : {}),
        ...(latest.current.stuck ? { declaredStuck: true } : {})
      });
    } catch (error) {
      dirty.current = true;
      throw error;
    }
  }, [assist, practiceItemId, schedulerCandidateId, sessionId]);

  useEffect(() => {
    if (!item || probeActive) return undefined;
    const timer = window.setTimeout(() => void saveDraft().catch(onError), DRAFT_DEBOUNCE_MS);
    return () => window.clearTimeout(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [answer, stuck, item, probeActive, saveDraft]);

  // Leaving the screen is no reason to lose the last 800 ms of typing.
  const flushOnLeave = useRef(() => undefined as void);
  flushOnLeave.current = () => void saveDraft().catch(onError);
  useEffect(() => () => flushOnLeave.current(), []);

  function edit(next: string) {
    setFailure(null);
    dirty.current = true;
    setAnswer(next);
    remember({ answer: next });
  }

  async function finish(attemptId: string, key: string) {
    // What was typed since is not this attempt's, and a flush on the way out would put it back.
    dirty.current = false;
    rememberPendingSubmit(null);
    clearQuestionDraft(sessionId, practiceItemId);
    await phone.acknowledge(sessionId, practiceItemId, key).catch(() => undefined);
    onFeedback(attemptId, practiceItemId);
  }

  /**
   * The key's last request may have reached the host. Ask before sending anything under it or
   * under another: true means the host had it, and the screen has moved on (F2). This read is the
   * only thing that settles a key: a submit's own error may be the job's end or a refusal that never
   * reached it, and the two look the same from here (a lost response, then host_busy on each retry).
   * An error here sends nothing, and the question stays as it is.
   */
  async function settledByTheHost(): Promise<boolean> {
    const key = submissionId.current;
    const status = await phone.submissionStatus(key);
    if (status.state === "completed") {
      await finish((status.result as AttemptResultDto).attemptId, key);
      return true;
    }
    if (status.state === "recorded" && status.attempt_id) {
      await finish(status.attempt_id, key);
      return true;
    }
    if (status.state === "accepted" || status.state === "running") {
      dirty.current = false;
      onWaiting(key, practiceItemId);
      return true;
    }
    outcome.current = status.state === "failed" ? "failed" : "none";
    remember();
    return false;
  }

  function nextRequest(key: string, currentItem: PracticeItemDetail): SubmitInput {
    // The desktop's count (`answerHints`): the authored reveals and one for the book. What the server
    // counts itself (its own hints, an earlier attempt's help) stays out of it.
    const hints = assist.hintsUsed + (assist.pageSeen ? 1 : 0);
    return {
      sessionId,
      practiceItemId,
      answerMd: latest.current.answer,
      attemptType: phoneAttemptType(currentItem.attemptTypesAllowed, hints),
      submissionId: key,
      latencySeconds: Math.round((Date.now() - shownAt.current) / 1000),
      schedulerCandidateId,
      assessmentContractVersionId: currentItem.assessmentContractVersionId,
      hintsUsed: hints,
      authoredHints: assist.hintsUsed,
      bookCounted: assist.pageSeen,
      ...(assist.planPresentationId ? { planPresentationId: assist.planPresentationId } : {}),
      ...(assist.firstHintProgress ? { firstHintProgress: assist.firstHintProgress } : {}),
      ...(latest.current.stuck ? { declaredStuck: true } : {})
    };
  }

  async function submit() {
    if (!item || submitting) return;
    setSubmitting(true);
    setFailure(null);
    let sending = false;
    try {
      if (outcome.current === "unknown") {
        if (await settledByTheHost()) return;
        // Whatever it was, the checkpoint gets this draft again before the request goes.
        dirty.current = true;
      }
      const sent = sentInput.current;
      const changed = sent !== null && (sent.answerMd !== latest.current.answer || Boolean(sent.declaredStuck) !== latest.current.stuck);
      if (outcome.current === "failed" && (changed || sent === null)) {
        // That key's job is over and its params are not these, so this is a new request. Short of
        // that, §6.3 compares a retry's params, so a retry resends the same one, field for field.
        submissionId.current = newUlid();
        sentInput.current = null;
        outcome.current = "none";
        dirty.current = true;
      } else if (changed) {
        // Nothing of the old request is on the host, so its key is free. If it still arrives, the
        // new one is a typed conflict and not a second grade.
        sentInput.current = null;
      }
      const key = submissionId.current;
      // The retry key is durable before grading begins, so a dead phone or host recovers this attempt.
      await saveDraft();
      const input = sentInput.current ?? nextRequest(key, item);
      sentInput.current = input;
      outcome.current = "unknown";
      remember();
      sending = true;
      const result: AttemptResultDto = await phone.submitAttempt(input, {
        // A closed or killed app finds its way back from here (A4).
        onAccepted: (job) => rememberPendingSubmit({ jobId: job.jobId, submissionId: key, sessionId, practiceItemId })
      });
      await finish(result.attemptId, key);
    } catch (error) {
      rememberPendingSubmit(null);
      const command = error as CommandError;
      // The outcome stays `unknown`, whatever the error says. A conflict does say one thing: the key
      // belongs to some other request, so resending this one could only conflict again.
      if (sending && command.code === "submission_conflict") {
        sentInput.current = null;
        remember();
      }
      // The attempt is in; only its completion's receipt is missing, and the host goes on trying.
      const committed = committedAttempt(error);
      if (committed) {
        await finish(committed, submissionId.current);
        return;
      }
      // The App's banner says where the session went; this screen has nothing to add.
      if (command.code === "session_moved") {
        onError(error);
      } else {
        setFailure(command);
        // A desktop gone away also has to show on the shell; the rest is said here, once.
        if (command.code === "desktop_offline") onError(error);
      }
    } finally {
      setSubmitting(false);
    }
  }

  async function skip() {
    if (skipInFlight.current) return;
    skipInFlight.current = true;
    setSkipping(true);
    // A skip forgets the key, and reopening would then mint another over a job that may still land.
    let skipped = false;
    try {
      skipped = (outcome.current === "unknown" && (await settledByTheHost())) || (await onSkipped(practiceItemId));
    } catch (error) {
      onError(error);
    }
    // Landed, it stays set: the skip ended this draft, and a flush on the way out would put it back.
    if (skipped) return;
    skipInFlight.current = false;
    setSkipping(false);
    // The question stays open, so what the skip held back is due now.
    void saveDraft().catch(onError);
  }

  if (loadError) {
    return (
      <div className="main">
        <p className="bad" role="alert">{loadError}</p>
        <div className="row">
          <button className="primary" type="button" onClick={() => setLoadRevision((value) => value + 1)}>Try again</button>
          <button className="plain" type="button" onClick={onBack}>Back</button>
        </div>
      </div>
    );
  }
  if (!item) return <div className="main"><p className="dim">Opening…</p></div>;
  // A serve's honest label when its cold check could not be taken (`queue.eligibility_dto`).
  const eligibilityMessage = (item as unknown as { eligibility?: { message?: string | null } }).eligibility?.message;
  if (probeActive) {
    // §6.4: the serve is committed and the check waits on the desktop; no skip is recorded.
    return (
      <div className="main">
        <h1>{item.learningObjectTitle}</h1>
        <p className="banner" role="status">This is a diagnostic check. Continue it on the desktop.</p>
        <div className="row">
          <button className="primary" type="button" onClick={() => onDesktopOnly(practiceItemId)}>Next</button>
        </div>
      </div>
    );
  }
  return (
    <div className="main">
      <h1>{item.learningObjectTitle}</h1>
      {item.intentCheck?.banner ? <p className="banner">{item.intentCheck.banner}</p> : null}
      {eligibilityMessage ? <p className="dim">{eligibilityMessage}</p> : null}
      {item.presentation.blocks.map((block, index) => (
        <div key={`${block.kind}:${index}`}>
          {block.label ? <div className="dim">{block.label}</div> : null}
          <div className="markdown"><MarkdownMath value={block.markdown} components={RemoteImageAsLink} /></div>
        </div>
      ))}
      <div className="symbols" aria-label="Math symbols">
        {SYMBOLS.map((symbol) => (
          <button
            key={symbol}
            type="button"
            disabled={submitting || skipping || frozen}
            // Keep the caret in the editor.
            onPointerDown={(event) => event.preventDefault()}
            onMouseDown={(event) => event.preventDefault()}
            onClick={() => insertSymbol(symbol, (text) => edit(latest.current.answer + text))}
          >
            {symbol}
          </button>
        ))}
      </div>
      <MathLiveEditor
        value={answer}
        onChange={edit}
        disabled={submitting || skipping || frozen}
        ariaLabel="Your answer"
        placeholder={stuck ? "Write what you can, or what's confusing you." : "Your answer. $…$ for math."}
      />
      {failure ? (
        <p className="bad" role="alert">{failure.code === "grading_fallback_required" ? GRADING_DOWN : failure.message}</p>
      ) : null}
      {submitting ? <p className="dim" role="status">Grading. You can leave; the result will be here when you come back.</p> : null}
      <div className="row">
        <button className="primary" type="button" disabled={submitting || skipping || frozen || (!stuck && !answer.trim())} onClick={() => void submit()}>
          {failure?.retryable ? "Try again" : "Submit"}
        </button>
        {stuck ? null : (
          <button className="plain" type="button" disabled={submitting || skipping || frozen} onClick={() => { dirty.current = true; setStuck(true); remember({ stuck: true }); }}>I'm stuck</button>
        )}
        <button className="plain" type="button" disabled={submitting || skipping || frozen} onClick={() => void skip()}>Skip</button>
        <button className="plain" type="button" disabled={submitting || skipping} onClick={onBack}>Back</button>
      </div>
    </div>
  );
}
