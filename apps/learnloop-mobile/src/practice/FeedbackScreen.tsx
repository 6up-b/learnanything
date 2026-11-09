import { useCallback, useEffect, useRef, useState } from "react";
import type { CommandError, DiagnosisCardDto, ElicitingResponseResultDto, FeedbackBundle, GradingClarificationDto } from "@desktop/api/dto";
import { MarkdownMath } from "@desktop/render/MarkdownMath";
import { staleRefusal } from "../api/http";
import { phone } from "../api/phone";
import { newUlid } from "../util/ulid";
import { useVisibleInterval } from "../util/useVisibleInterval";
import { RemoteImageAsLink } from "../components/RemoteImageAsLink";
import { Contest, FollowupPanel, FullAnswer, HypothesisMarks, useFollowup } from "./FeedbackParts";

/** The desktop's own interval for a pending diagnosis (`diagnosis_card.py`: every 2-3 s). */
const DIAGNOSIS_POLL_MS = 3000;

/**
 * The diagnosis's follow-up questions, one at a time and in the diagnosis's order: a later
 * question can name what an earlier one asks for. As on the desktop, the expected answer and
 * the corrected work are never shown, and an answer is recorded, not graded.
 */
function FollowUpQuestions({ attemptId, feedback }: { attemptId: string; feedback: FeedbackBundle }) {
  // Each keeps its index into `repairSuggestions`, which is what a response names.
  const questions = (feedback.repairSuggestions ?? []).flatMap((suggestion, index) =>
    suggestion.elicitingQuestion?.trim() ? [{ index, question: suggestion.elicitingQuestion }] : []
  );
  const [position, setPosition] = useState(0);
  const [answer, setAnswer] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [last, setLast] = useState<ElicitingResponseResultDto | null>(null);

  async function send(index: number) {
    setBusy(true);
    setError(null);
    try {
      setLast(await phone.submitElicitingResponse(attemptId, index, answer.trim()));
      setAnswer("");
      setPosition((value) => value + 1);
    } catch (failure) {
      // What was typed stays in the box. A second tap is the learner's choice: this call is not retried for them.
      // A stale app is the connection line's to say (F3).
      setError(staleRefusal(failure) ? null : (failure as CommandError).message);
    } finally {
      setBusy(false);
    }
  }

  if (questions.length === 0) return null;
  const current = questions[position];
  return (
    <section className="banner">
      <h2>Follow-up questions</h2>
      {last ? (
        <p className="dim" role="status">
          {last.admissibleAsIndependent
            ? "Answer recorded. It isn't graded."
            : "Answer recorded. It isn't graded, and it won't count as independent evidence because the answer was already on screen."}
        </p>
      ) : null}
      {current ? (
        <>
          <p className="dim">Question {position + 1} of {questions.length}</p>
          <div className="markdown"><MarkdownMath value={current.question} components={RemoteImageAsLink} /></div>
          <label htmlFor="follow-up">Your answer (optional)</label>
          <textarea id="follow-up" rows={3} value={answer} disabled={busy} onChange={(event) => setAnswer(event.target.value)} />
          {error ? <p className="bad" role="alert">{error}</p> : null}
          <div className="row">
            <button className="plain" type="button" disabled={busy || !answer.trim()} onClick={() => void send(current.index)}>Send</button>
          </div>
        </>
      ) : (
        <p className="dim">That's all of them.</p>
      )}
    </section>
  );
}

export function FeedbackScreen({
  attemptId,
  choosing = false,
  waitLine = null,
  onNext,
  onOpenFeedback,
  onSettled,
  onError
}: {
  attemptId: string;
  /** Next is with the host (a plan decision can take a while, mobile v2 §2.2). */
  choosing?: boolean;
  /** Mobile v2 V3: Next waits while this miss's question is being written, and says so (FG1 §6.1). */
  waitLine?: string | null;
  onNext: () => void;
  /** Mobile v2 V3: a probe's answer points back at the miss whose feedback it released (FG1 §3 step 8). */
  onOpenFeedback?: (attemptId: string) => void;
  /** The grade and its diagnosis are in, and no question of this miss comes next (spec_instruct_handoff_v1 §3a). */
  onSettled?: () => void;
  onError: (error: unknown) => void;
}) {
  const [feedback, setFeedback] = useState<FeedbackBundle | null>(null);
  const [clarification, setClarification] = useState<GradingClarificationDto | null>(null);
  const [answer, setAnswer] = useState("");
  const [busy, setBusy] = useState(false);
  const [note, setNote] = useState<string | null>(null);
  const [revision, setRevision] = useState(0);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [card, setCard] = useState<DiagnosisCardDto | null>(null);
  const { followup, refresh: refreshFollowup } = useFollowup(attemptId, feedback?.followup);
  const followupHeld = followup?.held === true;
  // Released (shown anyway, or its question answered on the desktop): the bundle is re-read, never re-opened.
  const wasHeld = useRef(false);
  useEffect(() => {
    if (followupHeld) wasHeld.current = true;
    if (!followupHeld && wasHeld.current) {
      wasHeld.current = false;
      void phone.getFeedback(attemptId, false).then(setFeedback, () => undefined);
    }
  }, [attemptId, followupHeld]);

  const load = useCallback(() => {
    setLoadError(null);
    phone
      .getFeedback(attemptId)
      .then(setFeedback)
      .catch((error: CommandError) => {
        // A stale app: the connection line says so and offers Reload; Try again and Next stay (F3).
        setLoadError(staleRefusal(error) ? "" : error.message);
        onError(error);
      });
    phone
      .getClarification(attemptId)
      .then((result) => setClarification(result.clarification))
      .catch(() => setClarification(null));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [attemptId, revision]);
  useEffect(load, [load]);

  const pending = feedback?.diagnosisStatus === "pending";
  useVisibleInterval(() => {
    void phone
      .diagnosisStatus(attemptId)
      .then((status) => {
        if (status.status === "pending") return;
        // Landed: the bundle's repairs are re-read, which is not another open of the screen.
        return phone.getFeedback(attemptId, false).then(setFeedback);
      })
      .catch(() => undefined);
  }, DIAGNOSIS_POLL_MS, pending);

  // Done on opening or just landed: the summary is on the card, not the bundle.
  const diagnosisDone = feedback?.diagnosisStatus === "done";
  useEffect(() => {
    if (!diagnosisDone) return;
    let current = true;
    phone
      .diagnosisStatus(attemptId)
      .then((result) => {
        if (current) setCard(result);
      })
      .catch(() => undefined);
    return () => {
      current = false;
    };
  }, [attemptId, diagnosisDone]);

  // Spec_instruct_handoff_v1 §3a: what Next decides depends on the outcome just graded and on what its diagnosis found,
  // and with a question still on its way Next isn't a plan boundary. Fires again if this comes back true: that's harmless.
  // The bundle's read counts until `useFollowup` has taken it: both arrive in this same render.
  const followupRead = followup ?? feedback?.followup;
  const questionComing = followupRead?.held === true || followupRead?.state === "pending" || followupRead?.state === "ready";
  const settled = feedback !== null && !pending && !questionComing;
  useEffect(() => {
    if (settled) onSettled?.();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [attemptId, settled]);

  async function answerClarification() {
    if (!answer.trim()) return;
    setBusy(true);
    try {
      const result = await phone.answerClarification(attemptId, answer.trim(), newUlid());
      setFeedback(result.feedback);
      setClarification(null);
      setNote(result.error);
    } catch (error) {
      onError(error);
    } finally {
      setBusy(false);
    }
  }

  if (loadError !== null) {
    return (
      <div className="screen">
        {loadError ? <p className="bad" role="alert">{loadError}</p> : null}
        <div className="actions">
          <button className="primary block" type="button" onClick={() => setRevision((value) => value + 1)}>Try again</button>
          <div className="row">
            <button className="plain" type="button" onClick={onNext}>Next</button>
          </div>
        </div>
      </div>
    );
  }
  if (!feedback) return <div className="screen"><p className="dim">Reading your feedback…</p></div>;
  // FG1 §3 step 8: this answered a generated probe, so what the earlier miss held appears there now.
  const heldFrom = feedback.heldFeedbackAttemptId ?? null;
  return (
    <div className="screen">
      <h1>{feedback.learningObjectTitle}</h1>
      <p className="score">{feedback.rubricScore} / {feedback.maxPoints}</p>
      {feedback.manualReviewReason ? <p className="dim">{feedback.manualReviewReason}</p> : null}
      {feedback.feedbackMd ? (
        <div className="markdown"><MarkdownMath value={feedback.feedbackMd} components={RemoteImageAsLink} /></div>
      ) : null}
      {feedback.criterionEvidence.map((row) => (
        <div className="criterion" key={row.criterionId}>
          <div>{row.criterionDescription} <span className="dim">({row.pointsAwarded}/{row.pointsPossible})</span></div>
          {row.notes ? <div className="dim markdown"><MarkdownMath value={row.notes} components={RemoteImageAsLink} /></div> : null}
        </div>
      ))}
      {followup && (followup.line || followup.held || followup.canContinueWithout || followup.routerDecision) ? (
        <FollowupPanel
          attemptId={attemptId}
          followup={followup}
          onRefresh={refreshFollowup}
          onReleased={() => void phone.getFeedback(attemptId, false).then(setFeedback, () => undefined)}
        />
      ) : null}
      <FullAnswer feedback={feedback} held={followupHeld} />
      {feedback.gradingSource !== "self" ? <Contest attemptId={attemptId} onBundle={setFeedback} /> : null}
      {pending ? <p className="dim" role="status">Looking into what happened here…</p> : null}
      {feedback.diagnosisStatus === "failed" ? (
        <p className="dim" role="status">The look into this answer didn't finish. Your grade stands.</p>
      ) : null}
      {card?.cardEnabled !== false && card?.summaryMd ? (
        <section>
          <h2>What happened here</h2>
          <div className="markdown"><MarkdownMath value={card.summaryMd} components={RemoteImageAsLink} /></div>
        </section>
      ) : null}
      {diagnosisDone ? <FollowUpQuestions attemptId={attemptId} feedback={feedback} /> : null}
      {feedback.hypothesisMarks && !followupHeld ? <HypothesisMarks marks={feedback.hypothesisMarks} /> : null}
      {clarification ? (
        <div className="banner">
          <div className="markdown"><MarkdownMath value={clarification.questionMd} components={RemoteImageAsLink} /></div>
          <label htmlFor="clarify">Your answer (optional; skipping leaves the grade as it stands)</label>
          <textarea id="clarify" rows={3} value={answer} onChange={(event) => setAnswer(event.target.value)} />
          <div className="row">
            <button className="plain" type="button" disabled={busy || !answer.trim()} onClick={() => void answerClarification()}>Send</button>
          </div>
        </div>
      ) : null}
      {note ? <p className="dim" role="status">{note}</p> : null}
      {heldFrom && onOpenFeedback ? (
        <div className="row">
          <button className="plain" type="button" onClick={() => onOpenFeedback(heldFrom)}>See the feedback on your earlier answer</button>
        </div>
      ) : null}
      {waitLine && !choosing ? <p className="dim" role="status" data-testid="followup-wait">{waitLine}</p> : null}
      {choosing ? <p className="dim" role="status">Choosing what's next…</p> : null}
      <div className="actions">
        <button className="primary block" type="button" disabled={choosing} onClick={onNext}>Next</button>
      </div>
    </div>
  );
}
