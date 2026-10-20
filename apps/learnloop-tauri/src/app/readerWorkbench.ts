/**
 * Reader workbench RW2a: the way back from a Reader workbench attempt (spec
 * §5.1 "back from feedback returns to the problem"; UX S6).
 *
 * A workbench submit in the Reader goes to feedback with a way back to its
 * problem: Esc or b opens the Reader at that problem, the submitted session
 * shown read-only (the Reader reads it with one RPC,
 * `workbench.session_for_attempt`), and a second Esc returns to reading at
 * its passage; Next returns to reading at the passage. Every other attempt
 * goes back as today.
 */
import type { SessionSnapshot, SourceLibraryCard, WorkbenchSubmitDto } from "../api/dto";
import type { ReaderWorkbenchCheck } from "../screens/reader/useReaderWorkbench";
import type { PracticeOffer } from "./practiceOffer";
import type { ReaderReturn } from "./readerCheck";

export interface ReaderWorkbenchOrigin {
  card: SourceLibraryCard;
  spanId: string;
}

/** The way back kept while feedback shows a Reader workbench attempt. */
export function workbenchReturn(result: WorkbenchSubmitDto, at: ReaderWorkbenchOrigin): ReaderReturn {
  return {
    card: at.card,
    spanId: at.spanId,
    practiceItemId: result.session.practiceItemId ?? "",
    workbenchAttemptId: result.attempt.attemptId,
  };
}

/** Where back from feedback opens the Reader, and whether with the problem. */
export function readerTargetBack(
  back: ReaderReturn,
  options: { showProblem: boolean },
): { source: ReaderWorkbenchOrigin; initialAttemptId: string | null } {
  return {
    source: { card: back.card, spanId: back.spanId },
    initialAttemptId: options.showProblem && back.workbenchAttemptId ? back.workbenchAttemptId : null,
  };
}

/** A submit may have started the practice session the app did not have. */
export function sessionAfterWorkbenchSubmit(
  current: SessionSnapshot | null,
  practiceSession: SessionSnapshot | null,
): SessionSnapshot | null {
  if (!practiceSession) return current;
  if (current && current.sessionId === practiceSession.sessionId) return current;
  return practiceSession;
}

/**
 * "Check me" on a margin cue with the workbench on (D40, UX S7): the check the
 * Reader opens in its working posture, book hidden, answering the pick's own
 * serve (its scheduler candidate and plan presentation, as `readerCheckOffer`
 * worked them out). The plan-off proposal's delivery is recorded by the serve
 * the shell makes first, exactly as the practice screen's serve did.
 */
export function readerWorkbenchCheck(
  request: {
    practiceItemId: string; spanId: string; card: SourceLibraryCard;
    entry?: ReaderWorkbenchCheck["entry"]; admitsSessionId?: string;
  },
  offer: PracticeOffer,
  servedPrompt: string,
): ReaderWorkbenchCheck {
  return {
    practiceItemId: request.practiceItemId,
    spanId: request.spanId,
    sourceId: request.card.sourceId,
    stemMd: servedPrompt,
    schedulerCandidateId: offer.candidateId ?? null,
    planPresentationId: offer.presentationId ?? null,
    // RW4b: an admitted exercise resumes its own problem, keeping the
    // learner's book choice ("practice_this"); a cue's check hides the book.
    ...(request.entry ? { entry: request.entry } : {}),
    // ...and the server acknowledges that exercise's pick when it opens.
    ...(request.admitsSessionId ? { admitsSessionId: request.admitsSessionId } : {}),
  };
}
