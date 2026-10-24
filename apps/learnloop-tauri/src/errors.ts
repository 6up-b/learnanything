import type { CommandError } from "./api/dto";

const DEFAULT_ERROR_MESSAGE = "Something went wrong. Please try again.";

/** The two kinds of shell message (UX Phase 2, docs/specs/ux_learnloop_v1.md
 *  §7.9): an error (red, persists, Try again when retryable) or a notice
 *  (neutral, small, gone after a few seconds). See app/notices.ts. */
export type MessageKind = "error" | "notice";

/** What a screen may hand the shell beside an error's sentence (UX Phase 2,
 *  Codex review F3): the rejection itself, so the shell can show its code and
 *  read `retryable`, and how to run the failed action again. The shell offers
 *  Try again only when both are there and the error is retryable. A retry
 *  must repeat the same action: a read reads again; a write passes the
 *  original request's idempotency key again.
 *
 *  Fix round 3 (whole-stage verify 20261021-130232-Uk06Al) makes this
 *  structural. An error that carries a retry has a `source`: its identity in
 *  the queue, the only thing errors are de-duplicated by (never their text,
 *  which the bridge shares between unrelated failures). The retry is
 *  self-contained: it runs the failed action itself (for a read, a forced
 *  fetch of the failed query's key, whatever the screen shows now or whether
 *  it is mounted; `useCachedQuery`'s `retryReport`). It resolves `RETRY_RAN`
 *  only when a request ran and succeeded. Anything else (a no-op, a skipped
 *  or disabled read, a plain `undefined`) counts as a failure and keeps the
 *  error. The shell runs it and reports a second failure itself. */
export interface RetryRan {
  readonly ran: true;
}

/** The one value a retry resolves with when its request ran and succeeded. */
export const RETRY_RAN: RetryRan = Object.freeze({ ran: true as const });

export type NoticeRetry = () => Promise<RetryRan>;

export function retryRan(value: unknown): value is RetryRan {
  return value === RETRY_RAN;
}

export type ErrorReport =
  | { error?: unknown; retry?: null; source?: string | null }
  | { error?: unknown; retry: NoticeRetry; source: string };

/** A screen's error callback. Screens that pass only the sentence still fit. */
export type ReportError = (message: string, report?: ErrorReport) => void;

/**
 * Narrow an unknown rejection to the stable error envelope returned by the
 * Tauri bridge. Calls made outside that bridge (dialogs, events, browser APIs)
 * can still reject with strings or ordinary Error instances, so callers must
 * not cast every rejection to CommandError.
 */
export function getCommandError(error: unknown): CommandError | null {
  if (!error || typeof error !== "object") return null;
  const candidate = error as Partial<CommandError>;
  if (typeof candidate.code !== "string" || typeof candidate.message !== "string") return null;
  return {
    code: candidate.code,
    message: candidate.message,
    retryable: candidate.retryable === true,
    ...(candidate.details === undefined ? {} : { details: candidate.details })
  };
}

/** Return non-empty, user-safe copy for any JavaScript rejection shape. */
export function errorMessage(error: unknown, fallback = DEFAULT_ERROR_MESSAGE): string {
  const command = getCommandError(error);
  if (command?.message.trim()) return command.message.trim();
  if (error instanceof Error && error.message.trim()) return error.message.trim();
  if (typeof error === "string" && error.trim()) return error.trim();
  if (error && typeof error === "object" && "message" in error) {
    const message = (error as { message?: unknown }).message;
    if (typeof message === "string" && message.trim()) return message.trim();
  }
  return fallback;
}
