import { useCallback, useEffect, useState } from "react";
import type { CommandError, FeedbackBundle, GradingClarificationDto } from "@desktop/api/dto";
import { MarkdownMath } from "@desktop/render/MarkdownMath";
import { phone } from "../api/phone";
import { newUlid } from "../util/ulid";
import { useVisibleInterval } from "../util/useVisibleInterval";
import { RemoteImageAsLink } from "../components/RemoteImageAsLink";

/** The desktop's own interval for a pending diagnosis (`diagnosis_card.py`: every 2-3 s). */
const DIAGNOSIS_POLL_MS = 3000;

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
