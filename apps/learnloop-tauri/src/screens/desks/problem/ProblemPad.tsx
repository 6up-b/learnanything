// An RW2 problem hosted on its pad (spec §15.2: "RW2's workbench session is shown as a pad of kind `problem`… its
// help ladder and checks are unchanged. Only the frame moves"). The pad shows the very workbench the Reader's working
// posture showed (screens/workbench/Workbench: its steps in `workbench_steps`, I'm stuck and the help ladder, the
// check, Submit, Leave for now and Abandon, through the workbench services), so a problem opened in a source window
// is worked on the desk's pad, beside the book rather than over it. Leave and Abandon keep the pad with a way back;
// a submit goes to feedback as the Reader's did, and the pad then shows the problem as submitted.
import { useState, useSyncExternalStore } from "react";
import { api } from "../../../api/client";
import type { SourceLibraryCard, WorkbenchSessionDto, WorkbenchSubmitDto } from "../../../api/dto";
import { errorMessage } from "../../../errors";
import { Workbench } from "../../workbench/Workbench";
import { handOver, noteProblem, problemOf, subscribeProblems } from "./problemPads";

/** What the desks give a problem pad. */
export interface ProblemHost {
  /** The app's open practice session, when there is one (the submit records in it). */
  practiceSessionId: string | null;
  /** A submit's hand-off to feedback, with the way back to its passage (the Reader's own). */
  onSubmitted?: (result: WorkbenchSubmitDto, at: { card: SourceLibraryCard; spanId: string }) => void;
  /** "show in the book": the problem's passage in its source window. */
  showInBook: (session: WorkbenchSessionDto) => void;
  /** The library card of a source (the way back from feedback names it). */
  cardFor: (sourceId: string | null) => SourceLibraryCard | null;
  onError: (message: string) => void;
}

export function ProblemPad({ sessionId, host }: { sessionId: string; host: ProblemHost }) {
  const problem = useSyncExternalStore(subscribeProblems, () => problemOf(sessionId));
  const [busy, setBusy] = useState(false);

  const resume = async () => {
    setBusy(true);
    try {
      // One explicit resume, by the problem's id, as the Reader's ✎ line resumes it (reopened when set aside).
      const result = await api.workbenchOpen({ origin: "reader", entry: "resume", sessionId, extractionId: problem?.session.extractionId ?? null });
      const card = problem?.card ?? host.cardFor(result.session.sourceId ?? null);
      handOver({ session: result.session, readOnly: false, autoFocus: true, card, spanId: result.session.spanIds[0] ?? null,
        schedulerCandidateId: problem?.schedulerCandidateId ?? null, planPresentationId: problem?.planPresentationId ?? null });
    } catch (error) {
      host.onError(errorMessage(error, "Couldn't reopen this problem."));
    } finally {
      setBusy(false);
    }
  };
  const reopen = async () => {
    setBusy(true);
    try {
      const result = await api.workbenchReopen({ sessionId });
      noteProblem(sessionId, { session: result.session, away: null, readOnly: false });
    } catch (error) {
      host.onError(errorMessage(error, "Couldn't reopen this problem."));
    } finally {
      setBusy(false);
    }
  };

  if (!problem || problem.away) {
    const line = !problem ? "✎ a problem from your reading" : problem.away === "abandoned" ? "abandoned · your steps are kept" : "set aside · your steps are kept";
    return (
      <div className="pb problem-away" data-problem-pad={sessionId} data-problem-state={problem?.away ?? "unread"}>
        <div className="gut">✎</div>
        <div className="bx">
          {line}{" "}
          <button type="button" className="desk-link" disabled={busy} onClick={() => void (problem?.away === "abandoned" ? reopen() : resume())}>
            {problem?.away === "abandoned" ? "reopen" : "resume"}
          </button>
        </div>
      </div>
    );
  }

  const { session } = problem;
  const readOnly = problem.readOnly || session.status === "submitted";
  return (
    <div className="problem-pad" data-problem-pad={sessionId} data-problem-state={readOnly ? "submitted" : "open"}>
      <Workbench
        key={`${session.sessionId}:${readOnly ? "ro" : "rw"}`}
        initial={session}
        layout="stacked"
        readOnly={readOnly}
        practiceSessionId={host.practiceSessionId}
        schedulerCandidateId={problem.schedulerCandidateId ?? null}
        planPresentationId={problem.planPresentationId ?? null}
        autoFocus={problem.autoFocus}
        onSession={(next) => noteProblem(sessionId, { session: next })}
        onLeave={(left) => noteProblem(sessionId, readOnly ? { session: left } : { session: left, away: "left" })}
        onAbandoned={(gone) => noteProblem(sessionId, { session: gone, away: "abandoned" })}
        onSubmitted={(result) => {
          noteProblem(sessionId, { session: result.session, readOnly: true, autoFocus: false });
          const card = problem.card ?? host.cardFor(result.session.sourceId ?? null);
          const spanId = problem.spanId ?? result.session.spanIds[0] ?? null;
          if (card && spanId) host.onSubmitted?.(result, { card, spanId });
        }}
        onShowInBook={() => host.showInBook(session)}
        onError={host.onError}
      />
    </div>
  );
}
