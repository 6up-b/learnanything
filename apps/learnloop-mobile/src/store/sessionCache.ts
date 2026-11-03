// The cached session id and what a closed app must find again (§0): which session this phone was
// in, a submit it left mid-grade, and the question it has open. Nothing here is learner state of
// record: the checkpoint and the job are, and this is what the phone was saying to them.
import type { FirstHintProgress, SessionCheckpoint } from "@desktop/api/dto";
import type { SubmitInput } from "../api/phone";

const SESSION_KEY = "learnloop.session";
const PENDING_KEY = "learnloop.pendingSubmit";
const DRAFTS_KEY = "learnloop.questionDrafts";

export interface PendingSubmit {
  readonly jobId: string;
  readonly submissionId: string;
  readonly sessionId: string;
  readonly practiceItemId: string;
}

function read<T>(key: string): T | null {
  try {
    const raw = localStorage.getItem(key);
    return raw ? (JSON.parse(raw) as T) : null;
  } catch {
    return null;
  }
}

export function cachedSessionId(): string | null {
  return read<string>(SESSION_KEY);
}

export function cacheSessionId(sessionId: string | null): void {
  if (sessionId) localStorage.setItem(SESSION_KEY, JSON.stringify(sessionId));
  else localStorage.removeItem(SESSION_KEY);
}

export function pendingSubmit(): PendingSubmit | null {
  return read<PendingSubmit>(PENDING_KEY);
}

export function rememberPendingSubmit(pending: PendingSubmit | null): void {
  if (pending) localStorage.setItem(PENDING_KEY, JSON.stringify(pending));
  else localStorage.removeItem(PENDING_KEY);
}

/** The help a draft already holds. The phone adds none; it carries a desktop's (§6.5, Codex review F1). */
export interface DraftAssist {
  /** The answer box's authored reveals, as the checkpoint counts them: no book in here. */
  readonly hintsUsed: number;
  /** The original page was opened: one hint-equivalent, the book. */
  readonly pageSeen: boolean;
  readonly hintSeen: boolean;
  readonly firstHintProgress: FirstHintProgress | null;
  readonly planPresentationId: string | null;
}

export const NO_ASSIST: DraftAssist = { hintsUsed: 0, pageSeen: false, hintSeen: false, firstHintProgress: null, planPresentationId: null };

export function assistOf(checkpoint: SessionCheckpoint): DraftAssist {
  return {
    hintsUsed: checkpoint.hintsUsed ?? 0,
    pageSeen: checkpoint.pageSeen === true,
    hintSeen: checkpoint.hintSeen === true,
    firstHintProgress: checkpoint.firstHintProgress ?? null,
    planPresentationId: checkpoint.planPresentationId ?? null
  };
}

/**
 * What is known of the request last sent under a draft's key. `unknown`: it may have reached the
 * host and nothing said how it ended, so the host is asked before anything else is sent (F2).
 * `failed`: the host said it ended without an attempt. `none`: nothing of it is on the host.
 */
export type SubmitOutcome = "none" | "unknown" | "failed";

/**
 * The question as this phone has it, written on every change, so leaving a screen or closing the app
 * loses nothing (F5), and with the request exactly as it was sent, so a retry after a reopen is the
 * same request and not a conflict with itself (F3). An adoption drops all of them: the checkpoint it
 * read is newer than anything here (F4).
 */
export interface QuestionDraft {
  readonly sessionId: string;
  readonly practiceItemId: string;
  readonly answer: string;
  readonly stuck: boolean;
  readonly submissionId: string;
  readonly schedulerCandidateId: string | null;
  readonly assist: DraftAssist;
  readonly sentInput: SubmitInput | null;
  readonly outcome: SubmitOutcome;
}

const draftId = (sessionId: string, practiceItemId: string) => `${sessionId}:${practiceItemId}`;

function allDrafts(): Record<string, QuestionDraft> {
  return read<Record<string, QuestionDraft>>(DRAFTS_KEY) ?? {};
}

function writeDrafts(drafts: Record<string, QuestionDraft>): void {
  try {
    localStorage.setItem(DRAFTS_KEY, JSON.stringify(drafts));
  } catch {
    // Storage full or refused: the checkpoint still has what was saved to it.
  }
}

export function readQuestionDraft(sessionId: string, practiceItemId: string): QuestionDraft | null {
  return allDrafts()[draftId(sessionId, practiceItemId)] ?? null;
}

export function writeQuestionDraft(draft: QuestionDraft): void {
  writeDrafts({ ...allDrafts(), [draftId(draft.sessionId, draft.practiceItemId)]: draft });
}

export function clearQuestionDraft(sessionId: string, practiceItemId: string): void {
  const { [draftId(sessionId, practiceItemId)]: _gone, ...rest } = allDrafts();
  writeDrafts(rest);
}

export function clearQuestionDrafts(): void {
  localStorage.removeItem(DRAFTS_KEY);
}

export function clearSessionCache(): void {
  localStorage.removeItem(SESSION_KEY);
  localStorage.removeItem(PENDING_KEY);
  localStorage.removeItem(DRAFTS_KEY);
}
