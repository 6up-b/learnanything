import { useCallback, useEffect, useRef, useState } from "react";
import type { AttemptResultDto, CommandError, PracticeItemDetail, SessionSnapshot } from "@desktop/api/dto";
import { MarkdownMath } from "@desktop/render/MarkdownMath";
import { MathLiveEditor } from "@desktop/render/MathLiveEditor";
import { committedAttempt, staleRefusal } from "../api/http";
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
import { Sheet } from "../shell/Sheet";

/** §3.4: plain LaTeX entry with a small bar of common commands; a real math keyboard is later. */
const SYMBOLS = ["$", "^{}", "_{}", "\\frac{}{}", "\\sqrt{}", "\\sum", "\\int", "\\infty", "\\pi", "\\theta", "\\lambda", "\\le", "\\ge", "\\ne", "\\to"];
const DRAFT_DEBOUNCE_MS = 800;

export interface QuestionTarget {
  readonly practiceItemId: string;
  readonly schedulerCandidateId: string | null;
  /** A draft the checkpoint holds for this item. */
  readonly restored?: { answer: string; submissionId: string | null; stuck: boolean; assist: DraftAssist } | null;
  /** Mobile v2 J1: the plan presentation this serve is (router R2a), which the answer binds to. */
  readonly planPresentationId?: string | null;
  /** Mobile v2 J6: a randomized check is answered cold. No help is offered, and no label says why. */
  readonly noHelp?: boolean;
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

/** A skip sent: the host says it did it, the host says it didn't, or no reply says either (F11). */
export type SkipOutcome = "recorded" | "refused" | "unknown";
/** An `unknown` skip, once the checkpoint has been read, if it could be. */
export type SkipSettled = "landed" | "landed_written_since" | "not_landed" | "unreachable";

const SKIP_UNSETTLED: CommandError = {
  code: "desktop_offline",
  message: "The desktop can't be reached, so this skip isn't settled. Your answer stays on this phone.",
  retryable: false
};
const SKIP_LANDED_WRITTEN_SINCE: CommandError = {
  code: "skip_landed",
  message: "That skip went through, and what you wrote since is kept as a new draft.",
  retryable: false
};
const SKIP_NOT_RECORDED: CommandError = {
  code: "skip_not_recorded",
  message: "The skip didn't reach the desktop, and the question is still open.",
  retryable: false
};

/** What this screen opens on: its own copy if it has one, else the checkpoint's draft, else nothing. */
function openedDraft(sessionId: string, target: QuestionTarget) {
  const own = readQuestionDraft(sessionId, target.practiceItemId);
  if (own) return { ...own, schedulerCandidateId: own.schedulerCandidateId ?? target.schedulerCandidateId, own: true };
  const restored = target.restored;
  const assist = restored?.assist ?? NO_ASSIST;
  return {
    answer: restored?.answer ?? "",
    stuck: restored?.stuck ?? false,
    submissionId: restored?.submissionId ?? newUlid(),
    schedulerCandidateId: target.schedulerCandidateId,
    // A plan step names its presentation; a checkpoint's own wins (it is the serve this draft is to).
    assist: target.planPresentationId && !assist.planPresentationId ? { ...assist, planPresentationId: target.planPresentationId } : assist,
    sentInput: null as SubmitInput | null,
    // A key that came with the checkpoint may have a job or an attempt behind it.
    outcome: (restored?.submissionId ? "unknown" : "none") as SubmitOutcome,
    revision: 0,
    skipRevision: null as number | null,
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
  onSkipUnknown,
  onBack,
  onBusy,
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
  /** A refusal is the App's to report. */
  onSkipped: (practiceItemId: string) => Promise<SkipOutcome>;
  /** Landed, the App has dropped the phone's copy and moved on, unless `writtenSince` says there's more to keep. */
  onSkipUnknown: (practiceItemId: string, writtenSince: () => boolean) => Promise<SkipSettled>;
  onBack: () => void;
  /** A submit or a skip on its way, so the frame's Back waits too (Codex review of V1, F1). */
  onBusy?: (busy: boolean) => void;
  onError: (error: unknown) => void;
}) {
  const { practiceItemId } = target;
  const sessionId = session.sessionId;
  const [opened] = useState(() => openedDraft(session.sessionId, target));
  // The help this draft has had: an item's own hint revealed here adds to it (J16).
  const [assist, setAssist] = useState<DraftAssist>(opened.assist);
  const assistRef = useRef(assist);
  assistRef.current = assist;
  const [helpOpen, setHelpOpen] = useState(false);
  // A fresh draft after a landed skip answers no offer: that serve's went with the skip.
  const schedulerCandidateId = useRef(opened.schedulerCandidateId);
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
  const revision = useRef(opened.revision ?? 0);
  // A skip with no reply and no read of the checkpoint since: the revision it was sent at. It may have
  // landed, so no write yet (F11), and landing would discard only that revision (verify finding 1).
  const skipRevision = useRef<number | null>(opened.skipRevision ?? null);
  const shownAt = useRef(Date.now());
  // Its own copy may hold what never reached the checkpoint, or the checkpoint may have moved on to
  // another item since. A request already sent settles that at the submit.
  const dirty = useRef(opened.own && !opened.sentInput);
  const latest = useRef({ answer, stuck, frozen, ready: false });
  latest.current = { answer, stuck, frozen, ready: item !== null && !probeActive };

  const busy = submitting || skipping;
  useEffect(() => {
    onBusy?.(busy);
  }, [busy, onBusy]);
  // Gone from the screen, it holds nothing back.
  useEffect(() => () => onBusy?.(false), [onBusy]);

  /** The phone's copy of all this, written as it changes. */
  function remember(next: { answer?: string; stuck?: boolean } = {}) {
    writeQuestionDraft({
      sessionId,
      practiceItemId,
      answer: next.answer ?? latest.current.answer,
      stuck: next.stuck ?? latest.current.stuck,
      submissionId: submissionId.current,
      schedulerCandidateId: schedulerCandidateId.current,
      assist: assistRef.current,
      sentInput: sentInput.current,
      outcome: outcome.current,
      revision: revision.current,
      skipRevision: skipRevision.current
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
        // A stale app: the connection line says so and offers Reload; Try again and Back stay (F3).
        setLoadError(staleRefusal(error) ? "" : error.message);
      });
    return () => {
      cancelled = true;
    };
    // One load per item and per retry.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [practiceItemId, sessionId, loadRevision]);

  const saveDraft = useCallback(async () => {
    if (!dirty.current || skipInFlight.current || skipRevision.current !== null || latest.current.frozen || !latest.current.ready) return;
    dirty.current = false;
    const assist = assistRef.current;
    try {
      await phone.saveDraft({
        sessionId,
        practiceItemId,
        answerMd: latest.current.answer,
        submissionId: submissionId.current,
        schedulerCandidateId: schedulerCandidateId.current,
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
  }, [practiceItemId, sessionId]);

  useEffect(() => {
    if (!item || probeActive) return undefined;
    const timer = window.setTimeout(() => void saveWhenSettled().catch(onError), DRAFT_DEBOUNCE_MS);
    return () => window.clearTimeout(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [answer, stuck, assist, item, probeActive, saveDraft]);

  // Leaving the screen is no reason to lose the last 800 ms of typing.
  const flushOnLeave = useRef(() => undefined as void);
  flushOnLeave.current = () => void saveDraft().catch(onError);
  useEffect(() => () => flushOnLeave.current(), []);

  function edit(next: string) {
    setFailure(null);
    dirty.current = true;
    revision.current += 1;
    setAnswer(next);
    remember({ answer: next });
  }

  /**
   * J16 partial: the item's next own hint. The sheet said what it changes before this (◌ with help);
   * the count rides on the draft and the submit as the desktop's does, and the reveal row is telemetry
   * the screen never waits on (`practice.record_hint_reveal`, which the server refuses in a probe).
   */
  function revealHint() {
    const current = assistRef.current;
    const index = current.hintsUsed;
    const next: DraftAssist = {
      ...current,
      hintsUsed: index + 1,
      hintSeen: true,
      firstHintProgress: current.firstHintProgress ?? (latest.current.answer.trim() ? "draft_started" : "no_draft")
    };
    assistRef.current = next;
    setAssist(next);
    dirty.current = true;
    revision.current += 1;
    remember();
    void phone
      .recordHintReveal({
        sessionId, practiceItemId, submissionId: submissionId.current, authoredIndex: index,
        answerMd: latest.current.answer, revealedAt: new Date().toISOString()
      })
      .catch(() => undefined);
  }

  /** Reads the checkpoint for a skip with no reply. Unreachable, the question stays and nothing is written. */
  async function settleSkip(): Promise<SkipSettled> {
    const sentAt = skipRevision.current ?? revision.current;
    const settled = await onSkipUnknown(practiceItemId, () => revision.current !== sentAt);
    if (settled === "unreachable") {
      skipRevision.current = sentAt;
      remember();
      setFailure(SKIP_UNSETTLED);
    } else if (settled === "not_landed") {
      skipRevision.current = null;
      remember();
    } else if (settled === "landed_written_since") {
      // The skip took the checkpoint, its key and its offer with it. What's on screen is a new draft.
      skipRevision.current = null;
      submissionId.current = newUlid();
      schedulerCandidateId.current = null;
      sentInput.current = null;
      outcome.current = "none";
      dirty.current = true;
      remember();
      setFailure(null);
      onError(SKIP_LANDED_WRITTEN_SINCE);
    }
    return settled;
  }

  /** The debounce's save. Past a skip with no reply it asks first, whenever this screen next has cause to write. */
  async function saveWhenSettled(): Promise<void> {
    if (skipRevision.current === null) return saveDraft();
    if (skipInFlight.current) return;
    skipInFlight.current = true;
    const settled = await settleSkip();
    if (settled === "landed") return;
    skipInFlight.current = false;
    if (settled !== "unreachable") await saveDraft();
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
    const assist = assistRef.current;
    const hints = assist.hintsUsed + (assist.pageSeen ? 1 : 0);
    return {
      sessionId,
      practiceItemId,
      answerMd: latest.current.answer,
      attemptType: phoneAttemptType(currentItem.attemptTypesAllowed, hints),
      submissionId: key,
      latencySeconds: Math.round((Date.now() - shownAt.current) / 1000),
      schedulerCandidateId: schedulerCandidateId.current,
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
      if (skipRevision.current !== null) {
        const settled = await settleSkip();
        if (settled === "landed" || settled === "unreachable") return;
      }
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
      // The App's banner says where the session went, and the connection line that this app is
      // stale (F3); this screen has nothing to add.
      if (command.code === "session_moved" || staleRefusal(command)) {
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
    let result: SkipOutcome = "refused";
    // Skip again means all of this, so a landed skip discards all of it.
    if (skipRevision.current !== null) skipRevision.current = revision.current;
    let settled: SkipSettled | null = skipRevision.current !== null ? await settleSkip() : null;
    if (settled !== "landed" && settled !== "unreachable") {
      try {
        // A skip forgets the key, and reopening would then mint another over a job that may still land.
        result = outcome.current === "unknown" && (await settledByTheHost()) ? "recorded" : await onSkipped(practiceItemId);
      } catch (error) {
        onError(error);
      }
      if (result === "unknown") {
        // Saving now could put back what a skip that landed cleared, so the checkpoint says first.
        settled = await settleSkip();
        if (settled === "not_landed") onError(SKIP_NOT_RECORDED);
      }
    }
    // Landed, it stays set: the skip ended this draft, and a flush on the way out would put it back.
    if (result === "recorded" || settled === "landed") return;
    skipInFlight.current = false;
    setSkipping(false);
    // The question stays open, so what the skip held back is due now, unless it may still have landed.
    if (settled !== "unreachable") void saveDraft().catch(onError);
  }

  if (loadError !== null) {
    return (
      <div className="screen">
        {loadError ? <p className="bad" role="alert">{loadError}</p> : null}
        <div className="actions">
          <button className="primary block" type="button" onClick={() => setLoadRevision((value) => value + 1)}>Try again</button>
          <div className="row">
            <button className="plain" type="button" onClick={onBack}>Back</button>
          </div>
        </div>
      </div>
    );
  }
  if (!item) return <div className="screen"><p className="dim">Opening…</p></div>;
  // A serve's honest label when its cold check could not be taken (`queue.eligibility_dto`).
  const eligibilityMessage = (item as unknown as { eligibility?: { message?: string | null } }).eligibility?.message;
  if (probeActive) {
    // §6.4: the serve is committed and the check waits on the desktop; no skip is recorded.
    return (
      <div className="screen">
        <h1>{item.learningObjectTitle}</h1>
        <p className="banner" role="status">This is a diagnostic check. Continue it on the desktop.</p>
        <div className="actions">
          <button className="primary block" type="button" onClick={() => onDesktopOnly(practiceItemId)}>Next</button>
        </div>
      </div>
    );
  }
  // J16: an item's own hints, unless this answer is to be cold (a randomized check, a check on your
  // own, a cold follow-up lane), where help would make it a non-success: none is offered then.
  const ownHints = item.hints ?? [];
  const helpOffered = !target.noHelp && !item.intentCheck && !item.activeFollowupKind && ownHints.length > 0;
  const revealed = helpOffered ? ownHints.slice(0, Math.min(assist.hintsUsed, ownHints.length)) : [];
  // Mobile v2 §4.3: the symbol bar and Submit sit together in the thumb zone, kept above the
  // keyboard by the shell's visual-viewport inset; the secondary actions wrap beneath.
  return (
    <div className="screen">
      <h1>{item.learningObjectTitle}</h1>
      {item.intentCheck?.banner ? <p className="banner">{item.intentCheck.banner}</p> : null}
      {eligibilityMessage ? <p className="dim">{eligibilityMessage}</p> : null}
      {item.presentation.blocks.map((block, index) => (
        <div key={`${block.kind}:${index}`}>
          {block.label ? <div className="dim">{block.label}</div> : null}
          <div className="markdown"><MarkdownMath value={block.markdown} components={RemoteImageAsLink} /></div>
        </div>
      ))}
      {revealed.length ? (
        <section className="banner" aria-label="Hints">
          <p className="dim">◌ with help</p>
          {revealed.map((hint, index) => (
            <div key={index} className="markdown"><MarkdownMath value={hint} components={RemoteImageAsLink} /></div>
          ))}
        </section>
      ) : null}
      {helpOpen ? (
        <Sheet title="A hint" onClose={() => setHelpOpen(false)}>
          {assist.hintsUsed < ownHints.length ? (
            <>
              <p>With a hint, this answer counts as answered with help (◌), not on your own.</p>
              <div className="actions">
                <button className="primary block" type="button" onClick={() => { revealHint(); setHelpOpen(false); }}>Show a hint</button>
              </div>
            </>
          ) : (
            <p className="dim">That's every hint this question has.</p>
          )}
        </Sheet>
      ) : null}
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
      <div className="actions">
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
        <button className="primary block" type="button" disabled={submitting || skipping || frozen || (!stuck && !answer.trim())} onClick={() => void submit()}>
          {failure?.retryable ? "Try again" : "Submit"}
        </button>
        <div className="row">
          {stuck ? null : (
            <button className="plain" type="button" disabled={submitting || skipping || frozen} onClick={() => { dirty.current = true; revision.current += 1; setStuck(true); remember({ stuck: true }); }}>I'm stuck</button>
          )}
          {helpOffered ? (
            <button className="plain" type="button" disabled={submitting || skipping || frozen} onClick={() => setHelpOpen(true)}>Hint</button>
          ) : null}
          <button className="plain" type="button" disabled={submitting || skipping || frozen} onClick={() => void skip()}>Skip</button>
          <button className="plain" type="button" disabled={submitting || skipping} onClick={onBack}>Back</button>
        </div>
      </div>
    </div>
  );
}
