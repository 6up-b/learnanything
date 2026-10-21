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
 *  The retry returns the action's promise (fix round 2): the shell runs it,
 *  keeps the error until it settles, and reports a failure itself, so the
 *  report never depends on the screen still being mounted. `source` names
 *  the failed action (a query), so the screen's and the shell's reports of
 *  one failure are one error, not two. */
export interface ErrorReport {
  error?: unknown;
  retry?: (() => unknown) | null;
  source?: string | null;
}

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
