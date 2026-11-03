import { useCallback, useEffect, useRef, useState } from "react";
import type { AttemptResultDto, CommandError, PracticeItemDetail, SessionSnapshot } from "@desktop/api/dto";
import { MarkdownMath } from "@desktop/render/MarkdownMath";
import { MathLiveEditor } from "@desktop/render/MathLiveEditor";
import { phone, type SubmitInput } from "../api/phone";
import { phoneAttemptType } from "../util/attemptType";
import { newUlid } from "../util/ulid";
import { rememberPendingSubmit } from "../store/sessionCache";
import { RemoteImageAsLink } from "../components/RemoteImageAsLink";

/** §3.4: plain LaTeX entry with a small bar of common commands; a real math keyboard is later. */
const SYMBOLS = ["$", "^{}", "_{}", "\\frac{}{}", "\\sqrt{}", "\\sum", "\\int", "\\infty", "\\pi", "\\theta", "\\lambda", "\\le", "\\ge", "\\ne", "\\to"];
const DRAFT_DEBOUNCE_MS = 800;

export interface QuestionTarget {
  readonly practiceItemId: string;
  readonly schedulerCandidateId: string | null;
  /** A draft the checkpoint holds for this item. */
  readonly restored?: { answer: string; submissionId: string | null; stuck: boolean } | null;
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

const GRADING_DOWN = "AI grading is unavailable; your answer is saved. Retry later or finish on the desktop.";

export function QuestionScreen({
  session,
  target,
  frozen,
  onFeedback,
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
  onDesktopOnly: (practiceItemId: string) => void;
  onSkipped: (practiceItemId: string) => void;
  onBack: () => void;
  onError: (error: unknown) => void;
}) {
  const { practiceItemId, schedulerCandidateId, restored } = target;
  const sessionId = session.sessionId;
  const [item, setItem] = useState<PracticeItemDetail | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [probeActive, setProbeActive] = useState(false);
  const [loadRevision, setLoadRevision] = useState(0);
  const [answer, setAnswer] = useState(restored?.answer ?? "");
  const [stuck, setStuck] = useState(restored?.stuck ?? false);
  const [submitting, setSubmitting] = useState(false);
  const [failure, setFailure] = useState<CommandError | null>(null);
  const submissionId = useRef(restored?.submissionId ?? newUlid());
  // A terminal failure closed this key's job; an edit after one is a new request, under a new key.
  const failedKey = useRef(false);
  const sentInput = useRef<SubmitInput | null>(null);
  const shownAt = useRef(Date.now());
  const dirty = useRef(false);
  const latest = useRef({ answer, stuck, frozen });
  latest.current = { answer, stuck, frozen };

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
    if (!dirty.current || latest.current.frozen) return;
    dirty.current = false;
    await phone.saveDraft({
      sessionId,
      practiceItemId,
      answerMd: latest.current.answer,
      submissionId: submissionId.current,
      schedulerCandidateId,
      ...(latest.current.stuck ? { declaredStuck: true } : {})
    });
  }, [practiceItemId, schedulerCandidateId, sessionId]);

  useEffect(() => {
    if (!item || probeActive) return undefined;
    const timer = window.setTimeout(() => void saveDraft().catch(onError), DRAFT_DEBOUNCE_MS);
    return () => window.clearTimeout(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [answer, stuck, item, probeActive, saveDraft]);

  function edit(next: string) {
    if (failedKey.current) {
      // Only a terminal failure ends a key. A retryable one (the job ran and wrote nothing)
      // would also retry under it, but its params are the old answer's, so a new answer is new.
      failedKey.current = false;
      submissionId.current = newUlid();
      setFailure(null);
    }
    dirty.current = true;
    setAnswer(next);
  }

  async function submit() {
    if (!item || submitting) return;
    setSubmitting(true);
    setFailure(null);
    const key = submissionId.current;
    try {
      // The retry key is durable before grading begins, so a dead phone or host recovers this attempt.
      await saveDraft();
      // One key, one request: §6.3 compares a retry's params, so a retry resends these exactly.
      if (sentInput.current?.submissionId !== key) {
        sentInput.current = {
          sessionId,
          practiceItemId,
          answerMd: latest.current.answer,
          attemptType: phoneAttemptType(item.attemptTypesAllowed),
          submissionId: key,
          latencySeconds: Math.round((Date.now() - shownAt.current) / 1000),
          schedulerCandidateId,
          assessmentContractVersionId: item.assessmentContractVersionId,
          ...(latest.current.stuck ? { declaredStuck: true } : {})
        };
      }
      const result: AttemptResultDto = await phone.submitAttempt(sentInput.current, {
        // A closed or killed app finds its way back from here (A4).
        onAccepted: (job) => rememberPendingSubmit({ jobId: job.jobId, submissionId: key, sessionId, practiceItemId })
      });
      rememberPendingSubmit(null);
      await phone.acknowledge(sessionId, practiceItemId, key).catch(() => undefined);
      onFeedback(result.attemptId, practiceItemId);
    } catch (error) {
      rememberPendingSubmit(null);
      const command = error as CommandError;
      if (command.code === "submission_committed") {
        // The attempt is in; only its completion's receipt is missing.
        const attemptId = (command.details as { attempt_id?: string; attemptId?: string } | undefined);
        const committed = attemptId?.attempt_id ?? attemptId?.attemptId;
        if (committed) {
          onFeedback(committed, practiceItemId);
          return;
        }
      }
      // The App's banner says where the session went; this screen has nothing to add.
      if (command.code === "session_moved") {
        onError(error);
      } else {
        failedKey.current = true;
        setFailure(command);
        // A desktop gone away also has to show on the shell; the rest is said here, once.
        if (command.code === "desktop_offline") onError(error);
      }
    } finally {
      setSubmitting(false);
    }
  }

  async function skip() {
    try {
      onSkipped(practiceItemId);
    } catch (error) {
      onError(error);
    }
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
        disabled={submitting || frozen}
        ariaLabel="Your answer"
        placeholder={stuck ? "Write what you can, or what's confusing you." : "Your answer. $…$ for math."}
      />
      {failure ? (
        <p className="bad" role="alert">{failure.code === "grading_fallback_required" ? GRADING_DOWN : failure.message}</p>
      ) : null}
      {submitting ? <p className="dim" role="status">Grading. You can leave; the result will be here when you come back.</p> : null}
      <div className="row">
        <button className="primary" type="button" disabled={submitting || frozen || (!stuck && !answer.trim())} onClick={() => void submit()}>
          {failure?.retryable ? "Try again" : "Submit"}
        </button>
        {stuck ? null : (
          <button className="plain" type="button" disabled={submitting || frozen} onClick={() => { dirty.current = true; setStuck(true); }}>I'm stuck</button>
        )}
        <button className="plain" type="button" disabled={submitting || frozen} onClick={() => void skip()}>Skip</button>
        <button className="plain" type="button" disabled={submitting} onClick={onBack}>Back</button>
      </div>
    </div>
  );
}
