import { useCallback, useEffect, useState } from "react";
import type { CommandError, DiagnosisCardDto, ElicitingResponseResultDto, FeedbackBundle, GradingClarificationDto } from "@desktop/api/dto";
import { MarkdownMath } from "@desktop/render/MarkdownMath";
import { phone } from "../api/phone";
import { newUlid } from "../util/ulid";
import { useVisibleInterval } from "../util/useVisibleInterval";
import { RemoteImageAsLink } from "../components/RemoteImageAsLink";

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
      setError((failure as CommandError).message);
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
            <button className="primary" type="button" disabled={busy || !answer.trim()} onClick={() => void send(current.index)}>Send</button>
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
  onNext,
  onError
}: {
  attemptId: string;
  onNext: () => void;
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

  const load = useCallback(() => {
    setLoadError(null);
    phone
      .getFeedback(attemptId)
      .then(setFeedback)
      .catch((error: CommandError) => {
        setLoadError(error.message);
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

  if (loadError) {
    return (
      <div className="main">
        <p className="bad" role="alert">{loadError}</p>
        <div className="row">
          <button className="primary" type="button" onClick={() => setRevision((value) => value + 1)}>Try again</button>
          <button className="plain" type="button" onClick={onNext}>Next</button>
        </div>
      </div>
    );
  }
  if (!feedback) return <div className="main"><p className="dim">Reading your feedback…</p></div>;
  return (
    <div className="main">
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
      {clarification ? (
        <div className="banner">
          <div className="markdown"><MarkdownMath value={clarification.questionMd} components={RemoteImageAsLink} /></div>
          <label htmlFor="clarify">Your answer (optional; skipping leaves the grade as it stands)</label>
          <textarea id="clarify" rows={3} value={answer} onChange={(event) => setAnswer(event.target.value)} />
          <div className="row">
            <button className="primary" type="button" disabled={busy || !answer.trim()} onClick={() => void answerClarification()}>Send</button>
          </div>
        </div>
      ) : null}
      {note ? <p className="dim" role="status">{note}</p> : null}
      <div className="row">
        <button className="primary" type="button" onClick={onNext}>Next</button>
      </div>
    </div>
  );
}
